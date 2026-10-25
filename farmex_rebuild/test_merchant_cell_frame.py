import unittest
from dataclasses import replace
from merchant_cell_actions import MerchantCellFrame as Frame,MerchantCellState as State,MerchantCellObservation as O
from action_queue import QueueState
from private_chat_request import PrivateChatObservation
from test_private_chat_request import sample as pm
from test_merchant_cell_actions import clicked,PM,MOVE,COMMON
from test_motion_genie_helpers import motion


class MerchantCellFrameTests(unittest.TestCase):
    def test_negative_selection_skips_all_children(self):
        f=Frame(State(4,5))
        p=f.advance(O(selected_index_dword=0xffffffff,normal_returns={'selected_index':True}))
        self.assertTrue(p.complete)
        self.assertEqual(p.state,State(4,5))
        self.assertIsNone(p.private_chat_plan);self.assertIsNone(p.movement_plan)
        self.assertEqual(p.queue.records,())

    def test_bound_PM_requires_handle_and_child_not_just_parent_receipt(self):
        f=Frame()
        p=f.advance(clicked(735))
        self.assertEqual(p.needed,('value','caption_ansi_dword'))
        p=f.advance(replace(clicked(735),caption_ansi_dword=0x5000))
        self.assertEqual(p.needed,('private_chat',('entry','004ca233')))
        self.assertEqual(p.queue.records,())
        self.assertEqual(f.private_child.argument,0x5000)

    def test_PM_child_cleanup_and_parent_return_and_parent_cleanup_are_separate(self):
        f=Frame(State(7,8));child=pm()
        partial=replace(child,normal_returns={**child.normal_returns,'argument_cleanup':False})
        o=replace(clicked(735),caption_ansi_dword=0x5000,private_chat_inputs=partial)
        p=f.advance(o)
        self.assertEqual(p.needed,('private_chat',('normal','argument_cleanup')))
        self.assertEqual(len(p.queue.records),1)
        # Changed front-end fields cannot change the already consumed prefix.
        o=replace(o,selected_index_dword=9,cursor_x_dword=900,caption_ansi=b'changed',caption_ansi_dword=0x8888,
                  private_chat_inputs=child,normal_returns={**PM,'private_chat':False})
        p=f.advance(o)
        self.assertEqual(p.needed,('normal','private_chat'))
        self.assertEqual((p.selected_index,p.private_chat_target),(2,b'Seller'))
        self.assertTrue(p.private_chat_plan.complete)
        self.assertEqual(len(p.queue.records),1)
        p=f.advance(replace(o,normal_returns={**PM,'pm_ansi_cleanup':False}))
        self.assertEqual(p.needed,('normal','pm_ansi_cleanup'))
        p=f.advance(replace(o,normal_returns=PM))
        self.assertTrue(p.complete)
        self.assertEqual((p.state,len(p.queue.records)),(State(7,8),1))
        self.assertEqual(p.private_chat_plan.payload,b'\x35\x01\x06\x00Seller')
        self.assertIs(f.advance(O()),p)

    def test_explicit_opaque_mode_does_not_claim_child_execution(self):
        p=Frame(bind_private_chat=False).advance(clicked(735))
        self.assertTrue(p.complete)
        self.assertIsNone(p.private_chat_plan)
        self.assertEqual(p.queue.records,())

    def test_move_preserves_preparse_state_and_UI_prefix_across_resume(self):
        f=Frame(State(7,8))
        o=clicked(780,normal_returns={**MOVE,'enable_b68':False})
        p=f.advance(o)
        self.assertEqual((p.state,p.needed),(State(0,0),('normal','enable_b68')))
        self.assertEqual(len(p.ui_enables),2)
        o=replace(o,selected_index_dword=99,cursor_x_dword=0,normal_returns={**MOVE,'x_cleanup':False})
        p=f.advance(o)
        self.assertEqual(p.needed,('normal','x_cleanup'))
        self.assertEqual(p.action,'move_to_seller')
        self.assertEqual(p.selected_index,2)
        self.assertEqual(len(p.ui_enables),3)
        # Original X bits were consumed before its cleanup gap.
        o=replace(o,x_float32_bits=0xdeadbeef,normal_returns=MOVE,movement_inputs=motion())
        p=f.advance(o)
        self.assertTrue(p.complete)
        self.assertEqual(p.movement_push_order,(0x44020000,0x444e4000))
        self.assertEqual([w.value for w in p.movement_plan.writes],[1,0x444e4000,0x44020000])

    def test_motion_child_cannot_be_bypassed_by_parent_normal(self):
        f=Frame();m=motion()
        p=f.advance(replace(clicked(780),movement_inputs=replace(m,normal_returns={**m.normal_returns,'write_x':False})))
        self.assertEqual(p.needed[0],'movement')
        self.assertEqual(p.movement_plan.missing,'write_x normal return')
        self.assertEqual(p.state,State(0,0))
        p=f.advance(replace(clicked(780),movement_inputs=m,normal_returns={**MOVE,'movement':False}))
        self.assertTrue(p.movement_plan.complete)
        self.assertEqual(p.needed,('normal','movement'))
        p=f.advance(replace(clicked(780),movement_inputs=m))
        self.assertTrue(p.complete)
        self.assertFalse(p.native_execution_verified or p.delivery_verified or p.live_compatibility_verified)

    def test_PM_gate0_child_leaves_queue_unchanged_without_skipping_parent(self):
        from direct_chat_packets import QueueAttempt
        child=replace(pm(),attempt=QueueAttempt(0,None,True))
        p=Frame().advance(replace(clicked(735),caption_ansi_dword=1,private_chat_inputs=child))
        self.assertTrue(p.complete)
        self.assertEqual(p.queue.records,())

    def test_unused_child_inputs_are_not_consumed_on_outside_window(self):
        f=Frame()
        p=f.advance(clicked(734))
        self.assertTrue(p.complete)
        self.assertIsNone(f.private_child);self.assertIsNone(f.motion_child)

    def test_contracts(self):
        with self.assertRaises(ValueError):Frame(queue='not own queue')
        with self.assertRaises(ValueError):Frame(bind_movement=1)
        with self.assertRaises(ValueError):O(private_chat_inputs='not typed')
        with self.assertRaises(ValueError):O(movement_inputs='not typed')
        with self.assertRaises(ValueError):O(caption_ansi_dword=-1)


if __name__=='__main__':unittest.main()
