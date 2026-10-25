import unittest
from enchant_engine import EnchantObservation, enchant_step, TEMPLATE
from npc_route_engine import NpcRouteFrame, npc_route_step


class EnchantTests(unittest.TestCase):
    def fields(self,phase=2,**changes):
        result={0x6c4:phase,0x6c8:0,0x604:8,0x60c:0x100000,0x6d0:0,0x6d4:0}
        result.update({int(k,16):v for k,v in changes.items()})
        return result

    def observation(self,now=1000,option=b'0',parsed=0,zone=b'Moradon',target=8,level=35):
        return EnchantObservation(now,option,parsed,zone,target,level)

    def test_initial_target_selection_before_current_target_observation(self):
        r=enchant_step(self.fields(0),self.observation(target=None))
        self.assertEqual(r.calls,('0046493c',));self.assertEqual(r.fields[0x6c8],1)

    def test_changed_target_reselects_without_advancing_phase(self):
        r=enchant_step(self.fields(4),self.observation(target=9))
        self.assertEqual(r.calls,('0046493c',));self.assertEqual(r.returned_phase,4)

    def test_wait499_vs500_advances_only_on_later_call(self):
        fields=self.fields(2,**{'6c8':1,'6d0':1000})
        self.assertEqual(enchant_step(fields,self.observation(now=1499)).returned_phase,2)
        r=enchant_step(fields,self.observation(now=1500))
        self.assertEqual(r.returned_phase,3);self.assertEqual(r.calls,())
        self.assertEqual((r.fields[0x6c8],r.fields[0x6d0],r.fields[0x6d4]),(0,0,0))

    def test_dword_clock_wrap_keeps_signed_qword_wait(self):
        r=enchant_step(self.fields(2,**{'6c8':1,'6d0':0xfffffff0}),self.observation(now=500))
        self.assertEqual(r.status,'waiting');self.assertEqual(r.returned_phase,2)

    def test_parameter_parse_required_even_when_waiting(self):
        r=enchant_step(self.fields(2,**{'6c8':1}),self.observation(parsed=None))
        self.assertEqual(r.status,'needs_observation')

    def test_phase1_interaction_and_phase7_wait(self):
        r=enchant_step(self.fields(1),self.observation());self.assertEqual(r.calls,('0046fb38',))
        r=enchant_step(self.fields(7),self.observation(zone=None));self.assertEqual(r.calls,())
        self.assertEqual(r.fields[0x6c8],1)

    def test_zone_script_bytes_and_unmatched_template(self):
        for zone,byte7,byte9 in ((b'Karus Eslant',0x35,0x4b),(b'Luferson',0x35,0x4b),
                (b'Human Eslant',0x37,0x45),(b'EMC',0x37,0x45),(b'Moradon',0x38,0x4e),(b'other',0,0x4b)):
            packet=enchant_step(self.fields(),self.observation(zone=zone)).queue_payloads[0]
            self.assertEqual(len(packet),21);self.assertEqual((packet[7],packet[9]),(byte7,byte9))

    def test_options0_to3_same_initial_packet_until_phase6(self):
        packets=[enchant_step(self.fields(2),self.observation(option=str(i).encode(),parsed=i)).queue_payloads[0]
                 for i in range(4)]
        self.assertEqual(len(set(packets)),1)
        for i in range(4):
            r=enchant_step(self.fields(6),self.observation(option=str(i).encode(),parsed=i))
            self.assertEqual(r.queue_payloads[0][1],i)

    def test_option4_phase2_select3_phase3_signed35_boundary(self):
        self.assertEqual(enchant_step(self.fields(2),self.observation(option=b'4',parsed=4)).queue_payloads[0][1],3)
        for level,value in ((35,0),(36,1),(-1,0)):
            r=enchant_step(self.fields(3),self.observation(option=b'4',parsed=4,level=level))
            self.assertEqual(r.queue_payloads[0][1],value)

    def test_option4_phases4_to6_skip_without_wait_or_queue(self):
        for phase in (4,5,6):
            r=enchant_step(self.fields(phase),self.observation(option=b'4',parsed=4))
            self.assertEqual(r.returned_phase,phase+1);self.assertEqual(r.queue_payloads,())
            self.assertEqual(r.fields[0x6c8],0)

    def test_numeric04_parses_but_exact_text_does_not_match(self):
        r=enchant_step(self.fields(2),self.observation(option=b'04',parsed=4))
        self.assertEqual(r.status,'pending');self.assertEqual(r.queue_payloads,())

    def test_numeric256_does_not_enter_option0_branch(self):
        r=enchant_step(self.fields(6),self.observation(option=b'256',parsed=256))
        self.assertEqual(r.queue_payloads,());self.assertEqual(r.status,'pending')

    def test_phase8_return_has_no_queued_action(self):
        r=enchant_step(self.fields(8),self.observation())
        self.assertEqual(r.returned_phase,8);self.assertEqual(r.queue_payloads,())

    def test_parent_npc_completes_on_7_wait_to8(self):
        fields=self.fields(7,**{'6c8':1,'6d0':1000,'6c0':1})
        r=npc_route_step(NpcRouteFrame(9,fields),{'Royal National Enchanter':True},
                         enchant_observation=self.observation(now=1500))
        self.assertTrue(r.returned_true);self.assertEqual(r.frame.phase,11)
        self.assertEqual((r.frame.fields[0x6c4],r.frame.fields[0x6c0]),(0,0))

    def test_parent_keeps_nested_packet_plan(self):
        fields=self.fields(2,**{'6c0':1})
        r=npc_route_step(NpcRouteFrame(9,fields),{'Royal National Enchanter':True},
                         enchant_observation=self.observation())
        self.assertEqual(len(r.queue_payloads),1);self.assertFalse(r.returned_true)
