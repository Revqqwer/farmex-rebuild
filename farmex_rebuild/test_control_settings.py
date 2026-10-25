import json,unittest
from dataclasses import replace
from control_settings import *
from control_settings_trial import *
from source_integer import SourceIntegerObservation

def fixture():
 values={};normals={};texts={};children={}
 for op in OPS:
  kind,slot=op[:2];key='%03x'%slot
  if kind=='flag':values['checked_'+key]=0;normals['checked_'+key]=True
  else:
   texts[key]='captured text without lexical inference'
   for s in ('init_','text_','text_cleanup_','parser_outer_'):normals[s+key]=True
   children[key]=SourceIntegerObservation(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True)
 return ControlSettingsObservation(True,values,normals,texts,integer_children=children)

def normal(value):return SourceIntegerObservation(True,'normal',True,value&((1<<64)-1),cleanup_returned=True)

class ControlSettingsTests(unittest.TestCase):
 def test_middle_span_entry_and_defaults(self):
  f=ControlSettingsFrame();self.assertEqual(f.advance(ControlSettingsObservation()).needed,('entry','004581b9'))
  p=f.advance(fixture());c=control_configuration_from_settings(p)
  self.assertTrue(p.complete);self.assertEqual(p.next_address,0x4584af)
  self.assertEqual({k:c.fields[k] for k in (0xc8,0xcc,0xd4,0xdc,0xe0,0xe4)}, {0xc8:0,0xcc:0,0xd4:54,0xdc:0,0xe0:0,0xe4:5})
  self.assertEqual(len(p.stores),16);self.assertFalse(p.native_execution_verified)

 def test_coin_full_qword_but_other_numbers_low_dword(self):
  o=fixture();children=dict(o.integer_children)
  children.update({'8b0':normal(0x12345678abcdef01),'8c8':normal(0x12345678ffffffff)})
  c=control_configuration_from_settings(ControlSettingsFrame().advance(replace(o,integer_children=children)))
  self.assertEqual((c.fields[0xc8],c.fields[0xcc],c.fields[0xd4]),(0xabcdef01,0x12345678,0xffffffff))

 def test_child_then_outer_return_then_cleanup_preserve_store_order(self):
  o=fixture();n=dict(o.normal_returns);n['parser_outer_8b0']=False;f=ControlSettingsFrame()
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.needed,('normal','parser_outer_8b0'));self.assertEqual(len(p.stores),4)
  p=f.advance(ControlSettingsObservation(normal_returns={'parser_outer_8b0':True}))
  self.assertEqual(p.needed,('normal','text_cleanup_8b0'));self.assertEqual(len(p.stores),6)
  self.assertEqual([a-0x562194 for a,_,_ in p.stores[-2:]],[0xc8,0xcc])

 def test_prefix_caches_flags_text_and_qword_across_gap(self):
  o=fixture();f=ControlSettingsFrame();n=dict(o.normal_returns);n['text_cleanup_8b0']=False
  p=f.advance(replace(o,normal_returns=n));before=p.stores
  changed=replace(o,values={k:255 for k in o.values},integer_children={k:normal(999) for k in o.integer_children})
  p=f.advance(changed);self.assertTrue(p.complete);self.assertEqual(p.stores[:6],before)
  self.assertIn((0x562194+0xd0,1,255),p.stores)

 def test_generated_consumer_stops_np_before_coin_and_clock(self):
  o=fixture();v=dict(o.values);v.update(checked_8a0=1,checked_8ac=1,checked_8b4=1)
  p=ControlSettingsFrame().advance(replace(o,values=v))
  c=replay_control_settings_consumer(p,ControlGuardObservation(np_462718=0,stop_returned=True,town_returned=True),ControlContinuationObservation())
  self.assertTrue(c.complete);self.assertEqual(c.consumer.status,'np_zero_stop_town')
  self.assertNotIn(('0046258c',()),c.consumer.calls);self.assertIsNone(c.consumer.continuation)

 def test_negative_qword_coin_threshold_does_not_become_positive_low32(self):
  o=fixture();v=dict(o.values);v['checked_8ac']=1;children=dict(o.integer_children);children['8b0']=normal(-1)
  p=ControlSettingsFrame().advance(replace(o,values=v,integer_children=children))
  c=replay_control_settings_consumer(p,ControlGuardObservation(coins_46258c=0),ControlContinuationObservation(runtime_mode=1))
  self.assertEqual(c.configuration.fields[0xcc],0xffffffff)
  self.assertTrue(c.complete);self.assertEqual(c.consumer.status,'mode_skips_party_section')

 def test_positive_high_coin_threshold_triggers_even_low_zero(self):
  o=fixture();v=dict(o.values);v['checked_8ac']=1;children=dict(o.integer_children);children['8b0']=normal(1<<32)
  p=ControlSettingsFrame().advance(replace(o,values=v,integer_children=children))
  c=replay_control_settings_consumer(p,ControlGuardObservation(coins_46258c=0xffffffff,stop_returned=True,town_returned=True),ControlContinuationObservation())
  self.assertTrue(c.complete);self.assertEqual(c.consumer.status,'coins_at_or_below_stop_town')

 def test_clock_consumer_call_is_only_a_plan(self):
  o=fixture();v=dict(o.values);v['checked_8b4']=1;p=ControlSettingsFrame().advance(replace(o,values=v))
  c=replay_control_settings_consumer(p,ControlGuardObservation(),ControlContinuationObservation(local_hour=0,local_minute=0,current_process_handle=0xffffffff))
  self.assertTrue(c.consumer.continuation.termination_call_planned);self.assertFalse(c.native_execution_verified)

 def test_incomplete_settings_does_not_run_consumer(self):
  p=ControlSettingsFrame().advance(ControlSettingsObservation())
  c=replay_control_settings_consumer(p,ControlGuardObservation(),ControlContinuationObservation())
  self.assertFalse(c.complete);self.assertIsNone(c.consumer)
  with self.assertRaises(ValueError):control_configuration_from_settings(p)

 def test_exact_span_context_and_store_shape_validation(self):
  p=ControlSettingsFrame(context=0xffffff80).advance(fixture())
  c=control_configuration_from_settings(p,context=0xffffff80);self.assertIn(0xcc,c.fields)
  with self.assertRaises(ValueError):control_configuration_from_settings(p)
  with self.assertRaises(ValueError):control_configuration_from_settings(replace(p,stores=p.stores[:-1]),context=0xffffff80)

 def test_own_panel_trial_qword_idempotence_stale_and_override(self):
  values={path:False if op[0]=='flag' else '5' for op,(_,path) in zip(OPS,CONTROL_SETTING_FIELDS)}
  values[dict(CONTROL_SETTING_FIELDS)[0x8b0]]='4294967296'
  t=ControlSettingsTrial(lambda:(values,{}));data=json.loads(example_control_settings_sample(t.current_snapshot()))
  p=t.step(json.dumps(data));self.assertTrue(p.complete);self.assertEqual(t.scalar_state[0x562194+0xcc],(4,1))
  f=t.frame;self.assertIs(t.step(json.dumps(data)),p);self.assertIs(t.frame,f)
  values[dict(CONTROL_SETTING_FIELDS)[0x8c8]]='99'
  with self.assertRaises(ValueError):t.step(json.dumps(data))
  t.reset();data=json.loads(example_control_settings_sample(t.current_snapshot()));data['values']={'checked_8a4':1}
  with self.assertRaises(ValueError):t.step(json.dumps(data))

 def test_party_count_defaults_feed_signed_count_consumer(self):
  o=fixture();v=dict(o.values);v['checked_bf4']=1;p=ControlSettingsFrame().advance(replace(o,values=v))
  c=replay_control_settings_consumer(p,ControlGuardObservation(),ControlContinuationObservation(runtime_mode=0,party_count_samples=(4,),alarm_returned=True))
  self.assertTrue(c.complete);self.assertEqual(c.consumer.status,'party_count_below')
  self.assertNotIn(('0040ae0c',(0x561f34,0)),c.consumer.calls)
