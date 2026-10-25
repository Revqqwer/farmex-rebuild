import unittest
from dataclasses import replace
from chat_prelude import (CHAT_LOG_INPUT,LOG_LABELS,compile_chat_log,
    ChatPreludeObservation as O,ChatPreludeFrame,ChatCommandEntryFrame,plan_chat_prelude)
from chat_party_invite import ChatPartyMessage
from chat_commands import SPECS,CommandSetting,ChatCommandsConfiguration as C,ChatCommandsObservation as CO

COMMON=('input_copy_and_sender_parse','text_buffers_prepare','message_objects_construct')
def message(channel=1):return ChatPartyMessage(channel,7,b'Alice',b'go')
def sample(channel=1):
    returns={k:True for k in COMMON+('log_strings_construct','log_assembly','log_sink','log_line_cleanup','log_strings_cleanup')}
    returns.update({'log_label_%d'%k:True for k in LOG_LABELS if k!=6})
    line=None if channel not in LOG_LABELS else b'['+LOG_LABELS[channel]+b'] Alice : go'
    return O(returns,line)
def config():return C(tuple(CommandSetting(s[0],int(s[0]=='disconnect'),b'go') for s in SPECS))
def command_sample():return CO({**{'compare:'+s[0]:True for s in SPECS},'action:disconnect':True})
CAPTURED=bytes.fromhex('1001000700000005416c696365027f676f')

class ChatPreludeTests(unittest.TestCase):
    def test_real_chat_log_flag_requires_known_checkbox(self):
        self.assertEqual(compile_chat_log({CHAT_LOG_INPUT:True}),1)
        self.assertEqual(compile_chat_log({CHAT_LOG_INPUT:False}),0)
        for value in (1,None,'yes'):
            with self.assertRaises(ValueError):compile_chat_log({CHAT_LOG_INPUT:value})

    def test_disabled_log_all_channels_reach_commands_without_log_observations(self):
        o=O({k:True for k in COMMON},b'unused wrong line')
        for channel in range(256):
            p=plan_chat_prelude(message(channel),0,o)
            self.assertTrue(p.complete);self.assertTrue(p.command_entry_reached);self.assertIsNone(p.log_intent)
            self.assertEqual(len([s for s in p.steps if s[0]=='normal_return']),3)

    def test_enabled_log_channel_filter_does_not_block_commands(self):
        for channel in range(256):
            p=plan_chat_prelude(message(channel),255,sample(channel))
            self.assertTrue(p.complete,channel);self.assertTrue(p.command_entry_reached)
            self.assertEqual(p.log_intent is not None,channel in LOG_LABELS)
            if p.log_intent is not None:
                self.assertTrue(p.log_intent.sink_normal_return_observed)
                self.assertFalse(p.log_intent.sink_effect_verified)
                self.assertEqual(p.log_intent.category,b'')

    def test_channel_six_logs_empty_label_without_label_helper(self):
        o=sample(6);p=plan_chat_prelude(message(6),1,o)
        self.assertEqual(p.log_intent.projected_line,b'[] Alice : go')
        self.assertFalse(any(s[0]=='normal_return' and s[1].startswith('log_label_') for s in p.steps))

    def test_exact_case_and_c_string_projection(self):
        msg=ChatPartyMessage(2,7,b'ALIce\0ignored',b'GO\0ignored')
        o=replace(sample(2),assembled_log_bytes=b'[PM] ALIce : GO')
        self.assertEqual(plan_chat_prelude(msg,1,o).log_intent.observed_line,b'[PM] ALIce : GO')

    def test_log_assembly_requires_distinct_exact_snapshot(self):
        p=plan_chat_prelude(message(),1,replace(sample(),assembled_log_bytes=None))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'assembled log byte snapshot')
        self.assertFalse(p.log_intent.sink_normal_return_observed)
        with self.assertRaises(ValueError):plan_chat_prelude(message(),1,replace(sample(),assembled_log_bytes=b'[All] alice : go'))

    def test_log_sink_normal_return_is_distinct_from_line_preparation(self):
        o=sample();p=plan_chat_prelude(message(),1,replace(o,normal_returns={**o.normal_returns,'log_sink':False}))
        self.assertFalse(p.complete);self.assertFalse(p.command_entry_reached)
        self.assertEqual(p.log_intent.observed_line,o.assembled_log_bytes)
        self.assertFalse(p.log_intent.sink_normal_return_observed)

    def test_each_reached_normal_boundary_is_required(self):
        for channel,flag in ((1,0),(1,1),(6,1),(7,1)):
            o=sample(channel);full=plan_chat_prelude(message(channel),flag,o)
            for step in full.steps:
                if step[0]!='normal_return':continue
                label=step[1];p=plan_chat_prelude(message(channel),flag,replace(o,normal_returns={**o.normal_returns,label:False}))
                self.assertFalse(p.complete,(channel,flag,label));self.assertEqual(p.missing,label+' normal return')

    def test_frame_retains_assembled_snapshot_and_prior_returns(self):
        f=ChatPreludeFrame(message(),1);o=sample()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'log_line_cleanup':False}))
        self.assertFalse(p.complete);self.assertTrue(p.log_intent.sink_normal_return_observed)
        p=f.advance(O({'log_line_cleanup':True,'log_strings_cleanup':True},b'consumed bad line'))
        self.assertTrue(p.complete);self.assertEqual(p.log_intent.observed_line,b'[All] Alice : go')
        self.assertIs(f.advance(O()),p)

    def test_entry_does_not_consume_command_receipts_before_prelude(self):
        f=ChatCommandEntryFrame(config(),CAPTURED,0)
        p=f.advance(O(),command_sample())
        self.assertFalse(p.complete);self.assertEqual(p.actions,())
        self.assertEqual(dict(f.commands.observation.helper_returns),{})
        p=f.advance(sample(),command_sample())
        self.assertTrue(p.complete);self.assertEqual([a.key for a in p.actions],['disconnect'])
        self.assertTrue(p.prelude.command_entry_reached);self.assertFalse(p.full_handler_verified)

    def test_entry_preserves_prelude_when_command_gap_resumes(self):
        f=ChatCommandEntryFrame(config(),CAPTURED,1)
        p=f.advance(sample(),CO({'compare:disconnect':True}))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'action:disconnect normal return')
        p=f.advance(O(),command_sample());self.assertTrue(p.complete)
        self.assertIs(f.advance(O(),CO()),p)

    def test_bounded_truncated_and_other_opcode_never_enter_source_span(self):
        f=ChatCommandEntryFrame(config(),b'\x10',0);p=f.advance(sample(),command_sample())
        self.assertFalse(p.complete);self.assertIsNone(f.prelude);self.assertEqual(p.actions,())
        f=ChatCommandEntryFrame(config(),b'\x2f',0);p=f.advance(O(),CO())
        self.assertTrue(p.complete);self.assertEqual(p.status,'other_opcode');self.assertEqual(p.actions,())

if __name__=='__main__':unittest.main()
