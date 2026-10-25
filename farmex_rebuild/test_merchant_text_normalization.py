import sys,unittest
from merchant_text_normalization import WindowsMerchantText


@unittest.skipUnless(sys.platform=='win32','Own Windows text policy')
class MerchantTextNormalizationTests(unittest.TestCase):
    def setUp(self):self.normalizer=WindowsMerchantText(1254)

    def test_ascii_query_and_record_are_distinct_typed_paths(self):
        q=self.normalizer.query('sword(+7)');a=self.normalizer.ansi_name(b'sword(+7)')
        self.assertTrue(q.complete and a.complete)
        self.assertEqual(q.output_bytes,b'SWORD(+7)')
        self.assertEqual(q.output_bytes,a.output_bytes)
        self.assertEqual(q.operation,'unicode_query');self.assertEqual(a.operation,'ansi_name')

    def test_counted_nul_is_processed_before_filter_truncation(self):
        q=self.normalizer.query('a\0b');a=self.normalizer.ansi_name(b'a\0b')
        self.assertEqual(q.upper_unicode,'A\0B')
        self.assertEqual(q.output_bytes,b'A\0B')
        self.assertEqual(a.output_bytes,b'A\0B')
        self.assertEqual((q.processed_units,a.processed_units),(3,3))

    def test_no_python_upper_expansion_or_linguistic_substitution(self):
        q=self.normalizer.query('iıİß')
        self.assertEqual(q.upper_unicode,'Iıİß')
        self.assertEqual(q.output_bytes,'Iıİß'.encode('cp1254'))
        self.assertNotEqual(q.upper_unicode,'iıİß'.upper())

    def test_explicit_codepage_and_loss_observation(self):
        a=WindowsMerchantText(1252).query('İ')
        b=WindowsMerchantText(65001).query('İ')
        self.assertEqual(b.output_bytes,'İ'.encode('utf-8'))
        self.assertNotEqual(a.output_bytes,b.output_bytes)
        self.assertEqual((a.code_page,b.code_page),(1252,65001))

    def test_utf16_length_and_unpaired_surrogate_are_not_python_length(self):
        q=self.normalizer.query('\U0001f600\ud800')
        self.assertTrue(q.complete)
        self.assertEqual(q.processed_units,3)

    def test_empty_values_and_metadata_do_not_claim_game(self):
        for p in (self.normalizer.query(''),self.normalizer.ansi_name(b'')):
            self.assertTrue(p.complete)
            self.assertEqual((p.output_bytes,p.processed_units),(b'',0))
            self.assertGreater(p.host_acp,0)
            self.assertFalse(p.source_runtime_verified or p.live_compatibility_verified)

    def test_contracts(self):
        with self.assertRaises(ValueError):self.normalizer.query(b'wrong')
        with self.assertRaises(ValueError):self.normalizer.ansi_name('wrong')
        with self.assertRaises(ValueError):WindowsMerchantText(0)


if __name__=='__main__':unittest.main()
