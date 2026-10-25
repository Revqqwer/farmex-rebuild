import json,unittest
from dataclasses import replace
from action_queue import QueueState,enqueue
from event_target_fallback import *
from event_join import EventJoinFrame
from event_join_trial import EventJoinTrial,event_snapshot,example_event_sample
from test_event_join import sample
from test_event_join_trial import panel

def profile1():
 return EventFallbackObservation(dict(first_profile_byte=1,profile1_root_slot=0x1000,profile1_ecx=0x2000,profile1_target=0x3000),{'profile1_callback':True,'return':True})

def profile2(allocation=0,found=0x87654321):
 v=dict(first_profile_byte=0,second_profile_byte=2,allocation_before=allocation,allocate_eax=0xa000,
 discarded_root_slot=0x4000,discarded_root=0x5000,argument_allocation=0x6000,
 search_root_slot=0x7000,search_ecx=0x8000,search_target=0x9000,search_eax=found,
 select_root_slot=0x1000,select_ecx=0x2000,select_target=0x3000,
 confirm_root_slot=0x1100,confirm_ecx=0x2200,confirm_target=0x3300)
 n={k:True for k in ('allocate','search_callback','select_callback','confirm_callback','return')}
 for i,bits in enumerate((0x80000000,0x7fc00000,0x3f800000)):
  pre='component%d.'%i;v.update({pre+'root_slot':0x1000+i,pre+'root_eax':0xfffffff0,pre+'offset':0x20+16*i,
   pre+'allocation':0x2000+0x100*i,pre+'fstp_bits':bits})
  n.update({pre+k:True for k in ('root','float','fstp')})
 return EventFallbackObservation(v,n)

class EventTargetFallbackTests(unittest.TestCase):
 def test_profile1_direct_callback_and_unsupported_fresh_second_profile(self):
  p=plan_event_fallback(profile1());self.assertTrue(p.complete);self.assertEqual(p.callbacks,(('profile1_callback',0x3000,0x2000,()),))
  self.assertEqual(p.stores,());self.assertNotIn('second_profile_byte',[r[2] for r in p.reads])
  p=plan_event_fallback(EventFallbackObservation({'first_profile_byte':2,'second_profile_byte':0},{'return':True}))
  self.assertEqual(p.status,'unsupported_profile');self.assertEqual(p.callbacks,())
 def test_profile2_allocation_and_three_distinct_captured_FSTP_stores(self):
  p=plan_event_fallback(profile2());self.assertTrue(p.complete)
  self.assertEqual(p.calls[0],('VirtualAlloc',(0x40,0x1000,12,0),'allocate'))
  self.assertEqual(p.stores,((0x553d18,4,0xa000,'allocation_pointer'),(0x2000,4,0x80000000,'component0.float_store'),(0x2104,4,0x7fc00000,'component1.float_store'),(0x2208,4,0x3f800000,'component2.float_store')))
  self.assertEqual(next(c for c in p.calls if c[2]=='component0.float')[1],(0x10,))
  self.assertFalse(p.memory_writes_verified);self.assertFalse(p.allocation_effect_verified)
 def test_nonzero_allocation_skips_allocate_and_zero_result_has_no_invented_guard(self):
  p=plan_event_fallback(profile2(allocation=1));self.assertNotIn('allocate',[c[2] for c in p.calls]);self.assertEqual(len(p.stores),3)
  o=profile2();v=dict(o.values);v['allocate_eax']=0;v['component0.allocation']=0
  p=plan_event_fallback(replace(o,values=v));self.assertTrue(p.complete);self.assertEqual(p.stores[1][0],0)
 def test_overwritten_direct_root_read_is_preserved_and_callbacks_use_saved_result(self):
  p=plan_event_fallback(profile2());self.assertIn((0x4000,4,'discarded_root'),p.reads)
  self.assertEqual(p.callbacks,(('search_callback',0x9000,0x8000,(0x6000,)),('select_callback',0x3000,0x2000,(0x87654321,)),('confirm_callback',0x3300,0x2200,(0,0x87654321))))
  p=plan_event_fallback(profile2(found=0));self.assertEqual(p.status,'search_zero');self.assertEqual(len(p.callbacks),1)
 def test_consumed_stores_and_found_result_survive_later_callback_gap(self):
  f=EventFallbackFrame();o=profile2();n=dict(o.normal_returns);n['select_callback']=False
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.needed,('normal','select_callback'));self.assertEqual(len(p.stores),4)
  changed=profile2(found=0);p=f.advance(changed);self.assertTrue(p.complete)
  self.assertEqual(p.callbacks[-1][-1],(0,0x87654321));self.assertEqual(len(p.stores),4)
 def test_worker_child_completion_and_outer_return_gate_stamp(self):
  seed=enqueue(QueueState(),b'seed',4,0,1,1).state;f=EventJoinFrame(queue=seed);o=sample(second_ft_byte=1,target_first_eax=3000)
  p=f.advance(replace(o,fallback_child=EventFallbackObservation()));self.assertEqual(p.needed,('child','target_fallback'));self.assertEqual(p.stores,())
  n=dict(o.normal_returns);n['target_fallback']=False;p=f.advance(replace(o,normal_returns=n,fallback_child=profile1()))
  self.assertEqual(p.needed,('normal','target_fallback'));self.assertEqual(p.stores,())
  p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(p.queue,seed);self.assertEqual(p.enqueue_requests,())
 def test_panel_reached_fallback_capture_and_bad_result_clearing(self):
  v=panel('ft');t=EventJoinTrial(lambda:(v,{}));d=json.loads(example_event_sample(event_snapshot(v)));d['values']['target_first_eax']=3000
  child=profile1();d['fallback_child']={'values':{**child.values,'future':'ignored'},'normal_returns':dict(child.normal_returns)}
  d['fallback_child']['normal_returns']['profile1_callback']=False;p=t.step(json.dumps(d));self.assertEqual(p.needed,('child','target_fallback'))
  d['fallback_child']['normal_returns']['profile1_callback']=True;p=t.step(json.dumps(d));self.assertTrue(p.complete);self.assertEqual(p.queue.records,())
  with self.assertRaises(ValueError):t.step('{bad')
  self.assertIsNone(t.last)
 def test_retroactive_fallback_binding_rejected(self):
  f=EventJoinFrame();o=sample(second_ft_byte=1,target_first_eax=3000);n=dict(o.normal_returns);n['second_post_tick']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):f.advance(replace(o,fallback_child=profile1()))
 def test_raw_types_are_strict(self):
  with self.assertRaises(ValueError):EventFallbackObservation({'first_profile_byte':256})
  with self.assertRaises(ValueError):EventFallbackObservation({'allocate_eax':True})
  with self.assertRaises(ValueError):EventFallbackObservation(normal_returns={'allocate':1})

if __name__=='__main__':unittest.main()
