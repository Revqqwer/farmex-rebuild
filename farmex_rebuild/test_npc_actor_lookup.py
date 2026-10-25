import unittest
from dataclasses import replace
from npc_actor_lookup import NpcLookupFrame,NpcLookupObservation,LookupContextSample


def sample(eax=0x1000):
    return NpcLookupObservation(0x8000,LookupContextSample(0x8000,0x9000),
                                0x700000,0xfeed,True,eax,True,True)


class NpcActorLookupTests(unittest.TestCase):
    def test_raw_call_context_is_not_guessed_function_signature(self):
        p=NpcLookupFrame(88).advance(sample())
        self.assertTrue(p.complete);self.assertEqual(p.capture.value,0x1000)
        self.assertEqual((p.call.target_dword,p.call.eax_dword,p.call.ecx_dword,p.call.edx_dword),(0x700000,0,0x9000,0xfeed))
        self.assertEqual(p.call.pushes,(1,88));self.assertEqual(p.call.entry_stack_dwords,(88,1))

    def test_missing_edx_and_return_are_never_fabricated(self):
        f=NpcLookupFrame(88);p=f.advance(replace(sample(),edx_dword=None))
        self.assertEqual(p.needed,('edx_dword',));self.assertIsNone(p.capture)
        p=f.advance(NpcLookupObservation(edx_dword=0,indirect_returned=False))
        self.assertEqual(p.needed,('indirect_returned',));self.assertIsNone(p.capture)

    def test_context_sample_address_mismatch_does_not_poison_cache(self):
        f=NpcLookupFrame(1)
        with self.assertRaises(ValueError):f.advance(replace(sample(),context_sample=LookupContextSample(99,0x9000)))
        self.assertIsNone(f.observation.context_sample);self.assertTrue(f.advance(sample()).complete)

    def test_reached_context_freezes_while_later_target_waits(self):
        f=NpcLookupFrame(1);p=f.advance(replace(sample(),target_address_dword=None))
        self.assertEqual(p.needed,('target_address_dword',))
        p=f.advance(replace(sample(),context_address_dword=99,context_sample={}))
        self.assertTrue(p.complete);self.assertEqual(p.call.ecx_dword,0x9000)

    def test_zero_context_target_has_no_invented_null_shortcut(self):
        f=NpcLookupFrame(0);p=f.advance(NpcLookupObservation(context_address_dword=0))
        self.assertEqual(p.needed,('context_sample','value_dword'))
        p=f.advance(NpcLookupObservation(context_sample=LookupContextSample(0,0),target_address_dword=0,edx_dword=0))
        self.assertEqual(p.needed,('indirect_returned',));self.assertEqual(p.call.target_dword,0)
        self.assertIsNone(p.capture)

    def test_three_normal_returns_are_independent_and_eax_zero_is_a_result(self):
        for field in ('indirect_returned','inner_returned','outer_returned'):
            f=NpcLookupFrame(5);p=f.advance(replace(sample(0),**{field:False}))
            self.assertFalse(p.complete);self.assertEqual(p.needed,(field,));self.assertIsNone(p.capture)
            p=f.advance(sample(0));self.assertTrue(p.complete);self.assertEqual(p.capture.value,0)

    def test_indirect_result_is_retained_before_parent_returns(self):
        f=NpcLookupFrame(5);p=f.advance(replace(sample(0xffffffff),inner_returned=False))
        self.assertEqual(p.needed,('inner_returned',))
        p=f.advance(sample(0));self.assertTrue(p.complete);self.assertEqual(p.capture.value,0xffffffff)
        self.assertIs(f.advance({}),p)

    def test_distinct_invocations_keep_separate_ids_and_unreached_fields_fresh(self):
        f=NpcLookupFrame(77);g=NpcLookupFrame(88)
        p=f.advance(NpcLookupObservation(context_address_dword=0x8000,target_address_dword={}))
        self.assertEqual(p.needed,('context_sample','value_dword'));self.assertIsNone(f.observation.target_address_dword)
        p=f.advance(sample());q=g.advance(sample())
        self.assertEqual(p.call.entry_stack_dwords,(77,1));self.assertEqual(q.call.entry_stack_dwords,(88,1))
        self.assertFalse(p.native_execution_verified);self.assertFalse(q.live_compatibility_verified)


if __name__=='__main__':unittest.main()
