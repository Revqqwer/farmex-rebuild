import unittest
from message_list_producer import *

def sample(count=1,*,grow=False,parser=None):
    values={};normals={k:True for k in ('clear_end_iterator','clear_begin_iterator','clear_range')};texts={};ansi={};integers={}
    for index in range(count):
        p='row%d.'%index
        values.update({p+'count_eax':count,p+'size_eax':index,p+'capacity_eax':index if grow else 10,p+'end_dword':0x1000+12*index})
        for role,text,data in (('channel','Party',b'Party'),('message','Captured Unicode',b'owned\x00bytes')):
            texts[p+role]=text;ansi[p+role]=data
            for stage in ('_init','_get','_ansi','_unicode_cleanup'):normals[p+role+stage]=True
        texts[p+'delay']='not lexically inferred'
        for role in ('delay_init','delay_get','parser_outer','delay_unicode_cleanup','record_channel_init',
                     'record_message_init','record_channel_assign','record_message_assign','size','capacity',
                     'fast_append','grow_end_iterator','grow_insert','record_message_cleanup','record_channel_cleanup',
                     'original_message_cleanup','original_channel_cleanup'):
            normals[p+role]=True
        integers[p+'delay_integer']=parser or SourceIntegerObservation(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True)
    values['row%d.count_eax'%count]=count;normals['row%d.count'%count]=True
    for index in range(count):normals['row%d.count'%index]=True
    return MessageListObservation(True,values,normals,texts,ansi,integers)

class MessageListProducerTests(unittest.TestCase):
    def test_clear_before_empty_list_count_and_no_rows(self):
        frame=MessageListFrame();s=sample(0)
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'clear_range':False}))
        self.assertFalse(plan.cleared);self.assertEqual(plan.needed,('normal','clear_range'))
        plan=frame.advance(s);self.assertTrue(plan.complete);self.assertTrue(plan.cleared);self.assertEqual(plan.rows,())

    def test_channel_caption_message_subitem_zero_and_delay_subitem_one(self):
        plan=MessageListFrame().advance(sample())
        self.assertEqual(plan.rows,(MessageListRow(b'Party',b'owned\x00bytes',10000,0),))
        self.assertIn(('0045f7f4',('form_field',0xb98,0,None),'row0.channel_get'),plan.calls)
        self.assertIn(('0045f6e0',('form_field',0xb98,0,0),'row0.message_get'),plan.calls)
        self.assertIn(('0045f6e0',('form_field',0xb98,0,1),'row0.delay_get'),plan.calls)

    def test_numeric_fallback_ten_is_explicit_not_text_inferred(self):
        s=sample();frame=MessageListFrame();plan=frame.advance(replace(s,integer_inputs={}))
        self.assertEqual(plan.needed,('integer','row0.delay_integer'));self.assertEqual(plan.rows,())
        self.assertEqual(plan.conversions[0][1].default_qword,10)

    def test_normal_qword_truncates_low_then_multiplies_with_wrap(self):
        child=SourceIntegerObservation(True,'normal',True,0x12345678ffffffff,cleanup_returned=True)
        plan=MessageListFrame().advance(sample(parser=child))
        self.assertEqual(plan.rows[0].delay_dword,0xfffffc18)
        child=replace(child,parser_qword=0x80000000)
        self.assertEqual(MessageListFrame().advance(sample(parser=child)).rows[0].delay_dword,0)

    def test_count_is_fresh_each_iteration_and_signed(self):
        s=sample(2);values={**s.values,'row1.count_eax':0}
        plan=MessageListFrame().advance(replace(s,values=values))
        self.assertTrue(plan.complete);self.assertEqual(len(plan.rows),1)
        s=sample(0);plan=MessageListFrame().advance(replace(s,values={'row0.count_eax':0xffffffff}))
        self.assertTrue(plan.complete);self.assertEqual(plan.rows,())

    def test_size_capacity_unsigned_choice_and_fast_end_store(self):
        fast=MessageListFrame().advance(sample());grow=MessageListFrame().advance(sample(grow=True))
        self.assertEqual(fast.stores,((0x569924,4,0x100c),));self.assertEqual(grow.stores,())
        self.assertIn('0045c8c8',[c[0] for c in grow.calls])
        s=sample();s=replace(s,values={**s.values,'row0.size_eax':0xffffffff,'row0.capacity_eax':1})
        self.assertIn('0045c8c8',[c[0] for c in MessageListFrame().advance(s).calls])

    def test_fast_end_wrap_and_contradictory_capture_rejected(self):
        s=sample();s=replace(s,values={**s.values,'row0.end_dword':0xfffffffc,'row0.new_end_eax':8})
        plan=MessageListFrame().advance(s);self.assertEqual(plan.stores[0][2],8)
        with self.assertRaises(ValueError):MessageListFrame().advance(replace(s,values={**s.values,'row0.new_end_eax':9}))

    def test_record_is_retained_before_separate_four_cleanup_returns(self):
        s=sample();frame=MessageListFrame()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'row0.record_message_cleanup':False}))
        self.assertEqual(len(plan.rows),1);self.assertEqual(len(plan.stores),1)
        self.assertEqual(plan.needed,('normal','row0.record_message_cleanup'))
        plan=frame.advance(MessageListObservation(normal_returns={'row0.record_message_cleanup':True}))
        self.assertEqual(plan.needed,('normal','row0.record_channel_cleanup'))
        plan=frame.advance(s);self.assertTrue(plan.complete);self.assertEqual(len(plan.rows),1)
        self.assertIs(frame.advance(sample(0)),plan)

    def test_accepted_bytes_and_integer_survive_later_changed_snapshot(self):
        s=sample();frame=MessageListFrame()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'row0.size':False}))
        changed=replace(s,ansi_bytes={**s.ansi_bytes,'row0.channel':b'Other'},texts={**s.texts,'row0.delay':'99'})
        final=frame.advance(changed)
        self.assertEqual(final.rows[0],plan.candidate)

    def test_row_budget_is_local_and_can_be_extended_without_replaying_prefix(self):
        frame=MessageListFrame(row_budget=1);s=sample(2)
        plan=frame.advance(s);self.assertEqual(plan.needed,('budget','row_limit'));self.assertEqual(len(plan.rows),1)
        frame.extend_budget(2);plan=frame.advance(s)
        self.assertTrue(plan.complete);self.assertEqual(len(plan.rows),2)
        self.assertEqual([r.source_index for r in plan.rows],[0,1])

    def test_parser_outer_and_unicode_cleanup_are_independent(self):
        s=sample();frame=MessageListFrame()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'row0.parser_outer':False}))
        self.assertEqual(plan.needed,('normal','row0.parser_outer'));self.assertEqual(plan.rows,())
        plan=frame.advance(MessageListObservation(normal_returns={'row0.parser_outer':True}))
        self.assertEqual(plan.needed,('normal','row0.delay_unicode_cleanup'))

    def test_types_and_verification_flags(self):
        with self.assertRaises(ValueError):MessageListObservation(ansi_bytes={'x':'not bytes'})
        with self.assertRaises(ValueError):MessageListObservation(integer_inputs={'x':{}})
        with self.assertRaises(ValueError):MessageListFrame(row_budget=0)
        plan=MessageListFrame().advance(sample())
        self.assertFalse(plan.codec_verified);self.assertFalse(plan.native_execution_verified)
        self.assertFalse(plan.whole_function_verified)

if __name__=='__main__':unittest.main()
