import unittest
from chat_skill_consumers import ChatConsumerObservation as O,ChatConsumerFrame,plan_chat_consumer

def sample(kind=1,**updates):
 v=dict(pending_byte=1,lock_byte=0,context_fc_dword=700,context_104_dword=701,
        buff_resolver_eax=702,ac_resolver_eax=703,priest_gate_eax=2,und_gate_eax=54,kind_gate_eax=99,
        lookup_sender_dword=0xffff1234,party_index_eax=0,object_sender_dword=0xffff5678,object_eax=0x2000,
        target_x_offset=0x10,target_x_f32_bits=0x3f800000,target_y_offset=0x14,target_y_f32_bits=0x40000000,
        distance_integer_eax=28,target_root_slot=0x1000,target_root_eax=0x3000,target_offset=0x18,target_state_eax=0,
        fresh_target_eax=0xffffffff,alternate_byte=1,generic_sender_dword=0xffff9999,generic_skill_eax=1,
        post_delay_tick=100,stamp_sender_dword=0xffff2222,stamp_index_eax=0,party_stamp_tick=101,
        movement_root_slot=0x1000,movement_root_eax=0x3000,movement_offset=0x20,movement_state_eax=0,
        direct_sender_word=0x1234,direct_sender_push_dword=0xbeef1234,direct_sender_dword=0xcafe1234)
 v.update({'kind_%d_dword'%i:kind for i in range(1,7)});v.update(updates)
 labels=('buff_resolver','ac_resolver','priest_gate','und_gate','kind_gate','party_lookup',
         'target_probe','target_root','target_state','fresh_target_id','target_action','select_index',
         'object_lookup','target_x','target_y','distance','distance_integer_convert',
         'generic_skill','post_delay_tick','stamp_lookup','party_stamp_tick',
         'movement_root','movement_state','stop_movement','direct_skill')
 return O(v,{k:True for k in labels})
def plan(o):return plan_chat_consumer('Priest',0x5000,o)
def calls(p):return [s for s in p.steps if s[0]=='opaque_helper']

class PriestConsumerTests(unittest.TestCase):
 def test_six_generic_skill_ids(self):
  for kind,skill in ((1,700),(2,701),(3,0x28e),(4,4),(5,0x20d),(6,0x217)):
   p=plan(sample(kind));self.assertTrue(p.complete);self.assertEqual(p.return_low_al,1)
   self.assertEqual(next(s for s in calls(p) if s[3]=='generic_skill')[2],(0xffff9999,skill))
   self.assertEqual(p.stores[:4],((0x561f80,4,2000),(0x561f84,4,100),(0x561f7e,1,1),(0x5693a0,1,0)))

 def test_both_skill_resolvers_precede_even_unsupported_kind(self):
  p=plan(sample(99,context_fc_dword=0,context_104_dword=0xffffffff))
  self.assertTrue(p.complete);self.assertEqual(p.return_low_al,0)
  self.assertEqual([s[3] for s in calls(p)],['buff_resolver','ac_resolver'])
  p=plan(sample(1,context_fc_dword=0,buff_resolver_eax=0))
  self.assertEqual(next(s for s in calls(p) if s[3]=='generic_skill')[2][1],0)

 def test_positive_fields_skip_resolvers_and_kind_reads_are_fresh(self):
  p=plan(sample(6,kind_1_dword=99,kind_2_dword=2))
  self.assertEqual(next(s for s in calls(p) if s[3]=='generic_skill')[2][1],701)
  self.assertFalse(any(s[3] in ('buff_resolver','ac_resolver') for s in calls(p)))

 def test_pending_lock_skip_all_resolvers(self):
  for values in ({'pending_byte':0},{'lock_byte':1}):
   p=plan(sample(**values));self.assertEqual(p.return_low_al,0);self.assertEqual(calls(p),[]);self.assertEqual(p.stores,())

 def test_signed_early_gates_clear_pending(self):
  for kind,field,minimum in ((1,'priest_gate_eax',2),(3,'und_gate_eax',54),(3,'priest_gate_eax',2),
                              (4,'kind_gate_eax',4),(5,'kind_gate_eax',25),(6,'kind_gate_eax',35)):
   for raw in (minimum-1,0xffffffff,0x80000000):
    p=plan(sample(kind,**{field:raw}));self.assertEqual(p.return_low_al,0)
    self.assertEqual(p.stores,((0x5693a0,1,0),))

 def test_negative_party_index_clears_for_buff_und(self):
  for kind in (1,3):
   p=plan(sample(kind,party_index_eax=0xffffffff));self.assertEqual(p.return_low_al,0)
   self.assertEqual(p.stores,((0x5693a0,1,0),));self.assertFalse(any(s[3]=='object_lookup' for s in calls(p)))

 def test_null_object_allowed_only_buff_und(self):
  for kind in range(1,7):
   p=plan(sample(kind,object_eax=0));self.assertTrue(p.complete)
   self.assertEqual(p.return_low_al,int(kind in (1,3)))
   self.assertFalse(any(s[3]=='distance' for s in calls(p)))

 def test_distance_is_observed_signed_integer_not_float_guess(self):
  for raw,ok in ((28,True),(29,False),(0xffffffff,True),(0x80000000,True)):
   p=plan(sample(2,distance_integer_eax=raw));self.assertEqual(p.return_low_al,int(ok))
  p=plan(sample(2));self.assertEqual(next(s for s in calls(p) if s[3]=='distance')[2],(0x40000000,0x3f800000))

 def test_generic_failure_preserves_pending(self):
  p=plan(sample(4,generic_skill_eax=0));self.assertEqual(p.return_low_al,0);self.assertEqual(p.stores,())
  self.assertTrue(any(s[3]=='target_probe' for s in calls(p)))
  self.assertFalse(any(s[3]=='stamp_lookup' for s in calls(p)))

 def test_party_stamp_only_four_kinds_and_fresh_tick(self):
  for kind in range(1,7):
   p=plan(sample(kind,stamp_index_eax=2))
   stamp=(0x569714,4,101)
   self.assertEqual(stamp in p.stores,kind in (2,4,5,6))
  p=plan(sample(2,stamp_index_eax=0xffffffff));self.assertEqual(len(p.stores),4)
  p=plan(sample(2,stamp_index_eax=0x40000000));self.assertEqual(p.stores[-1],(0x56970c,4,101))

 def test_direct_clear_precedes_helper_gap_for_all_kinds(self):
  for kind in range(1,7):
   o=sample(kind,alternate_byte=0);r=dict(o.normal_returns);r['direct_skill']=False
   p=plan(O(o.values,r));self.assertFalse(p.complete)
   self.assertEqual(p.stores[-1],(0x5693a0,1,0))
   call=next(s for s in calls(p) if s[3]=='direct_skill')
   expected={1:'004d3568',2:'004d3568',3:'004d3568',4:'004d36ac',5:'004d3674',6:'004d3690'}[kind]
   self.assertEqual(call[1],expected)

 def test_direct_word_push_ambiguity_and_str_full_dword(self):
  p=plan(sample(1,alternate_byte=0));self.assertEqual(next(s for s in calls(p) if s[3]=='direct_skill')[2],(0xbeef1234,700,0x5000))
  p=plan(sample(4,alternate_byte=0));self.assertEqual(next(s for s in calls(p) if s[3]=='direct_skill')[2],(0xcafe1234,0x5000))
  with self.assertRaises(ValueError):plan(sample(6,alternate_byte=0,direct_sender_push_dword=0x9999))

 def test_every_reached_value_and_call_gap(self):
  for kind,o in ((1,sample(1,context_fc_dword=0,context_104_dword=0,target_state_eax=1)),
                 (2,sample(2)),(3,sample(3,alternate_byte=0)),(6,sample(6,alternate_byte=0,movement_state_eax=1))):
   full=plan(o);self.assertTrue(full.complete)
   for s in full.steps:
    if s[0]=='source_value':
     v=dict(o.values);del v[s[1]];self.assertFalse(plan(O(v,o.normal_returns)).complete,s)
    elif s[0]=='opaque_helper':
     r=dict(o.normal_returns);r[s[3]]=False;self.assertFalse(plan(O(o.values,r)).complete,s)

 def test_frame_preserves_pending_clear_before_late_stamp_gap(self):
  f=ChatConsumerFrame('Priest',0x5000);o=sample(6,context_fc_dword=0,context_104_dword=0,target_state_eax=1)
  r=dict(o.normal_returns);r['party_stamp_tick']=False;p=f.advance(O(o.values,r))
  self.assertFalse(p.complete);self.assertEqual(p.stores[-1],(0x5693a0,1,0))
  final=f.advance(O({'party_stamp_tick':999},{'party_stamp_tick':True}))
  self.assertTrue(final.complete);self.assertEqual(final.stores[-1],(0x56970c,4,999))
  self.assertIs(f.advance(O()),final)

if __name__=='__main__':unittest.main()
