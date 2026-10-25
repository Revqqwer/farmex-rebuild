import unittest
from dataclasses import replace
from genie_getters import plan_genie_getter,source_getter_observation,source_getter_globals
from native_profile_versions import CURRENT_SOURCE_SHA256 as CURRENT,LEGACY_SOURCE_SHA256 as OLD
from motion_genie_helpers import GuardedReadReceipt as R
from genie_worker import GeniePrefixFrame,GenieWorkerFrame,GenieWorkerObservation as G,plan_genie_prefix
from notice_genie_window import NoticeGenieFrame,NoticeGenieObservation as N,plan_notice_genie_window
from test_genie_worker import sample as general_sample
from test_notice_genie_window import sample as notice_sample
from test_genie_getters import sample as getter_sample

def child(helper,raw=1,*,source=None,profile='us',normal=True):
 if source is None:o=getter_sample(helper,raw=raw)
 else:
  globals=source_getter_globals(source,profile,helper);slot=globals[0][1];offset=globals[1][1]
  o=source_getter_observation(source,profile,helper,(R(slot,4,0x2000,True),R(0x2000+offset,1,raw,True)),{'wrapper_return':normal})
 if source is None:o=replace(o,normal_returns={'wrapper_return':normal})
 return plan_genie_getter(helper,o,module_sha256=source,profile=profile if source else None)

CASES=(('general','initial_remaining','004631e8',1,dict(initial_bb_byte=1)),
 ('general','always_state','004631c8',0,dict(always_b8_byte=1)),
 ('general','always_remaining','004631e8',1,dict(always_b8_byte=1)),
 ('general','general_remaining','004631e8',1,dict(general_enabled_byte=1,general_active_byte=1)),
 ('notice','start_state','004631c8',0,{}),('notice','remaining','004631e8',1,{}),
 ('notice','stop_state','004631c8',1,dict(enabled_byte=0)))
def fixture(case):
 group,key,helper,raw,changes=case
 return (general_sample if group=='general' else notice_sample)(**{**changes,key+'_eax':raw})
def plan(group,o):return (plan_genie_prefix if group=='general' else plan_notice_genie_window)(o)

class GenieGetterBindingTests(unittest.TestCase):
 def test_all_seven_call_sites_keep_exact_child_metadata(self):
  for case in CASES:
   group,key,helper,raw,_=case;o=fixture(case);c=child(helper,raw)
   p=plan(group,replace(o,getter_executions={key:c}))
   self.assertTrue(p.complete,(group,key,p.missing));self.assertIs(dict(p.getter_executions)[key],c)
   self.assertFalse(p.native_execution_verified)

 def test_incomplete_child_cannot_be_bypassed_by_positive_outer_normal(self):
  for case in CASES:
   group,key,helper,raw,_=case;p=plan(group,replace(fixture(case),getter_executions={key:child(helper,raw,normal=False)}))
   self.assertFalse(p.complete);self.assertEqual(p.needed,('getter',key))

 def test_complete_child_still_requires_outer_normal_and_full_raw_eax(self):
  for case in CASES:
   group,key,helper,raw,_=case;o=fixture(case);r=dict(o.normal_returns);r[key]=False
   p=plan(group,replace(o,normal_returns=r,getter_executions={key:child(helper,raw)}))
   self.assertFalse(p.complete);self.assertEqual(p.needed,('normal',key))
   with self.assertRaises(ValueError):plan(group,replace(o,getter_executions={key:child(helper,raw^0x100)}))

 def test_wrong_helper_is_rejected_only_at_reached_call(self):
  o=notice_sample();wrong=child('004631e8',0)
  with self.assertRaises(ValueError):plan_notice_genie_window(replace(o,getter_executions={'start_state':wrong}))
  p=plan_notice_genie_window(replace(notice_sample(enabled_byte=0,other_stop_flag_2d=0),getter_executions={'start_state':wrong}))
  self.assertTrue(p.complete);self.assertEqual(p.getter_executions,())

 def test_frame_enriches_partial_child_then_needs_only_outer_fields(self):
  for case in CASES:
   group,key,helper,raw,_=case;o=fixture(case);f=(GeniePrefixFrame if group=='general' else NoticeGenieFrame)()
   self.assertFalse(f.advance(replace(o,getter_executions={key:child(helper,raw,normal=False)})).complete)
   c=child(helper,raw);p=f.advance(replace(o,getter_executions={key:c}))
   self.assertTrue(p.complete);self.assertIs(dict(p.getter_executions)[key],c)

 def test_consumed_getter_root_cannot_change_during_enrichment(self):
  o=notice_sample();c=child('004631c8',0,normal=False);f=NoticeGenieFrame()
  self.assertFalse(f.advance(replace(o,getter_executions={'start_state':c})).complete)
  a=c.input_snapshot;changed=replace(a,guarded_reads=(R(0x1000,4,0x3000,True),R(0x3020,1,0,True)),normal_returns={'wrapper_return':True})
  with self.assertRaises(ValueError):f.advance(N(getter_executions={'start_state':plan_genie_getter('004631c8',changed)}))

 def test_source_profile_mismatch_between_reached_getters_rejected(self):
  o=general_sample(initial_bb_byte=1,initial_remaining_eax=1,always_b8_byte=1,always_state_eax=2)
  good=child('004631e8',1,source=CURRENT)
  for sha,profile in ((OLD,'us'),(CURRENT,'steam')):
   with self.assertRaises(ValueError):plan_genie_prefix(replace(o,getter_executions={'initial_remaining':good,'always_state':child('004631c8',2,source=sha,profile=profile)}))
  p=plan_genie_prefix(replace(general_sample(initial_bb_byte=1,initial_remaining_eax=1),getter_executions={'initial_remaining':good,'always_state':child('004631c8',2,source=OLD)}))
  self.assertTrue(p.complete);self.assertEqual(len(p.getter_executions),1)

 def test_source_identity_is_preserved_across_general_notice_boundary(self):
  f=GenieWorkerFrame();o=replace(general_sample(initial_bb_byte=1,initial_remaining_eax=1),getter_executions={'initial_remaining':child('004631e8',1,source=CURRENT)})
  n=notice_sample(enabled_byte=0);bad=replace(n,getter_executions={'stop_state':child('004631c8',1,source=OLD)})
  with self.assertRaises(ValueError):f.advance(o,bad)
  good=replace(n,getter_executions={'stop_state':child('004631c8',1,source=CURRENT)})
  p=f.advance(notice=good);self.assertTrue(p.complete)
  self.assertEqual(dict(p.notice.getter_executions)['stop_state'].module_sha256,CURRENT)

 def test_completed_getter_survives_later_clock_gap(self):
  o=general_sample(always_b8_byte=1);v=dict(o.values);del v['always_post_tick'];c=child('004631e8',1)
  f=GeniePrefixFrame();self.assertFalse(f.advance(replace(o,values=v,getter_executions={'always_remaining':c})).complete)
  p=f.advance(G({'always_post_tick':777},{'epilogue':True},getter_executions={'always_remaining':child('004631c8',9)}))
  self.assertTrue(p.complete);self.assertIs(dict(p.getter_executions)['always_remaining'],c)

 def test_fresh_calls_can_return_different_raw_bytes_with_same_source_profile(self):
  o=general_sample(initial_bb_byte=1,initial_remaining_eax=0x101,always_b8_byte=1,always_remaining_eax=0x202)
  p=plan_genie_prefix(replace(o,getter_executions={'initial_remaining':child('004631e8',0x101,source=CURRENT),'always_remaining':child('004631e8',0x202,source=CURRENT)}))
  self.assertTrue(p.complete);self.assertEqual([p.raw_eax for k,p in p.getter_executions],[0x101,0x202])

 def test_forged_generated_result_or_native_claim_is_rejected(self):
  c=child('004631c8',0);o=notice_sample()
  for wrong in (replace(c,raw_eax=1,low_al=1),replace(c,native_execution_verified=True)):
   with self.assertRaises(ValueError):plan_notice_genie_window(replace(o,getter_executions={'start_state':wrong}))

if __name__=='__main__':unittest.main()
