import unittest
from dataclasses import replace
from item_name import *

class ItemNameTests(unittest.TestCase):
    def setUp(self):
        self.o=ItemNameObservation(0x1000,2,0x2000,2,4,0x6b726f46,0,b'Fork\0'+b'x'*250)
    def plan(self,o=None,**kwargs):return plan_item_name(123,o or self.o,**kwargs)
    def test_inline_lookup_reads255_not_reported_storage_count(self):
        p=self.plan()
        self.assertEqual((p.family,p.read_address,p.read_count,p.ansi_bytes),('lookup',0x1008,255,b'Fork'))
        self.assertIn(('0045dc44:buffer',(0x1008,)),p.calls)
    def test_all_five_category_values_choose_lookup_other_values_metadata(self):
        for cat in range(256):
            p=self.plan(replace(self.o,metadata_category=cat))
            self.assertEqual(p.family,'lookup' if cat in (0,1,2,5,11) else 'metadata')
            self.assertEqual(p.read_address,0x1008 if cat in (0,1,2,5,11) else 0x2004)
    def test_storage15_vs16_and_captured_prefix(self):
        p=self.plan(replace(self.o,storage_dword=15));self.assertEqual(p.read_count,255)
        p=self.plan(replace(self.o,storage_dword=16,pointer_dword=0x9000,captured=b'abcdefghijklmnop'))
        self.assertEqual((p.read_address,p.read_count,p.ansi_bytes),(0x9000,16,b'abcdefghijklmnop'))
    def test_pointer_copy_stops_at_first_nul_and_keeps_non_ascii_bytes(self):
        p=self.plan(replace(self.o,storage_dword=16,captured=b'\xdd\xfe\0'+b'x'*13))
        self.assertEqual(p.ansi_bytes,b'\xdd\xfe');self.assertIsInstance(p.ansi_bytes,bytes)
        self.assertFalse(p.independently_verified)
    def test_zero_item_lookup_metadata_paths_require_no_buffer_data(self):
        self.assertEqual(plan_item_name(0,ItemNameObservation()).ansi_bytes,b'')
        self.assertEqual(self.plan(ItemNameObservation(lookup_result=0)).status,'empty_lookup')
        self.assertEqual(self.plan(ItemNameObservation(metadata_result=0,resolver_type_raw=3),provided_lookup=0x1000).status,'empty_metadata')
    def test_provided_pointers_skip_lookup_resolver_observations(self):
        p=self.plan(replace(self.o,lookup_result=None,resolver_type_raw=None,metadata_result=None),
            provided_lookup=0x1000,provided_metadata=0x2000)
        self.assertEqual(p.ansi_bytes,b'Fork');self.assertNotIn('00465514',[a for a,args in p.calls])
        self.assertNotIn('00465580',[a for a,args in p.calls])
    def test_read_rejected_returns_empty_before_copy_hazards(self):
        p=self.plan(replace(self.o,storage_dword=0xffffffff,bad_read_result=1,captured=None))
        self.assertEqual((p.status,p.ansi_bytes),('read_rejected_empty',b''))
        self.assertNotIn('memcpy:source_buffer',[a for a,args in p.calls])
    def test_exact512_requires_nul_but_larger_readable_copy_unresolved(self):
        p=self.plan(replace(self.o,storage_dword=512,captured=b'x'*512))
        self.assertEqual(p.status,'unresolved_unterminated_source_buffer')
        p=self.plan(replace(self.o,storage_dword=512,captured=b'x'*511+b'\0'))
        self.assertEqual(len(p.ansi_bytes),511)
        self.assertEqual(self.plan(replace(self.o,storage_dword=513,captured=None)).status,'unresolved_source_stack_overflow')
    def test_unknown_and_short_capture_do_not_create_partial_name(self):
        for o,key in ((replace(self.o,metadata_category=None),'metadata_category'),
                      (replace(self.o,pointer_dword=None),'pointer_dword'),
                      (replace(self.o,bad_read_result=None),'IsBadReadPtr:EAX'),
                      (replace(self.o,captured=b'Fork\0'),'complete_captured_bytes:255')):
            p=self.plan(o);self.assertEqual(p.status,'needs_observation');self.assertEqual(p.reason,key)
            self.assertIsNone(p.ansi_bytes)
    def test_address_additions_follow_x86_dword_wrap(self):
        p=self.plan(provided_lookup=0xfffffffc,provided_metadata=0xfffffff0)
        self.assertEqual(p.read_address,4)
        self.assertIn(('0045dbdc:name_category',(0x34,)),p.calls)
    def test_invalid_raw_inputs_rejected(self):
        with self.assertRaises(ValueError):ItemNameObservation(metadata_category=256)
        with self.assertRaises(ValueError):ItemNameObservation(bad_read_result=True)
        with self.assertRaises(ValueError):plan_item_name(-1,self.o)
