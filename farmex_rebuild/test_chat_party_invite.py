import unittest
from dataclasses import replace
from chat_party_invite import *

def config(**kw):
    return replace(ChatPartyConfiguration(1, 1, b'add', (b'Alice',)), **kw)

def observations(**kw):
    return replace(ChatPartyObservation(actor_dword=9, use_owned_filter=True,
        helper_returns={k: True for k in ('command_compare','actor','filter_arguments','name_filter','invite_arguments','invite')}), **kw)

MSG = ChatPartyMessage(1, 7, b'Alice', b'add')

def captured(name=b'Alice', message=b'add', channel=1, sender=7):
    return bytes((0x10, channel, 0)) + sender.to_bytes(4,'little') + bytes((len(name),)) + name + bytes((len(message),0x7f)) + message

class ChatPrefixTests(unittest.TestCase):
    def test_offsets_embedded_nul_and_trailing_data(self):
        p = parse_chat_prefix(captured(b'Alice\0Bob', b'add\0rest', 3, 0xffffffff)+b'extra')
        self.assertTrue(p.complete)
        self.assertEqual(p.message, ChatPartyMessage(3,0xffffffff,b'Alice',b'add'))
        self.assertFalse(p.native_execution_verified)

    def test_each_truncated_prefix_stops_and_no_missing_byte_is_filled(self):
        data = captured()
        for end in range(len(data)):
            with self.subTest(end=end):
                p = parse_chat_prefix(data[:end])
                self.assertFalse(p.complete); self.assertIsNone(p.message)
        self.assertTrue(parse_chat_prefix(data).complete)
        self.assertEqual(parse_chat_prefix(b'\x2f').status,'other_opcode')
        with self.assertRaises(ValueError): parse_chat_prefix(bytearray(data))

    def test_zero_length_fields_still_require_skipped_message_header_byte(self):
        data = captured(b'',b'')
        self.assertFalse(parse_chat_prefix(data[:-1]).complete)
        self.assertEqual(parse_chat_prefix(data).message.name,b'')

class ChatDecisionTests(unittest.TestCase):
    def test_disabled_and_channel3_do_not_require_unreached_actor_filter(self):
        for c, msg in ((config(enabled_byte=0),MSG),(config(),replace(MSG,channel=3))):
            p = plan_chat_party(c,msg,ChatPartyObservation())
            self.assertTrue(p.complete); self.assertEqual(p.calls,()); self.assertIsNone(p.action)
        # Every other observed byte enters this gate; not just channel1/PM.
        self.assertFalse(plan_chat_party(config(),replace(MSG,channel=255),ChatPartyObservation()).complete)

    def test_exact_command_case_spaces_and_empty_command(self):
        for command in (b'ADD',b' add',b'add ',b'add\0'):
            p=plan_chat_party(config(command=command),MSG,observations(actor_dword=None))
            self.assertTrue(p.complete); self.assertEqual(p.status,'command_mismatch')
            self.assertNotIn(('00462650',),p.calls)
        p=plan_chat_party(config(command=b''),replace(MSG,message=b''),observations())
        self.assertTrue(p.complete); self.assertEqual(p.action,'invite')

    def test_actor_normal_and_full_dword_self_comparison(self):
        p=plan_chat_party(config(),MSG,observations(helper_returns={'command_compare':True}))
        self.assertEqual(p.missing,'actor normal return')
        p=plan_chat_party(config(),MSG,observations(actor_dword=None))
        self.assertEqual(p.missing,'actor DWORD')
        p=plan_chat_party(config(),MSG,observations(actor_dword=7))
        self.assertTrue(p.complete); self.assertEqual(p.status,'self_sender')
        self.assertFalse(any(c[0]=='004cbecc' for c in p.calls))
        p=plan_chat_party(config(),MSG,observations(actor_dword=0x10007))
        self.assertEqual(p.action,'invite')

    def test_all_mode_skips_filter_in_contrast_to_incoming_accept_handler(self):
        o=observations(use_owned_filter=False,filter_eax=None,
            helper_returns={'command_compare':True,'actor':True,'invite_arguments':True,'invite':True})
        p=plan_chat_party(config(list_only_byte=0,names=None),MSG,o)
        self.assertTrue(p.complete); self.assertIsNone(p.matched)
        self.assertFalse(any(c[0]=='004cbecc' for c in p.calls))

    def test_list_uses_exact_name_or_low_al_after_normal_receipt(self):
        p=plan_chat_party(config(names=(b'alice',)),MSG,observations())
        self.assertEqual(p.status,'unlisted'); self.assertIsNone(p.action)
        for eax, expected in ((0x100,'unlisted'),(0x101,'reached_invite_span_returned'),(0xff,'reached_invite_span_returned')):
            p=plan_chat_party(config(names=None),MSG,observations(use_owned_filter=False,filter_eax=eax))
            self.assertEqual(p.status,expected)
        p=plan_chat_party(config(),MSG,observations(helper_returns={'command_compare':True,'actor':True,'filter_arguments':True}))
        self.assertEqual(p.missing,'name_filter normal return')
        with self.assertRaises(ValueError):plan_chat_party(config(),MSG,observations(filter_eax=1))

    def test_bound_name_completion_and_outer_return_are_separate(self):
        f=ChatInviteEmissionFrame(b'Alice')
        p=plan_chat_party(config(),MSG,observations(invitation=f.advance()))
        self.assertFalse(p.complete); self.assertIn('bound invitation',p.missing)
        e=f.advance(gates=(1,1),ticks=(10,11),returned=(True,True),cleanup_returned=True)
        o=observations(invitation=e,helper_returns={**observations().helper_returns,'invite':False})
        self.assertEqual(plan_chat_party(config(),MSG,o).missing,'invite normal return')
        self.assertTrue(plan_chat_party(config(),MSG,replace(o,helper_returns=observations().helper_returns)).complete)
        e=ChatInviteEmissionFrame(b'Bob').advance(gates=(0,0),returned=(True,True),cleanup_returned=True)
        with self.assertRaises(ValueError):plan_chat_party(config(),MSG,observations(invitation=e))
        self.assertTrue(plan_chat_party(config(enabled_byte=0),MSG,observations(invitation=e)).complete)

class ChatEmissionTests(unittest.TestCase):
    def test_two_source_records_have_independent_clocks_and_keep_existing_queue(self):
        initial=enqueue(QueueState(),b'old',3,5,1,1).state
        f=ChatInviteEmissionFrame(b'Alice',initial)
        p=f.advance(gates=(1,1),ticks=(10,20),returned=(True,True),cleanup_returned=True)
        self.assertTrue(p.complete)
        self.assertEqual([r.payload for r in p.queue.records],[b'old',b'\x2f\x03\x05\x00Alice',b'\x2f\x01\x05\x00Alice'])
        self.assertEqual([r.created_tick for r in p.queue.records],[1,10,20])
        self.assertEqual([r.delay_dword for r in p.queue.records],[5,0,0])
        self.assertIs(f.advance(),p)

    def test_second_gate_clock_and_normal_gaps_do_not_duplicate_first_record(self):
        f=ChatInviteEmissionFrame(b'Alice')
        self.assertFalse(f.advance(gates=(1,),ticks=(10,)).complete)
        self.assertEqual(len(f.queue.records),1)
        self.assertIn('enqueue 2:',f.advance(returned=(True,)).missing)
        self.assertEqual(len(f.queue.records),1)
        self.assertIn('GetTickCount',f.advance(gates=(None,1)).missing)
        self.assertEqual(len(f.queue.records),1)
        self.assertIn('enqueue 2 normal',f.advance(gates=(0,1),ticks=(999,20)).missing)
        self.assertEqual(len(f.queue.records),2)
        self.assertIn('cleanup',f.advance(returned=(False,True)).missing)
        p=f.advance(cleanup_returned=True)
        self.assertTrue(p.complete);self.assertEqual([r.created_tick for r in p.queue.records],[10,20])

    def test_each_disconnected_enqueue_is_known_skip_not_retried(self):
        for gates, expected in (((0,1),[b'\x2f\x01']),((1,0),[b'\x2f\x03']),((0,0),[])):
            f=ChatInviteEmissionFrame(b'')
            p=f.advance(gates=gates,ticks=(10,20),returned=(True,True),cleanup_returned=True)
            self.assertTrue(p.complete)
            self.assertEqual([r.payload[:2] for r in p.queue.records],expected)
            self.assertIs(f.advance(gates=(1,1),ticks=(30,40)),p)

    def test_known_gate_is_consumed_before_missing_clock(self):
        f=ChatInviteEmissionFrame(b'Alice')
        self.assertIn('GetTickCount',f.advance(gates=(1,)).missing)
        p=f.advance(gates=(0,0),ticks=(10,),returned=(True,True),cleanup_returned=True)
        self.assertTrue(p.complete)
        self.assertEqual([r.payload[:2] for r in p.queue.records],[b'\x2f\x03'])

    def test_buffer_alias_boundary_remains_gap_instead_of_truncating_name(self):
        f=ChatInviteEmissionFrame(b'A'*96)
        p=f.advance(gates=(1,1),ticks=(10,20),returned=(True,True),cleanup_returned=True)
        self.assertTrue(p.complete); self.assertEqual(len(p.queue.records[0].payload),100)
        f=ChatInviteEmissionFrame(b'A'*97)
        p=f.advance(gates=(1,1),ticks=(10,20),returned=(True,True),cleanup_returned=True)
        self.assertFalse(p.complete);self.assertIn('stack overlap',p.missing);self.assertEqual(f.queue.records,())
        with self.assertRaises(ValueError):ChatInviteEmissionPlan(True,b'Alice',QueueState())

    def test_panel_compiler_keeps_unchecked_names_and_c_string_semantics(self):
        values=dict(zip(CHAT_PARTY_INPUTS,(True,'add\0tail',True)))
        c=compile_chat_party(values,{PARTY_LIST:[{'caption':'Çağrı\0tail','checked':False},{'caption':'Alice'}]},WindowsNameCodec(1254))
        self.assertEqual(c.command,b'add');self.assertEqual(c.names,('Çağrı'.encode('cp1254'),b'Alice'))
        self.assertEqual(c.codepage,1254)
        with self.assertRaises(ValueError):compile_chat_party(values,{PARTY_LIST:[{'caption':'😀'}]},WindowsNameCodec(1254))
        with self.assertRaises(ValueError):ChatPartyMessage(True,7,b'A',b'add')
        with self.assertRaises(ValueError):ChatPartyObservation(actor_dword=1<<32)

class ChatFrameTests(unittest.TestCase):
    def test_resume_after_first_enqueue_and_outer_return_preserves_prefix(self):
        f=ChatPartyInvitationFrame(config(),MSG)
        p=f.advance(observations(),gates=(1,),ticks=(10,),returned=(True,))
        self.assertFalse(p.complete);self.assertEqual(len(f.queue.records),1)
        # No actor/filter receipts are supplied again; consumed prefix is retained.
        p=f.advance(ChatPartyObservation(),gates=(0,1),ticks=(999,20),returned=(False,True),cleanup_returned=True)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'invite normal return')
        self.assertEqual([r.created_tick for r in f.queue.records],[10,20])
        p=f.advance(ChatPartyObservation(helper_returns={'invite':True}))
        self.assertTrue(p.complete);self.assertEqual(len(f.queue.records),2)
        self.assertIs(f.advance(ChatPartyObservation()),p)

    def test_unknown_prefix_and_filtered_messages_never_create_emission(self):
        f=ChatPartyInvitationFrame(config(),MSG)
        self.assertFalse(f.advance(ChatPartyObservation(),gates=(1,1),ticks=(10,20)).complete)
        self.assertIsNone(f.emission);self.assertEqual(f.queue.records,())
        f=ChatPartyInvitationFrame(config(names=()),MSG)
        self.assertEqual(f.advance(observations()).status,'unlisted')
        self.assertIsNone(f.emission)

    def test_external_child_rejected_only_if_owned_branch_reaches_invite(self):
        e=ChatInviteEmissionFrame(b'Alice').advance()
        with self.assertRaises(ValueError):ChatPartyInvitationFrame(config(),MSG).advance(observations(invitation=e))
        self.assertTrue(ChatPartyInvitationFrame(config(enabled_byte=0),MSG).advance(observations(invitation=e)).complete)

if __name__ == '__main__': unittest.main()
