import unittest
from dataclasses import replace
import test_dc_propagation as source_fixture
import test_dc_sender_template as transfer_fixture
from dc_full_chain import *

class DCFullChainTests(unittest.TestCase):
    def parent(self,**values):return source_fixture.DCPropagationTests().periodic(**values)
    def source(self,**values):return source_fixture.DCPropagationTests().consumer(**values)
    def transfer(self,**values):return transfer_fixture.DCTransferTests().observation(values)
    def observation(self):
        return DCFullChainObservation(self.parent(),DCSenderObservation(self.source(),{'row0.send':self.transfer()}))

    def test_positive_four_layer_chain_retains_payload_bytes_and_stamp(self):
        f=DCFullChainFrame();p=f.advance(self.observation())
        self.assertTrue(p.complete)
        self.assertEqual(p.parent.stores,((0x553ce4,4,300010),))
        self.assertEqual(p.payload_intents,((6,b'\x01'),));self.assertEqual(len(p.write_intents),2)
        self.assertEqual(p.write_intents[0],('row0.send','payload',0x2000,b'\x01'))
        self.assertEqual(len(p.stubs['row0.send']),26)
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified or p.whole_function_verified)
        self.assertIs(f.advance(DCFullChainObservation()),p)

    def test_short_interval_or_alternative_context_does_not_create_action(self):
        for parent in (self.parent(tick_eax=299999),self.parent(context_6e_byte=1),self.parent(enabled_byte=0)):
            f=DCFullChainFrame();p=f.advance(DCFullChainObservation(parent))
            self.assertTrue(p.complete);self.assertIsNone(f.action)
            self.assertEqual(p.payload_intents,());self.assertEqual(p.write_intents,())

    def test_early_receipts_cannot_skip_missing_inner_sender(self):
        f=DCFullChainFrame();p=f.advance(DCFullChainObservation(self.parent(),DCSenderObservation(self.source())))
        self.assertEqual(p.needed,('action',('sender','row0.send',('normal','prologue'))))
        self.assertNotIn('post_tick_eax',f.parent.values);self.assertEqual(p.parent.stores,())

    def test_wait_gap_retains_write_prefix_and_blocks_stamp(self):
        f=DCFullChainFrame();o=self.observation();t=transfer_fixture.DCTransferTests().observation(blocked=('stub.wait',))
        p=f.advance(replace(o,action=replace(o.action,transfers={'row0.send':t})))
        self.assertEqual(p.needed,('action',('sender','row0.send',('normal','stub.wait'))))
        self.assertEqual(len(p.write_intents),2);self.assertEqual(p.parent.stores,())
        self.assertNotIn('post_tick_eax',f.parent.values)
        p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(len(p.write_intents),2)

    def test_each_outer_return_and_post_tick_are_separate_and_preserve_trace(self):
        f=DCFullChainFrame();o=self.observation()
        source_normals=dict(o.action.consumer.normal_returns);source_normals['row0.send']=False
        action=replace(o.action,consumer=replace(o.action.consumer,normal_returns=source_normals))
        p=f.advance(replace(o,action=action))
        self.assertEqual(p.needed,('action',('consumer',('normal','row0.send'))))
        n=dict(o.parent.normal_returns);n['consumer']=False
        p=f.advance(replace(o,parent=replace(o.parent,normal_returns=n)))
        self.assertTrue(p.action.complete);self.assertEqual(p.needed,('parent',('normal','consumer')))
        n['consumer']=True;n['post_tick']=False
        p=f.advance(replace(o,parent=replace(o.parent,normal_returns=n)))
        self.assertEqual(p.needed,('parent',('normal','post_tick')))
        self.assertEqual(len(p.write_intents),2);self.assertEqual(p.parent.stores,())
        p=f.advance(DCFullChainObservation(JailObservation(values={'post_tick_eax':900000},normal_returns={'post_tick':True})))
        self.assertTrue(p.complete);self.assertEqual(p.parent.stores,((0x553ce4,4,900000),))

    def test_sender_allocation_failure_is_not_a_parent_success_gate(self):
        o=self.observation();t=self.transfer(payload_allocation_eax=0)
        p=DCFullChainFrame().advance(replace(o,action=replace(o.action,transfers={'row0.send':t})))
        self.assertTrue(p.complete);self.assertEqual(p.write_intents,())
        self.assertEqual(p.payload_intents,((6,b'\x01'),))
        self.assertEqual(p.parent.stores,((0x553ce4,4,300010),))

    def test_scan_selection_with_empty_snapshot_uses_no_transfer_children(self):
        o=DCFullChainObservation(self.parent(list_only_byte=0),DCSenderObservation(self.source(snapshot_handle=0xffffffff)))
        f=DCFullChainFrame();p=f.advance(o)
        self.assertTrue(p.complete);self.assertEqual(f.action.consumer.kind,'scan')
        self.assertEqual(f.action.children,{});self.assertEqual(p.write_intents,())
        self.assertEqual(p.parent.stores,((0x553ce4,4,300010),))
        with self.assertRaises(ValueError):DCFullChainObservation(action={})

if __name__=='__main__':unittest.main()
