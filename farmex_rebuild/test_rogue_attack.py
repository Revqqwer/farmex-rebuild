import unittest
from dataclasses import replace
from rogue_attack import *


def snapshot(**kw):
    args=dict(now_ms=100000,distance=5,configured_range=50,mp=1000,
        flags={r.flag_offset:False for r in MELEE_ROWS+BOW_ROWS+SPECIAL_ROWS},
        raw_stats={'00462e08':100,'00462ddc':100,'00462670':100},
        last_ms_by_offset={r.timer_offset:0 for r in MELEE_ROWS+BOW_ROWS+SPECIAL_ROWS if r.timer_offset is not None},
        locked_561f7e=False,alternate_561f88=False,timestamp_5620a4_5620a8=0,raw_skill_prefix_46256c=101)
    args['flags'].update({0x89:False,0x91:False})
    args['last_ms_by_offset'].update({0x2c:0,0x30:0,0x34:0})
    args.update(kw)
    return RogueSnapshot(**args)

def enable(s,*offsets): return replace(s,flags={**s.flags,**{o:True for o in offsets}})

class RogueTests(unittest.TestCase):
    def test_melee_every_row_threshold_and_cooldown(self):
        for row in MELEE_ROWS:
            with self.subTest(flag=row.flag_offset):
                s=enable(snapshot(),row.flag_offset)
                if row.stat_reader: s=replace(s,raw_stats={**s.raw_stats,row.stat_reader:row.stat_minimum})
                if row.mp_minimum is not None: s=replace(s,mp=row.mp_minimum)
                if row.timer_offset is not None: s=replace(s,last_ms_by_offset={**s.last_ms_by_offset,row.timer_offset:s.now_ms-row.interval_ms})
                d=select_rogue_melee(s)
                self.assertEqual(d.status,'local_attempt');self.assertEqual(d.row.flag_offset,row.flag_offset)
                if row.timer_offset is not None:
                    self.assertEqual(select_rogue_melee(replace(s,last_ms_by_offset={**s.last_ms_by_offset,row.timer_offset:s.now_ms-row.interval_ms+1})).status,'no_eligible_skill')
    def test_bow_every_row_threshold_and_cooldown(self):
        for row in BOW_ROWS:
            with self.subTest(flag=row.flag_offset):
                s=enable(snapshot(),row.flag_offset)
                s=replace(s,raw_stats={**s.raw_stats,row.stat_reader:row.stat_minimum})
                if row.mp_minimum is not None:s=replace(s,mp=row.mp_minimum)
                if row.timer_offset is not None:s=replace(s,last_ms_by_offset={**s.last_ms_by_offset,row.timer_offset:s.now_ms-row.interval_ms})
                d=select_rogue_bow(s);self.assertEqual(d.status,'selected');self.assertEqual(d.row.flag_offset,row.flag_offset)
                if row.timer_offset is not None:
                    self.assertEqual(select_rogue_bow(replace(s,last_ms_by_offset={**s.last_ms_by_offset,row.timer_offset:s.now_ms-row.interval_ms+1})).status,'no_eligible_skill')
    def test_priority_not_flag_numeric_order(self):
        s=enable(snapshot(),0x3d,0x41);self.assertEqual(select_rogue_melee(s).row.flag_offset,0x3d)
        s=enable(snapshot(),0x87,0x98);self.assertEqual(select_rogue_bow(s).row.flag_offset,0x87)
    def test_unknown_priority_cannot_fall_through(self):
        s=enable(snapshot(),0x38);s=replace(s,flags={**s.flags,0xdf:None})
        self.assertEqual(select_rogue_melee(s).status,'needs_observation')
    def test_disabled_rows_do_not_need_stat(self):
        s=enable(snapshot(raw_stats={}),0x38);self.assertEqual(select_rogue_melee(s).status,'local_attempt')
    def test_melee_range_equality_and_no_lock_gate(self):
        s=enable(snapshot(distance=12,locked_561f7e=True),0x38)
        self.assertEqual(select_rogue_melee(s).status,'local_attempt')
        self.assertEqual(select_rogue_melee(replace(s,distance=12.001)).status,'out_of_range')
    def test_bow_range_equality(self):
        s=enable(snapshot(distance=50,configured_range=1),0x84)
        self.assertEqual(select_rogue_bow(s).status,'selected')
        self.assertEqual(select_rogue_bow(replace(s,distance=50.001)).status,'out_of_range')
    def test_prefix_variant_skill_arguments(self):
        for prefix in (102,202,101):
            s=enable(snapshot(raw_skill_prefix_46256c=prefix),0x3a)
            self.assertEqual(select_rogue_melee(s).row.skill_number,7 if prefix in (102,202) else 6)
            s=enable(snapshot(raw_skill_prefix_46256c=prefix),0x85)
            self.assertEqual(select_rogue_bow(s).row.skill_number,8 if prefix in (102,202) else 7)
    def test_melee_target_and_local_timer_order(self):
        d=select_rogue_melee(enable(snapshot(),0xdf))
        self.assertEqual(d.row.target_source,'read:00553e7c')
        self.assertEqual(d.local_timer_updates,((0x20,100000),(0x108,100000)))
    def test_unsigned_tick_wrap_and_future_timestamp(self):
        s=enable(snapshot(now_ms=5000),0x39)
        s=replace(s,last_ms_by_offset={**s.last_ms_by_offset,0x48:0xfffffe00})
        self.assertEqual(select_rogue_melee(s).status,'local_attempt')
        s=replace(s,last_ms_by_offset={**s.last_ms_by_offset,0x48:6000})
        self.assertEqual(select_rogue_melee(s).status,'local_attempt')
    def test_special_strict_cooldown(self):
        s=enable(snapshot(),0x3f);s=replace(s,last_ms_by_offset={**s.last_ms_by_offset,0x60:89000})
        self.assertEqual(select_rogue_special(s).status,'no_eligible_skill')
        d=select_rogue_special(replace(s,now_ms=100001))
        self.assertEqual(d.status,'selected_requires_helpers');self.assertEqual(d.lock_interval_ms,1600)
        self.assertEqual(d.local_timer_updates,())
    def test_special_global_qword_gate(self):
        s=enable(snapshot(timestamp_5620a4_5620a8=40000),0x42)
        self.assertEqual(select_rogue_special(s).status,'no_eligible_skill')
        self.assertEqual(select_rogue_special(replace(s,now_ms=100001)).row.skill_number,0x28a)
        self.assertEqual(select_rogue_special(replace(s,timestamp_5620a4_5620a8=1<<32)).status,'no_eligible_skill')
    def test_special_alternate_helper_polarity(self):
        s=enable(snapshot(alternate_561f88=True),0x3f)
        self.assertEqual(select_rogue_special(s).status,'needs_observation')
        self.assertEqual(select_rogue_special(replace(s,helper_bools={'00464490:276':True})).status,'no_eligible_skill')
        d=select_rogue_special(replace(s,helper_bools={'00464490:276':False}))
        self.assertEqual(d.lock_interval_ms,2100);self.assertIn('004655e8',d.pending_helpers)
    def test_special_28_outer_range_and_last_row(self):
        s=enable(snapshot(distance=28,configured_range=1,helper_bools={'00463924:160ddbd8':True}),0x44)
        self.assertEqual(select_rogue_special(s).row.skill_number,0x290)
        self.assertEqual(select_rogue_special(replace(s,distance=28.001)).status,'out_of_range')
        self.assertEqual(select_rogue_special(replace(s,helper_bools={'00463924:160ddbd8':False})).status,'no_eligible_skill')
    def test_volley_all_three_actions_and_speed_plan(self):
        s=enable(snapshot(),0x84,0x89,0x91)
        d=plan_rogue_volley(s,1000,5,5,2,True,0.21)
        self.assertEqual(d.calls,(('00464714',None),('004df6f0',3),('0045ddf4',None),('0045de78',None),('004de710',None),('004dedec',None)))
        self.assertEqual(d.local_timer_updates,((0x2c,100000),(0x30,100000),(0x34,100000)))
    def test_volley_speed_equality_and_partial_unknown(self):
        s=enable(snapshot(),0x89)
        d=plan_rogue_volley(s,1000,5,5,2,True,0.2)
        self.assertEqual(d.calls,(('00464714',None),('004de710',None)))
        d=plan_rogue_volley(s,1000,5,None,2,True,0.21)
        self.assertEqual(d.status,'needs_observation');self.assertEqual(d.calls,())
    def test_volley_lock_and_cooldown_equality(self):
        self.assertEqual(plan_rogue_volley(snapshot(locked_561f7e=True),0).status,'locked')
        s=enable(snapshot(),0x89);s=replace(s,last_ms_by_offset={**s.last_ms_by_offset,0x30:99000})
        self.assertEqual(plan_rogue_volley(s,1000,5,5,1).status,'local_attempt')
        self.assertEqual(plan_rogue_volley(s,1001,5,5,1).status,'no_eligible_skill')
    def test_volley_preselection_timer_visible_before_unknown(self):
        s=enable(snapshot(),0x9a)
        d=plan_rogue_volley(s,1000,None,5,1)
        self.assertEqual(d.status,'needs_observation');self.assertEqual(d.calls,())
        self.assertEqual(d.local_timer_updates,((0xd0,100000),))
    def test_stat_and_mp_rejection(self):
        s=enable(snapshot(mp=199),0xdf);self.assertEqual(select_rogue_melee(s).status,'no_eligible_skill')
        s=enable(snapshot(raw_stats={'00462ddc':79}),0x9a);self.assertEqual(select_rogue_bow(s).status,'no_eligible_skill')
    def test_invalid_inputs(self):
        for kw in ({'distance':float('nan')},{'now_ms':True},{'last_ms_by_offset':{0:1<<32}},{'helper_bools':{'x':1}},{'timestamp_5620a4_5620a8':-1}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):snapshot(**kw)

if __name__=='__main__':unittest.main()
