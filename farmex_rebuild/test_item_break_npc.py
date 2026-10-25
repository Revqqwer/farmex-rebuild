import unittest
from item_break_npc import *
from item_break_cycle import ItemBreakClockObservation

def npc(**changes):
    values=dict(mode_dword=0,npc_id_eax=0x12345678,npc_object_eax=0x2000,
        first_offset=0x20,second_offset=0x24,first_coordinate_float_bits=0x41200000,
        second_coordinate_float_bits=0x41a00000,distance_float_bits=0x41200000,
        zero_compare_ax=0,ten_compare_ax=0x4000,selected_npc_eax=0x12345678,select_npc_eax=0xabcdef00)
    normals={key:True for key in ('empty_name_setup','moira_assignment','lookup_argument_setup','npc_lookup',
        'npc_object','first_coordinate','second_coordinate','distance','selected_npc','select_npc',
        'failure_cleanup','success_cleanup')}
    values.update(changes)
    return ItemBreakNpcObservation(True,values,normals)

def update(sample,**changes):return replace(sample,values={**sample.values,**changes})

class ItemBreakNpcTests(unittest.TestCase):
    def test_entry_and_managed_setup_precede_mode_read(self):
        frame=ItemBreakNpcFrame();plan=frame.advance(ItemBreakNpcObservation())
        self.assertEqual(plan.needed,('entry','00470da8'))
        plan=frame.advance(ItemBreakNpcObservation(True,{'mode_dword':0}))
        self.assertEqual(plan.needed,('normal','empty_name_setup'));self.assertEqual(plan.reads,())

    def test_mode_zero_assigns_moira_nonzero_keeps_empty_name(self):
        moira=ItemBreakNpcFrame().advance(npc())
        empty=ItemBreakNpcFrame().advance(npc(mode_dword=1))
        self.assertEqual(moira.lookup_name,b'Moira');self.assertEqual(empty.lookup_name,b'')
        self.assertNotIn('004038e4',[c[0] for c in empty.calls])

    def test_zero_id_skips_object_and_coordinate_reads_and_requires_cleanup(self):
        frame=ItemBreakNpcFrame();sample=npc(npc_id_eax=0)
        plan=frame.advance(replace(sample,normal_returns={**sample.normal_returns,'failure_cleanup':False}))
        self.assertEqual(plan.needed,('normal','failure_cleanup'));self.assertEqual(plan.result_eax,0)
        self.assertEqual(plan.stores,());self.assertNotIn('00464a10',[c[0] for c in plan.calls])
        plan=frame.advance(ItemBreakNpcObservation(normal_returns={'failure_cleanup':True}))
        self.assertEqual(plan.status,'npc_id_zero')

    def test_zero_object_skips_coordinates_and_selection(self):
        plan=ItemBreakNpcFrame().advance(npc(npc_object_eax=0))
        self.assertEqual(plan.status,'npc_object_zero')
        self.assertNotIn('0045ddb8',[c[0] for c in plan.calls]);self.assertEqual(plan.result_eax,0)

    def test_coordinate_addresses_wrap_and_distance_pushes_second_then_first(self):
        plan=ItemBreakNpcFrame().advance(npc(npc_object_eax=0xfffffff0,first_offset=0x20,second_offset=0x24))
        self.assertIn(('0045ddb8',(0x10,),'first_coordinate'),plan.calls)
        self.assertIn(('0045ddb8',(0x14,),'second_coordinate'),plan.calls)
        self.assertIn(('00460548',(0x41a00000,0x41200000),'distance'),plan.calls)

    def test_negative_or_unordered_zero_status_fails_before_ten(self):
        for status in (0x0100,0x4500):
            plan=ItemBreakNpcFrame().advance(npc(zero_compare_ax=status))
            self.assertEqual(plan.status,'distance_zero_compare_rejected')
            self.assertFalse(any(r[2]=='ten_compare_ax' for r in plan.reads))
            self.assertEqual(plan.result_eax,0)

    def test_ten_less_or_equal_pass_but_greater_or_unordered_fail(self):
        for status in (0x0100,0x4000):
            self.assertTrue(ItemBreakNpcFrame().advance(npc(ten_compare_ax=status)).result_eax&255)
        for status in (0,0x4500):
            plan=ItemBreakNpcFrame().advance(npc(ten_compare_ax=status))
            self.assertEqual(plan.status,'distance_ten_compare_rejected')
            self.assertNotIn('00462630',[c[0] for c in plan.calls])

    def test_comparison_low_ax_bits_do_not_change_test_ah_masks(self):
        plan=ItemBreakNpcFrame().advance(npc(zero_compare_ax=0x00ff,ten_compare_ax=0x40ff))
        self.assertEqual(plan.status,'selected_npc_already_matches')

    def test_matching_selected_id_skips_select_preserves_upper_eax_and_stores_id(self):
        plan=ItemBreakNpcFrame().advance(npc())
        self.assertEqual(plan.result_eax,0x12345601)
        self.assertEqual(plan.stores,((0x569a28,4,0x12345678),))
        self.assertNotIn('0046493c',[c[0] for c in plan.calls])

    def test_changed_selection_requires_separate_return_and_raw_register(self):
        sample=npc(selected_npc_eax=5);normals={**sample.normal_returns,'select_npc':False}
        frame=ItemBreakNpcFrame();plan=frame.advance(replace(sample,normal_returns=normals))
        self.assertEqual(plan.needed,('normal','select_npc'));self.assertEqual(plan.stores,())
        plan=frame.advance(ItemBreakNpcObservation(normal_returns={'select_npc':True}))
        self.assertEqual(plan.needed,('value','select_npc_eax'))
        self.assertEqual(plan.stores,((0x569a28,4,0x12345678),))
        plan=frame.advance(ItemBreakNpcObservation(values={'select_npc_eax':0xabcdef00},normal_returns={'success_cleanup':True}))
        self.assertEqual(plan.result_eax,0xabcdef01)
        self.assertIn(('0046493c',(0x2000,),'select_npc'),plan.calls)

    def test_success_cleanup_gap_retains_stores_name_coordinates_and_result(self):
        sample=npc();frame=ItemBreakNpcFrame()
        plan=frame.advance(replace(sample,normal_returns={**sample.normal_returns,'success_cleanup':False}))
        self.assertEqual(plan.needed,('normal','success_cleanup'));self.assertEqual(len(plan.stores),1)
        final=frame.advance(npc(mode_dword=1,npc_id_eax=5,selected_npc_eax=5))
        self.assertEqual(final.stores,plan.stores);self.assertEqual(final.result_eax,plan.result_eax)
        self.assertEqual(final.lookup_name,b'Moira');self.assertIs(frame.advance(ItemBreakNpcObservation()),final)

    def test_distance_fstp_capture_cannot_substitute_comparison_ax(self):
        sample=npc();values=dict(sample.values);del values['zero_compare_ax']
        plan=ItemBreakNpcFrame().advance(replace(sample,values=values))
        self.assertEqual(plan.needed,('value','zero_compare_ax'))
        self.assertEqual(plan.stores,())

    def test_typed_caller_child_requires_cleanup_then_parent_before_clock(self):
        frame=ItemBreakNpcCycleFrame();caller=ItemBreakCycleObservation(True,1,1,0,second_work_byte=1)
        plan=frame.advance(caller,npc_parent_returned=True)
        self.assertEqual(plan.needed,('npc',('entry','00470da8')))
        plan=frame.advance(ItemBreakCycleObservation(),npc())
        self.assertEqual(plan.needed,'npc_parent_returned')
        plan=frame.advance(ItemBreakCycleObservation(),npc_parent_returned=True)
        self.assertEqual(plan.needed,'clock_inputs')
        plan=frame.advance(ItemBreakCycleObservation(clock_inputs=ItemBreakClockObservation(True,1),clock_returned=True))
        self.assertTrue(plan.complete);self.assertEqual(plan.caller.caller.status,'clock_child_returned')

    def test_typed_npc_failure_drives_stop_in_existing_caller(self):
        frame=ItemBreakNpcCycleFrame()
        plan=frame.advance(ItemBreakCycleObservation(True,1,1,0,second_work_byte=1),npc(npc_id_eax=0),npc_parent_returned=True)
        self.assertEqual(plan.needed,'stop_returned')
        plan=frame.advance(ItemBreakCycleObservation(stop_returned=True,npc_notice_span_returned=True))
        self.assertTrue(plan.complete);self.assertEqual(plan.caller.caller.status,'npc_zero_stop_notice_returned')

    def test_disabled_caller_does_not_force_npc_inputs(self):
        plan=ItemBreakNpcCycleFrame().advance(ItemBreakCycleObservation(True,0))
        self.assertTrue(plan.complete);self.assertIsNone(plan.npc)

    def test_raw_parent_overrides_and_width_errors_rejected(self):
        for sample in (ItemBreakCycleObservation(npc_returned=True),ItemBreakCycleObservation(npc_eax=1)):
            with self.assertRaises(ValueError):ItemBreakNpcCycleFrame().advance(sample)
        with self.assertRaises(ValueError):ItemBreakNpcObservation(values={'zero_compare_ax':65536})
        with self.assertRaises(ValueError):ItemBreakNpcObservation(normal_returns={'npc_lookup':1})
        with self.assertRaises(ValueError):ItemBreakNpcObservation(values={'npc_id_eax':True})

if __name__=='__main__':unittest.main()
