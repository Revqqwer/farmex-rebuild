import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_controller import RelogControllerFrame


HEADER_LABELS=('base_root','base_value','alternate_root','alternate_value',
    'first_input_root','first_input','second_input_root','second_input',
    'prepare_object','unused_object','advance_object','advance_alt_object','selection_object')
RETURNS=('prologue','sleep','watchdog_tick','watchdog')+HEADER_LABELS+(
    'prepare_ui','prepare_tick','prepare_post_tick','prepare_inputs','advance_ui','advance_alt_ui',
    'advance','bootstrap_probe','bootstrap_replace','alternate_ui','alternate_prepare','alternate_tick',
    'alternate_action','alternate_first','alternate_second','alternate_post_tick','select_ui',
    'first_selection','select_first','first_selection_fresh','second_selection','select_second',
    'second_selection_fresh','confirm_tick','confirm_root','confirm_state','confirm','confirm_post_tick',
    'original','epilogue')


def sample(**extra):
    # Synthetic raw results only; not values read from a running game.
    v=dict(sleep_enabled_byte=0,sleep_delay=0xffffffff,watchdog_first_byte=0,
        watchdog_second_byte=1,watchdog_third_byte=1,watchdog_tick_eax=5000,watchdog_low=0,watchdog_high=0,
        base_slot=0x1000,base_root_eax=0x2000,base_value_offset=0x10,base_value_eax=0x3000,
        alternate_slot=0x4000,alternate_root_eax=0x5000,alternate_offset=0x20,alternate_value_eax=0x6000,
        first_input_root_eax=0x7000,first_input_offset=0x30,first_input_eax=0x8000,
        second_input_root_eax=0x9000,second_input_offset=0x40,second_input_eax=0xa000,
        prepare_ui_offset=1,prepare_ui_eax=0,prepare_enabled_byte=1,prepare_pending_byte=1,
        prepare_tick_eax=5000,prepare_low=0,prepare_high=0,prepare_post_tick_eax=5010,prepare_mode_byte=1,
        advance_ui_offset=2,advance_ui_eax=0,advance_alt_ui_offset=3,advance_alt_ui_eax=0,
        advance_enabled_byte=1,advance_pending_byte=1,bootstrap_done_byte=1,
        bootstrap_probe_eax=0,bootstrap_local_dword=91,bootstrap_target=0x111,
        alternate_ui_offset=4,alternate_ui_eax=0,alternate_ready_first_byte=1,
        alternate_mode_byte=1,alternate_enabled_byte=1,alternate_ready_second_byte=1,
        alternate_tick_eax=5000,alternate_low=0,alternate_high=0,
        alternate_post_tick_eax=5020,alternate_counter=0xffffffff,
        select_enabled_byte=0,select_pending_byte=0,select_ui_offset=5,select_ui_eax=1,
        first_selection_offset=6,first_selection_eax=1,first_desired=0xffffffff,
        first_selection_fresh_offset=7,first_selection_fresh_eax=1,
        second_selection_offset=8,second_selection_eax=3,second_desired_compare=3,
        second_desired_push=4,second_selection_fresh_offset=9,second_selection_fresh_eax=3,
        second_desired_fresh=3,confirm_tick_eax=30000,confirm_low=0,confirm_high=0,
        confirm_root_slot=0x120,confirm_root_eax=0x130,confirm_state_offset=0x10,
        confirm_state_eax=0,confirm_post_tick_eax=30010,
        original_slot=0x200,original_root=0x300,original_offset=0x40,
        original_object=0x500,original_target=0x600,original_eax=0xdeadbeef)
    for i,label in enumerate(('prepare','unused','advance','advance_alt','selection')):
        v[label+'_object_offset']=0x100+i*4
        v[label+'_object_eax']=0xb000+i*0x100
    v.update(extra)
    return JailObservation(True,v,{n:True for n in RETURNS})


class RelogControllerTests(unittest.TestCase):
    def test_explicit_entry_and_prologue_then_source_header_calls(self):
        f=RelogControllerFrame()
        p=f.advance(replace(sample(),entry_reached=False))
        self.assertEqual(p.needed,('entry','00412adc'))
        p=f.advance(JailObservation(True))
        self.assertEqual(p.needed,('normal','prologue'))
        self.assertEqual(p.reads,())
        p=f.advance(sample())
        self.assertTrue(p.complete)
        self.assertEqual([c[2] for c in p.calls[1:14]],list(HEADER_LABELS))

    def test_sleep_ex_captured_delay_and_physical_push_order(self):
        f=RelogControllerFrame();o=sample(sleep_enabled_byte=2)
        p=f.advance(replace(o,normal_returns={'prologue':True}))
        self.assertEqual(p.needed,('normal','sleep'))
        self.assertEqual(p.calls[-1],('SleepEx',(0,0xffffffff),'sleep'))
        self.assertNotIn('base_slot',[r[2] for r in p.reads])

    def test_watchdog_gate_short_circuit_and_signed5000_boundary(self):
        for now,high,expected in ((4999,0,False),(5000,0,True),(0,1,False)):
            p=RelogControllerFrame().advance(sample(watchdog_first_byte=1,watchdog_tick_eax=now,watchdog_high=high))
            self.assertEqual(any(c[2]=='watchdog' for c in p.calls),expected)
        p=RelogControllerFrame().advance(sample())
        self.assertNotIn('watchdog_second_byte',[r[2] for r in p.reads])

    def test_all_header_reads_even_unused_complete_before_first_ui_branch(self):
        f=RelogControllerFrame();o=sample();v=dict(o.values);del v['unused_object_eax']
        p=f.advance(replace(o,values=v))
        self.assertEqual(p.needed,('value','unused_object_eax'))
        self.assertNotIn('prepare_ui_offset',[r[2] for r in p.reads])

    def test_fresh_roots_offsets_and_extra_base_dereferences_are_preserved(self):
        p=RelogControllerFrame().advance(sample())
        calls={c[2]:c for c in p.calls}
        self.assertEqual(calls['base_value'][1],(0x2010,))
        self.assertEqual(calls['alternate_value'][1],(0x5028,))
        self.assertEqual(calls['first_input_root'][1],(0x3000,))
        self.assertEqual(calls['first_input'][1],(0x7030,))
        self.assertEqual(dict(p.captured_locals)['second_input'],0xa000)

    def test_prepare_exact_al_one_and_timestamp_precedes_mode_action(self):
        p=RelogControllerFrame().advance(sample(prepare_ui_eax=2))
        self.assertFalse(any(c[2]=='prepare_tick' for c in p.calls))
        f=RelogControllerFrame();o=sample(prepare_ui_eax=0x101)
        p=f.advance(replace(o,normal_returns={k:v for k,v in o.normal_returns.items() if k!='prepare_inputs'}))
        self.assertEqual(p.needed,('normal','prepare_inputs'))
        self.assertEqual(p.stores,((0x553c6c,4,5010),(0x553c70,4,0)))
        self.assertNotIn('prepare_pending_byte',[r[2] for r in p.reads])

    def test_prepare_pending_and_mode_are_separate_fresh_byte_observations(self):
        p=RelogControllerFrame().advance(sample(prepare_ui_eax=1,prepare_enabled_byte=0,
            prepare_pending_byte=1,prepare_mode_byte=2))
        self.assertIn('prepare_pending_byte',[r[2] for r in p.reads])
        self.assertEqual(len(p.stores),2)
        self.assertFalse(any(c[2]=='prepare_inputs' for c in p.calls))

    def test_advance_or_short_circuit_skips_alternate_ui_when_first_is_one(self):
        p=RelogControllerFrame().advance(sample(advance_ui_eax=1))
        self.assertIn('advance',[c[2] for c in p.calls])
        self.assertNotIn('advance_alt_ui_offset',[r[2] for r in p.reads])
        p=RelogControllerFrame().advance(sample(advance_ui_eax=0x100,advance_alt_ui_eax=0x101,
            advance_enabled_byte=0,advance_pending_byte=1))
        self.assertIn('advance',[c[2] for c in p.calls])

    def test_bootstrap_probe_low_al_nonzero_skips_unneeded_local_capture(self):
        o=sample(bootstrap_done_byte=0,bootstrap_probe_eax=0x101)
        v=dict(o.values);del v['bootstrap_local_dword']
        p=RelogControllerFrame().advance(replace(o,values=v))
        self.assertTrue(p.complete)
        self.assertEqual(p.stores,((0x553c8c,1,1),))
        self.assertNotIn('alternate_ui_offset',[r[2] for r in p.reads])

    def test_bootstrap_signed90_boundary_and_original_callback_always_reached(self):
        for value,replace_expected in ((90,False),(91,True),(0xffffffff,False)):
            p=RelogControllerFrame().advance(sample(bootstrap_done_byte=0,bootstrap_local_dword=value))
            self.assertTrue(p.complete)
            self.assertEqual(any(c[2]=='bootstrap_replace' for c in p.calls),replace_expected)
            self.assertEqual(p.calls[-2][2],'original')

    def test_bootstrap_flag_store_waits_for_replacement_normal(self):
        o=sample(bootstrap_done_byte=0);n=dict(o.normal_returns);n['bootstrap_replace']=False
        p=RelogControllerFrame().advance(replace(o,normal_returns=n))
        self.assertEqual(p.needed,('normal','bootstrap_replace'))
        self.assertEqual(p.stores,())
        self.assertEqual(p.calls[-1],('0046b8fc',(0x412874,0x111,0x554224),'bootstrap_replace'))

    def test_alternate_prepare_clear_survives_gap_and_ready_is_reloaded(self):
        f=RelogControllerFrame();o=sample(alternate_ui_eax=1,alternate_ready_first_byte=0)
        n=dict(o.normal_returns);n['alternate_prepare']=False
        p=f.advance(replace(o,normal_returns=n))
        self.assertEqual(p.stores,((0x553c88,4,0),))
        self.assertEqual(p.needed,('normal','alternate_prepare'))
        p=f.advance(o)
        self.assertIn('alternate_ready_second_byte',[r[2] for r in p.reads])
        self.assertEqual(p.stores[-1],(0x553c88,4,0)) # freshFFFFFFFF increment, not assumed previous0.

    def test_alternate_three_helpers_post_tick_then_fresh_counter_increment(self):
        p=RelogControllerFrame().advance(sample(alternate_ui_eax=1,alternate_counter=9))
        labels=[c[2] for c in p.calls]
        i=labels.index('alternate_action')
        self.assertEqual(labels[i:i+4],['alternate_action','alternate_first','alternate_second','alternate_post_tick'])
        self.assertEqual(p.stores,((0x553c74,4,5020),(0x553c78,4,0),(0x553c88,4,10)))

    def test_select_disabled_short_circuits_all_selection_reads(self):
        p=RelogControllerFrame().advance(sample())
        self.assertNotIn('select_ui_offset',[r[2] for r in p.reads])
        self.assertIn('select_pending_byte',[r[2] for r in p.reads])

    def test_first_selection_zero_calls_selector_then_requires_fresh_nonzero(self):
        p=RelogControllerFrame().advance(sample(select_enabled_byte=1,first_selection_eax=0,
                                               first_selection_fresh_eax=0))
        self.assertIn(('0041272c',(0xffffffff,),'select_first'),p.calls)
        self.assertNotIn('second_selection_offset',[r[2] for r in p.reads])

    def test_desired_second_value_reloads_for_compare_push_and_fresh_compare(self):
        p=RelogControllerFrame().advance(sample(select_enabled_byte=1,second_selection_eax=2,
            second_desired_compare=3,second_desired_push=4,second_selection_fresh_eax=5,
            second_desired_fresh=5))
        self.assertIn(('0041279c',(4,),'select_second'),p.calls)
        self.assertIn('confirm_tick',[c[2] for c in p.calls])
        self.assertEqual([r[0] for r in p.reads if r[2].startswith('second_desired')],[0x50b2d0]*3)

    def test_second_fresh_mismatch_skips_confirmation_even_after_selector_return(self):
        p=RelogControllerFrame().advance(sample(select_enabled_byte=1,second_selection_eax=2,
            second_selection_fresh_eax=5,second_desired_fresh=6))
        self.assertIn('select_second',[c[2] for c in p.calls])
        self.assertNotIn('confirm_tick',[c[2] for c in p.calls])

    def test_confirm_exact30000_signed_delta_and_low_al_one_gate(self):
        for tick,high,state,expected in ((29999,0,0,False),(30000,0,0,True),
                (0,1,0,False),(30000,0,0x101,False),(30000,0,2,True)):
            p=RelogControllerFrame().advance(sample(select_enabled_byte=1,
                confirm_tick_eax=tick,confirm_high=high,confirm_state_eax=state))
            self.assertEqual(any(c[2]=='confirm' for c in p.calls),expected)
            self.assertEqual(any(s[0]==0x553c7c for s in p.stores),expected)

    def test_original_uses_fresh_direct_chain_wrapping_address_and_full_return(self):
        p=RelogControllerFrame().advance(sample(original_root=0xfffffffe,original_offset=5,
                                                original_object=0x777,original_target=0))
        self.assertTrue(p.complete)
        self.assertIn((3,4,'original_object'),p.reads)
        self.assertEqual(p.calls[-2],('captured_original_callback',
                         (('EAX',0),('ECX',0x777),('stack_args',())),'original'))
        self.assertEqual(p.return_eax,0xdeadbeef)
        self.assertFalse(p.whole_function_verified or p.native_execution_verified or p.live_compatibility_verified)

    def test_original_normal_value_and_epilogue_receipts_are_distinct(self):
        f=RelogControllerFrame();o=sample();v=dict(o.values);del v['original_eax']
        p=f.advance(replace(o,values=v));self.assertEqual(p.needed,('value','original_eax'))
        p=f.advance(JailObservation(values={'original_eax':0xffffffff}))
        self.assertEqual(p.needed,('normal','epilogue'))
        self.assertEqual(p.return_eax,0xffffffff)
        p=f.advance(JailObservation(normal_returns={'epilogue':True}))
        self.assertTrue(p.complete)
        self.assertIs(f.advance(JailObservation()),p)

    def test_no_native_or_credential_operations_and_raw_validation(self):
        p=RelogControllerFrame().advance(sample())
        self.assertEqual(p.external_actions_executed,0)
        with self.assertRaises(ValueError):RelogControllerFrame().advance({})
        with self.assertRaises(ValueError):JailObservation(True,{'sleep_enabled_byte':256})


if __name__=='__main__':unittest.main()
