import unittest,tempfile
from pathlib import Path
from name_cfg_codec import NameCfgDocument as Doc,decode_name_cfg as decode,encode_name_cfg as encode,read_name_cfg,write_name_cfg

class NameCfgCodecTests(unittest.TestCase):
    def test_three_boms_override_explicit_default_codepage(self):
        for cp,bom,codec in ((65001,b'\xef\xbb\xbf','utf-8'),(1200,b'\xff\xfe','utf-16-le'),(1201,b'\xfe\xff','utf-16-be')):
            p=decode(bom+'İsim 😀\r\n'.encode(codec),1254)
            self.assertTrue(p.complete);self.assertEqual(p.document.rows,('İsim 😀',));self.assertEqual(p.document.encoding_codepage,cp)
            self.assertEqual(encode(p.document).payload,bom+'İsim 😀\r\n'.encode(codec))
    def test_no_bom_uses_given_codepage_not_utf8_guess(self):
        data='Türk\r\n'.encode('utf-8')
        a=decode(data,65001);b=decode(data,1254)
        self.assertEqual(a.document.rows,('Türk',));self.assertNotEqual(b.document.rows,('Türk',))
    def test_ansi_turkish_duplicate_space_and_crlf_export(self):
        data=' İsim \r\nABC\nABC\r'.encode('cp1254');p=decode(data,1254)
        self.assertEqual(p.document.rows,(' İsim ','ABC','ABC'))
        self.assertEqual(encode(p.document).payload,' İsim \r\nABC\r\nABC\r\n'.encode('cp1254'))
    def test_explicit_encoding_does_not_strip_other_preamble(self):
        p=decode(b'\xef\xbb\xbfABC',1254,explicit_codepage=1254)
        self.assertTrue(p.complete);self.assertEqual(p.preamble_size,0);self.assertTrue(p.document.rows[0].endswith('ABC'))
        self.assertNotEqual(p.document.rows,('ABC',))
    def test_invalid_utf8_odd_utf16_and_surrogate_are_held(self):
        for data in (b'\xef\xbb\xbf\xff',b'\xff\xfeA',b'\xff\xfe\x00\xd8'):
            self.assertFalse(decode(data,1254).complete)
    def test_nul_parse_and_blank_lines(self):
        p=decode(b'\n\nA\0B\r\n',1254)
        self.assertEqual(p.document.rows,('','','A'))
    def test_empty_bom_file_encoding_retained_when_resaved(self):
        p=decode(b'\xef\xbb\xbf',1254);self.assertEqual(p.document.rows,())
        self.assertEqual(encode(p.document).payload,b'\xef\xbb\xbf')
        self.assertEqual(encode(Doc((),1254)).payload,b'')
    def test_bom_and_trailing_flags_independent(self):
        p=encode(Doc(('A',),65001,flags_byte=0x0c));self.assertEqual(p.payload,b'A\r\n')
        p=encode(Doc(('A',),65001,flags_byte=0x0a));self.assertEqual(p.payload,b'\xef\xbb\xbfA')
    def test_lossy_codepage_export_is_held(self):
        self.assertFalse(encode(Doc(('😀',),1254)).complete)
    def test_custom_linebreak_and_negative_length_are_not_faked(self):
        self.assertFalse(decode(b'A|B',1254,line_break='|').complete)
        self.assertFalse(encode(Doc((),65001,flags_byte=0x0a)).complete)
    def test_length_based_export_can_contain_nul_then_pchar_import_stops(self):
        p=encode(Doc(('A\0B',),65001));self.assertTrue(p.complete)
        self.assertEqual(decode(p.payload,1254).document.rows,('A',))
    def test_own_atomic_file_roundtrip_and_loss_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/'own.cfg')
            p=write_name_cfg(path,Doc(('ABC','İsim'),65001));self.assertTrue(p.complete)
            before=Path(path).read_bytes();self.assertEqual(read_name_cfg(path,1254).document.rows,('ABC','İsim'))
            p=write_name_cfg(path,Doc(('😀',),1254));self.assertFalse(p.complete);self.assertEqual(Path(path).read_bytes(),before)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()),['own.cfg'])
    def test_file_budget_exact_boundary_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'own.cfg';path.write_bytes(b'ABC')
            self.assertTrue(read_name_cfg(str(path),1254,max_bytes=3).complete)
            self.assertEqual(read_name_cfg(str(path),1254,max_bytes=2).status,'local_file_budget')
            self.assertEqual(read_name_cfg(str(path.parent/'missing.cfg'),1254).status,'file_unreadable')
    def test_metadata_and_path_types(self):
        with self.assertRaises(ValueError):decode(b'A',0)
        with self.assertRaises(ValueError):decode('A',1254)
        with self.assertRaises(ValueError):Doc([],1254)
        with self.assertRaises(ValueError):Doc((),1254,True)
        with self.assertRaises(ValueError):read_name_cfg('relative.cfg',1254)

if __name__=='__main__':unittest.main()
