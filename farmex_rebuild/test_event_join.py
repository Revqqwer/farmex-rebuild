import unittest
from dataclasses import replace
from event_join import *

def sample(**updates):
 v=dict(first_chaos_byte=0,first_bdw_byte=0,first_royale_byte=0,first_tick_eax=200,first_low=0,first_high=0,
 priority_chaos_byte=0,priority_bdw_byte=0,priority_royale_byte=0,first_post_tick_eax=201,
 second_ft_byte=0,second_utc_byte=0,second_jr_byte=0,second_tick_eax=201,second_low=0,second_high=0,
 target_first_eax=3001,target_second_eax=3001,target_third_eax=3002,
 priority_ft_byte=0,priority_utc_byte=0,priority_jr_byte=0,nation_eax=1,second_post_tick_eax=202)
 n={k:True for k in ('entry_setup','first_tick','first_post_tick','second_tick','second_post_tick','chaos_join','bdw_join','royale_join',
 'target_first','target_second','target_third','target_prepare','target_fallback','nation','ft_copy','utc_copy','jr_copy','ft_enqueue','utc_enqueue','jr_enqueue0','jr_enqueue200','return')}
 v.update(updates);return EventJoinObservation(v,n)

class EventJoinTests(unittest.TestCase):
 def test_six_checkbox_mapping_is_source_order_not_visual_order(self):
  values={p:i%2==0 for i,p in enumerate(EVENT_JOIN_INPUTS)}
  self.assertEqual(dict(compile_event_join(values)),{0x68:1,0x69:0,0x6a:1,0x6b:0,0x6c:1,0x6d:0})
  with self.assertRaises(ValueError):compile_event_join({p:1 for p in EVENT_JOIN_INPUTS})
 def test_bounded_producer_raw_AL_and_consumed_getter_return(self):
  f=EventSettingsFrame();self.assertFalse(f.advance(EventSettingsObservation()).complete)
  p=f.advance(EventSettingsObservation(True,(True,),()));self.assertEqual(p.missing,'getter0 EAX')
  p=f.advance(EventSettingsObservation(True,(False,True,True,True,True,True),(0x100,0x101,0xff,2,3,4)))
  self.assertTrue(p.complete);self.assertEqual([v for at,width,v in p.stores],[0,1,255,2,3,4])
  self.assertFalse(p.whole_producer_verified);self.assertEqual(p.next_source_address,0x457d02)
  self.assertEqual(f.advance(EventSettingsObservation()).stores,p.stores)
 def test_disabled_groups_need_no_clocks_or_targets(self):
  p=plan_event_join(EventJoinObservation({k:0 for k in ('first_chaos_byte','first_bdw_byte','first_royale_byte','second_ft_byte','second_utc_byte','second_jr_byte')},{'entry_setup':True,'return':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores,());self.assertEqual(p.enqueue_requests,())
 def test_first_group_executes_at_most200_signedQWORD_including_negative(self):
  for now,lo,expected in ((199,0,True),(200,0,True),(201,0,False),(0x100,0xffffff00,True)):
   p=plan_event_join(sample(first_chaos_byte=1,priority_chaos_byte=1,first_tick_eax=now,first_low=lo))
   self.assertEqual(any(c[2]=='chaos_join' for c in p.calls),expected)
   self.assertEqual(bool(p.stores),expected)
 def test_first_group_priority_and_fresh_flags_even_if_all_turn_off(self):
  p=plan_event_join(sample(first_chaos_byte=1,priority_chaos_byte=1,priority_bdw_byte=1))
  self.assertEqual([c[2] for c in p.calls if c[2].endswith('_join')],['chaos_join'])
  self.assertNotIn('first_bdw_byte',[r[2] for r in p.reads])
  p=plan_event_join(sample(first_bdw_byte=1))
  self.assertFalse(any(c[2].endswith('_join') for c in p.calls));self.assertEqual(p.stores[:2],((0x553d04,4,201),(0x553d08,4,0)))
 def test_second_group_strictly_above200_and_independent_fresh_shared_stamp(self):
  self.assertEqual(plan_event_join(sample(second_ft_byte=1,second_tick_eax=200)).status,'second_group_wait')
  p=plan_event_join(sample(first_chaos_byte=1,priority_chaos_byte=1,second_ft_byte=1,second_low=201,second_tick_eax=201))
  self.assertEqual(p.status,'second_group_wait');self.assertEqual(len(p.stores),2)
  p=plan_event_join(sample(second_ft_byte=1,priority_ft_byte=1));self.assertEqual(p.enqueue_requests,(('ft_enqueue',0x5212e0,17,0),))
 def test_target_boundary_fresh_target_reads_and_fallback_stamp(self):
  for first,second in ((3000,3001),(0,3001),(3001,0)):
   p=plan_event_join(sample(second_ft_byte=1,target_first_eax=first,target_second_eax=second))
   self.assertIn('target_fallback',[c[2] for c in p.calls]);self.assertEqual(p.enqueue_requests,());self.assertEqual(len(p.stores),2)
  p=plan_event_join(sample(second_utc_byte=1,priority_utc_byte=1,target_first_eax=0xffffffff,target_third_eax=0))
  self.assertEqual(next(c for c in p.calls if c[2]=='target_prepare')[1],(0,0x561ef8))
  self.assertEqual(p.enqueue_requests,(('utc_enqueue',0x5212f1,18,0),))
 def test_second_priority_and_JR_nation_double_request_delays(self):
  p=plan_event_join(sample(second_ft_byte=1,priority_ft_byte=1,priority_utc_byte=1,priority_jr_byte=1))
  self.assertEqual(len(p.enqueue_requests),1);self.assertEqual(p.enqueue_requests[0][0],'ft_enqueue')
  for nation,template,length in ((1,0x521303,18),(2,0x521315,19),(0,0x521315,19)):
   p=plan_event_join(sample(second_jr_byte=1,priority_jr_byte=1,nation_eax=nation))
   self.assertEqual(p.enqueue_requests,(('jr_enqueue0',template,length,0),('jr_enqueue200',template,length,200)))
   self.assertFalse(p.queue_effect_verified);self.assertFalse(p.event_admission_verified)
 def test_normal_gap_retains_request_prefix_before_second_enqueue_and_stamp(self):
  f=EventJoinFrame();o=sample(second_jr_byte=1,priority_jr_byte=1);n=dict(o.normal_returns);n['jr_enqueue200']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertEqual(len(p.enqueue_requests),2);self.assertEqual(p.stores,())
  p=f.advance(replace(sample(second_jr_byte=0,nation_eax=2),values={**o.values,'nation_eax':2,'second_post_tick_eax':999}))
  self.assertTrue(p.complete);self.assertEqual(p.enqueue_requests[0][1],0x521303);self.assertEqual(p.stores[0],(0x553d04,4,999))

if __name__=='__main__':unittest.main()
