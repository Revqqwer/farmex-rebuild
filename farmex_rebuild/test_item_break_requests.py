import unittest
from item_break_requests import *
from item_break_npc import ItemBreakNpcObservation

def target(gate=1,tick=100,returned=True):
    return EventPacketObservation(normal_returns={k:True for k in ('frame_setup','template_copy','target_copy','return')},
                                  attempt=QueueAttempt(gate,tick,returned))
def request(first=5,second=7,gates=(1,1,1)):
    return ItemBreakRequestObservation(True,{'first_selected_eax':first,'second_selected_eax':second},
        {'first_selected':True,'second_selected':True,'target_parent':True},target(gates[0]),
        {0:QueueAttempt(gates[1],101,True),1:QueueAttempt(gates[2],102,True)})

def caller_clock(**changes):
    return replace(ItemBreakClockObservation(True,0,True,1000,0,0,1,None,True,1010),**changes)

def candidate():
    return ItemBreakNpcObservation(True,dict(mode_dword=1,npc_id_eax=5,npc_object_eax=0x2000,
        first_offset=0x20,second_offset=0x24,first_coordinate_float_bits=0,second_coordinate_float_bits=0,
        distance_float_bits=0,zero_compare_ax=0x4000,ten_compare_ax=0x0100,selected_npc_eax=5),
        {key:True for key in ('empty_name_setup','lookup_argument_setup','npc_lookup','npc_object',
         'first_coordinate','second_coordinate','distance','selected_npc','success_cleanup')})

def caller():return ItemBreakCycleObservation(True,1,1,0,second_work_byte=1,clock_inputs=caller_clock(),clock_returned=True)

class ItemBreakRequestTests(unittest.TestCase):
    def test_three_records_include_existing_target_prepare_then_two_fixed_templates(self):
        plan=ItemBreakRequestFrame().advance(request())
        self.assertTrue(plan.complete);self.assertEqual(len(plan.queue.records),3)
        self.assertEqual([r.payload for r in plan.queue.records],[bytes.fromhex('200107000000ffffffff'),FIRST_TEMPLATE,SECOND_TEMPLATE])
        self.assertEqual([r.delay_dword for r in plan.queue.records],[0,200,250])
        self.assertEqual([r.created_tick for r in plan.queue.records],[100,101,102])
        self.assertEqual(len(FIRST_TEMPLATE),6);self.assertEqual(len(SECOND_TEMPLATE),19)
        self.assertEqual(SECOND_TEMPLATE[-1],255)

    def test_first_zero_skips_second_getter_and_all_queue_children(self):
        plan=ItemBreakRequestFrame().advance(ItemBreakRequestObservation(True,{'first_selected_eax':0},{'first_selected':True}))
        self.assertTrue(plan.complete);self.assertEqual(plan.status,'first_selected_zero')
        self.assertEqual(plan.queue.records,());self.assertIsNone(plan.target);self.assertEqual(len(plan.calls),1)

    def test_selected_reads_are_independent_even_when_second_is_zero(self):
        plan=ItemBreakRequestFrame().advance(request(first=5,second=0))
        self.assertEqual(plan.queue.records[0].payload,bytes.fromhex('200100000000ffffffff'))
        self.assertEqual(len(plan.queue.records),3)

    def test_second_getter_normal_and_eax_are_separate(self):
        frame=ItemBreakRequestFrame();sample=request()
        plan=frame.advance(replace(sample,normal_returns={'first_selected':True}))
        self.assertEqual(plan.needed,('normal','second_selected'));self.assertEqual(plan.payloads,(FIRST_TEMPLATE,SECOND_TEMPLATE))
        plan=frame.advance(ItemBreakRequestObservation(normal_returns={'second_selected':True}))
        self.assertEqual(plan.needed,('value','second_selected_eax'));self.assertEqual(plan.queue.records,())

    def test_target_child_and_parent_normal_both_required_before_fixed_records(self):
        frame=ItemBreakRequestFrame();sample=request()
        plan=frame.advance(replace(sample,target_child=None))
        self.assertEqual(plan.needed,('target_child',('normal','frame_setup')))
        plan=frame.advance(ItemBreakRequestObservation(target_child=target()))
        self.assertEqual(plan.needed,('normal','target_parent'));self.assertEqual(len(plan.queue.records),1)
        plan=frame.advance(ItemBreakRequestObservation(normal_returns={'target_parent':True}))
        self.assertEqual(plan.needed[0:2],('enqueue',0));self.assertEqual(len(plan.queue.records),1)

    def test_gates_are_independent_and_disconnected_calls_need_no_tick(self):
        for gates,wanted in (((0,0,0),0),((0,1,0),1),((1,0,1),2)):
            plan=ItemBreakRequestFrame().advance(request(gates=gates))
            self.assertTrue(plan.complete);self.assertEqual(len(plan.queue.records),wanted)
        sample=request(gates=(0,0,0))
        sample=replace(sample,target_child=target(0,None),attempts={0:QueueAttempt(0,None,True),1:QueueAttempt(0,None,True)})
        self.assertTrue(ItemBreakRequestFrame().advance(sample).complete)

    def test_first_fixed_enqueue_commit_not_duplicated_when_normal_missing(self):
        frame=ItemBreakRequestFrame();sample=request()
        sample=replace(sample,attempts={0:QueueAttempt(1,101,False)})
        plan=frame.advance(sample);self.assertEqual(len(plan.queue.records),2)
        self.assertEqual(plan.needed[0:2],('enqueue',0))
        plan=frame.advance(ItemBreakRequestObservation(attempts={0:QueueAttempt(0,999,True)}))
        self.assertEqual(len(plan.queue.records),2);self.assertEqual(plan.queue.records[-1].created_tick,101)
        self.assertEqual(plan.needed[0:2],('enqueue',1))
        plan=frame.advance(ItemBreakRequestObservation(attempts={1:QueueAttempt(1,103,True)}))
        self.assertEqual(len(plan.queue.records),3);self.assertEqual([r.record_id for r in plan.queue.records],[1,2,3])
        self.assertIs(frame.advance(request(first=0)),plan)

    def test_second_enqueue_gap_preserves_existing_target_and_first_record(self):
        frame=ItemBreakRequestFrame();sample=request()
        plan=frame.advance(replace(sample,attempts={0:sample.attempts[0],1:QueueAttempt(1,None,True)}))
        self.assertEqual(len(plan.queue.records),2)
        plan=frame.advance(ItemBreakRequestObservation(attempts={1:QueueAttempt(0,202,True)}))
        self.assertEqual(len(plan.queue.records),3) #Reached gate1 retained despite changed sample0.
        self.assertEqual(plan.queue.records[-1].created_tick,202)

    def test_initial_queue_is_preserved_and_ids_advance(self):
        from action_queue import enqueue
        initial=enqueue(QueueState(),b'old',3,0,1,1).state
        plan=ItemBreakRequestFrame(initial).advance(request())
        self.assertEqual([r.record_id for r in plan.queue.records],[1,2,3,4])
        self.assertEqual(plan.queue.records[0].payload,b'old')

    def test_full_cycle_binds_action_child_before_post_tick_stores(self):
        frame=ItemBreakRequestCycleFrame()
        plan=frame.advance(caller(),npc=candidate(),npc_parent_returned=True,action_parent_returned=True)
        self.assertEqual(plan.needed,('request',('entry','004ca9c2')))
        self.assertEqual(plan.caller.caller.caller.clock.stores,())
        plan=frame.advance(ItemBreakCycleObservation(),request())
        self.assertEqual(plan.needed,'action_parent_returned')
        plan=frame.advance(ItemBreakCycleObservation(),action_parent_returned=True)
        self.assertEqual(plan.needed,'clock_inputs')
        plan=frame.advance(ItemBreakCycleObservation(clock_inputs=ItemBreakClockObservation(second_tick_returned=True,second_tick_dword=1234),clock_returned=True))
        self.assertTrue(plan.complete);self.assertEqual(len(plan.queue.records),3)
        self.assertEqual(plan.caller.caller.caller.clock.stores,((0x553d50,4,1234),(0x553d54,4,0)))

    def test_action_early_zero_still_allows_clock_update_after_parent_return(self):
        frame=ItemBreakRequestCycleFrame()
        plan=frame.advance(caller(),request(first=0),candidate(),npc_parent_returned=True,action_parent_returned=True)
        self.assertTrue(plan.complete);self.assertEqual(plan.queue.records,())
        self.assertEqual(plan.request.status,'first_selected_zero')
        self.assertEqual(plan.caller.caller.caller.clock.stores[0],(0x553d50,4,1010))

    def test_waiting_clock_and_disabled_caller_do_not_force_requests(self):
        plan=ItemBreakRequestCycleFrame().advance(ItemBreakCycleObservation(True,0))
        self.assertTrue(plan.complete);self.assertIsNone(plan.request)
        sample=replace(caller(),clock_inputs=caller_clock(first_tick_dword=999))
        plan=ItemBreakRequestCycleFrame().advance(sample,npc=candidate(),npc_parent_returned=True)
        self.assertTrue(plan.complete);self.assertIsNone(plan.request)

    def test_overrides_types_and_delivery_claims(self):
        with self.assertRaises(ValueError):
            ItemBreakRequestCycleFrame().advance(replace(caller(),clock_inputs=caller_clock(action_returned=True)))
        with self.assertRaises(ValueError):ItemBreakRequestObservation(attempts={2:QueueAttempt()})
        with self.assertRaises(ValueError):ItemBreakRequestObservation(target_child={})
        plan=ItemBreakRequestFrame().advance(request())
        self.assertFalse(plan.native_execution_verified);self.assertFalse(plan.delivery_verified)
        self.assertFalse(plan.live_compatibility_verified)

if __name__=='__main__':unittest.main()
