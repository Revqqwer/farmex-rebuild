import unittest
from source_message_cycle import *

def sample(**changes):
    values=dict(first_test_begin=0x1000,first_end=0x1018,first_subtract_begin=0x1000,
        first_tick_eax=1000,last_tick_low=0,last_tick_high=0,delay_index=0,delay_begin=0x1000,delay_value=1000,
        argument4_index=0,argument4_begin=0x1000,argument4_value=0x3000,
        argument0_index=0,argument0_begin=0x1000,argument0_value=0x2000,
        second_tick_eax=1010,increment_index_before=0,tail_test_begin=0x1000,tail_end=0x1018,
        tail_subtract_begin=0x1000,tail_compare_index=1)
    values.update(changes)
    return SourceMessageCycleObservation(True,values,{k:True for k in ('first_tick','message_helper','second_tick')})

class SourceMessageCycleTests(unittest.TestCase):
    def test_zero_begin_or_truncated_zero_count_skips_tick_and_tail(self):
        for values in ({'first_test_begin':0},{'first_end':0x100b}):
            plan=SourceMessageCycleFrame().advance(sample(**values))
            self.assertEqual(plan.status,'first_count_zero');self.assertEqual(plan.calls,());self.assertEqual(plan.stores,())

    def test_count_subtraction_begin_is_fresh_and_signed_division_truncates_zero(self):
        plan=SourceMessageCycleFrame().advance(sample(first_subtract_begin=0x1024))
        self.assertEqual(plan.first_count_signed,-1);self.assertTrue(plan.complete)
        plan=SourceMessageCycleFrame().advance(sample(first_subtract_begin=0x1019))
        self.assertEqual(plan.first_count_signed,0);self.assertEqual(plan.status,'first_count_zero')

    def test_equal_delay_due_and_helper_push_order_from_separate_row_reads(self):
        plan=SourceMessageCycleFrame().advance(sample(argument4_index=1,argument4_begin=0x4000,
            argument0_index=3,argument0_begin=0x5000))
        self.assertEqual(plan.helper_pushes,(0x3000,0x2000,0x569910))
        self.assertIn((0x4010,4,'argument4_value'),plan.reads)
        self.assertIn((0x5024,4,'argument0_value'),plan.reads)
        self.assertEqual(plan.elapsed_signed_qword,1000)

    def test_wait_still_reads_tail_and_resets_only_equal_index(self):
        equal=SourceMessageCycleFrame().advance(sample(first_tick_eax=999,tail_compare_index=2))
        larger=SourceMessageCycleFrame().advance(sample(first_tick_eax=999,tail_compare_index=3))
        self.assertEqual(equal.status,'waiting_tail_reset')
        self.assertEqual(equal.stores,((0x569934,4,0),))
        self.assertEqual(larger.status,'waiting_index_retained');self.assertEqual(larger.stores,())
        self.assertEqual([c[0] for c in equal.calls],['GetTickCount'])

    def test_delay_address_uses_raw_index_without_preclamp(self):
        plan=SourceMessageCycleFrame().advance(sample(delay_index=0xffffffff,delay_begin=4))
        self.assertIn((0,4,'delay_value'),plan.reads)

    def test_helper_return_blocks_second_tick_and_all_stores(self):
        s=sample();frame=SourceMessageCycleFrame()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'message_helper':False}))
        self.assertEqual(plan.needed,('normal','message_helper'));self.assertEqual(plan.stores,())
        plan=frame.advance(SourceMessageCycleObservation(normal_returns={'message_helper':True}))
        self.assertEqual(plan.needed,('normal','second_tick'));self.assertEqual(plan.stores,())

    def test_timestamp_stores_precede_index_rmw_and_tail_uses_fresh_index(self):
        frame=SourceMessageCycleFrame();s=sample();values=dict(s.values);del values['increment_index_before']
        plan=frame.advance(replace(s,values=values))
        self.assertEqual(plan.needed,('value','increment_index_before'))
        self.assertEqual(plan.stores,((0x569938,4,1010),(0x56993c,4,0)))
        plan=frame.advance(SourceMessageCycleObservation(values={'increment_index_before':0xffffffff}))
        self.assertEqual(plan.needed,('value','tail_test_begin'))
        self.assertEqual(plan.stores[-1],(0x569934,4,0))
        plan=frame.advance(SourceMessageCycleObservation(values={'tail_test_begin':0,'tail_compare_index':5}))
        self.assertEqual(plan.status,'helper_returned_index_retained')

    def test_tick_wrap_and_signed_negative_delay_follow_source_qword_math(self):
        wrap=SourceMessageCycleFrame().advance(sample(first_tick_eax=10,last_tick_low=0xfffffff0,delay_value=0))
        self.assertLess(wrap.elapsed_signed_qword,0);self.assertEqual(wrap.status,'waiting_index_retained')
        negative=SourceMessageCycleFrame().advance(sample(first_tick_eax=0,delay_value=0xffffffff))
        self.assertEqual(negative.status,'helper_returned_index_retained')

    def test_tail_empty_vector_can_reset_zero_after_nonempty_first_count(self):
        plan=SourceMessageCycleFrame().advance(sample(tail_test_begin=0,tail_compare_index=0))
        self.assertEqual(plan.tail_count_signed,0)
        self.assertEqual(plan.stores[-1],(0x569934,4,0))

    def test_reached_operand_prefix_survives_changed_snapshot(self):
        frame=SourceMessageCycleFrame();s=sample()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'message_helper':False}))
        final=frame.advance(sample(first_test_begin=0,delay_value=9999,argument4_value=8,tail_compare_index=2))
        self.assertEqual(final.helper_pushes,plan.helper_pushes)
        self.assertEqual(final.elapsed_signed_qword,plan.elapsed_signed_qword)
        self.assertEqual(final.status,'helper_returned_tail_reset');self.assertIs(frame.advance(sample()),final)

    def test_callback_gate_zero_skips_child_and_nonzero_requires_parent(self):
        plan=MessageCallbackFrame().advance(MessageCallbackObservation(True,0))
        self.assertTrue(plan.complete);self.assertIsNone(plan.child)
        frame=MessageCallbackFrame();plan=frame.advance(MessageCallbackObservation(True,1,cycle_parent_returned=True))
        self.assertEqual(plan.needed,('cycle',('entry','0045cceb')))
        plan=frame.advance(MessageCallbackObservation(cycle=sample(first_test_begin=0)))
        self.assertEqual(plan.needed,'cycle_parent_returned')
        plan=frame.advance(MessageCallbackObservation(cycle_parent_returned=True))
        self.assertTrue(plan.complete);self.assertEqual(plan.next_address,0x46f1cf)

    def test_types_context_and_verification_scope(self):
        with self.assertRaises(ValueError):SourceMessageCycleObservation(values={'first_tick_eax':-1})
        with self.assertRaises(ValueError):MessageCallbackObservation(gate_byte=256)
        with self.assertRaises(ValueError):SourceMessageCycleFrame(context=None)
        plan=SourceMessageCycleFrame(context=0xfffffff0).advance(sample())
        self.assertTrue(plan.complete);self.assertFalse(plan.native_execution_verified)
        self.assertFalse(plan.delivery_verified);self.assertFalse(plan.live_compatibility_verified)

if __name__=='__main__':unittest.main()
