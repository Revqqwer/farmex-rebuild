import unittest
from dataclasses import replace
from item_break_cycle import *

def clock(**changes):
    return replace(ItemBreakClockObservation(True,0,True,1000,0,0,1,True,True,1011),**changes)

def cycle(**changes):
    return replace(ItemBreakCycleObservation(True,1,1,1,True,1,True,1,clock(),True,True,True),**changes)

class ItemBreakCycleTests(unittest.TestCase):
    def test_outer_gates_stop_before_unreached_operands(self):
        frame = ItemBreakCycleFrame()
        self.assertEqual(frame.advance(ItemBreakCycleObservation()).needed,'entry_reached')
        plan = frame.advance(ItemBreakCycleObservation(entry_reached=True,gate_561f60=0))
        self.assertEqual(plan.status,'outer_gate_zero')
        self.assertEqual(plan.calls,())
        plan = ItemBreakCycleFrame().advance(ItemBreakCycleObservation(True,1,0))
        self.assertEqual(plan.status,'settings_disabled')

    def test_independent_work_reads_allow_zero_then_nonzero(self):
        plan = ItemBreakCycleFrame().advance(cycle(first_work_byte=0,second_work_byte=255))
        self.assertTrue(plan.complete)
        self.assertNotIn('00470f6c',[call[0] for call in plan.calls])
        self.assertEqual(plan.calls[0][0],'00470d98')

    def test_guard_return_does_not_imply_second_work_byte(self):
        frame = ItemBreakCycleFrame()
        plan = frame.advance(cycle(second_work_byte=None))
        self.assertEqual(plan.needed,'second_work_byte')
        self.assertEqual([call[0] for call in plan.calls],['00470f6c'])
        plan = frame.advance(ItemBreakCycleObservation(second_work_byte=0))
        self.assertEqual(plan.status,'second_work_gate_zero')

    def test_guard_receipt_blocks_npc_and_is_retained_across_gap(self):
        frame = ItemBreakCycleFrame()
        plan = frame.advance(cycle(inventory_guard_returned=False))
        self.assertEqual(plan.needed,'inventory_guard_returned')
        self.assertEqual(len(plan.calls),1)
        plan = frame.advance(cycle(first_work_byte=0))
        self.assertTrue(plan.complete)
        self.assertEqual([call[0] for call in plan.calls],['00470f6c','00470d98','004710d4'])

    def test_npc_low_al_zero_takes_stop_then_separate_notice(self):
        frame = ItemBreakCycleFrame()
        plan = frame.advance(cycle(npc_eax=0x12340000,stop_returned=False))
        self.assertEqual(plan.needed,'stop_returned')
        self.assertIsNone(plan.clock)
        plan = frame.advance(ItemBreakCycleObservation(stop_returned=True))
        self.assertEqual(plan.needed,'npc_notice_span_returned')
        plan = frame.advance(ItemBreakCycleObservation(npc_notice_span_returned=True))
        self.assertEqual(plan.status,'npc_zero_stop_notice_returned')
        self.assertEqual(plan.calls[-2],('0040ae0c',(0x561f34,0),'stop_returned'))

    def test_clock_child_cannot_be_bypassed_by_parent_return(self):
        frame = ItemBreakCycleFrame()
        plan = frame.advance(cycle(clock_inputs=None))
        self.assertEqual(plan.needed,'clock_inputs')
        self.assertEqual(plan.clock.needed,'entry_reached')
        plan = frame.advance(ItemBreakCycleObservation(clock_inputs=clock(action_returned=False)))
        self.assertEqual(plan.clock.needed,'action_returned')
        self.assertEqual(plan.clock.stores,())
        plan = frame.advance(ItemBreakCycleObservation(
            clock_inputs=ItemBreakClockObservation(action_returned=True,second_tick_returned=True,second_tick_dword=1099)))
        self.assertEqual(plan.needed,'clock_returned')
        plan = frame.advance(ItemBreakCycleObservation(clock_returned=True))
        self.assertTrue(plan.complete)
        self.assertEqual(plan.clock.stores,((0x553d50,4,1099),(0x553d54,4,0)))

    def test_clock_nonzero_mode_avoids_tick_speed_and_action(self):
        plan = ItemBreakClockFrame().advance(ItemBreakClockObservation(True,0xffffffff))
        self.assertEqual(plan.status,'nonzero_mode_skips_clock')
        self.assertEqual(plan.calls,())
        self.assertIsNone(plan.elapsed_signed_qword)

    def test_clock_equal_threshold_due_and_below_waits(self):
        waiting = ItemBreakClockFrame().advance(clock(first_tick_dword=999))
        due = ItemBreakClockFrame().advance(clock(first_tick_dword=1000))
        self.assertEqual(waiting.status,'waiting')
        self.assertEqual([call[0] for call in waiting.calls],['GetTickCount'])
        self.assertEqual(due.status,'action_returned_clock_updated')
        self.assertEqual((due.elapsed_signed_qword,due.threshold_signed_dword),(1000,1000))

    def test_clock_wrap_is_signed_qword_subtraction_not_dword_elapsed(self):
        plan = ItemBreakClockFrame().advance(clock(first_tick_dword=10,last_tick_low=0xfffffff0,speed_dword=0))
        self.assertEqual(plan.elapsed_signed_qword,10-0xfffffff0)
        self.assertEqual(plan.status,'waiting')
        plan = ItemBreakClockFrame().advance(clock(first_tick_dword=10,last_tick_low=0,last_tick_high=0xffffffff))
        self.assertEqual(plan.elapsed_signed_qword,(1 << 32)+10)
        self.assertEqual(plan.status,'action_returned_clock_updated')

    def test_speed_product_wraps_before_signed_extension(self):
        negative = ItemBreakClockFrame().advance(clock(first_tick_dword=0,speed_dword=0xffffffff))
        zero = ItemBreakClockFrame().advance(clock(first_tick_dword=0,speed_dword=0x80000000))
        self.assertEqual(negative.threshold_signed_dword,-1000)
        self.assertEqual(zero.threshold_signed_dword,0)
        self.assertEqual(negative.status,zero.status)
        self.assertEqual(negative.status,'action_returned_clock_updated')

    def test_action_and_second_tick_normals_precede_any_timestamp_store(self):
        frame = ItemBreakClockFrame()
        plan = frame.advance(clock(action_returned=False))
        self.assertEqual(plan.needed,'action_returned')
        self.assertEqual(plan.stores,())
        plan = frame.advance(ItemBreakClockObservation(action_returned=True,second_tick_dword=777))
        self.assertEqual(plan.needed,'second_tick_returned')
        self.assertEqual(plan.stores,())
        plan = frame.advance(ItemBreakClockObservation(second_tick_returned=True))
        self.assertEqual(plan.needed,'second_tick_dword')
        plan = frame.advance(ItemBreakClockObservation(second_tick_dword=888))
        self.assertEqual(plan.stores,((0x553d50,4,888),(0x553d54,4,0)))
        self.assertIs(frame.advance(clock()),plan)

    def test_clock_reached_operands_survive_action_gap(self):
        frame = ItemBreakClockFrame()
        partial = frame.advance(clock(action_returned=False))
        plan = frame.advance(clock(first_tick_dword=0,speed_dword=999,second_tick_dword=1234))
        self.assertEqual(plan.elapsed_signed_qword,partial.elapsed_signed_qword)
        self.assertEqual(plan.threshold_signed_dword,1000)
        self.assertEqual(plan.stores[0],(0x553d50,4,1234))

    def test_cycle_context_only_binds_helper_argument_and_is_idempotent(self):
        frame = ItemBreakCycleFrame(context=0xffffffff)
        plan = frame.advance(cycle(npc_eax=0xff))
        self.assertEqual(plan.calls[0][1],(0xffffffff,))
        self.assertTrue(plan.clock.complete)
        self.assertIs(frame.advance(ItemBreakCycleObservation()),plan)
        self.assertFalse(plan.whole_function_verified)
        self.assertFalse(plan.native_execution_verified)
        self.assertFalse(plan.live_compatibility_verified)

    def test_input_types_and_widths_are_enforced(self):
        for ctor, kwargs in ((ItemBreakClockObservation,{'speed_dword':-1}),
                             (ItemBreakClockObservation,{'first_tick_returned':1}),
                             (ItemBreakCycleObservation,{'first_work_byte':256}),
                             (ItemBreakCycleObservation,{'npc_eax':True}),
                             (ItemBreakCycleObservation,{'clock_inputs':{}})):
            with self.assertRaises(ValueError):
                ctor(**kwargs)
        with self.assertRaises(ValueError):
            ItemBreakCycleFrame(context=None)

if __name__ == '__main__':
    unittest.main()
