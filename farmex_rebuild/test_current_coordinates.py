import unittest
from dataclasses import replace
from current_coordinates import *


def sample(root_address=0x100,root=0x1000,offset=4,eax=7):
    address=(root+offset)&0xffffffff
    return CurrentAxisObservation(root_address,GuardedDwordSample(root_address,1,root),True,offset,
                                  GuardedFloatSample(address,1,0x3fc00000),True,True,eax,True)


class CurrentCoordinatesTests(unittest.TestCase):
    def test_guarded_float_null_failed_protection_and_observed_bits(self):
        self.assertEqual(plan_guarded_float(0).bits,0)
        self.assertEqual(plan_guarded_float(4,GuardedFloatSample(4,0)).bits,0)
        self.assertFalse(plan_guarded_float(4,GuardedFloatSample(4,1)).complete)
        p=plan_guarded_float(4,GuardedFloatSample(4,1,0x80000000))
        self.assertTrue(p.complete);self.assertEqual(p.bits,0x80000000);self.assertFalse(p.native_effects_verified)

    def test_normal_axis_records_exact_dependency_order_and_dword_wrap(self):
        p=plan_current_axis('x',sample(root=0xfffffffc,offset=8,eax=0xffffffff))
        self.assertTrue(p.complete);self.assertEqual(p.address,4);self.assertEqual(p.eax,0xffffffff)
        self.assertEqual([s[0] for s in p.steps],['global','0045dc44','global','0045ddb8','CC32260MT.DLL:__ftol'])

    def test_root_parent_gap_prevents_offset_float_and_conversion(self):
        p=plan_current_axis('x',replace(sample(),root_returned=None))
        self.assertFalse(p.complete);self.assertEqual(len(p.steps),2);self.assertIsNone(p.address)

    def test_zero_root_does_not_skip_nonzero_offset_float_read(self):
        o=CurrentAxisObservation(0,None,True,16,GuardedFloatSample(16,0),True,True,0,True)
        p=plan_current_axis('y',o)
        self.assertTrue(p.complete);self.assertEqual(p.address,16);self.assertEqual(p.float_bits,0)

    def test_two_axes_have_fresh_root_and_offset_observations(self):
        p=plan_current_coordinates(sample(root_address=0x100,root=0x1000,offset=4,eax=0xffffffff),
                                   sample(root_address=0x200,root=0x2000,offset=8,eax=0x80000000))
        self.assertTrue(p.complete);self.assertEqual([a.address for a in p.axes],[0x1004,0x2008])
        self.assertEqual(p.parameters,('-1','-2147483648'))
        self.assertEqual([a.steps[0] for a in p.axes],[('global',0x553e7c)]*2)

    def test_y_pending_preserves_x_prefix_without_publishing_partial_parameters(self):
        p=plan_current_coordinates(sample(eax=123),CurrentAxisObservation())
        self.assertFalse(p.complete);self.assertEqual(p.eax_prefix,(123,));self.assertIsNone(p.parameters)

    def test_zero_float_bits_and_eax_do_not_infer_native_normal_returns(self):
        o=CurrentAxisObservation(0,None,True,0,None,True,True,0,True)
        for field in ('float_returned','ftol_returned','axis_returned'):
            p=plan_current_axis('x',replace(o,**{field:None}))
            self.assertFalse(p.complete);self.assertIn('return',p.missing)

    def test_wrong_sample_address_axis_and_bool_dword_rejected(self):
        with self.assertRaises(ValueError):plan_guarded_float(4,GuardedFloatSample(8,1,0))
        with self.assertRaises(ValueError):plan_current_axis('z',sample())
        with self.assertRaises(ValueError):CurrentAxisObservation(root_address_dword=True)
        with self.assertRaises(ValueError):plan_current_axis('x',replace(sample(),float_sample=GuardedFloatSample(99,1,0)))


if __name__=='__main__':unittest.main()
