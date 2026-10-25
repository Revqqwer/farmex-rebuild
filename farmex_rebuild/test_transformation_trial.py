import json,unittest
from transformation_trial import *
from transformation import SKILLS

def panel():return dict(zip(TRANSFORMATION_INPUTS,(True,'10',False,0)))
class TransformationTrialTests(unittest.TestCase):
 def setup_trial(self):
  values=panel();trial=TransformationTrial(lambda:(values,{}))
  data=json.loads(example_transformation_sample(transformation_snapshot(values)))
  return values,trial,data
 def test_empty_sample_waits_at_source_entry(self):
  _,trial,_=self.setup_trial();p=trial.step('{}')
  self.assertEqual(p.settings.needed,('entry','0040929a'));self.assertIsNone(p.use)
  self.assertEqual(p.queue.records,())
 def test_real_panel_fields_and_full_actor_are_serialized(self):
  values,trial,data=self.setup_trial();values[TRANSFORMATION_INPUTS[3]]=17
  data=json.loads(example_transformation_sample(transformation_snapshot(values)));p=trial.step(json.dumps(data))
  self.assertTrue(p.settings.complete and p.use.complete)
  self.assertEqual(p.settings.selected_skill,SKILLS[17]);self.assertEqual(p.settings.milliseconds_dword,10000)
  payload=p.queue.records[0].payload
  self.assertEqual(payload[2:6],SKILLS[17].to_bytes(4,'little'))
  self.assertEqual(payload[6:14],bytes.fromhex('7856341278563412'))
  self.assertFalse(p.periodic_consumer_verified or p.native_execution_verified or p.live_compatibility_verified)
 def test_prefix_preserved_until_cast_return_without_duplicate(self):
  _,trial,data=self.setup_trial();data['use']['cast_returned']=False
  p=trial.step(json.dumps(data));self.assertFalse(p.use.complete);self.assertEqual(len(p.queue.records),1)
  data['use']['actor_dword']=999;data['use']['queue_gate']=0;data['use']['cast_returned']=True
  p=trial.step(json.dumps(data));self.assertTrue(p.use.complete);self.assertEqual(len(p.queue.records),1)
  trial.step(json.dumps(data));self.assertEqual(len(trial.queue.records),1)
 def test_explicit_helper_entry_is_separate_from_enabled_flag(self):
  _,trial,data=self.setup_trial();data['helper_entry_reached']=False
  p=trial.step(json.dumps(data));self.assertTrue(p.settings.complete);self.assertIsNone(p.use)
  self.assertEqual(p.queue.records,())
 def test_parser_exception_retains_enabled_rearm_but_no_later_fields(self):
  values,trial,data=self.setup_trial();values[TRANSFORMATION_INPUTS[1]]='bad'
  data.pop('panel_snapshot_sha256');data['settings']['parser_route']='exception_unresolved'
  p=trial.step(json.dumps(data));self.assertFalse(p.settings.complete)
  self.assertEqual(p.settings.stores,((0x562070,1,1),(0x562071,1,1)))
  self.assertIsNone(p.use);self.assertEqual(p.queue.records,())
 def test_panel_change_rejects_stale_example_preserves_queue_and_reset_clears(self):
  values,trial,data=self.setup_trial();trial.step(json.dumps(data));values[TRANSFORMATION_INPUTS[3]]=1
  with self.assertRaises(ValueError):trial.step(json.dumps(data))
  self.assertIsNone(trial.last);self.assertEqual(len(trial.queue.records),1)
  fresh=example_transformation_sample(transformation_snapshot(values));p=trial.step(fresh)
  self.assertEqual(len(p.queue.records),2);trial.reset();self.assertEqual(trial.queue.records,())
 def test_panel_derived_getters_cannot_be_overridden(self):
  _,trial,data=self.setup_trial();data['settings']['values']['enabled_eax']=0
  with self.assertRaises(ValueError):trial.step(json.dumps(data))
  self.assertIsNone(trial.last)
 def test_invalid_reached_json_and_unsupported_synthetic_parser(self):
  values,trial,data=self.setup_trial()
  for text in ('{bad','[]'):
   with self.assertRaises(ValueError):trial.step(text)
   self.assertIsNone(trial.last)
  data['use']['copy_returns']=1
  with self.assertRaises(ValueError):trial.step(json.dumps(data))
  values[TRANSFORMATION_INPUTS[1]]='bad'
  with self.assertRaises(ValueError):example_transformation_sample(transformation_snapshot(values))

if __name__=='__main__':unittest.main()
