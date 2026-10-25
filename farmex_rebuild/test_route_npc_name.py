import unittest
from dataclasses import replace
from source_coin import GuardedDwordSample
from route_npc_name import RouteNpcNameObservation,plan_route_npc_name
from route_npc_click import NpcClickFrame,NpcClickInput,NpcValueCapture
from test_route_coordinate_click import Sink


def observed(storage=5,*,actor=0x1000,pointer=0x9000,data=b'Potion'):
    count=255 if storage<16 or storage>=0x80000000 else storage
    return RouteNpcNameObservation(8,GuardedDwordSample((actor+8)&0xffffffff,1,storage),True,
        True,True,True,True,4,GuardedDwordSample((actor+4)&0xffffffff,1,pointer),True,
        True,True,data+b'\0'*(count-len(data)),True,True,True,True)


class RouteNpcNameTests(unittest.TestCase):
    def test_inline_uses255_and_never_demands_pointer(self):
        o=replace(observed(),pointer_sample={},pointer_returned={})
        p=plan_route_npc_name(0x1000,o)
        self.assertTrue(p.complete);self.assertEqual(p.name_bytes,b'Potion')
        self.assertEqual((p.request.address,p.request.byte_count,p.request.indirect),(0x1004,255,False))
        self.assertEqual(len(p.guards),1);self.assertTrue(p.capture.returned)

    def test_signed_negative_storage_uses_inline_and_long16_requires_pointer(self):
        for storage in (0xffffffff,0x80000000):
            p=plan_route_npc_name(0x1000,observed(storage))
            self.assertTrue(p.complete);self.assertEqual(p.request.byte_count,255)
        p=plan_route_npc_name(0x1000,observed(16))
        self.assertTrue(p.complete);self.assertEqual((p.request.address,p.request.byte_count),(0x9000,16))
        self.assertEqual(len(p.guards),2)

    def test_guard_zero_is_not_a_helper_return_receipt(self):
        o=replace(observed(),storage_sample=GuardedDwordSample(0x1008,0),storage_returned=None)
        p=plan_route_npc_name(0x1000,o)
        self.assertFalse(p.complete);self.assertEqual(p.needed,'storage_returned');self.assertIsNone(p.request)
        p=plan_route_npc_name(0x1000,replace(o,storage_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.request.byte_count,255)

    def test_unreadable_and_unsafe_copy_paths_do_not_invent_bytes(self):
        o=replace(observed(513),readable=False,copied_bytes={})
        p=plan_route_npc_name(0x1000,o);self.assertTrue(p.complete);self.assertEqual(p.name_bytes,b'')
        p=plan_route_npc_name(0x1000,replace(o,readable=True))
        self.assertFalse(p.complete);self.assertIn('overflow',p.status);self.assertIsNone(p.capture)
        p=plan_route_npc_name(0x1000,replace(observed(512),copied_bytes=b'A'*512))
        self.assertFalse(p.complete);self.assertIn('overread',p.status)

    def test_all_normal_boundaries_remain_independent_even_for_empty(self):
        o=replace(observed(),readable=False,copied_bytes=None)
        for field in ('local_ansi_init_returned','std_factory_returned','std_copy_returned',
                      'std_initial_cleanup_returned','temporary_ansi_init_returned','copy_returned',
                      'ansi_assignment_returned','temporary_cleanup_returned','std_assignment_returned'):
            p=plan_route_npc_name(0x1000,replace(o,**{field:False}))
            self.assertFalse(p.complete,field);self.assertEqual(p.needed,field);self.assertIsNone(p.capture)

    def test_address_wrap_and_wrong_sample_address_rejection(self):
        p=plan_route_npc_name(0xfffffffc,observed(actor=0xfffffffc))
        self.assertTrue(p.complete);self.assertEqual(p.request.address,0)
        with self.assertRaises(ValueError):
            plan_route_npc_name(0x1000,replace(observed(),storage_sample=GuardedDwordSample(99,1,5)))

    def test_exact_copy_range_and_first_nul_without_encoding_guess(self):
        p=plan_route_npc_name(0x1000,observed(data=b'Potion\0DC\xff'))
        self.assertTrue(p.complete);self.assertEqual(p.name_bytes,b'Potion')
        p=plan_route_npc_name(0x1000,observed(data=b'\xffDC'))
        self.assertTrue(p.complete);self.assertEqual(p.name_bytes,b'\xffDC')
        with self.assertRaises(ValueError):plan_route_npc_name(0x1000,replace(observed(),copied_bytes=b'Potion'))

    def test_produced_name_feeds_route_frame_without_ready_made_name_metadata(self):
        p=plan_route_npc_name(0x1000,observed(data=b'DC Sundries'))
        s=Sink();c=lambda v:NpcValueCapture(v,True)
        result=NpcClickFrame(s).advance(NpcClickInput(c(1),c(2),c(0x1000),p.capture,c(3001)))
        self.assertTrue(result.complete);self.assertEqual(s.rows,[['NPC',['DC Sundries','-']]])
        self.assertFalse(p.native_execution_verified);self.assertFalse(result.live_compatibility_verified)


if __name__=='__main__':unittest.main()
