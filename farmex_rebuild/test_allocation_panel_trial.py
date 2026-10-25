import json,unittest
from allocation_panel_trial import *

def panel():
 values=dict(zip(AUTO_ALLOCATION_FLAGS,(False,False)))
 lists={ALLOCATION_LISTS['stat']:[dict(caption='3',subitems=['STR','100'],checked=False)],
  ALLOCATION_LISTS['skill']:[dict(caption='1',subitems=['Attack','50'],checked=False)]}
 return values,lists

class AllocationPanelTests(unittest.TestCase):
 def test_real_panel_values_cannot_be_overridden_by_JSON_and_missing_native_spans_wait(self):
  v,l=panel();t=AllocationPanelTrial(lambda:(v,l))
  p=t.step('{"values":{"stat_enabled_eax":255}}');self.assertFalse(p.complete)
  self.assertEqual(p.stores[:2],((0x5621b4,1,0),(0x5621b5,1,0)))
  self.assertEqual(p.needed,('normal','stat_clear'))

 def test_explicit_example_uses_hidden_caption_name_and_threshold_even_unchecked(self):
  v,l=panel();t=AllocationPanelTrial(lambda:(v,l));p=t.step(example_allocation_sample(compile_allocation_panel(v,l)))
  self.assertTrue(p.complete);self.assertEqual((p.stat_rows[0].name_bytes,p.stat_rows[0].action_dword,p.stat_rows[0].threshold_dword),(b'STR',3,100))
  self.assertEqual((p.skill_rows[0].name_bytes,p.skill_rows[0].action_dword,p.skill_rows[0].threshold_dword),(b'Attack',1,50))
  self.assertFalse(p.native_execution_verified)

 def test_snapshot_is_immutable_checked_is_unused_and_changed_text_requires_fresh_example(self):
  v,l=panel();snapshot=compile_allocation_panel(v,l);t=AllocationPanelTrial(lambda:(v,l));s=example_allocation_sample(snapshot)
  t.step(s);frame=t.frame;l[ALLOCATION_LISTS['stat']][0]['checked']=True
  self.assertTrue(t.step(s).complete);self.assertIs(t.frame,frame)
  l[ALLOCATION_LISTS['stat']][0]['subitems'][1]='120'
  self.assertEqual(snapshot.stat_rows[0].subitems[1],'100')
  with self.assertRaisesRegex(ValueError,'Panel değişti'):t.step(s)
  self.assertIsNone(t.last);self.assertIsNot(t.frame,frame)
  p=t.step(example_allocation_sample(compile_allocation_panel(v,l)));self.assertEqual(p.stat_rows[0].threshold_dword,120)

 def test_partial_JSON_only_new_return_needed_and_prefix_remains_single(self):
  v,l=panel();t=AllocationPanelTrial(lambda:(v,l));r=json.loads(example_allocation_sample(compile_allocation_panel(v,l)))
  r['normal_returns']['stat0.row_cleanup']=False
  p=t.step(json.dumps(r));self.assertFalse(p.complete);self.assertEqual(len(p.stat_rows),1)
  r['normal_returns']['stat0.row_cleanup']=True;p=t.step(json.dumps(r));self.assertTrue(p.complete)
  self.assertEqual(len(p.stat_rows),1)

 def test_missing_reached_subitem_rejects_without_inventing_empty_default(self):
  v,l=panel();good=example_allocation_sample(compile_allocation_panel(v,l));r=json.loads(good);del r['panel_snapshot_sha256']
  l[ALLOCATION_LISTS['stat']][0]['subitems']=['STR'];t=AllocationPanelTrial(lambda:(v,l))
  with self.assertRaisesRegex(ValueError,'lacks subitem'):t.step(json.dumps(r))
  self.assertIsNone(t.last);self.assertEqual(t.frame.observation.texts['stat0.caption'],'3')

 def test_unreached_malformed_receipts_ignore_but_bad_JSON_clears_last(self):
  v,l=panel();t=AllocationPanelTrial(lambda:(v,l))
  p=t.step('{"integer_inputs":"not reached"}');self.assertEqual(p.needed,('normal','stat_clear'))
  with self.assertRaises(ValueError):t.step('{bad')
  self.assertIsNone(t.last)

 def test_example_refuses_to_guess_nonASCII_codec_or_invalid_integer_fallback(self):
  v,l=panel();l[ALLOCATION_LISTS['stat']][0]['subitems'][0]='Güç'
  with self.assertRaises(ValueError):example_allocation_sample(compile_allocation_panel(v,l))
  l[ALLOCATION_LISTS['stat']][0]['subitems'][0]='STR';l[ALLOCATION_LISTS['stat']][0]['caption']='bad'
  with self.assertRaises(ValueError):example_allocation_sample(compile_allocation_panel(v,l))

if __name__=='__main__':unittest.main()
