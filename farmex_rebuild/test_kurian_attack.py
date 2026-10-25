import unittest
from dataclasses import replace
from rogue_attack import RogueSnapshot
from kurian_attack import *

def attack(**kw):
    args=dict(now_ms=1000,distance=5,configured_range=20,mp=1000,locked_561f7e=False,
       flags={r.flag_offset:False for r in KURIAN_ATTACK_ROWS+KURIAN_SPECIAL_ROWS},
       raw_stats={'00462ddc':100,'00462e34':100,'00462670':100,'preparation.3c_dword':0},
       helper_bools={**{'00464490:%x'%r.skill_number:False for r in KURIAN_ATTACK_ROWS+KURIAN_SPECIAL_ROWS},**{'004655e8:%x'%r.skill_number:True for r in KURIAN_ATTACK_ROWS+KURIAN_SPECIAL_ROWS}})
    args.update(kw);return RogueSnapshot(**args)

def enabled(s,flag):return replace(s,flags={**s.flags,flag:True})
def cycle(**kw):
    args=dict(now_ms=1000,distance=1,configured_range=20,locked_561f7e=False,enabled_561fcc=True,mode_562011=False,mode_562012=False,attack_return_al=1,target_462630=99);args.update(kw);return KurianCycleSnapshot(**args)

class KurianTests(unittest.TestCase):
    def test_all_23_attack_candidate_thresholds(self):
        for row in KURIAN_ATTACK_ROWS:
            with self.subTest(flag=row.flag_offset):
                s=enabled(attack(mp=row.mp_minimum),row.flag_offset)
                if row.stat_reader:s=replace(s,raw_stats={**s.raw_stats,row.stat_reader:row.stat_minimum})
                d=select_kurian_attack(s);self.assertEqual(d.row,row);self.assertEqual(d.source_return,1)
                self.assertEqual(select_kurian_attack(replace(s,mp=row.mp_minimum-1)).status,'no_eligible_skill')
    def test_all_three_special_candidates(self):
        for row in KURIAN_SPECIAL_ROWS:
            with self.subTest(flag=row.flag_offset):
                s=enabled(attack(mp=row.mp_minimum,distance=32,configured_range=1),row.flag_offset)
                s=replace(s,raw_stats={**s.raw_stats,row.stat_reader:row.stat_minimum})
                d=select_kurian_special(s);self.assertEqual(d.row,row);self.assertEqual(d.local_writes,(('00561f80',2000),('00561f84',1000),('00561f7e',1)))
    def test_priority_late_32_and_helper_absent(self):
        s=enabled(enabled(attack(),3),0x32);self.assertEqual(select_kurian_attack(s).row.flag_offset,3)
        s=enabled(attack(helper_bools={'004655e8:21c':True}),0x32)
        self.assertEqual(select_kurian_attack(s).source_return,1)
    def test_helper_polarity_and_send_result(self):
        s=enabled(attack(),0x3a)
        self.assertEqual(select_kurian_attack(replace(s,helper_bools={**s.helper_bools,'00464490:23c':True})).status,'no_eligible_skill')
        self.assertEqual(select_kurian_attack(replace(s,helper_bools={**s.helper_bools,'004655e8:23c':False})).source_return,0)
        self.assertEqual(select_kurian_attack(replace(s,helper_bools={})).status,'needs_observation')
    def test_range_and_lock(self):
        s=enabled(attack(distance=8),0)
        self.assertEqual(select_kurian_attack(s).source_return,1)
        self.assertEqual(select_kurian_attack(replace(s,distance=8.01)).status,'out_of_range')
        self.assertEqual(select_kurian_attack(replace(s,locked_561f7e=True)).status,'locked')
    def test_special_zero_target_preparation(self):
        s=enabled(attack(),0xda);s=replace(s,raw_stats={**s.raw_stats,'preparation.3c_dword':1,'preparation.target_462630':0})
        self.assertIn(('00465ef8',(0,0)),select_kurian_special(s).calls)
    def test_cycle_zero_stores_raw_al_even_zero(self):
        d=step_kurian_cycle(cycle(attack_return_al=0));self.assertEqual(d.state.phase,1);self.assertEqual(d.state.attack_return_al,0)
        self.assertEqual(step_kurian_cycle(cycle(attack_return_al=None)).status,'needs_observation')
    def test_cycle_phase1_strict_50ms_gate(self):
        st=KurianCycleState(phase=1,attack_return_al=1,start_ms=951)
        self.assertEqual(step_kurian_cycle(cycle(),st).status,'waiting')
        d=step_kurian_cycle(cycle(now_ms=1001),st);self.assertEqual(d.state.phase,2);self.assertEqual(d.calls,(('00462630',()),('00465ef8',(99,1))))
        self.assertEqual(step_kurian_cycle(cycle(),replace(st,attack_return_al=0)).state.phase,2)
    def test_cycle_phase2_200ms_gate_and_mode_shortcircuit(self):
        st=KurianCycleState(phase=2,target_change_ms=801)
        self.assertEqual(step_kurian_cycle(cycle(),st).status,'waiting')
        d=step_kurian_cycle(cycle(now_ms=1001),st);self.assertEqual(d.calls[-1],('00465ef8',(99,0)))
        d=step_kurian_cycle(cycle(now_ms=1001,mode_562011=True,mode_562012=None),st);self.assertEqual(d.state.phase,3)
    def test_cycle_phase3_raw_modes_and_distance_boundary(self):
        st=KurianCycleState(phase=3)
        for dist,value in ((0.99,2),(1,1),(1.01,1)):
            with self.subTest(dist=dist):
                d=step_kurian_cycle(cycle(distance=dist,mode_562012=True),st);self.assertEqual(d.calls,(('00465f30',(value,)),))
        d=step_kurian_cycle(cycle(mode_562011=True),st);self.assertEqual(d.calls,(('00465f30',(1,)),))
    def test_cycle_both_modes_counter_alternates_and_resets_at10(self):
        s=cycle(mode_562011=True,mode_562012=True)
        for counter,expected,next_counter in ((0,2,1),(1,1,2),(9,1,0),(10,2,11),(0xffffffff,1,0)):
            d=step_kurian_cycle(s,KurianCycleState(phase=3,alternate_counter=counter))
            self.assertEqual(d.calls[0],('00465f30',(expected,)));self.assertEqual(d.state.alternate_counter,next_counter)
    def test_cycle_phase4_20ms_gate(self):
        st=KurianCycleState(phase=4,mode_start_ms=981)
        self.assertEqual(step_kurian_cycle(cycle(mode_562011=True),st).status,'waiting')
        d=step_kurian_cycle(cycle(now_ms=1001,mode_562011=True,mode_562012=None),st)
        self.assertEqual(d.calls,(('00465f30',(0,)),));self.assertEqual(d.state.mode_stop_ms,1001)
    def test_cycle_phase5_target_clear_only_enabled(self):
        st=KurianCycleState(phase=5,mode_stop_ms=980)
        d=step_kurian_cycle(cycle(mode_562011=True,enabled_561fcc=False),st)
        self.assertEqual(d.calls,());self.assertEqual(d.state.phase,6)
        d=step_kurian_cycle(cycle(mode_562011=True),st);self.assertEqual(d.calls[-1],('00465ef8',(99,0)))
    def test_cycle_phase6_900ms_gate_and_wrap(self):
        st=KurianCycleState(phase=6,start_ms=101)
        self.assertEqual(step_kurian_cycle(cycle(),st).status,'waiting')
        self.assertEqual(step_kurian_cycle(cycle(now_ms=1001),st).state.phase,0)
        self.assertEqual(step_kurian_cycle(cycle(now_ms=500),replace(st,start_ms=0xfffffe00)).state.phase,0)
    def test_cycle_range_checked_before_lock_reset(self):
        st=KurianCycleState(phase=3)
        self.assertEqual(step_kurian_cycle(cycle(distance=10.1,locked_561f7e=True),st).state.phase,3)
        self.assertEqual(step_kurian_cycle(cycle(distance=10,locked_561f7e=True),st).state.phase,0)
    def test_cycle_no_mode_skips_unneeded_clock_and_helpers(self):
        d=step_kurian_cycle(cycle(target_462630=None),KurianCycleState(phase=4));self.assertEqual(d.state.phase,5)
        d=step_kurian_cycle(cycle(target_462630=None),KurianCycleState(phase=5));self.assertEqual(d.state.phase,6)
    def test_unknowns_failclosed_and_invalid_inputs(self):
        d=step_kurian_cycle(cycle(target_462630=None),KurianCycleState(phase=1));self.assertEqual(d.status,'needs_observation');self.assertEqual(d.state.phase,1)
        with self.assertRaises(ValueError):cycle(attack_return_al=256)
        with self.assertRaises(ValueError):cycle(now_ms=True)

if __name__=='__main__':unittest.main()
