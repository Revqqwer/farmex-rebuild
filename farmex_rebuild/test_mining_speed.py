import unittest
from mining_speed import *

def cfg(mode):return MiningPanelConfiguration('fixture',{0x6048:mode})
def fixture(**updates):
    values=dict(lock_561f7e=0,dead_561f6f=0,ready_561f6e=1,blocked_561f70=0,
        merchant_568d81=0,route_5f54=1,actor_gate_initial=1,rogue_predicate_505d20=1,
        class_1=101,class_2=102,class_3=103,gate_464490=0,retry_tick=2000,retry_qword=0,
        buff_1=0,buff_2=0,buff_3=0,actor_462650=0x12345678,retry_stamp_tick=2013,
        **{'returned:004655e8':True})
    values.update(updates);return values

class MiningSpeedTests(unittest.TestCase):
    def test_lock_short_circuit_requires_nothing_else(self):
        p=plan_mining_speed(cfg(1),{'lock_561f7e':1})
        self.assertTrue(p.complete);self.assertEqual(p.calls,())

    def test_merchant_short_circuit_does_not_require_route_byte(self):
        o=fixture(merchant_568d81=1,actor_gate_initial=0);del o['route_5f54']
        self.assertEqual(plan_mining_speed(cfg(1),o).status,'actor_gate_zero')

    def test_sprint_uses_three_fresh_class_values_and_ignores_cast_result(self):
        p=plan_mining_speed(cfg(1),fixture(cast_result=0))
        self.assertEqual(p.checks,(('00464490',2),('00464268',101002),('00464268',102010),('00464268',103725)))
        self.assertEqual(p.calls,(('004655e8',(2,0x12345678)),))
        self.assertEqual(p.writes,((0x553de8,2013,64),))

    def test_sprint_cadence_before_buff_reads(self):
        o=fixture(retry_tick=1999)
        for i in range(1,4):del o['buff_'+str(i)]
        p=plan_mining_speed(cfg(1),o)
        self.assertEqual(p.status,'retry_wait');self.assertEqual(len(p.checks),1)

    def test_swift_buff_checks_precede_cadence(self):
        o=fixture(stat_462670=10,retry_tick=0,buff_1=1)
        p=plan_mining_speed(cfg(2),o)
        self.assertEqual(p.status,'buff_present');self.assertEqual(p.checks,(('00464268',101002),))

    def test_swift_signed_stat_boundary(self):
        for value in (9,0xffffffff):
            self.assertEqual(plan_mining_speed(cfg(2),fixture(stat_462670=value)).status,'swift_stat_low')
        p=plan_mining_speed(cfg(2),fixture(stat_462670=10))
        self.assertEqual(p.missing,'actor_gate_refresh')

    def test_swift_target_zero_still_reads_gate_and_requeries_target(self):
        o=fixture(stat_462670=10,actor_gate_refresh=0,target_462630_first=0,
            target_gate_45dc44=1,target_462630_second=0x77,cast_result=1,
            lock_stamp_tick=2009,**{'returned:00465ef8':True})
        p=plan_mining_speed(cfg(2),o)
        self.assertEqual(p.calls,(('00465ef8',(0x77,0)),('004655e8',(10,0x12345678))))
        self.assertEqual(p.writes,((0x561f80,2000,32),(0x561f84,2009,32),(0x561f7e,1,8),(0x553de8,2013,64)))

    def test_swift_failed_cast_does_not_stamp_or_lock(self):
        o=fixture(stat_462670=10,actor_gate_refresh=0,target_462630_first=0,
                  target_gate_45dc44=0,cast_result=0)
        p=plan_mining_speed(cfg(2),o)
        self.assertEqual(p.status,'swift_cast_failed');self.assertEqual(p.writes,())

    def test_refresh_callback_return_precedes_fresh_target_query(self):
        o=fixture(stat_462670=10,actor_gate_refresh=1)
        p=plan_mining_speed(cfg(2),o)
        self.assertEqual(p.calls,(('00464714',()),));self.assertEqual(p.missing,'returned:00464714')

    def test_lightfeet_level25_and_only_first_sprint_buff_id(self):
        self.assertEqual(plan_mining_speed(cfg(3),fixture(stat_462e34=24)).status,'lightfeet_stat_low')
        o=fixture(stat_462e34=25);del o['buff_2'];del o['buff_3']
        p=plan_mining_speed(cfg(3),o)
        self.assertEqual(p.checks,(('00464490',725),('00464268',101002)))
        self.assertEqual(p.calls,(('004655e8',(725,0x12345678)),))

    def test_warrior_fallback_keeps_uninitialized_stack_gap(self):
        o=fixture(rogue_predicate_505d20=0,warrior_predicate_505d20=1)
        for i in range(1,4):del o['class_'+str(i)]
        p=plan_mining_speed(cfg(1),o)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'stack_uninitialized_1')
        o.update(stack_uninitialized_1=7,stack_uninitialized_2=8,stack_uninitialized_3=9)
        p=plan_mining_speed(cfg(1),o)
        self.assertTrue(p.complete);self.assertEqual(p.checks[-3:],(('00464268',7),('00464268',8),('00464268',9)))

    def test_unknown_mode_still_requires_all_three_source_reads(self):
        o=fixture();del o['class_3']
        self.assertEqual(plan_mining_speed(cfg(99),o).missing,'class_3')
        self.assertEqual(plan_mining_speed(cfg(99),fixture()).status,'unknown_mode_no_action')

    def test_class_id_math_wraps_dword(self):
        p=plan_mining_speed(cfg(1),fixture(class_1=0xffffffff))
        self.assertEqual(p.checks[1],('00464268',0xfffffc1a))

    def test_missing_normal_return_does_not_stamp(self):
        o=fixture();del o['returned:004655e8']
        p=plan_mining_speed(cfg(1),o)
        self.assertFalse(p.complete);self.assertEqual(p.writes,())

if __name__=='__main__':unittest.main()
