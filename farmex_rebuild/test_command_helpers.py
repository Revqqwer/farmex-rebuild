import unittest
from dataclasses import replace
from command_helpers import *
from chat_commands import (SPECS,CommandSetting,ChatCommandsConfiguration,ChatCommandsObservation,
                           ChatCommandsFrame,plan_chat_commands)
from chat_party_invite import ChatPartyMessage

TOWN_RETURNS=('town_string_construct','text_string_lifetime','allocate_record','strlen','zero_record',
    'copy_text','copy_length','copy_type','patch_root','patch_buffer','patch_target','thread_helper',
    'free_record','text_cleanup','text_helper','town_cleanup')
def town_samples(**kw):
    return replace(TownObservation(0x3000,((0x553e80,0x1128a7c),(0x553eec,0x88776655)),
                                   {k:True for k in TOWN_RETURNS}),**kw)
def config(key):return ChatCommandsConfiguration(tuple(CommandSetting(k,int(k==key),b'go') for k,*_ in SPECS))
def obs(**kw):return replace(ChatCommandsObservation(helper_returns={prefix+k:True for k,*_ in SPECS for prefix in ('compare:','action:')}),**kw)
MSG=ChatPartyMessage(1,7,b'Alice',b'go')

class CommandSeedTests(unittest.TestCase):
    def test_exact_dc_and_stand_seeds_without_actor_or_name(self):
        for key,payload in (('disconnect',b'\0'),('stand',b'\x12\x01')):
            f=CommandQueueFrame(key);p=f.advance(1,100)
            self.assertTrue(p.complete);self.assertEqual(p.payload,payload)
            self.assertEqual(f.queue.records[0].payload,payload);self.assertEqual(f.queue.records[0].delay_dword,0)
            self.assertFalse(p.native_execution_verified)

    def test_unknown_gate_tick_cache_and_no_duplicate_completed_record(self):
        f=CommandQueueFrame('disconnect')
        self.assertFalse(f.advance().complete)
        self.assertFalse(f.advance(1).complete)
        p=f.advance(0,100)
        self.assertTrue(p.complete);self.assertEqual(len(f.queue.records),1)
        self.assertIs(f.advance(1,200),p);self.assertEqual(len(f.queue.records),1)

    def test_gate_zero_is_known_skip_not_successful_transmission(self):
        f=CommandQueueFrame('stand');p=f.advance(0)
        self.assertTrue(p.complete);self.assertEqual(p.decision.status,'not_enqueued');self.assertEqual(f.queue.records,())
        self.assertIs(f.advance(1,100),p)
        with self.assertRaises(ValueError):CommandQueuePlan(True,'stand',b'\x12\x01')

class TownHelperTests(unittest.TestCase):
    def test_fixed_record_and_patched_stub_are_not_a_network_packet(self):
        p=plan_town_helper(town_samples());self.assertTrue(p.complete)
        record=bytearray(80);record[:5]=b'/Town';record[0x10]=5;record[0x14]=0xf
        self.assertEqual(p.record_image,bytes(record))
        stub=bytearray(TOWN_STUB);stub[3:7]=(0x1128a7c).to_bytes(4,'little');stub[8:12]=(0x3000).to_bytes(4,'little');stub[14:18]=(0x88776655).to_bytes(4,'little')
        self.assertEqual(p.stub_image,bytes(stub));self.assertEqual(len(p.stub_image),22)
        self.assertFalse(p.native_execution_verified or p.thread_callback_verified)

    def test_each_opaque_copy_thread_and_cleanup_return_is_required(self):
        for label in TOWN_RETURNS:
            with self.subTest(label=label):
                p=plan_town_helper(town_samples(helper_returns={**town_samples().helper_returns,label:False}))
                self.assertFalse(p.complete);self.assertEqual(p.missing,label+' normal return')

    def test_unchecked_null_allocation_remains_native_fault_gap(self):
        p=plan_town_helper(town_samples(buffer_address=0))
        self.assertFalse(p.complete);self.assertEqual(p.status,'unchecked_null_allocation')
        self.assertIsNone(p.record_image);self.assertIsNone(p.stub_image)
        self.assertFalse(any(s[0]=='memset_plan' for s in p.steps))

    def test_global_patch_order_is_separate_from_buffer_and_runtime_root(self):
        p=plan_town_helper(town_samples(global_samples=((0x553e80,0x1128a7c),)))
        self.assertFalse(p.complete);self.assertIn('00553eec',p.missing)
        self.assertEqual(p.stub_image[3:7],(0x1128a7c).to_bytes(4,'little'))
        self.assertEqual(p.stub_image[14:18],b'\0'*4)
        with self.assertRaises(ValueError):plan_town_helper(town_samples(global_samples=((0x553eec,1),(0x553e80,2))))

    def test_town_frame_keeps_allocation_and_root_prefix_across_late_gap(self):
        f=TownFrame();first=town_samples(helper_returns={**town_samples().helper_returns,'thread_helper':False})
        p=f.advance(first);self.assertFalse(p.complete);self.assertIn('thread_helper normal return',p.missing)
        p=f.advance(TownObservation(buffer_address=999,helper_returns={k:True for k in ('thread_helper','free_record','text_cleanup','text_helper','town_cleanup')}))
        self.assertTrue(p.complete);self.assertEqual(p.buffer_address,0x3000)
        self.assertEqual(p.stub_image[3:7],(0x1128a7c).to_bytes(4,'little'))
        self.assertIs(f.advance(TownObservation()),p)

    def test_bound_town_result_cannot_substitute_other_record_or_code(self):
        p=plan_town_helper(town_samples())
        with self.assertRaises(ValueError):replace(p,record_image=b'x'*80)
        with self.assertRaises(ValueError):replace(p,stub_image=b'x'*22)
        with self.assertRaises(ValueError):replace(p,buffer_address=0x4000)

class CommandHelperBindingTests(unittest.TestCase):
    def test_child_incomplete_cannot_be_bypassed_by_action_return(self):
        p=plan_chat_commands(config('disconnect'),MSG,obs(action_executions={'disconnect':CommandQueueFrame('disconnect').advance()}))
        self.assertFalse(p.complete);self.assertIn('bound action:disconnect',p.missing)
        child=CommandQueueFrame('disconnect').advance(0)
        p=plan_chat_commands(config('disconnect'),MSG,obs(helper_returns={**obs().helper_returns,'action:disconnect':False},action_executions={'disconnect':child}))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'action:disconnect normal return')

    def test_wrong_helper_kind_rejected_only_for_reached_action(self):
        child=CommandQueueFrame('stand').advance(0)
        with self.assertRaises(ValueError):plan_chat_commands(config('disconnect'),MSG,obs(action_executions={'disconnect':child}))
        p=plan_chat_commands(config('town'),MSG,obs(action_executions={'disconnect':child}))
        self.assertTrue(p.complete);self.assertEqual(p.actions[0].key,'town')

    def test_parent_frame_resumes_bound_town_without_repeating_prior_receipts(self):
        f=ChatCommandsFrame(config('town'),MSG);child=plan_town_helper(town_samples(helper_returns={**town_samples().helper_returns,'free_record':False}))
        p=f.advance(obs(action_executions={'town':child}))
        self.assertFalse(p.complete);self.assertIn('bound action:town',p.missing)
        child=plan_town_helper(town_samples())
        p=f.advance(ChatCommandsObservation(helper_returns={'action:town':True},action_executions={'town':child}))
        self.assertTrue(p.complete);self.assertIs(p.actions[0].helper_execution,child)

if __name__=='__main__':unittest.main()
