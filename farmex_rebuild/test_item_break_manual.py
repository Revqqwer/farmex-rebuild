import unittest
from item_break_manual import *
from direct_chat_packets import QueueAttempt
from event_packets import EventPacketObservation

def candidate(zero=False):
    return ItemBreakNpcObservation(True,dict(mode_dword=0,npc_id_eax=0 if zero else 5,npc_object_eax=0x2000,
        first_offset=0x20,second_offset=0x24,first_coordinate_float_bits=0,second_coordinate_float_bits=0,
        distance_float_bits=0,zero_compare_ax=0x4000,ten_compare_ax=0x100,selected_npc_eax=5),
        {key:True for key in ('empty_name_setup','moira_assignment','lookup_argument_setup','npc_lookup',
         'npc_object','first_coordinate','second_coordinate','distance','selected_npc','success_cleanup','failure_cleanup')})

def requests():
    target=EventPacketObservation(normal_returns={k:True for k in ('frame_setup','template_copy','target_copy','return')},
        attempt=QueueAttempt(1,10,True))
    return ItemBreakRequestObservation(True,{'first_selected_eax':5,'second_selected_eax':7},
        {'first_selected':True,'second_selected':True,'target_parent':True},target,
        {0:QueueAttempt(1,11,True),1:QueueAttempt(1,12,True)})

def sample():
    return ItemBreakManualObservation(True,{'fresh_mode_dword':0,'gem_lookup_eax':1},
        {k:True for k in ('npc_parent','gem_text_created','gem_lookup','gem_text_cleanup',
                         'gem_notice','npc_notice','request_parent')},candidate(),requests())

class ItemBreakManualTests(unittest.TestCase):
    def test_manual_success_has_no_work_enable_inventory_or_cooldown_gate(self):
        plan=ItemBreakManualFrame().advance(sample())
        self.assertTrue(plan.complete);self.assertEqual(plan.status,'request_child_returned')
        self.assertEqual(len(plan.queue.records),3)
        self.assertFalse(any(c[0] in ('00463ac0','00470f6c','004710d4','0040ae0c','GetTickCount') for c in plan.calls))
        self.assertEqual(plan.next_address,0x471276)

    def test_npc_child_and_parent_normal_are_required_before_mode(self):
        frame=ItemBreakManualFrame();plan=frame.advance(replace(sample(),npc_inputs=None))
        self.assertEqual(plan.needed,('npc','npc_selection'))
        plan=frame.advance(ItemBreakManualObservation(npc_inputs=candidate()))
        self.assertEqual(plan.needed,('normal','npc_parent'))
        plan=frame.advance(ItemBreakManualObservation(normal_returns={'npc_parent':True}))
        self.assertEqual(plan.needed,('value','fresh_mode_dword'))

    def test_npc_zero_only_notifies_without_stop_or_gem(self):
        plan=ItemBreakManualFrame().advance(replace(sample(),npc_inputs=candidate(True)))
        self.assertEqual(plan.status,'npc_zero_notice_returned');self.assertEqual(plan.queue.records,())
        self.assertEqual([c[0] for c in plan.calls],['00470d98','00471216..00471276'])

    def test_fresh_mode_may_differ_from_npc_helper_mode(self):
        values={**sample().values,'fresh_mode_dword':1}
        plan=ItemBreakManualFrame().advance(replace(sample(),values=values))
        self.assertEqual(plan.npc.lookup_name,b'Moira')
        self.assertEqual(plan.status,'nonzero_mode_skips_manual_action');self.assertIsNone(plan.request)

    def test_gem_low_al_zero_notifies_without_stop_or_request(self):
        plan=ItemBreakManualFrame().advance(replace(sample(),values={'fresh_mode_dword':0,'gem_lookup_eax':0xabcd0000}))
        self.assertEqual(plan.status,'gem_zero_notice_returned');self.assertIsNone(plan.request)
        self.assertNotIn('0040ae0c',[c[0] for c in plan.calls])

    def test_noncanonical_nonzero_gem_al_allows_request(self):
        plan=ItemBreakManualFrame().advance(replace(sample(),values={'fresh_mode_dword':0,'gem_lookup_eax':255}))
        self.assertEqual(plan.status,'request_child_returned')

    def test_gem_decision_survives_cleanup_gap_and_blocks_request(self):
        frame=ItemBreakManualFrame();s=sample()
        plan=frame.advance(replace(s,values={'fresh_mode_dword':0,'gem_lookup_eax':0},
            normal_returns={**s.normal_returns,'gem_text_cleanup':False}))
        self.assertEqual(plan.needed,('normal','gem_text_cleanup'));self.assertIsNone(plan.request)
        plan=frame.advance(replace(s,values={'fresh_mode_dword':1,'gem_lookup_eax':1}))
        self.assertEqual(plan.status,'gem_zero_notice_returned');self.assertEqual(plan.queue.records,())

    def test_request_child_normal_and_parent_are_separate_without_duplicates(self):
        frame=ItemBreakManualFrame();plan=frame.advance(replace(sample(),request_inputs=None))
        self.assertEqual(plan.needed,('request','item_break_requests'))
        plan=frame.advance(ItemBreakManualObservation(request_inputs=requests()))
        self.assertEqual(plan.needed,('normal','request_parent'));self.assertEqual(len(plan.queue.records),3)
        plan=frame.advance(ItemBreakManualObservation(normal_returns={'request_parent':True}))
        self.assertTrue(plan.complete);self.assertEqual(len(plan.queue.records),3)
        self.assertIs(frame.advance(sample()),plan)

    def test_notice_return_gaps_are_explicit(self):
        s=sample();frame=ItemBreakManualFrame()
        plan=frame.advance(replace(s,npc_inputs=candidate(True),normal_returns={'npc_parent':True}))
        self.assertEqual(plan.needed,('normal','npc_notice'))
        plan=frame.advance(ItemBreakManualObservation(normal_returns={'npc_notice':True}))
        self.assertTrue(plan.complete)

    def test_manual_click_requires_entry_child_and_handler_return(self):
        frame=ItemBreakManualClickFrame();plan=frame.advance(sample())
        self.assertEqual(plan.needed,'callback_entry')
        plan=frame.advance(sample(),clicked=True)
        self.assertEqual(plan.needed,'handler_returned')
        plan=frame.advance(handler_returned=True)
        self.assertTrue(plan.complete);self.assertEqual(len(plan.manual.queue.records),3)
        self.assertIs(frame.advance(),plan)

    def test_existing_queue_and_context_forwarding(self):
        from action_queue import enqueue
        queue=enqueue(QueueState(),b'old',3,0,1,1).state
        plan=ItemBreakManualFrame(queue,context=0xfffffff0).advance(sample())
        self.assertEqual(plan.calls[0][1],(0xfffffff0,));self.assertEqual(len(plan.queue.records),4)
        self.assertEqual(plan.queue.records[0].payload,b'old')

    def test_types_and_verification_limits(self):
        with self.assertRaises(ValueError):ItemBreakManualObservation(npc_inputs={})
        with self.assertRaises(ValueError):ItemBreakManualObservation(values={'fresh_mode_dword':-1})
        with self.assertRaises(ValueError):ItemBreakManualClickFrame().advance(clicked=1)
        plan=ItemBreakManualFrame().advance(sample())
        self.assertFalse(plan.native_execution_verified);self.assertFalse(plan.delivery_verified)
        self.assertFalse(plan.live_compatibility_verified)

if __name__=='__main__':unittest.main()
