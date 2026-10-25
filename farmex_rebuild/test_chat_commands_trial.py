import json,unittest
from chat_commands_trial import *
from chat_commands import ROOT

class CommandTrialTests(unittest.TestCase):
    def trial(self,enabled=('disconnect',)):
        values={}
        for key,check,text,*_ in SPECS:values[ROOT+check]=key in enabled;values[ROOT+text]='go'
        return ChatCommandsTrial(lambda:(values,{})),values

    def test_default_unknown_prefix_and_observations_wait(self):
        t,_=self.trial();self.assertFalse(t.step('10','{}',1254).complete);self.assertIsNone(t.frame)
        p=t.step(EXAMPLE_COMMAND_HEX,'{}',1254)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'compare:disconnect normal return');self.assertEqual(p.actions,())

    def test_real_panel_flags_command_case_and_explicit_codepage_are_fresh(self):
        t,v=self.trial();s=example_chat_commands_sample()
        self.assertEqual(len(t.step(EXAMPLE_COMMAND_HEX,s,1254).actions),1)
        v[ROOT+'chkmtbotbaslat']=True
        self.assertEqual([a.key for a in t.step(EXAMPLE_COMMAND_HEX,s,1254).actions],['disconnect','bot_start'])
        v[ROOT+'txtkmtdc']='GO'
        self.assertEqual([a.key for a in t.step(EXAMPLE_COMMAND_HEX,s,65001).actions],['bot_start'])
        self.assertEqual(t.configuration.codepage,65001)

    def test_all_same_command_and_repeated_tick_reuses_completed_frame(self):
        t,_=self.trial(tuple(s[0] for s in SPECS));p=t.step(EXAMPLE_COMMAND_HEX,example_chat_commands_sample(),1254)
        self.assertTrue(p.complete);self.assertEqual(len(p.actions),8);frame=t.frame
        self.assertIs(t.step(EXAMPLE_COMMAND_HEX,'{}',1254),p);self.assertIs(t.frame,frame)

    def test_action_gap_resumes_without_requiring_prior_comparison_again(self):
        t,_=self.trial(('disconnect','bot_start'));raw=json.loads(example_chat_commands_sample())
        raw['helper_returns']['action:disconnect']=False
        raw['helper_returns']['compare:return_center']='unvisited'
        p=t.step(EXAMPLE_COMMAND_HEX,json.dumps(raw),1254)
        self.assertFalse(p.complete);self.assertEqual([a.key for a in p.actions],['disconnect'])
        raw=json.loads(example_chat_commands_sample());del raw['helper_returns']['compare:disconnect']
        p=t.step(EXAMPLE_COMMAND_HEX,json.dumps(raw),1254)
        self.assertTrue(p.complete);self.assertEqual([a.key for a in p.actions],['disconnect','bot_start'])

    def test_center_consumed_y_is_not_reparsed_when_x_bits_arrive(self):
        t,_=self.trial(('return_center',));raw=json.loads(example_chat_commands_sample());del raw['center_x_f32_bits']
        p=t.step(EXAMPLE_COMMAND_HEX,json.dumps(raw),1254);self.assertIn('X post-FSTP',p.missing)
        raw['center_x_f32_bits']=0x41200000;raw['center_y_dword']='already consumed'
        p=t.step(EXAMPLE_COMMAND_HEX,json.dumps(raw),1254)
        self.assertTrue(p.complete);self.assertEqual(p.actions[0].push_order,(0x41a00000,0x41200000))

    def test_unreached_genie_and_action_fields_are_ignored(self):
        t,_=self.trial(('genie_start',));raw=json.loads(example_chat_commands_sample())
        raw.update(genie_blocked_byte=1,genie_start_state_eax='unused',genie_remaining_eax='unused')
        raw['helper_returns']['action:genie_start']='unused'
        p=t.step(EXAMPLE_COMMAND_HEX,json.dumps(raw),1254)
        self.assertTrue(p.complete);self.assertEqual(p.actions,())

    def test_bad_new_hex_json_or_reached_field_clears_stale_invocation(self):
        for h,s in (('not hex','{}'),(EXAMPLE_COMMAND_HEX,'{bad'),(EXAMPLE_COMMAND_HEX,'[]')):
            t,_=self.trial();t.step(EXAMPLE_COMMAND_HEX,example_chat_commands_sample(),1254)
            with self.assertRaises((ValueError,TypeError)):t.step(h,s,1254)
            self.assertIsNone(t.last);self.assertIsNone(t.frame);self.assertIsNone(t.captured)
        t,_=self.trial()
        with self.assertRaises(ValueError):t.step(EXAMPLE_COMMAND_HEX,'{"helper_returns":{"compare:disconnect":1}}',1254)
        self.assertIsNone(t.frame)

    def test_other_opcode_reset_and_reader_contract(self):
        t,_=self.trial();self.assertEqual(t.step('2f','{}',1254).status,'other_opcode');self.assertIsNone(t.frame)
        t.step(EXAMPLE_COMMAND_HEX,example_chat_commands_sample(),1254);t.reset();self.assertIsNone(t.configuration)
        with self.assertRaises(ValueError):ChatCommandsTrial(None).step('10','{}',1254)
        with self.assertRaises(ValueError):t.step('10','{}',0)

if __name__=='__main__':unittest.main()
