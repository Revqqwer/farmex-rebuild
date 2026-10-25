import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_gate import RelogGateFrame,RelogGateSelectionsFrame,RelogGateSelectionsObservation
from relog_selection import RelogSelectionFrame,RelogControllerSelectionsObservation
import test_relog_selection as selector_fixture


def sample(**extra):
    v=dict(sleep_enabled_byte=0,sleep_delay=7,header_slot=0x1000,header_root_eax=0x2000,
      header_base_offset=0x10,header_base_eax=0x3000,first_object_offset=0x20,first_object_eax=0x4000,
      middle_object_offset=0x30,middle_object_eax=0x5000,last_object_offset=0x40,last_object_eax=0x6000,
      initial_state_offset=1,initial_state_eax=1,install_attempted_byte=1,install_probe_eax=0,
      install_probe_local=91,install_root_slot=0x100,install_root_eax=0x200,install_context_offset=0x10,
      install_context_eax=0x300,install_table_eax=0xfffffff0,install_slot_offset=0x30,
      install_slot_fresh=0x7777,actor_slot=0x400,actor_root_eax=0x500,actor_state_offset=0x20,
      actor_state_eax=0,actor_once_done_byte=1,gate_enabled_byte=0,gate_pending_byte=0,
      idle_phase_first_offset=2,idle_phase_first_eax=0,idle_phase_second_offset=3,idle_phase_second_eax=0,
      active_phase_offset=4,active_phase_eax=5,candidate_slot_first=0x100,candidate_first_eax=8,saved_first=8,
      candidate_slot_second=0x200,candidate_second_eax=1,saved_second=2,
      active_fallback_first_offset=5,active_fallback_first_eax=0,active_fallback_second_offset=6,
      active_fallback_second_eax=0,active_fallback_third_offset=7,active_fallback_third_eax=0,
      original_slot=0x700,original_root=0x800,original_offset=0x30,original_object=0x900,
      original_target=0xa00,original_eax=0xcafebabe)
    v.update(extra)
    labels=('prologue','sleep','header_root','header_base','first_object','middle_object','last_object',
      'initial_state','install_probe','install_root','install_context','install_table','install_replace',
      'actor_root','actor_state','actor_once','idle_phase_first','idle_phase_second','active_phase',
      'candidate_first','candidate_second','active_fallback_first','active_fallback_second',
      'active_fallback_third','gate_select','gate_advance','original','epilogue')
    return JailObservation(True,v,{n:True for n in labels})


class RelogGateTests(unittest.TestCase):
    def test_header_zero_test_follows_all_object_and_initial_byte_calls(self):
        p=RelogGateFrame().advance(sample(header_base_eax=0))
        self.assertTrue(p.complete)
        self.assertIn('initial_state',[c[2] for c in p.calls])
        self.assertNotIn('install_attempted_byte',[r[2] for r in p.reads])
        self.assertEqual(p.calls[-2][2],'original')

    def test_sleep_and_entry_are_explicit(self):
        f=RelogGateFrame();p=f.advance(replace(sample(),entry_reached=False))
        self.assertEqual(p.needed,('entry','00412874'))
        p=f.advance(sample(sleep_enabled_byte=1))
        self.assertIn(('SleepEx',(0,7),'sleep'),p.calls)

    def test_install_probe_low_al_and_signed90_boundary_only_mark_attempt(self):
        for al,value,replaced in ((0,90,False),(0,91,True),(0,0xffffffff,False),(0x101,91,False)):
            p=RelogGateFrame().advance(sample(install_attempted_byte=0,install_probe_eax=al,install_probe_local=value))
            self.assertTrue(p.complete)
            self.assertEqual(any(c[2]=='install_replace' for c in p.calls),replaced)
            self.assertIn((0x553c84,1,1),p.stores)

    def test_install_slot_store_precedes_fresh_reload_and_attempt_flag_waits_for_helper(self):
        f=RelogGateFrame();o=sample(install_attempted_byte=0);n=dict(o.normal_returns);n['install_replace']=False
        p=f.advance(replace(o,normal_returns=n))
        self.assertEqual(p.needed,('normal','install_replace'))
        self.assertEqual(p.stores,((0x554218,4,0x20),))
        self.assertEqual(p.calls[-1],('0046b8fc',(0x46f520,0x7777,0x554228),'install_replace'))
        p=f.advance(o);self.assertIn((0x553c84,1,1),p.stores)

    def test_actor_nonzero_al_one_time_helper_exits_before_phase_work(self):
        for eax,called in ((0x100,False),(2,True),(0x1ff,True)):
            p=RelogGateFrame().advance(sample(actor_state_eax=eax,actor_once_done_byte=0))
            self.assertEqual(any(c[2]=='actor_once' for c in p.calls),called)
            self.assertEqual((0x553c85,1,1) in p.stores,called)
            if called:self.assertNotIn('gate_enabled_byte',[r[2] for r in p.reads])

    def test_initial_saved_al_must_equal_one(self):
        p=RelogGateFrame().advance(sample(initial_state_eax=2,gate_enabled_byte=1))
        self.assertNotIn('active_phase_offset',[r[2] for r in p.reads])

    def test_idle_only_one_or_two_fresh_phases_advance_not_four(self):
        for first,second,expected in ((1,0,True),(0,2,True),(0,4,False),(0x101,0,True)):
            p=RelogGateFrame().advance(sample(idle_phase_first_eax=first,idle_phase_second_eax=second))
            self.assertEqual(any(c[2]=='gate_advance' for c in p.calls),expected)
            if first&255==1:self.assertNotIn('idle_phase_second_offset',[r[2] for r in p.reads])

    def test_enabled_or_pending_short_circuit_and_equal_candidate_select_first_object(self):
        p=RelogGateFrame().advance(sample(gate_enabled_byte=1))
        self.assertIn(('00412828',(0x4000,),'gate_select'),p.calls)
        self.assertNotIn('gate_pending_byte',[r[2] for r in p.reads])
        self.assertNotIn('candidate_slot_second',[r[2] for r in p.reads])
        p=RelogGateFrame().advance(sample(gate_pending_byte=1))
        self.assertIn('gate_select',[c[2] for c in p.calls])

    def test_second_candidate_and_saved_value_are_fresh_unsigned_less_than(self):
        p=RelogGateFrame().advance(sample(gate_enabled_byte=1,candidate_first_eax=9,
            saved_first=8,candidate_second_eax=0x80000000,saved_second=0xffffffff))
        self.assertIn(('00412828',(0x6000,),'gate_select'),p.calls)
        self.assertEqual([r[0] for r in p.reads if r[2] in ('saved_first','saved_second')],[0x50b2d4]*2)

    def test_active_fallback_fresh_one_two_four_and_short_circuits(self):
        for first,second,third,expected in ((1,0,0,True),(0,2,0,True),(0,0,4,True),(0,0,3,False)):
            p=RelogGateFrame().advance(sample(gate_enabled_byte=1,active_phase_eax=0,
                active_fallback_first_eax=first,active_fallback_second_eax=second,active_fallback_third_eax=third))
            self.assertEqual(any(c[2]=='gate_advance' for c in p.calls),expected)
            if first==1:self.assertNotIn('active_fallback_second_offset',[r[2] for r in p.reads])

    def test_failed_second_comparison_falls_through_to_active_phase_checks(self):
        p=RelogGateFrame().advance(sample(gate_enabled_byte=1,candidate_first_eax=9,saved_first=8,
            candidate_second_eax=8,saved_second=7,active_fallback_third_eax=4))
        self.assertNotIn('gate_select',[c[2] for c in p.calls])
        self.assertIn('gate_advance',[c[2] for c in p.calls])

    def test_original_fresh_direct_chain_and_full_eax_return(self):
        f=RelogGateFrame();o=sample(original_root=0xfffffff0,original_offset=0x30)
        n=dict(o.normal_returns);n['epilogue']=False;p=f.advance(replace(o,normal_returns=n))
        self.assertEqual(p.needed,('normal','epilogue'))
        self.assertIn((0x20,4,'original_object'),p.reads)
        self.assertIn((0x554224,4,'original_target'),p.reads)
        self.assertEqual(p.return_eax,0xcafebabe)
        p=f.advance(JailObservation(normal_returns={'epilogue':True}));self.assertTrue(p.complete)
        self.assertFalse(p.whole_function_verified or p.native_execution_verified)


class RelogGateWrapperTests(unittest.TestCase):
    def test_ui_select_uses_second_root_family_and_virtual_argument_one_object(self):
        p=RelogSelectionFrame('ui_select',argument=0x4444).advance(selector_fixture.child())
        self.assertTrue(p.complete)
        self.assertIn((0x553f64,4,'direct_slot'),p.reads)
        self.assertIn((0x5541e4,4,'direct_base_offset'),p.reads)
        self.assertEqual(p.calls[-2][1][-1],('physical_pushes',(1,0x4444)))

    def test_ui_advance_uses_root_itself_no_object_offset_no_argument(self):
        p=RelogSelectionFrame('ui_advance').advance(selector_fixture.child())
        self.assertTrue(p.complete)
        self.assertNotIn('direct_base_offset',[r[2] for r in p.reads])
        self.assertIn((0x553f74,4,'direct_target'),p.reads)
        self.assertEqual(p.calls[-2][1],(('ECX',0x6000),('target',0x8000),('physical_pushes',())))

    def test_bound_gate_select_derives_argument_and_child_entry(self):
        o=RelogGateSelectionsObservation(sample(gate_enabled_byte=1),{'gate_select':selector_fixture.child()})
        p=RelogGateSelectionsFrame().advance(o)
        self.assertTrue(p.complete)
        self.assertEqual(p.children['gate_select'].argument,0x4000)

    def test_child_and_outer_gate_returns_remain_separate(self):
        f=RelogGateSelectionsFrame();parent=sample(gate_enabled_byte=1)
        n=dict(parent.normal_returns);n['gate_select']=False
        p=f.advance(RelogGateSelectionsObservation(replace(parent,normal_returns=n),{'gate_select':selector_fixture.child()}))
        self.assertEqual(p.needed,('parent',('normal','gate_select')))
        self.assertTrue(p.children['gate_select'].complete)
        p=f.advance(RelogGateSelectionsObservation(parent))
        self.assertTrue(p.complete)

    def test_gate_advance_missing_child_cannot_be_skipped_by_parent_receipt(self):
        f=RelogGateSelectionsFrame();o=RelogGateSelectionsObservation(sample(idle_phase_first_eax=1),{'gate_advance':JailObservation()})
        p=f.advance(o);self.assertEqual(p.needed,('child','gate_advance',('normal','prologue')))
        p=f.advance(RelogGateSelectionsObservation(o.parent));self.assertFalse(p.complete)
        self.assertIsNotNone(p.children['gate_advance'])

    def test_gate_frame_and_observation_reject_mixed_controller_labels(self):
        with self.assertRaises(ValueError):RelogGateSelectionsObservation(children={'select_first':JailObservation()})
        with self.assertRaises(ValueError):RelogGateSelectionsFrame().advance(RelogControllerSelectionsObservation())
        with self.assertRaises(ValueError):RelogSelectionFrame('ui_select')


if __name__=='__main__':unittest.main()
