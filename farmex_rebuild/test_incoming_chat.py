import unittest
from dataclasses import replace
from incoming_chat import (ChatBlockConfiguration as C,IncomingChatObservation as O,
    IncomingChatFrame,compile_chat_block,plan_chat_block,plan_incoming_chat)

EMPTY=C((0,)*8)
def sample(**values):
    v=dict(opcode_for_eight=0x10,opcode_for_chat=0x10,handler_length_dword=17,handler_buffer_dword=0x1000,
           channel_for_exemption=1,channel_for_filter=1,channel_for_clan=1,
           clan_sender_word=7,clan_object_eax=0x2000,clan_flag_offset_dword=0x10,clan_flag_eax=1)
    v.update(values)
    return O(v,{k:True for k in ('dispatcher_frame_setup','whole_chat_handler','chat_filter','clan_sender_parse','clan_lookup','clan_flag_read')})

class IncomingChatTests(unittest.TestCase):
    def test_checkbox_rows_map_by_position_not_caption(self):
        expected=(None,1,2,3,6,5,14,34)
        for index,channel in enumerate(expected):
            rows=[{'caption':'arbitrary','checked':i==index} for i in range(8)]
            c=compile_chat_block(rows)
            for candidate in range(256):
                p=plan_chat_block(c,candidate)
                self.assertEqual(p.low_al,int(index==0 or candidate==channel),(index,candidate))
        with self.assertRaises(ValueError):compile_chat_block([])

    def test_source_channel_four_has_no_specific_checkbox_branch(self):
        c=compile_chat_block([{'checked':i==5} for i in range(8)])
        self.assertEqual(plan_chat_block(c,5).low_al,1)
        self.assertEqual(plan_chat_block(c,4).low_al,0)

    def test_filter_uses_low_byte_and_does_not_claim_full_eax(self):
        c=C((0,1,0,0,0,0,0,0));p=plan_chat_block(c,0x101)
        self.assertEqual(p.low_al,1);self.assertFalse(p.native_full_eax_verified)
        self.assertEqual(p.tested_offsets,(1,2))
        self.assertEqual(plan_chat_block(C((255,)*8),99).tested_offsets,(1,))

    def test_handler_always_precedes_filter_even_block_all(self):
        o=sample();p=plan_incoming_chat(C((1,)*8),replace(o,normal_returns={**o.normal_returns,'whole_chat_handler':False}))
        self.assertFalse(p.complete);self.assertIsNone(p.filter_plan)
        self.assertEqual(p.handler_push_order,(17,0x1000,0x569220))
        p=plan_incoming_chat(C((1,)*8),o);self.assertTrue(p.complete);self.assertEqual(p.source_return_dword,0)
        self.assertFalse(p.packet_delivery_effect_verified)

    def test_channel_seven_bypasses_filter_even_block_all(self):
        o=sample(channel_for_exemption=7,channel_for_clan=7)
        v=dict(o.values);del v['channel_for_filter']
        r=dict(o.normal_returns);del r['chat_filter']
        p=plan_incoming_chat(C((1,)*8),O(v,r))
        self.assertTrue(p.complete);self.assertEqual(p.source_return_dword,1);self.assertIsNone(p.filter_plan)

    def test_channel_values_are_fresh_separate_observations(self):
        p=plan_incoming_chat(C((0,0,1,0,0,0,0,0)),sample(channel_for_exemption=1,channel_for_filter=2,channel_for_clan=99))
        self.assertEqual(p.source_return_dword,0)
        o=sample(channel_for_exemption=7,channel_for_clan=5,clan_flag_eax=0)
        self.assertEqual(plan_incoming_chat(EMPTY,o).source_return_dword,0)

    def test_clan_zero_sender_and_zero_lookup_skip_flag_read(self):
        for values in (dict(clan_sender_word=0),dict(clan_object_eax=0)):
            o=sample(channel_for_clan=5,**values);v=dict(o.values)
            del v['clan_flag_offset_dword'];del v['clan_flag_eax']
            p=plan_incoming_chat(EMPTY,O(v,o.normal_returns))
            self.assertTrue(p.complete);self.assertEqual(p.source_return_dword,1)

    def test_clan_guarded_byte_uses_low_al_and_wrapped_address(self):
        for eax,ret in ((0,0),(0x100,0),(1,1),(0x101,1)):
            p=plan_incoming_chat(EMPTY,sample(channel_for_clan=5,clan_object_eax=0xfffffff8,clan_flag_eax=eax))
            self.assertTrue(p.complete);self.assertEqual(p.source_return_dword,ret)
            step=next(s for s in p.steps if s[0]=='guarded_BYTE_helper')
            self.assertEqual(step[2],8)

    def test_other_dispatch_branches_remain_explicit_gaps(self):
        for values in (dict(opcode_for_eight=8),dict(opcode_for_chat=0x68)):
            p=plan_incoming_chat(EMPTY,sample(**values))
            self.assertFalse(p.complete);self.assertEqual(p.request[0],'scope');self.assertIsNone(p.handler_push_order)

    def test_every_reached_normal_and_value_is_required(self):
        o=sample(channel_for_clan=5);p=plan_incoming_chat(EMPTY,o)
        self.assertTrue(p.complete)
        for step in p.steps:
            kind,label=step[:2]
            if kind=='source_value':
                v=dict(o.values);del v[label]
                self.assertFalse(plan_incoming_chat(EMPTY,O(v,o.normal_returns)).complete,label)
            elif kind=='normal_return':
                r=dict(o.normal_returns);r[label]=False
                gap=plan_incoming_chat(EMPTY,O(o.values,r));self.assertFalse(gap.complete,label)
                self.assertEqual(gap.missing,label+' normal return')

    def test_frame_keeps_whole_handler_receipt_and_fresh_read_prefix(self):
        f=IncomingChatFrame(EMPTY);o=sample(channel_for_clan=5)
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'clan_flag_read':False}))
        self.assertFalse(p.complete)
        p=f.advance(O({'clan_flag_eax':0},{'clan_flag_read':True}))
        self.assertTrue(p.complete);self.assertEqual(p.source_return_dword,0)
        self.assertIs(f.advance(O()),p)

    def test_raw_widths_and_boolean_flags_are_not_coerced(self):
        for field,value in (('opcode_for_chat',256),('clan_sender_word',0x10000),('handler_buffer_dword',True)):
            with self.assertRaises(ValueError):O({field:value})
        with self.assertRaises(ValueError):O(normal_returns={'whole_chat_handler':1})

if __name__=='__main__':unittest.main()
