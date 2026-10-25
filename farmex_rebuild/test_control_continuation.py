import unittest,json
from pathlib import Path
from dataclasses import replace
from profiles import Profiles
from control_guards import ControlGuardConfiguration,ControlGuardObservation
from control_continuation import *

class ControlContinuationTests(unittest.TestCase):
    def config(self,clock=0,count_stop=0,count_alarm=0,priest_stop=0,priest_alarm=0,minimum=5):
        return ControlGuardConfiguration({0xd8:clock,0xdc:15,0xe0:0,0xe4:minimum&0xffffffff,
            0xe8:count_stop,0xe9:count_alarm,0xea:priest_stop,0xeb:priest_alarm})
    def obs(self,**kw):return replace(ControlContinuationObservation(runtime_mode=0,
        stop_returned=True,town_returned=True,alarm_returned=True),**kw)

    def test_default_profile_compiler_and_low32_decimal_subset(self):
        p=Profiles(json.loads(Path(__file__).with_name('ui_model.json').read_text(encoding='utf-8')))
        values=dict(p.defaults);c=compile_control_continuation(values)
        self.assertEqual((c.fields[0xdc],c.fields[0xe0],c.fields[0xe4]),(15,0,5))
        self.assertEqual(len(CONTROL_CONTINUATION_INPUTS),8)
        values[ROOT+'txtPartyControlCount']='4294967295'
        self.assertEqual(compile_control_continuation(values).fields[0xe4],0xffffffff)

    def test_clock_match_plans_only_current_process_termination(self):
        p=plan_control_continuation(self.config(clock=1),self.obs(local_hour=15,local_minute=0,current_process_handle=0xffffffff,runtime_mode=None))
        self.assertTrue(p.complete);self.assertTrue(p.termination_call_planned)
        self.assertFalse(p.source_return_planned);self.assertIsNone(p.next_address)
        self.assertEqual(p.calls[-2:],(('0050749e',()),('0050755e',(0xffffffff,0))))
        self.assertFalse(p.native_execution_verified)

    def test_clock_hour_mismatch_does_not_require_minute(self):
        c=self.config(clock=1);fields=dict(c.fields);fields.pop(0xe0)
        p=plan_control_continuation(ControlGuardConfiguration(fields),self.obs(local_hour=14,local_minute=None,runtime_mode=2))
        self.assertTrue(p.complete);self.assertEqual(p.next_address,0x459519)
        self.assertEqual([x[0] for x in p.calls],['00507984','0050791e'])

    def test_clock_unknown_hour_or_matched_minute_or_handle_stays_unknown(self):
        for obs,label in ((self.obs(),'localtime hour DWORD'),
            (self.obs(local_hour=15),'localtime minute DWORD'),
            (self.obs(local_hour=15,local_minute=0),'GetCurrentProcess handle')):
            p=plan_control_continuation(self.config(clock=1),obs)
            self.assertFalse(p.complete);self.assertEqual(p.missing,label)

    def test_mode_guard_is_read_even_if_party_flags_disabled(self):
        p=plan_control_continuation(self.config(),self.obs(runtime_mode=None))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'global00561f58')
        for mode in (1,2,0xffffffff):
            p=plan_control_continuation(ControlGuardConfiguration({0xd8:0}),self.obs(runtime_mode=mode))
            self.assertTrue(p.complete);self.assertEqual(p.next_address,0x459519)

    def test_party_threshold_strict_less_not_caption_less_equal(self):
        for count,trigger in ((4,True),(5,False),(6,False),(0xffffffff,True)):
            p=plan_control_continuation(self.config(count_stop=1),self.obs(party_count_samples=(count,)))
            self.assertTrue(p.complete);self.assertEqual(p.source_return_planned,trigger)
        p=plan_control_continuation(self.config(count_stop=1,minimum=-1),self.obs(party_count_samples=(0,)))
        self.assertFalse(p.source_return_planned)

    def test_stop_town_alarm_order_and_separate_normal_returns(self):
        config=self.config(count_stop=1,count_alarm=1)
        for name,missing,last in (('stop_returned','0040ae0c normal return','0040ae0c'),
            ('town_returned','00465678 normal return','00465678'),('alarm_returned','00404260 normal return','00404260')):
            p=plan_control_continuation(config,self.obs(party_count_samples=(4,),**{name:None}))
            self.assertFalse(p.complete);self.assertEqual(p.missing,missing);self.assertEqual(p.calls[-1][0],last)
        p=plan_control_continuation(config,self.obs(party_count_samples=(4,)))
        self.assertEqual([x[0] for x in p.calls],['004645e4','0040ae0c','00465678','00404260'])

    def test_alarm_only_does_not_require_stop_or_town(self):
        p=plan_control_continuation(self.config(count_alarm=1),self.obs(party_count_samples=(4,),stop_returned=None,town_returned=None))
        self.assertTrue(p.complete);self.assertEqual(p.calls[-1][1],(0x569568,('literal',0x52139c)))

    def test_priest_scan_initial_count_below2_skips_comparisons_and_alerts(self):
        p=plan_control_continuation(self.config(priest_alarm=1),self.obs(party_count_samples=(1,),priest_matches={1:True}))
        self.assertEqual(p.status,'party_priest_not_found')
        self.assertEqual([x[0] for x in p.calls],['004645e4','00404260'])

    def test_priest_scan_uses_fresh_loop_counts_and_stops_on_first_match(self):
        p=plan_control_continuation(self.config(priest_alarm=1),self.obs(party_count_samples=(3,3,3),priest_matches={1:False,2:True}))
        self.assertEqual(p.status,'clock_party_prefix_passed');self.assertEqual(p.next_address,0x4592a7)
        self.assertEqual([x[0] for x in p.calls].count('004645e4'),3)
        self.assertEqual(p.calls[-1][1],(('party_text',0x569658),('literal',0x5213a4)))
        shrank=plan_control_continuation(self.config(priest_alarm=1),self.obs(party_count_samples=(3,0)))
        self.assertEqual(shrank.status,'party_priest_not_found')
        self.assertNotIn('00505d20',[x[0] for x in shrank.calls])

    def test_priest_unknown_count_or_comparison_never_means_no_priest(self):
        for samples,matches,label in (((3,),{},'004645e4 count sample1'),((3,3),{},'00505d20 member1')):
            p=plan_control_continuation(self.config(priest_alarm=1),self.obs(party_count_samples=samples,priest_matches=matches))
            self.assertFalse(p.complete);self.assertEqual(p.missing,label)
            self.assertNotIn('00404260',[x[0] for x in p.calls])

    def test_source_chain_early_return_excludes_continuation_and_success_composes(self):
        e=ControlGuardConfiguration({0xbf:1,0xc0:0,0xd0:0})
        p=replay_control_chain(e,ControlGuardObservation(np_462718=0,stop_returned=True,town_returned=True),None,None)
        self.assertTrue(p.complete);self.assertIsNone(p.continuation)
        p=replay_control_chain(e,ControlGuardObservation(np_462718=1),self.config(count_alarm=1),self.obs(party_count_samples=(4,)))
        self.assertEqual(p.status,'party_count_below');self.assertEqual(p.calls[0],('00462718',()))
        self.assertEqual(p.calls[-1][0],'00404260')

if __name__=='__main__':unittest.main()
