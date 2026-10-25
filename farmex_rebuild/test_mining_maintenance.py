import unittest
from mining_maintenance import *

def cfg(**updates):
    fields={0x603b:0,0x6038:0,0x6039:0,0x604c:0,0x6036:0,0x6028:0,0x6037:0,0x5ff8:1}
    fields.update({int(k,16):v for k,v in updates.items()});return MiningPanelConfiguration('fixture',fields)
def fixture(**updates):
    o=dict(storage_5690b8=0,storage_helper_4fe384=0,inn_helper_46fe90=0,
           full_463ac0=0,repair_item_4634a4=0,tail_gate_4631a8=1)
    o.update(updates);return o

class MiningMaintenanceTests(unittest.TestCase):
    def test_storage_short_circuit(self):
        p=plan_mining_maintenance(cfg(),{'storage_5690b8':1})
        self.assertTrue(p.complete);self.assertEqual(p.calls,())

    def test_mattock_change_uses_fresh_second_name_and_returns_early(self):
        o=fixture(mattock_first_equal=0,mattock_second_equal=1,change_item_4634a4=1,
            change_quantity_46358c=0,replacement_slot_477544=17,**{'returned:004651bc':True})
        p=plan_mining_maintenance(cfg(**{'603b':1}),o)
        self.assertEqual(p.status,'change_mattock_planned');self.assertEqual(p.calls,(('004651bc',(17,)),))

    def test_mattock_minus_one_is_no_replacement(self):
        o=fixture(mattock_first_equal=1,change_item_4634a4=1,change_quantity_46358c=0,replacement_slot_477544=0xffffffff)
        self.assertEqual(plan_mining_maintenance(cfg(**{'603b':1}),o).status,'tail_gate_blocked')

    def test_hammer_4000_boundary_stamps_and_continues(self):
        o=fixture(hammer_item_4634a4=1,hammer_quantity_46358c=0,magic_hammer_present_463950=1,
            hammer_gate_4631a8=0,hammer_tick=3999,hammer_qword=0,
            hammer_actor_462650=8,hammer_stamp_tick=4001,**{'returned:00465640':True})
        self.assertEqual(plan_mining_maintenance(cfg(**{'6038':1}),o).calls,())
        o['hammer_tick']=4000;p=plan_mining_maintenance(cfg(**{'6038':1}),o)
        self.assertEqual(p.calls,(('00465640',(0x77ada,8)),))
        self.assertEqual(p.writes,((0x553de0,4001,64),));self.assertEqual(p.status,'tail_gate_blocked')

    def test_fresh_hammer_stamp_delays_npc_repair(self):
        o=fixture(hammer_item_4634a4=1,hammer_quantity_46358c=0,magic_hammer_present_463950=1,
            hammer_gate_4631a8=0,hammer_tick=4000,hammer_qword=0,hammer_actor_462650=8,
            hammer_stamp_tick=4001,repair_item_4634a4=1,repair_quantity_46358c=0,
            repair_hammer_tick=4002,**{'returned:00465640':True})
        p=plan_mining_maintenance(cfg(**{'6038':1,'6037':1}),o)
        self.assertEqual(p.status,'repair_hammer_retry_wait');self.assertEqual(len(p.calls),1)

    def test_missing_hammer_stop_priority(self):
        o=fixture(hammer_item_4634a4=1,hammer_quantity_46358c=0,magic_hammer_present_463950=0,
            **{'returned:00464d10':True,'returned:0040ae0c':True})
        p=plan_mining_maintenance(cfg(**{'6038':1,'6039':1}),o)
        self.assertEqual(p.status,'missing_hammer_stop_planned')
        self.assertEqual([a for a,_ in p.calls],['00464d10','0040ae0c'])

    def test_vip_strict_1000_and_operation4_reset_widths(self):
        o=fixture(full_463ac0=1,vip_tick=1000,vip_qword=0)
        c=cfg(**{'604c':1})
        self.assertEqual(plan_mining_maintenance(c,o).status,'tail_gate_blocked')
        o['vip_tick']=1001;p=plan_mining_maintenance(c,o)
        self.assertEqual(p.status,'vip_operation4_planned')
        self.assertEqual(p.writes,((0x5690bc,4,32),(0x5690c0,0,8),(0x5690c1,0,8),
            (0x5690c4,0,32),(0x5690c8,0,32),(0x5690cc,0,32),(0x5690b8,1,8)))

    def test_alarm_precedes_ore_crash(self):
        o=fixture(full_463ac0=1,**{'returned:00464d10':True,'returned:00404260':True,'returned:0040ae0c':True})
        p=plan_mining_maintenance(cfg(**{'6036':1,'6028':1}),o)
        self.assertEqual(p.status,'full_alarm_stop_planned')
        self.assertEqual([a for a,_ in p.calls],['00464d10','00404260','0040ae0c'])

    def test_crash_count_is_signed_positive(self):
        for count in (0,0xffffffff):
            p=plan_mining_maintenance(cfg(**{'6028':1}),fixture(full_463ac0=1,ore_count_477770=count))
            self.assertEqual(p.status,'tail_gate_blocked')
        p=plan_mining_maintenance(cfg(**{'6028':1}),fixture(full_463ac0=1,ore_count_477770=1,**{'returned:004779dc':True}))
        self.assertEqual(p.status,'ore_crash_start_planned')

    def test_repair_quantity_unsigned_nonzero_skips_route(self):
        p=plan_mining_maintenance(cfg(**{'6037':1}),fixture(repair_item_4634a4=1,repair_quantity_46358c=0xffffffff))
        self.assertEqual(p.status,'tail_gate_blocked')

    def test_region_route_recovered_but_helper_return_remains_explicit(self):
        o=fixture(repair_item_4634a4=1,repair_quantity_46358c=0,repair_region_1_equal=1,repair_distance_fpu_ah=0,repair_use_constructor_defaults=1,
            **{'returned:00465678':True})
        p=plan_mining_maintenance(cfg(**{'6037':1}),o)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'returned:004eb9f4')
        self.assertTrue(p.repair_route.complete);self.assertEqual(p.repair_route.name,'EMCMiningRoute2')
        self.assertFalse(p.repair_route.native_pointer_blob_reconstructed)
        o['returned:004eb9f4']=True;p=plan_mining_maintenance(cfg(**{'6037':1}),o)
        self.assertTrue(p.complete);self.assertEqual(p.status,'tail_gate_blocked')
        self.assertEqual([a for a,_ in p.calls],['00465678','004eb9f4'])

    def test_constructor_route_not_assumed_to_be_current_runtime_vector(self):
        o=fixture(repair_item_4634a4=1,repair_quantity_46358c=0,repair_region_1_equal=1,repair_distance_fpu_ah=0x40)
        p=plan_mining_maintenance(cfg(**{'6037':1}),o)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'repair_use_constructor_defaults')
        o['repair_use_constructor_defaults']=0
        self.assertEqual(plan_mining_maintenance(cfg(**{'6037':1}),o).missing,'fresh_repair_vector_capture')

    def test_mode3_routes_to_mine_then_still_reaches_tail(self):
        o=fixture(repair_item_4634a4=1,repair_quantity_46358c=0,
                  **{'returned:004ebca0':True})
        p=plan_mining_maintenance(cfg(**{'6037':1,'5ff8':3}),o)
        self.assertTrue(p.complete);self.assertEqual(p.status,'tail_gate_blocked')
        self.assertEqual(p.calls,(('004ebca0',(0x5687a8,('literal',0x5293d5))),))

    def test_tail_ftol_boundaries_and_signed_float_coordinates(self):
        o=fixture(tail_gate_4631a8=0,tail_actor_gate_45dc44=0,tail_distance_ftol_dword=1)
        self.assertEqual(plan_mining_maintenance(cfg(),o).status,'near_start')
        o.update(tail_distance_ftol_dword=2,tail_state_4677f0=0,start_x_dword=0xffffffff,start_y_dword=20,
                 **{'returned:004646b4':True})
        self.assertEqual(plan_mining_maintenance(cfg(),o).calls,(('004646b4',(-1.0,20.0)),))
        o.update(tail_distance_ftol_dword=50,**{'returned:00477bd4':True})
        self.assertEqual(plan_mining_maintenance(cfg(),o).calls,(('00477bd4',('self',)),))

    def test_missing_stop_return_is_only_prefix(self):
        p=plan_mining_maintenance(cfg(**{'6036':1}),fixture(full_463ac0=1))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'returned:00464d10')

if __name__=='__main__':unittest.main()
