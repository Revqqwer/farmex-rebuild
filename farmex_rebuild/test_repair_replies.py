import unittest
from dataclasses import replace
from repair_replies import plan_repair_reply,replay_repair_reply
from repair_engine import RepairObservation
from mining_configuration import MiningPanelConfiguration
from mining_npc_pipeline import replay_mining_npc
from npc_route_engine import NpcRouteFrame,NpcRouteObservation
from repair_refresh import RepairRefreshObservation

class RepairReplyTests(unittest.TestCase):
    def frame(self):return NpcRouteFrame(3,{0x604:17,0x63c:1,0x640:1,0x644:0},
        {0x561faa:1,0x561f58:1,0x56fad2:0,0x56fae4:0,0x553e44:1})

    def test_source_short_circuits_inactive_before_status_read(self):
        self.assertEqual(plan_repair_reply(b'\x3b',0).status,'repair_inactive')
        self.assertTrue(plan_repair_reply(b'\x24',None).complete)
        self.assertFalse(plan_repair_reply(b'',0).complete)

    def test_active_and_status_missing_are_unknown_not_zero(self):
        self.assertEqual(plan_repair_reply(b'\x3b\0',None).missing,'global00561faa')
        self.assertEqual(plan_repair_reply(b'\x3b',1).missing,'reply status byte1')

    def test_all_non_success_status_bytes_write_without_slot_or_refresh(self):
        for status in range(256):
            if status==1:continue
            p=plan_repair_reply(bytes((0x3b,status)),255)
            self.assertEqual(p.global_writes,((0x561fb0,status),))
            self.assertEqual(p.calls,());self.assertEqual(p.dispatch_return,0)
            self.assertTrue(p.handled)
            self.assertFalse(p.server_acknowledged)

    def test_success_requires_exact_readable_dword_prefix(self):
        for count in range(2,6):
            p=plan_repair_reply((b'\x3b\1'+b'\xff'*4)[:count],1,current_slot=7,refresh_returned=True)
            self.assertFalse(p.complete);self.assertFalse(p.global_writes)
        p=plan_repair_reply(b'\x3b\1\x78\x56\x34\x12trailing',1,current_slot=255,refresh_returned=True)
        self.assertEqual(p.refresh_value,0x12345678)
        self.assertEqual(p.calls, (('004d804f',(2,)),('00467f10',(0x12345678,255))))
        self.assertEqual(p.global_writes,((0x561fb0,1),))

    def test_success_refresh_order_precedes_ack_write(self):
        packet=b'\x3b\1'+b'\0'*4
        self.assertEqual(plan_repair_reply(packet,1).missing,'global00561fac')
        for returned in (None,False):
            p=plan_repair_reply(packet,1,current_slot=1,refresh_returned=returned)
            self.assertEqual(p.missing,'00467f10 normal return')
            self.assertFalse(p.global_writes);self.assertIsNone(p.dispatch_return)

    def test_success_without_refresh_preserves_entire_frame(self):
        frame=replace(self.frame(),globals={**self.frame().globals,0x561fb0:0xffffffff,0x561fac:1})
        r=replay_repair_reply(frame,b'\x3b\1'+b'\0'*4)
        self.assertIs(r.frame,frame);self.assertFalse(r.plan.complete)

    def test_repair_request_no_response_then_failure_response_advances_only_after_timer(self):
        cfg=MiningPanelConfiguration('fixture',{0x603a:0,0x604c:0})
        def step(frame,now,**kw):return replay_mining_npc(cfg,NpcRouteObservation(frame,{'Sundries':True},
            repair_observation=RepairObservation(now,current_target=17,**kw)),1)
        requested=step(self.frame(),1000,item_id_4634a4=100,durability_46358c=1,
            maximum_4635e0=100,producer_item_id_4634a4=200)
        self.assertEqual(requested.result.queue_payloads[0].hex(),'3b010111000000c8000000')
        self.assertEqual(requested.frame.globals[0x561fb0],0xffffffff)
        waiting=step(requested.frame,1200)
        self.assertEqual(waiting.frame.fields[0x640],1)
        self.assertEqual(waiting.frame.fields[0x644],1)
        self.assertFalse(waiting.result.queue_payloads)
        applied=replay_repair_reply(waiting.frame,b'\x3b\0')
        self.assertTrue(applied.plan.handled);self.assertEqual(applied.frame.globals[0x561fb0],0)
        before=step(applied.frame,1199)
        self.assertEqual(before.frame.fields[0x640],1)
        after=step(before.frame,1200)
        self.assertEqual(after.frame.fields[0x640],4)
        self.assertEqual(after.frame.fields[0x644],0)
        self.assertEqual(after.frame.phase,3)
        self.assertFalse(after.server_acknowledged)
        self.assertFalse(applied.plan.server_acknowledged)

    def test_reply_does_not_invent_npc_or_item_correlation(self):
        # This source branch reads neither IDs nor the pending-kind561fab.
        p=plan_repair_reply(b'\x3b\2',1)
        self.assertTrue(p.handled);self.assertEqual(p.reply_status,2)

    def refresh_observation(self):
        return RepairRefreshObservation(0x12345678,1,
            {0x553e80:0x1000,0x5540a8:0x20,0x5540ac:0x80,0x5540b8:0x400,
             0x553e46:0,0x553ef4:0x8000},
            ((0x1000,0x2000),(0x2020,0x3000),(0x3084,0x4000),
             (0x1000,0x5000),(0x5020,0x6000)),second_profile_byte=0)

    def test_optional_refresh_plan_does_not_substitute_for_normal_return(self):
        obs=self.refresh_observation();packet=b'\x3b\1\x78\x56\x34\x12'
        p=plan_repair_reply(packet,1,current_slot=1,refresh_observation=obs)
        self.assertTrue(p.refresh_plan.complete);self.assertFalse(p.complete)
        self.assertEqual(p.missing,'00467f10 normal return');self.assertFalse(p.global_writes)
        p=plan_repair_reply(packet,1,current_slot=1,refresh_observation=obs,refresh_returned=True)
        self.assertTrue(p.complete);self.assertEqual(p.global_writes,((0x561fb0,1),))
        self.assertFalse(p.refresh_plan.helper_return_verified)

    def test_incomplete_or_conflicting_refresh_operands_cannot_authorize_ack(self):
        obs=self.refresh_observation();packet=b'\x3b\1\x78\x56\x34\x12'
        p=plan_repair_reply(packet,1,current_slot=1,
            refresh_observation=replace(obs,protected_samples=()),refresh_returned=True)
        self.assertFalse(p.complete);self.assertFalse(p.global_writes)
        self.assertTrue(p.missing.startswith('refresh:protected sample0'))
        for bad in (replace(obs,value=0),replace(obs,slot=2)):
            with self.assertRaises(ValueError):plan_repair_reply(packet,1,current_slot=1,refresh_observation=bad,refresh_returned=True)

    def test_mutable_or_out_of_range_observations_rejected(self):
        for packet,active,slot in ((bytearray(b'\x3b\0'),1,None),(b'\x3b\0',True,None),(b'\x3b\0',256,None),(b'\x3b\1'+b'\0'*4,1,256)):
            with self.assertRaises(ValueError):plan_repair_reply(packet,active,current_slot=slot)

if __name__=='__main__':unittest.main()
