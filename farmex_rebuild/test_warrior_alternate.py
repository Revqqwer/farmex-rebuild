import unittest
from dataclasses import replace
from warrior_alternate import *


def support(row=None,**changes):
    flags={r.flag:False for r in SUPPORT_ROWS}
    replies={}
    if row:
        flags[row.flag]=True
        if row.gate_64490:replies[(row.flag,'00464490',row.skill)]=False
        for b in row.buffs:replies[(row.flag,'00464268',b)]=False
        replies[(row.flag,'004655e8',row.skill)]=True
    s=SupportSnapshot(1000,flags,{'00462670':100,'00462e34':100},2000,
                      False,True,True,replies)
    return replace(s,**changes)


def provoke(**changes):
    flags={r[0]:True for r in PROVOKE_ROWS}
    replies={(flag,'00464490',skill):False for flag,skill,*_ in PROVOKE_ROWS}
    replies.update({(flag,'004655e8',skill):True for flag,skill,*_ in PROVOKE_ROWS})
    return replace(ProvokeSnapshot(10000,flags,{'00462e34':100,'00462e08':100},1000,
                                   60,0,0,True,0,replies),**changes)


def attack(**changes):
    return replace(AlternateAttackSnapshot(1000,1,10,False,True,True,True,1),**changes)


class SupportTests(unittest.TestCase):
    def test_all_thirteen_support_rows_exact_thresholds(self):
        self.assertEqual(len(SUPPORT_ROWS),13)
        for r in SUPPORT_ROWS:
            with self.subTest(flag=r.flag):
                s=support(r,mp=r.mp_min,raw_stats={r.stat_reader:r.stat_min} if r.stat_reader else {})
                d=select_warrior_support(s)
                self.assertEqual((d.status,d.selected_flag),('local_return_nonzero',r.flag))
                self.assertEqual(d.calls[-1],AlternateCall('004655e8',r.skill,'00462650'))

    def test_mp_and_stat_minus_one_reject(self):
        for r in SUPPORT_ROWS:
            if r.mp_min is not None:self.assertEqual(select_warrior_support(support(r,mp=r.mp_min-1)).status,'no_local_nonzero_return')
            if r.stat_reader:self.assertEqual(select_warrior_support(support(r,raw_stats={r.stat_reader:r.stat_min-1})).status,'no_local_nonzero_return')

    def test_buff_sequences_preserve_source_order(self):
        for flag,expected in ((0x100,(705,710)),(0x101,(710,705)),(0x103,(730,750,780)),(0x106,(730,750,780)),(0x109,(730,750,780))):
            r=next(r for r in SUPPORT_ROWS if r.flag==flag)
            d=select_warrior_support(support(r))
            self.assertEqual(tuple(c.skill_number for c in d.calls if c.helper=='00464268'),expected)

    def test_each_gate_blocks_with_no_attempt(self):
        for r in SUPPORT_ROWS:
            s=support(r)
            keys=[key for key in s.replies if key[1]!='004655e8']
            for key in keys:
                rep=dict(s.replies);rep[key]=True
                d=select_warrior_support(replace(s,replies=rep))
                self.assertFalse(any(c.helper=='004655e8' for c in d.calls))

    def test_attempt_reply_false_continues_later_priority(self):
        a,b=SUPPORT_ROWS[:2];s=support(a)
        second=support(b);s.flags[b.flag]=True;s.replies.update(second.replies)
        s.replies[(a.flag,'004655e8',a.skill)]=False
        d=select_warrior_support(s)
        self.assertEqual(d.selected_flag,b.flag)
        self.assertEqual([c.skill_number for c in d.calls if c.helper=='004655e8'],[2,7])

    def test_missing_helper_return_is_observation_not_success(self):
        r=SUPPORT_ROWS[0];s=support(r);del s.replies[(r.flag,'004655e8',r.skill)]
        self.assertEqual(select_warrior_support(s).status,'needs_observation')

    def test_attack_only_rows_and_no_mp_requirement_for_731(self):
        r=next(r for r in SUPPORT_ROWS if r.flag==0x104)
        self.assertEqual(select_warrior_support(support(r,mp=None)).status,'local_return_nonzero')
        self.assertEqual(select_warrior_support(support(r,attack_enabled=False)).status,'no_local_nonzero_return')

    def test_final_skill_has_no64490_gate_and_lock_only_after_nonzero(self):
        r=SUPPORT_ROWS[-1];s=support(r)
        d=select_warrior_support(s);self.assertEqual((d.local_lock_ms,d.local_lock_started_ms),(1500,1000))
        self.assertFalse(any(c.helper=='00464490' for c in d.calls))
        s.replies[(r.flag,'004655e8',r.skill)]=False
        self.assertIsNone(select_warrior_support(s).local_lock_ms)

    def test_initial_lock_and_raw_field_gates(self):
        self.assertEqual(select_warrior_support(support(locked=True)).status,'locked')
        self.assertEqual(select_warrior_support(support(locked=None)).status,'needs_observation')
        self.assertEqual(select_warrior_support(support(SUPPORT_ROWS[0],raw_field_554020_nonzero=False)).status,'no_local_nonzero_return')


class ProvokeTests(unittest.TestCase):
    def test_priority_all_four_rows_and_used_flags(self):
        st=ProvokeState()
        for flag,skill,stat,mp,index in PROVOKE_ROWS:
            d=replay_warrior_provoke(provoke(mp=mp,raw_stats={'00462e34':stat}),st)
            self.assertEqual(d.selected_flag,flag)
            self.assertTrue(d.state.used[index]);st=d.state

    def test_outer198_mandatory(self):
        self.assertEqual(replay_warrior_provoke(provoke(caller_flag_198=False)).status,'caller_disabled')
        self.assertEqual(replay_warrior_provoke(provoke(caller_flag_198=None)).status,'needs_observation')

    def test_window_exact_boundary_selects_reset_branch(self):
        s=provoke(now_ms=60000)
        self.assertEqual(replay_warrior_provoke(s).status,'wait_reset')
        self.assertEqual(replay_warrior_provoke(replace(s,now_ms=59999)).status,'local_return_nonzero')

    def test_reset_exact300000_and_stats_and_MP(self):
        s=provoke(now_ms=300000,raw_stats={'00462e08':45},mp=60)
        d=replay_warrior_provoke(s,ProvokeState(used=(True,)*4))
        self.assertEqual(d.status,'local_reset_helper_plan')
        self.assertEqual(d.state.used,(False,)*4)
        self.assertEqual((d.state.start_ms,d.state.reset_ms),(300000,300000))
        self.assertEqual(d.calls,(AlternateCall('0050378c'),))
        self.assertEqual(replay_warrior_provoke(replace(s,now_ms=299999)).status,'wait_reset')
        self.assertEqual(replay_warrior_provoke(replace(s,mp=59)).status,'reset_MP_gate')

    def test_delays_equality_and_raw_six_gate(self):
        self.assertEqual(replay_warrior_provoke(provoke(start_delay_seconds=11)).status,'wait_start_delay')
        self.assertEqual(replay_warrior_provoke(provoke(start_delay_seconds=10)).status,'local_return_nonzero')
        self.assertEqual(replay_warrior_provoke(provoke(skill_delay_seconds=11)).status,'wait_skill_delay')
        self.assertEqual(replay_warrior_provoke(provoke(raw_field_554020=6)).status,'raw_state_gate')

    def test_periodic_helper500ms_includes_boundary(self):
        s=provoke(now_ms=500)
        self.assertEqual(replay_warrior_provoke(s).calls[0],AlternateCall('00464b2c'))
        self.assertNotEqual(replay_warrior_provoke(replace(s,now_ms=499)).calls[0],AlternateCall('00464b2c'))

    def test_failed_attempt_falls_through_unknown_stops(self):
        s=provoke();s.replies[(0x19d,'004655e8',779)]=False
        self.assertEqual(replay_warrior_provoke(s).selected_flag,0x19c)
        del s.replies[(0x19d,'004655e8',779)]
        d=replay_warrior_provoke(s);self.assertEqual(d.status,'needs_observation');self.assertFalse(any(d.state.used))

    def test_config_multiplication_is_DWORD_wrapped(self):
        self.assertEqual(replay_warrior_provoke(provoke(window_seconds=-1)).status,'local_return_nonzero')
        self.assertEqual(replay_warrior_provoke(provoke(window_seconds=0)).status,'wait_reset')


class AttackTests(unittest.TestCase):
    def test_phase_zero_needs_byte_observation_and_keeps_state(self):
        st=AlternateAttackState()
        d=replay_warrior_alternate_attack(attack(helper_501f3c_byte=None),st)
        self.assertEqual(d.status,'needs_observation');self.assertEqual(d.state,st)
        self.assertEqual(d.calls,(AlternateCall('00501f3c'),))

    def test_range_equality_and_lock_reset_only_in_range(self):
        st=AlternateAttackState(phase=4)
        self.assertEqual(replay_warrior_alternate_attack(attack(distance=10),st).state.phase,5)
        self.assertEqual(replay_warrior_alternate_attack(attack(distance=7,configured_range=7),st).state.phase,5)
        self.assertEqual(replay_warrior_alternate_attack(attack(distance=10.01),st).status,'out_of_range')
        self.assertEqual(replay_warrior_alternate_attack(attack(locked=True),st).state.phase,0)
        self.assertEqual(replay_warrior_alternate_attack(attack(locked=True,distance=10.01),st).state.phase,4)

    def test_phase_one_49wait_50advance_zero_reply_skips_wait(self):
        st=AlternateAttackState(phase=1,initial_reply_byte=1,initial_ms=1000)
        self.assertEqual(replay_warrior_alternate_attack(attack(now_ms=1049),st).status,'wait_50ms')
        d=replay_warrior_alternate_attack(attack(now_ms=1050),st)
        self.assertEqual(d.state.phase,2);self.assertEqual(d.state.clear_ms,1050)
        self.assertEqual(replay_warrior_alternate_attack(attack(),replace(st,initial_reply_byte=0)).state.phase,2)

    def test_phase_two200_boundary_and_flags_false_clear(self):
        st=AlternateAttackState(phase=2,clear_ms=1000)
        self.assertEqual(replay_warrior_alternate_attack(attack(now_ms=1199),st).status,'wait_200ms')
        d=replay_warrior_alternate_attack(attack(now_ms=1200,flag_562011=False,flag_562012=False),st)
        self.assertEqual(d.calls,(AlternateCall('00465ef8',target_reader='00462630'),));self.assertEqual(d.state.phase,3)
        self.assertEqual(replay_warrior_alternate_attack(attack(flag_561fcc=False),st).state.phase,3)

    def test_phase_three_bothflags_counter_and_repeat(self):
        st=AlternateAttackState(phase=3,counter=9)
        d=replay_warrior_alternate_attack(attack(),st)
        self.assertEqual((d.state.phase,d.state.counter,d.state.repeat_ms),(4,0,1000))
        self.assertEqual(d.calls,(AlternateCall('00465f30'),))
        d=replay_warrior_alternate_attack(attack(flag_562011=False,flag_562012=False),st)
        self.assertEqual(d.state.counter,9);self.assertEqual(d.state.repeat_ms,0)

    def test_phase_four_and_five20boundaries(self):
        st=AlternateAttackState(phase=4,repeat_ms=1000)
        self.assertEqual(replay_warrior_alternate_attack(attack(now_ms=1019),st).status,'wait_20ms')
        d=replay_warrior_alternate_attack(attack(now_ms=1020),st)
        self.assertEqual(d.state.phase,5);self.assertEqual(d.state.second_repeat_ms,1020)
        self.assertEqual(replay_warrior_alternate_attack(attack(now_ms=1039),d.state).status,'wait_second_20ms')
        d=replay_warrior_alternate_attack(attack(now_ms=1040),d.state)
        self.assertEqual(d.state.phase,6);self.assertEqual(d.calls[0].helper,'00465ef8')

    def test_phase_six900_boundary_and_dword_rollover(self):
        st=AlternateAttackState(phase=6,initial_ms=1000)
        self.assertEqual(replay_warrior_alternate_attack(attack(now_ms=1899),st).status,'wait_900ms')
        self.assertEqual(replay_warrior_alternate_attack(attack(now_ms=1900),st).state.phase,0)
        st=replace(st,initial_ms=0xfffffff0)
        self.assertEqual(replay_warrior_alternate_attack(attack(now_ms=884),st).state.phase,0)

    def test_flag_or_short_circuit_does_not_require_second(self):
        st=AlternateAttackState(phase=4)
        self.assertEqual(replay_warrior_alternate_attack(attack(flag_562012=None),st).state.phase,5)

    def test_invalid_and_unknown_observations(self):
        for changes in ({'now_ms':True},{'distance':float('nan')},{'distance':float('inf')},{'helper_501f3c_byte':256}):
            with self.assertRaises(ValueError):attack(**changes)
        self.assertEqual(replay_warrior_alternate_attack(attack(locked=None)).status,'needs_observation')


if __name__=='__main__':unittest.main()
