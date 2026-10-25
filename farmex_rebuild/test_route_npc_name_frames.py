import unittest
from dataclasses import replace
from route_npc_name import RouteNpcNameFrame,RouteNpcNameObservation
from source_coin import GuardedDwordSample
from test_route_npc_name import observed


class RouteNpcNameFrameTests(unittest.TestCase):
    def test_storage_nested_protection_freezes_before_value(self):
        f=RouteNpcNameFrame(0x1000)
        p=f.advance(replace(observed(),storage_sample=GuardedDwordSample(0x1008,1)))
        self.assertIn('storage_sample:',p.needed);self.assertIsNone(f.observation.name_offset_dword)
        p=f.advance(replace(observed(),storage_sample=GuardedDwordSample(0x1008,0,5)))
        self.assertTrue(p.complete);self.assertEqual(f.observation.storage_sample.protection_return_dword,1)

    def test_completed_storage_does_not_change_while_init_waits(self):
        f=RouteNpcNameFrame(0x1000);p=f.advance(replace(observed(),local_ansi_init_returned=False))
        self.assertEqual(p.needed,'local_ansi_init_returned');self.assertIsNone(f.observation.pointer_sample)
        p=f.advance(replace(observed(16),pointer_sample={},copied_bytes=observed().copied_bytes))
        self.assertTrue(p.complete);self.assertFalse(p.request.indirect)

    def test_short_copy_is_replaceable_and_complete_copy_frozen_before_return(self):
        f=RouteNpcNameFrame(0x1000)
        p=f.advance(replace(observed(),copied_bytes=b'Po'))
        self.assertEqual(p.needed,'copied_bytes');self.assertIsNone(f.observation.copied_bytes)
        p=f.advance(replace(observed(),copy_returned=None))
        self.assertEqual(p.needed,'copy_returned')
        p=f.advance(replace(observed(data=b'Other'),copy_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.name_bytes,b'Potion')

    def test_wrong_guard_address_or_copy_length_does_not_poison_cache(self):
        f=RouteNpcNameFrame(0x1000)
        with self.assertRaises(ValueError):f.advance(replace(observed(),storage_sample=GuardedDwordSample(8,1,5)))
        self.assertIsNone(f.observation.storage_sample)
        with self.assertRaises(ValueError):f.advance(replace(observed(),copied_bytes=b'A'*256))
        self.assertIsNone(f.observation.copied_bytes);self.assertTrue(f.advance(observed()).complete)

    def test_unreadable_fallback_ignores_unused_bytes_but_requires_returns(self):
        f=RouteNpcNameFrame(0x1000);o=replace(observed(),readable=False,copied_bytes={},std_assignment_returned=False)
        p=f.advance(o);self.assertEqual(p.needed,'std_assignment_returned')
        p=f.advance(RouteNpcNameObservation(std_assignment_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.name_bytes,b'');self.assertIsNone(f.observation.copied_bytes)

    def test_overflow_and_unterminated_source_are_not_silently_truncated(self):
        f=RouteNpcNameFrame(0x1000);p=f.advance(observed(513))
        self.assertFalse(p.complete);self.assertIn('overflow',p.status)
        self.assertIsNone(f.observation.copied_bytes)
        g=RouteNpcNameFrame(0x1000);p=g.advance(replace(observed(512),copied_bytes=b'A'*512))
        self.assertFalse(p.complete);self.assertIn('overread',p.status)
        p=g.advance(observed(512));self.assertFalse(p.complete);self.assertIn('overread',p.status)

    def test_only_reached_values_and_true_receipts_are_consumed(self):
        f=RouteNpcNameFrame(0x1000);p=f.advance(RouteNpcNameObservation(storage_offset_dword=8,storage_sample=None,pointer_sample={}))
        self.assertIn('storage_sample:',p.needed);self.assertIsNone(f.observation.pointer_sample)
        p=f.advance(observed());self.assertTrue(p.complete);self.assertIs(f.advance({}),p)

    def test_new_name_invocation_is_fresh_and_actor_zero_is_unreachable(self):
        f=RouteNpcNameFrame(0x1000);f.advance(observed())
        g=RouteNpcNameFrame(0x1000);p=g.advance()
        self.assertFalse(p.complete);self.assertEqual(p.needed,'storage_offset_dword')
        with self.assertRaises(ValueError):RouteNpcNameFrame(0)


if __name__=='__main__':unittest.main()
