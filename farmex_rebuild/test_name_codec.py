import sys,unittest
from name_codec import WindowsNameCodec,convert_name_chain
from item_name import ItemNameObservation,plan_item_name
from loot_classifier import LootListObservation,LootMetadataObservation
from loot_name_cache import LootCacheRow,classify_loot_with_name_cache

@unittest.skipUnless(sys.platform=='win32','Actual Windows conversion fixture')
class NameCodecTests(unittest.TestCase):
    def test_cp1254_turkish_roundtrip(self):
        p=convert_name_chain(b'\xd0\xdd\xfe',1254)
        self.assertEqual(p.first_unicode,'Ğİş');self.assertEqual(p.compare_unicode,'Ğİş')
        self.assertEqual(p.cache_ansi,b'\xd0\xdd\xfe');self.assertFalse(p.used_default)
        self.assertFalse(p.independently_verified)
    def test_utf8_supplementary_char_and_embedded_nul(self):
        data='İ\U0001f600\0X'.encode('utf-8');p=convert_name_chain(data,65001)
        self.assertEqual(p.compare_unicode,'İ\U0001f600\0X');self.assertEqual(p.cache_ansi,data)
        self.assertIsNone(p.used_default)
    def test_empty_chain_is_empty_nonempty_guard_false(self):
        p=convert_name_chain(b'',1254)
        self.assertEqual((p.first_unicode,p.cache_ansi,p.compare_unicode,p.preconversion_nonempty),('',b'','',False))
    def test_same_bytes_different_explicit_codepage_changes_name(self):
        a=convert_name_chain(b'\xdd',1254);b=convert_name_chain(b'\xdd',1252)
        self.assertEqual(a.compare_unicode,'İ');self.assertEqual(b.compare_unicode,'Ý')
    def test_default_substitution_is_reported_for_unrepresentable_input(self):
        data,used=WindowsNameCodec(1254).encode('\U0001f600')
        self.assertTrue(used);self.assertTrue(data)
    def test_invalid_utf8_uses_explicit_local_flags0_policy(self):
        p=convert_name_chain(b'\xff',65001)
        self.assertEqual(p.compare_unicode,'\ufffd')
        self.assertNotEqual(p.cache_ansi,b'\xff')
    def test_codepage_must_be_concrete_supported_and_not_bool(self):
        for page in (0,True,-1,99999,65535):
            with self.subTest(page=page),self.assertRaises((ValueError,OSError)):WindowsNameCodec(page)
    def test_captured_ansi_to_cache_to_mask_composition(self):
        captured=b'\xddtem\0'+b'x'*250
        n=plan_item_name(123,ItemNameObservation(metadata_category=2,storage_dword=4,
            pointer_dword=1,bad_read_result=0,captured=captured),provided_lookup=0x1000,provided_metadata=0x2000)
        p=convert_name_chain(n.ansi_bytes,1254)
        fields={4:3,0x18:1,0x1c:7,0x21:0,0x20:0,0x11:0,0x14:0}
        names=(p.compare_unicode,'','','','','','','')
        obs=LootListObservation({0:LootMetadataObservation(1,1,2,7,0)})
        result=classify_loot_with_name_cache((123,0,0,0,0,0,0,0),fields,obs,names,
            (LootCacheRow('İtem',1),),input_nonempty=(p.preconversion_nonempty,False,False,False,False,False,False,False))
        self.assertEqual(result.classification.attempt_slots,(0,))
