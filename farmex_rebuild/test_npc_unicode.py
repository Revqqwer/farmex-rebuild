import sys,unittest
from dataclasses import replace
from unittest.mock import patch
from npc_unicode import NpcUnicodeFrame,NpcUnicodeObservation


def observed(**changes):
    values=dict(ansi_is_null=False,codepage_word=1254,rtl_returned=True,
                wrapper_returned=True,constructor_returned=True)
    values.update(changes);return NpcUnicodeObservation(**values)


class NpcUnicodeTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform=='win32','Windows flags0 reference')
    def test_seven_strict_decode_rejections_match_finite_rtl_reference(self):
        for byte in (0x81,0x8d,0x8e,0x8f,0x90,0x9d,0x9e):
            with self.subTest(byte=byte):
                data=bytes([byte])
                with self.assertRaises(UnicodeDecodeError):data.decode('cp1254')
                p=NpcUnicodeFrame(data).advance(observed())
                self.assertEqual(p.capture.value,chr(byte));self.assertTrue(p.complete)
                self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

    def test_normal_receipts_are_independent_and_decoding_does_not_supply_them(self):
        for field in ('rtl_returned','wrapper_returned','constructor_returned'):
            with self.subTest(field=field):
                f=NpcUnicodeFrame(b'Name')
                with patch('npc_unicode.WindowsNameCodec') as codec:
                    codec.return_value.decode.return_value='Name'
                    p=f.advance(observed(**{field:False}))
                    self.assertEqual(p.needed,(field,));self.assertIsNone(p.capture)
                    self.assertTrue(f.advance(observed()).complete)
                    codec.return_value.decode.assert_called_once_with(b'Name')

    def test_zero_header_requires_explicit_effective_codepage_and_freezes_consumed_values(self):
        f=NpcUnicodeFrame(b'Name')
        with patch('npc_unicode.WindowsNameCodec') as codec:
            codec.return_value.decode.return_value='Name'
            p=f.advance(observed(codepage_word=0))
            self.assertEqual(p.needed,('effective_codepage',));codec.assert_not_called()
            p=f.advance(observed(codepage_word=1251,effective_codepage=1254))
            self.assertTrue(p.complete);codec.assert_called_once_with(1254)
            self.assertEqual(f.cache['codepage_word'],0)

    def test_nil_and_counted_empty_do_not_guess_codepage_or_call_decoder(self):
        with patch('npc_unicode.WindowsNameCodec') as codec:
            f=NpcUnicodeFrame(b'');p=f.advance(observed(ansi_is_null=True,codepage_word={}))
            self.assertEqual(p.capture.value,'');self.assertNotIn('codepage_word',f.cache)
            g=NpcUnicodeFrame(b'');p=g.advance(observed(codepage_word=0,effective_codepage={}))
            self.assertEqual(p.capture.value,'');self.assertNotIn('effective_codepage',g.cache)
            codec.assert_not_called()

    def test_unknown_nullness_and_header_stay_pending_even_for_empty(self):
        f=NpcUnicodeFrame(b'');p=f.advance(NpcUnicodeObservation(codepage_word={}))
        self.assertEqual(p.needed,('ansi_is_null',));self.assertEqual(f.cache,{})
        p=f.advance(NpcUnicodeObservation(ansi_is_null=False))
        self.assertEqual(p.needed,('codepage_word',))

    def test_invalid_observations_do_not_poison_unreached_values(self):
        f=NpcUnicodeFrame(b'Name')
        with self.assertRaises(ValueError):f.advance(observed(ansi_is_null=True))
        self.assertEqual(f.cache,{})
        with self.assertRaises(ValueError):f.advance(observed(codepage_word=True))
        self.assertNotIn('codepage_word',f.cache)
        g=NpcUnicodeFrame(b'Name')
        with self.assertRaises(ValueError):g.advance(observed(codepage_word=0,effective_codepage=0))
        self.assertNotIn('effective_codepage',g.cache)

    def test_decoding_error_never_produces_receipt_or_completed_text(self):
        f=NpcUnicodeFrame(b'Name')
        with patch('npc_unicode.WindowsNameCodec',side_effect=OSError('decode unavailable')):
            with self.assertRaises(OSError):f.advance(observed())
        self.assertIsNone(f.final);self.assertNotIn('rtl_returned',f.cache)

    def test_terminal_frame_ignores_future_inputs_and_rejects_raw_pchar_buffers(self):
        with self.assertRaises(ValueError):NpcUnicodeFrame(b'A\0B')
        f=NpcUnicodeFrame(b'');p=f.advance(observed(ansi_is_null=True))
        self.assertIs(f.advance({}),p)


if __name__=='__main__':unittest.main()
