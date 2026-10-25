import unittest
from dataclasses import replace
from chat_skill_consumers import ChatConsumerObservation as O,ChatConsumerFrame,plan_chat_consumer

def sample(**updates):
 v=dict(pending_byte=1,lock_byte=0,kind_dword=1,level_eax=30,mage_gate_eax=5,mage_gate2_eax=2,
        lookup_sender_dword=0xffff1234,party_index_eax=0,movement_root_slot=0x1000,movement_root_eax=0x2000,
        movement_offset=0x20,movement_state_eax=0,target_root_slot=0x3000,target_root_eax=0x4000,
        target_offset=0x30,target_state_eax=0,alternate_byte=1,generic_sender_dword=0xffff5678,
        generic_skill_eax=1,post_delay_tick=100,direct_sender_dword=0xffff9999,
        direct_sender_word=0x1234,direct_sender_push_dword=0xbeef1234,fresh_target_eax=0xffffffff)
 v.update(updates)
 if 'kind_second_dword' not in updates:v['kind_second_dword']=v['kind_dword']
 labels=('level','mage_gate','mage_gate2','party_lookup','movement_root','movement_state','stop_movement',
         'target_probe','target_root','target_state','fresh_target_id','target_action','select_index',
         'generic_skill','post_delay_tick','direct_mage','direct_sw','direct_wolf')
 return O(v,{k:True for k in labels})
def calls(p):return [s for s in p.steps if s[0]=='opaque_helper']

class ChatConsumerTests(unittest.TestCase):
 def test_early_pending_lock_and_unsupported_kind_preserve_request(self):
  for family in ('Mage','Rogue'):
   for fields in (dict(pending_byte=0),dict(lock_byte=1),dict(kind_dword=99)):
    p=plan_chat_consumer(family,0x5000,sample(**fields))
    self.assertTrue(p.complete);self.assertEqual(p.return_low_al,0);self.assertEqual(p.stores,())

 def test_mage_signed_gate_failure_retains_rogue_level_failure_clears(self):
  for eax in (0,9,0xffffffff,0x80000000):
   p=plan_chat_consumer('Mage',0x5000,sample(level_eax=eax));self.assertEqual(p.stores,())
   p=plan_chat_consumer('Rogue',0x5000,sample(level_eax=eax));self.assertEqual(p.stores,((0x5693a0,1,0),))
  self.assertEqual(plan_chat_consumer('Rogue',0x5000,sample(kind_dword=2,level_eax=29)).return_low_al,0)

 def test_mage_all_signed_gates_and_party_index(self):
  for field,value in (('mage_gate_eax',4),('mage_gate2_eax',1),('party_index_eax',0xffffffff)):
   p=plan_chat_consumer('Mage',0x5000,sample(**{field:value}));self.assertEqual(p.return_low_al,0);self.assertEqual(p.stores,())

 def test_rogue_kind_two_comparison_reads_fresh_global(self):
  p=plan_chat_consumer('Rogue',0x5000,sample(kind_dword=99,kind_second_dword=2))
  self.assertEqual(p.return_low_al,1)
  self.assertEqual(next(s for s in calls(p) if s[3]=='generic_skill')[2][1],30)
  p=plan_chat_consumer('Rogue',0x5000,sample(kind_dword=2,kind_second_dword=99))
  self.assertEqual(p.return_low_al,0);self.assertEqual(p.stores,())
  self.assertFalse(any(s[3]=='level' for s in calls(p)))

 def test_generic_ids_full_eax_and_fresh_sender(self):
  for family,kind,skill in (('Mage',1,4),('Rogue',1,10),('Rogue',2,30)):
   p=plan_chat_consumer(family,0x5000,sample(kind_dword=kind,generic_skill_eax=0x100))
   self.assertEqual(p.return_low_al,1)
   call=next(s for s in calls(p) if s[3]=='generic_skill')
   self.assertEqual(call[2],(0xffff5678,skill))
   self.assertEqual(p.stores,((0x561f80,4,2000),(0x561f84,4,100),(0x561f7e,1,1),(0x5693a0,1,0)))
   self.assertFalse(p.true_full_eax_verified);self.assertFalse(p.skill_effect_verified)

 def test_generic_failure_retains_pending_after_other_helpers(self):
  p=plan_chat_consumer('Mage',0x5000,sample(generic_skill_eax=0,movement_state_eax=1,target_state_eax=1))
  self.assertEqual(p.return_low_al,0);self.assertEqual(p.stores,())
  self.assertTrue(any(s[3]=='stop_movement' for s in calls(p)))
  self.assertTrue(any(s[3]=='target_action' for s in calls(p)))

 def test_test_clears_carry_no_initial_target_eax_needed(self):
  p=plan_chat_consumer('Rogue',0x5000,sample(target_state_eax=1))
  self.assertTrue(p.complete)
  self.assertIn(('TEST_EAX_EAX_CF',0,'source_JC_not_taken'),p.steps)
  self.assertEqual(next(s for s in calls(p) if s[3]=='target_action')[2],(0,0xffffffff))

 def test_movement_state_full_dword_and_wrapped_address(self):
  p=plan_chat_consumer('Mage',0x5000,sample(movement_root_eax=0xfffffff8,movement_state_eax=0x100))
  self.assertTrue(any(s[3]=='stop_movement' for s in calls(p)))
  self.assertEqual(next(s for s in calls(p) if s[3]=='movement_state')[2],(0x18,))

 def test_direct_mage_lock_precedes_call_pending_clear_follows_return(self):
  o=sample(alternate_byte=0);r=dict(o.normal_returns);r['direct_mage']=False
  p=plan_chat_consumer('Mage',0x5000,O(o.values,r))
  self.assertFalse(p.complete);self.assertEqual(p.stores,((0x561f80,4,1500),(0x561f84,4,100),(0x561f7e,1,1)))
  self.assertEqual(next(s for s in calls(p) if s[3]=='direct_mage')[2],(0xffff9999,0x5000))

 def test_rogue_direct_sw_observed_upper_edx_not_zero_extended(self):
  p=plan_chat_consumer('Rogue',0x5000,sample(alternate_byte=0))
  self.assertEqual(next(s for s in calls(p) if s[3]=='direct_sw')[2],(0xbeef1234,0x5000))
  with self.assertRaises(ValueError):plan_chat_consumer('Rogue',0x5000,sample(alternate_byte=0,direct_sender_push_dword=0x9999))

 def test_direct_wolf_does_not_require_sender_argument(self):
  o=sample(kind_dword=2,alternate_byte=0);v={k:v for k,v in o.values.items() if not k.startswith('direct_sender')}
  p=plan_chat_consumer('Rogue',0x5000,O(v,o.normal_returns))
  self.assertTrue(p.complete);self.assertEqual(next(s for s in calls(p) if s[3]=='direct_wolf')[2],(0x5000,))

 def test_each_reached_value_and_call_return_is_required(self):
  for family,o in (('Mage',sample(target_state_eax=1)),('Mage',sample(alternate_byte=0)),('Rogue',sample()),('Rogue',sample(alternate_byte=0,kind_dword=2))):
   full=plan_chat_consumer(family,0x5000,o);self.assertTrue(full.complete)
   for step in full.steps:
    if step[0]=='source_value':
     v=dict(o.values);del v[step[1]];self.assertFalse(plan_chat_consumer(family,0x5000,O(v,o.normal_returns)).complete,step)
    elif step[0]=='opaque_helper':
     r=dict(o.normal_returns);r[step[3]]=False;self.assertFalse(plan_chat_consumer(family,0x5000,O(o.values,r)).complete,step)

 def test_frame_retains_delay_prefix_and_prior_reads_at_late_direct_gap(self):
  f=ChatConsumerFrame('Rogue',0x5000);o=sample(alternate_byte=0)
  p=f.advance(replace(o,normal_returns={**o.normal_returns,'direct_sw':False}))
  self.assertFalse(p.complete);self.assertEqual(len(p.stores),3)
  final=f.advance(O(normal_returns={'direct_sw':True}))
  self.assertTrue(final.complete);self.assertEqual(final.stores[-1],(0x5693a0,1,0))
  self.assertIs(f.advance(O()),final)

if __name__=='__main__':unittest.main()
