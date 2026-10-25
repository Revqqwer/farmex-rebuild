import unittest
from dataclasses import replace
from target_id_frames import TargetIdObservation,TargetIdFrame,plan_target_id_capture
from source_coin import GuardedDwordSample
from route_npc_click import NpcClickFrame,NpcClickInput,NpcValueCapture
from test_route_coordinate_click import Sink


def sample(value=12,slot=0x100,root=0x1000,offset=4):
    return TargetIdObservation(slot,GuardedDwordSample(slot,1,root),True,offset,
        GuardedDwordSample((root+offset)&0xffffffff,1,value),True,True)


class TargetIdFrameTests(unittest.TestCase):
    def test_missing_fields_never_fabricate_target_or_normal_return(self):
        f=TargetIdFrame();p=f.advance();self.assertEqual(p.needed,('root_address_dword',));self.assertIsNone(p.capture)
        p=f.advance(replace(sample(0),getter_returned=False))
        self.assertFalse(p.complete);self.assertEqual(p.needed,('getter_returned',))
        p=f.advance(TargetIdObservation(getter_returned=True));self.assertTrue(p.complete);self.assertEqual(p.value,0)

    def test_root_zero_still_reads_nonzero_offset_and_target(self):
        o=sample(9,slot=0,root=0,offset=8)
        p=TargetIdFrame().advance(o)
        self.assertTrue(p.complete);self.assertEqual(p.value,9);self.assertEqual(p.address,8)
        self.assertEqual(p.steps,(('global',0x553e7c),('0045dc44',0),('global',0x554044),('0045dc44',8)))

    def test_nested_protection_and_value_are_frozen_only_when_reached(self):
        f=TargetIdFrame();o=sample()
        p=f.advance(replace(o,root_sample=GuardedDwordSample(0x100,1)))
        self.assertEqual(p.needed,('root_sample','value_dword'));self.assertIsNone(f.observation.offset_dword)
        p=f.advance(replace(o,root_sample=GuardedDwordSample(0x100,0,0x1000)))
        self.assertTrue(p.complete);self.assertEqual(f.observation.root_sample.protection_return_dword,1)
        self.assertEqual(p.value,12)

    def test_wrong_reached_address_does_not_poison_frame(self):
        f=TargetIdFrame()
        with self.assertRaises(ValueError):f.advance(replace(sample(),root_sample=GuardedDwordSample(7,1,8)))
        self.assertIsNone(f.observation.root_sample)
        self.assertTrue(f.advance(sample()).complete)

    def test_completed_root_is_retained_while_fresh_offset_waits(self):
        f=TargetIdFrame();p=f.advance(replace(sample(),offset_dword=None))
        self.assertEqual(p.needed,('offset_dword',))
        o=sample(7,root=0x9000,offset=8)
        p=f.advance(replace(o,target_sample=GuardedDwordSample(0x1008,1,7)))
        self.assertTrue(p.complete);self.assertEqual(p.root,0x1000);self.assertEqual(p.address,0x1008)

    def test_wrapped_address_and_protection_failure_keep_return_gap(self):
        o=sample(0,root=0xfffffffc,offset=4)
        p=TargetIdFrame().advance(o);self.assertTrue(p.complete);self.assertEqual(p.address,0);self.assertEqual(p.value,0)
        f=TargetIdFrame();o=replace(sample(),target_sample=GuardedDwordSample(0x1004,0),target_returned=None)
        p=f.advance(o);self.assertEqual(p.needed,('target_returned',))
        p=f.advance(TargetIdObservation(target_returned=True));self.assertEqual(p.needed,('getter_returned',))
        p=f.advance(TargetIdObservation(getter_returned=True));self.assertTrue(p.complete);self.assertEqual(p.value,0)

    def test_three_invocations_feed_distinct_npc_call_sites(self):
        frames=[TargetIdFrame() for _ in range(3)]
        captures=[frame.advance(sample(v,slot=0x100+i*4,root=0x1000+i*0x100)).capture
                  for i,(frame,v) in enumerate(zip(frames,(77,88,0)))]
        c=lambda v:NpcValueCapture(v,True);sink=Sink()
        p=NpcClickFrame(sink).advance(NpcClickInput(captures[0],captures[1],c(0x2000),c(b'Name'),captures[2],trade_text=c('Name')))
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['User Trade',['Name','-']]])
        self.assertEqual([f.final.value for f in frames],[77,88,0])

    def test_terminal_input_ignored_and_invalid_unreached_fields_not_cached(self):
        f=TargetIdFrame();p=f.advance(replace(sample(),root_returned=False,offset_dword={},target_sample={}))
        self.assertEqual(p.needed,('root_returned',));self.assertIsNone(f.observation.offset_dword)
        p=f.advance(sample());self.assertTrue(p.complete);self.assertIs(f.advance({}),p)
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)


if __name__=='__main__':unittest.main()
