import unittest
from message_channels import *

def channel(which='all',**changes):
    values={key+'_compare_eax':int(key==which) for key,_,_ in CHANNELS}
    values['fresh_message_argument_dword']=0x4000;values.update(changes)
    normals={key:True for key in ('message_argument_copy','channel_argument_copy','serializer',
                                 'channel_argument_cleanup','message_argument_cleanup')}
    for key,_,_ in CHANNELS:
        for suffix in ('_literal','_compare','_literal_cleanup'):normals[key+suffix]=True
    return MessageChannelObservation(True,values,normals)

def cycle():
    return SourceMessageCycleObservation(True,dict(first_test_begin=0x1000,first_end=0x100c,first_subtract_begin=0x1000,
        first_tick_eax=1000,last_tick_low=0,last_tick_high=0,delay_index=0,delay_begin=0x1000,delay_value=1000,
        argument4_index=0,argument4_begin=0x1000,argument4_value=0x3000,
        argument0_index=0,argument0_begin=0x1000,argument0_value=0x2000,
        second_tick_eax=1010,increment_index_before=0,tail_test_begin=0x1000,tail_end=0x100c,
        tail_subtract_begin=0x1000,tail_compare_index=1),{'first_tick':True,'second_tick':True})

class MessageChannelTests(unittest.TestCase):
    def test_all_six_ids_and_first_match_order(self):
        for key,_,identifier in CHANNELS:
            plan=MessageChannelFrame(1,2).advance(channel(key))
            self.assertEqual((plan.channel_key,plan.channel_id),(key,identifier))
            self.assertEqual(plan.serializer_physical_pushes,(0x4000,identifier,0x561ef8))
            compared=[c[2] for c in plan.calls if c[0]=='00505134']
            self.assertEqual(compared,[k+'_compare' for k,_,_ in CHANNELS[:[r[0] for r in CHANNELS].index(key)+1]])

    def test_comparator_uses_low_byte_nonzero_and_first_true_wins(self):
        plan=MessageChannelFrame(1,2).advance(channel('noah',all_compare_eax=0xff,party_compare_eax=1))
        self.assertEqual(plan.channel_key,'all')
        plan=MessageChannelFrame(1,2).advance(channel('party',all_compare_eax=0x100))
        self.assertEqual(plan.channel_key,'party')

    def test_no_match_skips_serializer_and_still_cleans_both_arguments(self):
        plan=MessageChannelFrame(1,2).advance(channel('unknown'))
        self.assertEqual(plan.status,'no_channel_match');self.assertIsNone(plan.channel_id)
        self.assertNotIn('004c9b74',[c[0] for c in plan.calls])
        self.assertEqual([c[2] for c in plan.calls[-2:]],['channel_argument_cleanup','message_argument_cleanup'])

    def test_argument_copy_order_and_explicit_normals(self):
        frame=MessageChannelFrame(1,2);plan=frame.advance(MessageChannelObservation(True))
        self.assertEqual(plan.needed,('normal','message_argument_copy'))
        plan=frame.advance(MessageChannelObservation(normal_returns={'message_argument_copy':True}))
        self.assertEqual(plan.needed,('normal','channel_argument_copy'))

    def test_comparison_result_before_literal_cleanup_is_cached(self):
        frame=MessageChannelFrame(1,2);sample=channel('party')
        plan=frame.advance(replace(sample,normal_returns={**sample.normal_returns,'party_literal_cleanup':False}))
        self.assertEqual(plan.needed,('normal','party_literal_cleanup'));self.assertIsNone(plan.channel_id)
        plan=frame.advance(channel('all',party_compare_eax=0))
        self.assertEqual(plan.channel_key,'party')

    def test_fresh_message_handle_not_assumed_equal_to_input(self):
        sample=channel();values=dict(sample.values);del values['fresh_message_argument_dword']
        frame=MessageChannelFrame(0x2000,0x3000,source_context=0xffffffff)
        plan=frame.advance(replace(sample,values=values))
        self.assertEqual(plan.needed,('value','fresh_message_argument_dword'))
        plan=frame.advance(MessageChannelObservation(values={'fresh_message_argument_dword':0x5000},
            normal_returns={'serializer':True,'channel_argument_cleanup':True,'message_argument_cleanup':True}))
        self.assertEqual(plan.serializer_physical_pushes,(0x5000,0,0x561ef8))
        self.assertEqual(plan.source_arguments,(0xffffffff,0x2000,0x3000))

    def test_serializer_and_two_cleanup_returns_are_separate(self):
        sample=channel();frame=MessageChannelFrame(1,2)
        plan=frame.advance(replace(sample,normal_returns={**sample.normal_returns,'serializer':False}))
        self.assertEqual(plan.needed,('normal','serializer'))
        plan=frame.advance(MessageChannelObservation(normal_returns={'serializer':True}))
        self.assertEqual(plan.needed,('normal','channel_argument_cleanup'))
        plan=frame.advance(MessageChannelObservation(normal_returns={'channel_argument_cleanup':True}))
        self.assertEqual(plan.needed,('normal','message_argument_cleanup'))
        plan=frame.advance(MessageChannelObservation(normal_returns={'message_argument_cleanup':True}))
        self.assertTrue(plan.complete);self.assertIs(frame.advance(MessageChannelObservation()),plan)

    def test_cycle_field_order_binding_and_parent_return_gate(self):
        frame=ChannelMessageCycleFrame();plan=frame.advance(cycle(),channel_parent_returned=True)
        self.assertEqual(plan.needed,('channel',('entry','0045c208')))
        self.assertEqual(plan.channel.source_arguments,(0x569910,0x2000,0x3000))
        plan=frame.advance(SourceMessageCycleObservation(),channel('clan'))
        self.assertEqual(plan.needed,'channel_parent_returned');self.assertEqual(plan.cycle.stores,())
        plan=frame.advance(SourceMessageCycleObservation(),channel_parent_returned=True)
        self.assertEqual(plan.needed,('normal','second_tick'))
        plan=frame.advance(cycle())
        self.assertTrue(plan.complete);self.assertEqual(plan.channel.channel_id,3)
        self.assertEqual(plan.cycle.stores[-1],(0x569934,4,0))

    def test_unmatched_channel_still_allows_parent_timestamp_and_index_update(self):
        plan=ChannelMessageCycleFrame().advance(cycle(),channel('unknown'),channel_parent_returned=True)
        self.assertTrue(plan.complete);self.assertEqual(plan.channel.status,'no_channel_match')
        self.assertEqual(plan.cycle.stores[0],(0x569938,4,1010))

    def test_empty_cycle_skips_channel_and_rejects_parent_override(self):
        plan=ChannelMessageCycleFrame().advance(SourceMessageCycleObservation(True,{'first_test_begin':0}))
        self.assertTrue(plan.complete);self.assertIsNone(plan.channel)
        with self.assertRaises(ValueError):
            ChannelMessageCycleFrame().advance(SourceMessageCycleObservation(normal_returns={'message_helper':True}))

    def test_types_and_scope_flags(self):
        with self.assertRaises(ValueError):MessageChannelFrame(None,2)
        with self.assertRaises(ValueError):MessageChannelObservation(values={'all_compare_eax':True})
        with self.assertRaises(ValueError):MessageChannelObservation(normal_returns={'serializer':1})
        plan=MessageChannelFrame(1,2).advance(channel())
        self.assertFalse(plan.string_equality_verified);self.assertFalse(plan.native_execution_verified)
        self.assertFalse(plan.delivery_verified)

if __name__=='__main__':unittest.main()
