import unittest
from mining_scheduler import *

def config(**fields):
    values={0x603c:1,0x6040:1,0x6047:0};values.update({int(k,16):v for k,v in fields.items()})
    return MiningPanelConfiguration('fixture',values)

def alive(**updates):
    values=dict(active_initial=1,dead=0,merchant_after_speed=0,mining_after_merchant=0,
        route_after_mining=0,active_after_route=1,mining_after_route=1,
        actor_gate_45dc44=0,helper_4631a8=0,control_5fe0_25=0,
        normal_retry_tick=5000,normal_retry_qword=0,helper_4634a4=0,normal_stamp_tick=5001)
    values.update(updates);return values

class MiningScheduleTests(unittest.TestCase):
    def test_inactive_short_circuit_needs_no_panel(self):
        p=plan_mining_schedule(MiningPanelConfiguration('empty',{}),{'active_initial':0})
        self.assertTrue(p.complete);self.assertEqual(p.calls,())

    def test_dead_branch_never_runs_normal_helpers(self):
        p=plan_mining_schedule(config(**{'603c':0}),{'active_initial':1,'dead':1})
        self.assertEqual(p.status,'dead_respawn_disabled');self.assertEqual(p.calls,())

    def test_respawn_exact_boundaries_and_fresh_stamp(self):
        o=dict(active_initial=1,dead=1,death_qword=100,respawn_wait_tick=4099)
        self.assertEqual(plan_mining_schedule(config(),o).status,'respawn_wait')
        o.update(respawn_wait_tick=4100,respawn_retry_tick=1999,respawn_retry_qword=1000)
        self.assertEqual(plan_mining_schedule(config(),o).status,'respawn_retry_wait')
        o.update(respawn_retry_tick=2000,respawn_stamp_tick=2017,**{'returned:004c8d48':True})
        p=plan_mining_schedule(config(),o)
        self.assertEqual(p.calls,(('004c8d48',(0x561ef8,)),))
        self.assertEqual(p.writes,((0x553df0,2017,0),))

    def test_qword_subtraction_is_not_dword_wrap(self):
        self.assertEqual(signed_elapsed(5,0xfffffff0),-4294967275)
        self.assertEqual(signed_elapsed(5,0xfffffffffffffff0),21)

    def test_respawn_duration_signed_low_dword(self):
        o=dict(active_initial=1,dead=1,death_qword=1,respawn_wait_tick=1,
               respawn_retry_tick=1000,respawn_retry_qword=0,respawn_stamp_tick=1001,
               **{'returned:004c8d48':True})
        self.assertEqual(plan_mining_schedule(config(**{'6040':0xffffffff}),o).status,'respawn_wait')
        self.assertEqual(plan_mining_schedule(config(**{'6040':0xfffffffc}),o).status,'respawn_planned')

    def test_ordered_helpers_require_return_before_later_read(self):
        o=alive(merchant_after_speed=1,mining_after_merchant=1,route_after_mining=1,
            active_after_route=0,**{'returned:0047b384':True,'returned:004eb2a8':True,
            'returned:0047a61c':True,'returned:00479d70':True})
        p=plan_mining_schedule(config(**{'6047':1}),o)
        self.assertEqual([a for a,_ in p.calls],['0047b384','004eb2a8','0047a61c','00479d70'])
        self.assertEqual(p.status,'inactive_after_helpers')
        del o['returned:004eb2a8'];p=plan_mining_schedule(config(**{'6047':1}),o)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'returned:004eb2a8')
        self.assertEqual(len(p.calls),2)

    def test_initial_active_is_not_reused_after_helpers(self):
        o=alive();del o['active_after_route']
        self.assertEqual(plan_mining_schedule(config(),o).missing,'active_after_route')

    def test_item_branch_two_second_boundary_excludes_normal_branch(self):
        o=alive(control_5fe0_25=1,helper_463950=1,item_retry_tick=1999,item_retry_qword=0)
        self.assertEqual(plan_mining_schedule(config(),o).status,'item_retry_wait')
        o.update(item_retry_tick=2000,item_stamp_tick=2009,**{'returned:004c8290':True})
        p=plan_mining_schedule(config(),o)
        self.assertEqual(p.status,'item_planned');self.assertEqual(p.writes,((0x553df8,2009,0),))

    def test_normal_failing_predicate_still_stamps_and_short_circuits(self):
        p=plan_mining_schedule(config(),alive())
        self.assertTrue(p.complete);self.assertEqual(p.calls,())
        self.assertEqual(p.writes,((0x553e00,5001,0),))

    def test_normal_success_call_arguments_and_unsigned_quantity(self):
        o=alive(helper_4634a4=1,helper_46358c=0xffffffff,helper_463ac0=0,
            helper_4677f0=0x44,**{'returned:004c806c':True})
        p=plan_mining_schedule(config(),o)
        self.assertEqual(p.calls,(('004c806c',(0x561ef8,1)),))

    def test_missing_return_prevents_stamp(self):
        o=alive(control_5fe0_25=1,helper_463950=1,item_retry_tick=2000,item_retry_qword=0)
        p=plan_mining_schedule(config(),o)
        self.assertFalse(p.complete);self.assertEqual(p.writes,())

    def test_raw_byte_validation(self):
        with self.assertRaises(ValueError):plan_mining_schedule(config(),{'active_initial':True})

    def test_normal_retry_boundary_skips_predicates_and_stamp(self):
        o=alive(normal_retry_tick=4999)
        del o['helper_4634a4'];del o['normal_stamp_tick']
        p=plan_mining_schedule(config(),o)
        self.assertEqual(p.status,'normal_retry_wait');self.assertEqual(p.writes,())
        o['normal_retry_tick']=5000
        self.assertEqual(plan_mining_schedule(config(),o).missing,'helper_4634a4')

if __name__=='__main__':unittest.main()
