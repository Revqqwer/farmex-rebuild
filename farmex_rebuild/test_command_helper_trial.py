import json,unittest
from chat_commands import ROOT,SPECS
from chat_commands_trial import ChatCommandsTrial,EXAMPLE_COMMAND_HEX,example_chat_commands_sample,example_detailed_commands_sample

class HelperTrialTests(unittest.TestCase):
    def trial(self,enabled=None):
        enabled=tuple(s[0] for s in SPECS) if enabled is None else enabled
        values={}
        for key,check,text,*_ in SPECS:
            values[ROOT+check]=key in enabled;values[ROOT+text]='go'
        return ChatCommandsTrial(lambda:(values,{})),values
    def step(self,t,raw=None,detailed=True):
        if raw is None:raw=json.loads(example_detailed_commands_sample())
        return t.step(EXAMPLE_COMMAND_HEX,json.dumps(raw),1254,detailed)

    def test_all_eight_helpers_bind_and_share_two_record_queue(self):
        t,_=self.trial();p=self.step(t)
        self.assertTrue(p.complete);self.assertEqual(len(p.actions),8)
        self.assertTrue(all(a.helper_execution.complete for a in p.actions))
        self.assertEqual([r.payload for r in t.helpers.queue.records],[b'\0',b'\x12\x01'])
        self.assertEqual([r.record_id for r in t.helpers.queue.records],[1,2])
        self.assertEqual(len(p.actions[-1].helper_execution.record_image),80)
        self.assertFalse(p.actions[-1].helper_execution.thread_callback_verified)
        helpers=t.helpers;self.assertIs(self.step(t,{}),p);self.assertIs(t.helpers,helpers)
        self.assertEqual(len(t.helpers.queue.records),2)

    def test_detailed_toggle_restarts_completed_legacy_invocation(self):
        t,_=self.trial(('disconnect',))
        self.assertTrue(t.step(EXAMPLE_COMMAND_HEX,example_chat_commands_sample(),1254).complete)
        frame=t.frame;p=self.step(t,json.loads(example_chat_commands_sample()))
        self.assertFalse(p.complete);self.assertIsNot(t.frame,frame)
        self.assertIn('bound action:disconnect',p.missing);self.assertEqual(t.helpers.queue.records,())

    def test_parent_positive_returns_cannot_bypass_missing_helper_inputs(self):
        for key in ('disconnect','return_center','bot_start','bot_stop','genie_start','genie_stop','stand','town'):
            t,_=self.trial((key,));raw=json.loads(example_detailed_commands_sample());raw['helpers'][key]={}
            p=self.step(t,raw);self.assertFalse(p.complete,key);self.assertIn('bound action:'+key,p.missing)
            self.assertFalse(p.actions[-1].helper_execution.complete)

    def test_completed_queue_child_still_needs_parent_return_without_duplicate(self):
        t,_=self.trial(('disconnect','stand'));raw=json.loads(example_detailed_commands_sample())
        raw['helper_returns']['action:disconnect']=False
        p=self.step(t,raw);self.assertFalse(p.complete);self.assertEqual(len(t.helpers.queue.records),1)
        self.step(t,raw);self.assertEqual(len(t.helpers.queue.records),1)
        p=self.step(t);self.assertTrue(p.complete);self.assertEqual(len(t.helpers.queue.records),2)

    def test_consumed_queue_gate_ignored_when_tick_arrives(self):
        t,_=self.trial(('disconnect',));raw=json.loads(example_detailed_commands_sample());del raw['helpers']['disconnect']['tick']
        self.assertIn('GetTickCount',self.step(t,raw).missing)
        raw['helpers']['disconnect']={'gate':'consumed bad gate','tick':999}
        p=self.step(t,raw);self.assertTrue(p.complete);self.assertEqual(t.helpers.queue.records[0].created_tick,999)

    def test_gate_zero_does_not_parse_unreached_tick(self):
        t,_=self.trial(('disconnect','stand'));raw=json.loads(example_detailed_commands_sample())
        raw['helpers']['disconnect']={'gate':0,'tick':'unreached bad tick'}
        p=self.step(t,raw);self.assertTrue(p.complete)
        self.assertEqual([r.payload for r in t.helpers.queue.records],[b'\x12\x01'])

    def test_town_late_gap_keeps_allocation_and_consumed_global_prefix(self):
        t,_=self.trial(('town',));raw=json.loads(example_detailed_commands_sample())
        raw['helpers']['town']['helper_returns']['thread_helper']=False
        p=self.step(t,raw);self.assertFalse(p.complete);self.assertIn('thread_helper',p.missing)
        raw['helpers']['town']['buffer_address']='consumed bad allocation'
        raw['helpers']['town']['global_samples']='consumed bad globals'
        raw['helpers']['town']['helper_returns']['thread_helper']=True
        p=self.step(t,raw);self.assertTrue(p.complete);self.assertEqual(p.actions[0].helper_execution.buffer_address,0x1000)

    def test_town_null_allocation_does_not_parse_later_fields(self):
        t,_=self.trial(('town',));raw=json.loads(example_detailed_commands_sample())
        raw['helpers']['town']['buffer_address']=0;raw['helpers']['town']['global_samples']='unreached'
        p=self.step(t,raw);self.assertFalse(p.complete);self.assertIn('null-buffer',p.missing)

    def test_motion_late_write_receipt_does_not_reparse_globals(self):
        t,_=self.trial(('return_center',));raw=json.loads(example_detailed_commands_sample())
        raw['helpers']['return_center']['normal_returns']['write_y']=False
        p=self.step(t,raw);self.assertFalse(p.complete)
        #Globals0..3 and guarded0 were consumed; last offset and guarded1 remain needed.
        raw['helpers']['return_center']['global_samples'][:4]=['already consumed']*4
        raw['helpers']['return_center']['guarded_reads'][0]='already consumed'
        raw['helpers']['return_center']['normal_returns']['write_y']=True
        p=self.step(t,raw);self.assertTrue(p.complete)

    def test_genie_guarded_failure_does_not_parse_unobserved_eax(self):
        t,_=self.trial(('genie_start',));raw=json.loads(example_detailed_commands_sample())
        row=raw['helpers']['genie_start']['guarded_reads'][0]
        row.update(normal_returned=False,eax='unobserved')
        p=self.step(t,raw);self.assertFalse(p.complete)
        row.update(normal_returned=True,eax=0x4000)
        self.assertTrue(self.step(t,raw).complete)

    def test_switch_late_gap_ignores_consumed_mode_and_other_helper_fields(self):
        t,_=self.trial(('bot_stop',));raw=json.loads(example_detailed_commands_sample())
        raw['helpers']['bot_stop']['normal_returns']['stop_movement']=False
        p=self.step(t,raw);self.assertFalse(p.complete);self.assertEqual(len(p.actions[0].helper_execution.stores),49)
        raw['helpers']['bot_stop']['values']='consumed bad values'
        raw['helpers']['bot_stop']['normal_returns']['stop_movement']=True
        self.assertTrue(self.step(t,raw).complete)

    def test_disabled_helper_and_skipped_genie_fields_not_parsed(self):
        t,_=self.trial(('disconnect','genie_start'));raw=json.loads(example_detailed_commands_sample())
        raw['helpers']['town']='not reached';raw['genie_blocked_byte']=1;raw['helpers']['genie_start']='not reached'
        self.assertTrue(self.step(t,raw).complete);self.assertNotIn('genie_start',t.helpers.frames)

    def test_invalid_reached_nested_value_clears_every_helper_and_queue(self):
        for change in ('helpers','row','normal','gate'):
            t,_=self.trial(('disconnect','town'));raw=json.loads(example_detailed_commands_sample())
            if change=='helpers':raw['helpers']=[]
            elif change=='row':raw['helpers']['town']['global_samples'][0]=[1]
            elif change=='normal':raw['helpers']['town']['helper_returns']['allocate_record']=1
            else:raw['helpers']['disconnect']['gate']=True
            with self.assertRaises((ValueError,TypeError)):self.step(t,raw)
            self.assertIsNone(t.helpers);self.assertIsNone(t.frame);self.assertIsNone(t.last)

    def test_new_panel_or_capture_resets_helper_queue(self):
        t,v=self.trial(('disconnect',));self.step(t);old=t.helpers
        v[ROOT+'chkmtkalk']=True
        self.step(t);self.assertIsNot(t.helpers,old);self.assertEqual(len(t.helpers.queue.records),2)
        t.reset();self.assertIsNone(t.helpers)

if __name__=='__main__':unittest.main()
