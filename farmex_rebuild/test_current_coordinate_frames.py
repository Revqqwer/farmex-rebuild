import unittest
from dataclasses import replace
from current_coordinates import *
from test_current_coordinates import sample


class CurrentCoordinateFrameTests(unittest.TestCase):
    def test_root_protection_and_value_freeze_separately_offset_stays_fresh(self):
        f=CurrentAxisFrame('x')
        p=f.advance(CurrentAxisObservation(0x100,GuardedDwordSample(0x100,1),offset_dword=4))
        self.assertEqual(p.needed,('root_sample','value_dword'));self.assertIsNone(f.observation.offset_dword)
        p=f.advance(CurrentAxisObservation(0x200,GuardedDwordSample(0x100,0,0x2000),offset_dword=8))
        self.assertEqual(p.needed,('root_returned',));self.assertEqual(f.observation.root_address_dword,0x100)
        self.assertEqual(f.observation.root_sample.protection_return_dword,1)
        p=f.advance(CurrentAxisObservation(root_sample=GuardedDwordSample(0x100,1,0x3000),root_returned=True,offset_dword=12))
        self.assertEqual(p.address,0x200c);self.assertEqual(f.observation.offset_dword,12)

    def test_ftol_eax_is_not_frozen_before_normal_return(self):
        f=CurrentAxisFrame('x');p=f.advance(replace(sample(eax=1),ftol_returned=None))
        self.assertEqual(p.needed,('ftol_returned',));self.assertIsNone(f.observation.ftol_eax)
        p=f.advance(CurrentAxisObservation(ftol_returned=True,ftol_eax=2,axis_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.eax,2)

    def test_axis_parent_wait_preserves_completed_getters_and_eax(self):
        f=CurrentAxisFrame('y');p=f.advance(replace(sample(eax=7),axis_returned=None))
        self.assertEqual(p.needed,('axis_returned',))
        p=f.advance(replace(sample(root_address=0x200,root=0x3000,eax=9),axis_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.eax,7);self.assertEqual(p.root,0x1000)

    def test_completed_x_is_not_revalidated_or_replaced_while_y_waits(self):
        f=CurrentCoordinatesFrame();p=f.advance(sample(eax=123),CurrentAxisObservation())
        self.assertEqual(p.eax_prefix,(123,))
        p=f.advance('unreached changed X capture',sample(root_address=0x200,root=0x2000,eax=456))
        self.assertTrue(p.complete);self.assertEqual(p.parameters,('123','456'))

    def test_unreached_y_values_are_not_cached_while_x_waits(self):
        f=CurrentCoordinatesFrame();p=f.advance(CurrentAxisObservation(),sample(eax=1))
        self.assertFalse(p.complete);self.assertIsNone(f.y.observation.root_address_dword)
        p=f.advance(sample(eax=2),sample(root_address=0x200,root=0x2000,eax=3))
        self.assertEqual(p.parameters,('2','3'))

    def test_wrong_reached_sample_address_does_not_poison_cached_protection(self):
        f=CurrentAxisFrame('x');f.advance(CurrentAxisObservation(0x100))
        with self.assertRaises(ValueError):f.advance(CurrentAxisObservation(root_sample=GuardedDwordSample(0x200,1,0x1000)))
        self.assertIsNone(f.observation.root_sample)
        p=f.advance(sample());self.assertTrue(p.complete)

    def test_failed_protection_skips_unused_raw_value_and_still_demands_parent(self):
        f=CurrentAxisFrame('x');p=f.advance(CurrentAxisObservation(4,GuardedDwordSample(4,0,0xdeadbeef)))
        self.assertEqual(p.needed,('root_returned',));self.assertIsNone(f.observation.root_sample.value_dword)
        p=f.advance(CurrentAxisObservation(root_returned=True,offset_dword=0,float_returned=True,ftol_returned=True,ftol_eax=0,axis_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.root,0)

    def test_final_frame_is_terminal_and_false_receipt_is_pending(self):
        f=CurrentAxisFrame('x');p=f.advance(replace(sample(),root_returned=False))
        self.assertEqual(p.needed,('root_returned',))
        p=f.advance(sample());self.assertTrue(p.complete);self.assertIs(f.advance('not reached'),p)
        with self.assertRaises(ValueError):CurrentAxisFrame('x').advance({})


if __name__=='__main__':unittest.main()
