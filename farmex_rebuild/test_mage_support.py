import unittest
from dataclasses import replace
from mage_support import *


def buff(row=None,**changes):
    flags={r.flag:False for r in MAGE_BUFF_ROWS};replies={}
    if row:
        flags[row.flag]=True
        for skill in row.buffs:replies[(row.flag,'00464268',skill)]=False
        replies[(row.flag,'00464490',row.skill)]=False
        for i in range(row.string_queries):replies[(row.flag,'00463950',i)]=True
    return replace(MageBuffSnapshot(100000,flags,{n:100 for n in ('00462ddc','00462e08','00462e34','00462e60')},1000,
                                    False,False,replies,20,0,False,False,True),**changes)


def tp(**changes):
    members=(MagePartyMember(1,1,100,100,'Self',True,0),
             MagePartyMember(2,2,20,100,'Target',False,21),
             MagePartyMember(3,3,30,100,'Other',False,30))
    timers={0x56972c+i*4:0 for i in range(1,4)}
    return replace(MageTPSnapshot(10000,members,3,10,5,timers,False,False,True,50,True,'Target',1,
                                  False,False,True,True,1,2),**changes)


class BuffTests(unittest.TestCase):
    def test_all18rows_reachable_exact_stat_mp_thresholds(self):
        self.assertEqual(len(MAGE_BUFF_ROWS),18)
        for r in MAGE_BUFF_ROWS:
            with self.subTest(flag=r.flag):
                d=select_mage_buff(buff(r,mp=r.mp_min,raw_stats={r.stat_reader:r.stat_min}))
                self.assertEqual(d.skill_number,r.skill)
                self.assertEqual(d.status,'local_helper_plan')

    def test_stat_mp_minus_one(self):
        for r in MAGE_BUFF_ROWS:
            self.assertEqual(select_mage_buff(buff(r,mp=r.mp_min-1)).status,'no_eligible_skill')
            self.assertEqual(select_mage_buff(buff(r,raw_stats={r.stat_reader:r.stat_min-1})).status,'no_eligible_skill')

    def test_priority_and_three_buff_gates(self):
        r=next(r for r in MAGE_BUFF_ROWS if r.flag==0x1cf)
        d=select_mage_buff(buff(r))
        self.assertEqual([c.skill_number for c in d.calls if c.helper=='00464268'],[654,630,612])
        s=buff();s.flags.update({r.flag:True for r in MAGE_BUFF_ROWS})
        for r in MAGE_BUFF_ROWS:s.helper_replies.update(buff(r).helper_replies)
        self.assertEqual(select_mage_buff(s).skill_number,802)

    def test_unknown_helper_and_string_query_block(self):
        r=MAGE_BUFF_ROWS[0];s=buff(r);del s.helper_replies[(r.flag,'00463950',1)]
        self.assertEqual(select_mage_buff(s).status,'needs_observation')
        s.helper_replies[(r.flag,'00463950',1)]=False
        self.assertEqual(select_mage_buff(s).status,'no_eligible_skill')

    def test_802_slow_timer_exact60000_updates_before_transport(self):
        r=MAGE_BUFF_ROWS[0]
        self.assertEqual(select_mage_buff(buff(r,now_ms=59999)).status,'no_eligible_skill')
        d=select_mage_buff(buff(r,now_ms=60000,raw_field_55403c_nonzero=None))
        self.assertEqual(d.status,'needs_observation')
        self.assertEqual(d.local_timer_updates,((0x553e08,60000),))
        self.assertIsNone(select_mage_buff(buff(r)).local_lock_ms)

    def test_802_fast_uses_gate_without_timer(self):
        r=MAGE_BUFF_ROWS[0]
        d=select_mage_buff(buff(r,fast_mode=True,timer_553e08=None))
        self.assertEqual(d.status,'local_return_nonzero')
        self.assertEqual(d.local_lock_ms,0)
        self.assertEqual(d.local_timer_updates,())
        self.assertTrue(any(c.helper=='00464490' for c in d.calls))

    def test_826_truncated_metric_threshold51(self):
        r=MAGE_BUFF_ROWS[1]
        self.assertEqual(select_mage_buff(buff(r,metric_460548=50.999)).skill_number,826)
        self.assertEqual(select_mage_buff(buff(r,metric_460548=51)).status,'no_eligible_skill')
        self.assertEqual(select_mage_buff(buff(r,metric_460548=None)).status,'needs_observation')

    def test_fast_helper_false_no_lock_slow_mode_clear_plan(self):
        r=MAGE_BUFF_ROWS[2]
        d=select_mage_buff(buff(r,fast_mode=True,helper_655e8_nonzero=False))
        self.assertEqual(d.status,'local_return_zero');self.assertIsNone(d.local_lock_ms)
        d=select_mage_buff(buff(r,raw_field_554020_nonzero=True,raw_field_55403c_nonzero=True))
        self.assertEqual([c.helper for c in d.calls][-3:],['00464714','00465ef8','0049e630'])
        self.assertEqual(d.local_lock_ms,2000)

    def test_lock_and_unknown_lock(self):
        self.assertEqual(select_mage_buff(buff(locked=True)).status,'locked')
        self.assertEqual(select_mage_buff(buff(locked=None)).status,'needs_observation')


class TPTests(unittest.TestCase):
    def test_low_hp_lowest_absolute_hp_and_tie_later(self):
        s=tp();members=list(s.members);members[2]=replace(members[2],hp=20)
        d=select_mage_tp(replace(s,members=tuple(members)))
        self.assertEqual(d.target_id,3)
        self.assertEqual(d.local_timer_updates,((0x569738,10000),))

    def test_self_positive_hp_and50000cap(self):
        s=tp();members=list(s.members);members[1]=replace(members[1],hp=0);members[2]=replace(members[2],hp=50001,hp_max=200000)
        self.assertEqual(select_mage_tp(replace(s,members=tuple(members))).status,'no_eligible_member')
        members[2]=replace(members[2],hp=50000)
        self.assertEqual(select_mage_tp(replace(s,members=tuple(members))).target_id,3)

    def test_low_hp_retry2500_equality_and_distance20_strict(self):
        s=tp();members=(s.members[0],s.members[1]);s=replace(s,members=members,party_count=2)
        self.assertEqual(select_mage_tp(replace(s,timer_slots={0x569734:7501})).status,'no_eligible_member')
        self.assertEqual(select_mage_tp(replace(s,timer_slots={0x569734:7500})).target_id,2)
        self.assertEqual(select_mage_tp(replace(s,members=(members[0],replace(members[1],distance=20)))).status,'no_eligible_member')

    def test_lookup_zero_skips_distance_observation(self):
        s=tp();members=(s.members[0],replace(s.members[1],lookup_64a10_zero=True,distance=None))
        self.assertEqual(select_mage_tp(replace(s,members=members,party_count=2)).target_id,2)

    def test_lowhp_priority_does_not_fallback_to_named_when_invalid(self):
        self.assertEqual(select_mage_tp(tp(threshold=0)).status,'threshold_gate')
        self.assertEqual(select_mage_tp(tp(threshold=100)).status,'threshold_gate')

    def test_named_exact_case_first_match(self):
        self.assertEqual(select_mage_tp(tp(low_hp_enabled=False,target_name='target')).status,'name_not_found')
        s=tp(low_hp_enabled=False);members=list(s.members);members[2]=replace(members[2],name='Target')
        self.assertEqual(select_mage_tp(replace(s,members=tuple(members))).target_id,2)

    def test_named_timer3001_and_slow_write_discrepancy(self):
        s=tp(low_hp_enabled=False)
        self.assertEqual(select_mage_tp(replace(s,timer_slots={0x569734:7000})).status,'wait_named_timer')
        d=select_mage_tp(replace(s,timer_slots={0x569734:6999}))
        self.assertEqual(d.local_timer_updates,((0x569730,10000),))

    def test_named_fast_writes_same_physical_read_slot(self):
        d=select_mage_tp(tp(low_hp_enabled=False,fast_mode=True))
        self.assertEqual(d.local_timer_updates,((0x569734,10000),))
        self.assertEqual(d.local_lock_ms,2000)
        self.assertEqual(d.calls[-1],MageSupportCall('004655e8',4,2))

    def test_named_including_self_no_hp_guard(self):
        d=select_mage_tp(tp(low_hp_enabled=False,target_name='Self'))
        self.assertEqual(d.target_id,1)

    def test_nonbmp_UTF16_equivalence(self):
        s=tp(low_hp_enabled=False,target_name='\U0001f600')
        members=list(s.members);members[1]=replace(members[1],name='\ud83d\ude00')
        self.assertEqual(select_mage_tp(replace(s,members=tuple(members))).target_id,2)

    def test_fast_false_or_unknown_not_success(self):
        d=select_mage_tp(tp(fast_mode=True,helper_655e8_nonzero=False))
        self.assertEqual(d.status,'local_return_zero');self.assertEqual(d.local_timer_updates,())
        self.assertEqual(select_mage_tp(tp(fast_mode=True,helper_655e8_nonzero=None)).status,'needs_observation')

    def test_incomplete_party_and_unknown_distance_fail_closed(self):
        s=tp();self.assertEqual(select_mage_tp(replace(s,members=s.members[:2])).status,'needs_observation')
        members=list(s.members);members[1]=replace(members[1],distance=None)
        self.assertEqual(select_mage_tp(replace(s,members=tuple(members))).status,'needs_observation')

    def test_signed32_hp_product_wrap_preserved(self):
        s=tp();members=list(s.members);members[1]=replace(members[1],hp=1,hp_max=0x7fffffff);members[2]=replace(members[2],hp=0)
        self.assertEqual(select_mage_tp(replace(s,members=tuple(members))).status,'no_eligible_member')

    def test_dword_clock_wrap(self):
        s=tp(now_ms=2484);timers={a:0xfffffff0 for a in s.timer_slots}
        self.assertEqual(select_mage_tp(replace(s,timer_slots=timers)).target_id,2)


class PendingTests(unittest.TestCase):
    def test_pending_modes_member_lookup_and_no_distance_gate(self):
        self.assertEqual(replay_pending_mage_tp(tp(pending=False)).status,'no_pending')
        self.assertEqual(replay_pending_mage_tp(tp(pending_mode=2)).status,'pending_mode_gate')
        self.assertEqual(replay_pending_mage_tp(tp(pending_target_id=999)).status,'pending_not_in_party')
        s=tp();members=list(s.members);members[1]=replace(members[1],distance=None,lookup_64a10_zero=None)
        d=replay_pending_mage_tp(replace(s,members=tuple(members)))
        self.assertEqual(d.target_id,2);self.assertTrue(d.clear_pending);self.assertEqual(d.local_timer_updates,())

    def test_pending_cleared_only_successful_local_fast_result(self):
        d=replay_pending_mage_tp(tp(fast_mode=True,helper_655e8_nonzero=False))
        self.assertFalse(d.clear_pending);self.assertIsNone(d.local_lock_ms)
        self.assertTrue(replay_pending_mage_tp(tp(fast_mode=True)).clear_pending)

    def test_entry_stat_and_MP_and_party_boundaries(self):
        self.assertEqual(replay_pending_mage_tp(tp(level_462670=9)).status,'entry_gate')
        self.assertEqual(replay_pending_mage_tp(tp(mp=4)).status,'entry_gate')
        self.assertEqual(replay_pending_mage_tp(tp(party_count=1)).status,'entry_gate')

    def test_invalid_typed_inputs(self):
        for changes in ({'now_ms':True},{'party_count':9},{'fast_mode':1},{'timer_slots':{1:-1}}):
            with self.assertRaises(ValueError):tp(**changes)
        with self.assertRaises(ValueError):MagePartyMember(1,2,10,100,distance=float('nan'))


if __name__=='__main__':unittest.main()
