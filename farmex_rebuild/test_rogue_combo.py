import unittest
from dataclasses import replace
from rogue_combo import ComboState,ComboObservation,plan_rogue_combo
from rogue_alternate_bow import AlternateBowObservation
from rogue_attack import RogueSnapshot,BOW_ROWS
from attack_configuration import RogueAlternateBowRanges

class ComboTests(unittest.TestCase):
    def setUp(self):
        self.o=ComboObservation(locked_byte=0,actor_byte=0,actor_float_ah=0x40,
            byte_562011=1,byte_562012=0,byte_561ffc=0,helper_464564=0,
            actor_state=0,interval_ms=250,clocks={k:1000 for k in
            ('start','wait1','stage3','wait4','after4','wait5','wait6','after6','noncombo6','wait7')},
            helper_completed={k:True for k in ('pattern','reset','first','second')})
        flags={r.flag_offset:False for r in BOW_ROWS};flags.update({0x91:True,0x89:False})
        self.selector=dict(selector_snapshot=RogueSnapshot(1000,5,45,1000,flags,{'00462ddc':100}),
            selector_ranges=RogueAlternateBowRanges(5,5,5),
            selector_observation=AlternateBowObservation(1,0,target_id=99,send_return=1,helper_returns={0x22b:0}))
    def plan(self,state=ComboState(),o=None,**kwargs):
        return plan_rogue_combo(state,o or self.o,**(kwargs or self.selector))
    def test_initial_selection_executes_nested_model_and_captures_category(self):
        p=self.plan()
        self.assertTrue(p.complete);self.assertEqual((p.state.stage,p.state.category,p.state.start_ms),(1,1,1000))
        self.assertIn(('00561f7e',1),p.local_writes)
        self.assertEqual(p.selector.calls[-1],('004655e8',(0x22b,99)))
    def test_send_zero_leaves_stage0_and_retains_lock_plan(self):
        args=dict(self.selector);args['selector_observation']=replace(args['selector_observation'],send_return=0)
        p=self.plan(**args)
        self.assertEqual(p.state,ComboState());self.assertIn(('00561f7e',1),p.local_writes)
        self.assertEqual(p.local_writes[-1],('0056fedc',0))
    def test_lock_and_actor_gate_reset_only_stage(self):
        st=ComboState(7,3,11,12,13,14,9)
        for o,status in ((replace(self.o,locked_byte=255),'reset_locked'),
                         (replace(self.o,actor_byte=1),'reset_actor_gate'),
                         (replace(self.o,actor_float_ah=0),'reset_actor_gate')):
            with self.subTest(status=status):
                p=self.plan(st,o);self.assertEqual(p.status,status)
                self.assertEqual(p.state,replace(st,stage=0));self.assertEqual(p.calls,())
        self.assertEqual(self.plan(ComboState(2),replace(self.o,actor_float_ah=0x45)).status,'unknown_stage_unchanged')
    def test_start_delays_and_dword_wrap(self):
        for raw,delay in ((0,460),(1,650)):
            for elapsed,stage in ((delay-1,1),(delay,3)):
                o=replace(self.o,helper_464564=raw,clocks={'wait1':elapsed-1})
                self.assertEqual(self.plan(ComboState(1,start_ms=0xffffffff),o).state.stage,stage)
        p=self.plan(ComboState(1),replace(self.o,byte_562011=0,byte_562012=0,clocks={'wait1':0}))
        self.assertEqual(p.state.stage,3);self.assertNotIn(('00464564',()),p.calls)
    def test_stage3_plain_skip_and_ordinary_pattern_arguments(self):
        p=self.plan(ComboState(3),replace(self.o,byte_562011=0,byte_562012=0))
        self.assertEqual((p.state.stage,p.calls),(6,()))
        p=self.plan(ComboState(3,category=3),replace(self.o,byte_561ffc=1))
        self.assertEqual(p.calls,(('00465f30',(2,)),('00465f30',(0,))))
        self.assertEqual(p.state.stage,6)
    def test_stage3_second_switch_distance_status_parity(self):
        for ah,arg in ((1,2),(0,1),(0x40,1),(0x45,1)):
            p=self.plan(ComboState(3),replace(self.o,byte_562011=0,byte_562012=1,distance_vs_one_ah=ah))
            self.assertEqual(p.calls,(('00465f30',(arg,)),));self.assertEqual(p.state.stage,4)
    def test_both_switches_alternate_and_reset_only_at10(self):
        for old,counter,arg in ((0,1,2),(1,2,1),(9,0,1),(10,11,2),(0xffffffff,0,1)):
            p=self.plan(ComboState(3,pattern_counter=old),replace(self.o,byte_562012=1))
            self.assertEqual((p.state.pattern_counter,p.calls[-1][1]),(counter,(arg,)))
    def test_five_millisecond_steps_have_separate_fresh_clocks(self):
        for delta,stage in ((4,4),(5,5)):
            p=self.plan(ComboState(4,first_ms=1000),replace(self.o,clocks={'wait4':1000+delta,'after4':2000}))
            self.assertEqual(p.state.stage,stage)
            if stage==5:self.assertEqual(p.state.second_ms,2000)
        for delta,stage in ((4,5),(5,6)):
            p=self.plan(ComboState(5,second_ms=2000),replace(self.o,clocks={'wait5':2000+delta}))
            self.assertEqual(p.state.stage,stage)
    def test_switch_off_skips_five_ms_and_actor6_holds_stage6(self):
        off=replace(self.o,byte_562011=0,byte_562012=0,clocks={})
        self.assertEqual(self.plan(ComboState(4),off).state.stage,5)
        self.assertEqual(self.plan(ComboState(5),off).state.stage,6)
        self.assertEqual(self.plan(ComboState(6),replace(off,actor_state=6)).status,'wait_actor_state')
        p=self.plan(ComboState(6),replace(off,clocks={'noncombo6':33}))
        self.assertEqual((p.state.stage,p.state.end_ms),(7,33))
    def test_reselection_is_query_only_and_1000ms_uses_initial_clock(self):
        for now,stage in ((1999,6),(2000,7)):
            p=self.plan(ComboState(6,category=1,start_ms=1000),replace(self.o,clocks={'wait6':now,'after6':2010}))
            self.assertEqual(p.state.stage,stage)
            self.assertEqual(p.selector.local_writes,())
            self.assertNotIn('004655e8',[a for a,args in p.selector.calls])
            if stage==7:self.assertEqual(p.state.end_ms,2010)
    def test_reselection_category3_1280ms_other100ms(self):
        for flags,category,delay in (({0x84:True},3,1280),({},0,100)):
            s=self.selector['selector_snapshot'];allflags={key:False for key in s.flags};allflags.update(flags)
            args=dict(self.selector);args['selector_snapshot']=replace(s,flags=allflags,raw_stats={'00462670':100})
            for elapsed,stage in ((delay-1,6),(delay,7)):
                p=self.plan(ComboState(6,category=1,start_ms=0),replace(self.o,clocks={'wait6':elapsed,'after6':elapsed}),**args)
                self.assertEqual(p.selector.source_return,category);self.assertEqual(p.state.stage,stage)
    def test_finish_interval_retains_other_fields(self):
        st=ComboState(7,2,1,2,3,1000,9)
        self.assertEqual(self.plan(st,replace(self.o,clocks={'wait7':1249})).status,'wait_interval')
        self.assertEqual(self.plan(st,replace(self.o,clocks={'wait7':1250})).state,replace(st,stage=0))
    def test_unknown_clock_and_helper_keep_only_prospective_prefix(self):
        p=self.plan(o=replace(self.o,clocks={}))
        self.assertFalse(p.complete);self.assertEqual(p.state.category,1);self.assertEqual(p.state.stage,0)
        p=self.plan(ComboState(3,pattern_counter=9),replace(self.o,byte_562012=1,helper_completed={}))
        self.assertFalse(p.complete);self.assertEqual(p.state.pattern_counter,0);self.assertEqual(p.state.stage,3)
    def test_unknown_stage_and_invalid_types(self):
        self.assertEqual(self.plan(ComboState(2)).state.stage,2)
        for value in (True,-1,0x100000000):
            with self.assertRaises(ValueError):ComboState(stage=value)
        with self.assertRaises(ValueError):ComboObservation(actor_float_ah=True)
