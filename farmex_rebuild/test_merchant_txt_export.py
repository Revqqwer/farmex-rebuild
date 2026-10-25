import sys,tempfile,unittest
from pathlib import Path
from merchant_txt_export import OwnedExportContext,export_displayed_txt
from merchant_result_rows import MerchantResultRow as Row
from name_codec import WindowsNameCodec


@unittest.skipUnless(sys.platform=='win32','Own Windows path and codec policy')
class OwnTxtExportTests(unittest.TestCase):
    def context(self,directory,identity=b'Character'):
        return OwnedExportContext(str(directory),identity,(3,2,1,4,0,126,0,0,0),1254,1254)
    def row(self,caption='Seller',item='Item',record_index=99):
        return Row(record_index,caption,(item,'2','1.000','PM','GİT','825','520'))
    def run_export(self,context,rows=(),**kw):
        return export_displayed_txt(context,'Selling Merchant','Tümü','',rows,**kw)

    def test_real_file_name_bytes_and_current_display_order(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.run_export(self.context(directory),(self.row('Z',record_index=99),self.row('A',record_index=3)))
            self.assertTrue(p.complete,p.error);data=Path(p.path).read_bytes()
            self.assertEqual(Path(p.path).name,'Character Merchant Tarama 4.0.2026  1-2-3.txt')
            self.assertTrue(data.startswith('Selling Merchant - Tümü - Filtre :  \r\n'.encode('cp1254')))
            self.assertIn(b'1 - Sat\xfdc\xfd : Z',data);self.assertIn(b'2 - Sat\xfdc\xfd : A',data)
            self.assertNotIn(b'825',data);self.assertEqual((p.rows_written,p.bytes_written),(2,len(data)))
            self.assertTrue(p.file_closed);self.assertFalse(p.source_ostream_executed)

    def test_empty_result_writes_only_header(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.run_export(self.context(d));self.assertTrue(p.complete)
            self.assertEqual(Path(p.path).read_bytes(),'Selling Merchant - Tümü - Filtre :  \r\n'.encode('cp1254'))

    def test_existing_file_truncated_without_extra_tail(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.run_export(self.context(d),(self.row(),));Path(p.path).write_bytes(b'old'*1000)
            q=self.run_export(self.context(d));self.assertTrue(q.complete)
            self.assertEqual(Path(q.path).stat().st_size,q.bytes_written)
            self.assertNotIn(b'old',Path(q.path).read_bytes())

    def test_header_and_row_C_string_boundaries_are_separate(self):
        with tempfile.TemporaryDirectory() as d:
            p=export_displayed_txt(self.context(d),'V','C','A\0hidden',(self.row('S\0tail'),self.row('Next')))
            data=Path(p.path).read_bytes()
            self.assertTrue(p.complete);self.assertTrue(data.startswith(b'V - C - Filtre : A1 - '))
            self.assertNotIn(b'hidden',data);self.assertNotIn(b'tail',data)
            self.assertIn(b'S2 - ',data)

    def test_missing_context_skips_codec_and_rows(self):
        def fail(*args):raise AssertionError('not reached')
        p=export_displayed_txt(None,None,None,None,None,codec_factory=fail,opener=fail)
        self.assertEqual(p.status,'needs_export_context');self.assertFalse(p.file_opened)

    def test_directory_is_not_created(self):
        with tempfile.TemporaryDirectory() as d:
            missing=Path(d)/'not-created';p=self.run_export(self.context(missing))
            self.assertFalse(p.complete);self.assertEqual(p.status,'failed:open');self.assertFalse(missing.exists())

    def test_header_codec_failure_precedes_open(self):
        with tempfile.TemporaryDirectory() as d:
            def fail(cp):raise ValueError('codec unavailable')
            p=self.run_export(self.context(d),codec_factory=fail)
            self.assertEqual(p.status,'failed:header_conversion');self.assertFalse(p.file_opened)
            self.assertEqual(tuple(Path(d).iterdir()),())

    def test_late_conversion_error_keeps_written_prefix_and_closes(self):
        class Codec:
            def __init__(self,cp):self.code_page=cp;self.actual=WindowsNameCodec(cp)
            def encode(self,text):
                if text=='FAIL':raise ValueError('late item conversion')
                return self.actual.encode(text)
            def decode(self,data):return self.actual.decode(data)
        with tempfile.TemporaryDirectory() as d:
            p=self.run_export(self.context(d),(self.row('First'),self.row('Second','FAIL')),codec_factory=Codec)
            self.assertFalse(p.complete);self.assertEqual((p.failed_row,p.rows_written),(1,1))
            data=Path(p.path).read_bytes();self.assertIn(b'First',data);self.assertNotIn(b'Second',data)
            self.assertEqual(p.bytes_written,len(data));self.assertTrue(p.file_closed)
            labels=[o[0] for o in p.encoding_observations]
            self.assertEqual(labels[-2:],[(1,'price_ansi'),(1,'amount_ansi')])

    def test_short_write_is_incomplete_and_prefix_retained(self):
        class Short:
            def __init__(self,path,mode):self.file=open(path,mode)
            def write(self,data):return self.file.write(data[:3])
            def close(self):self.file.close()
        with tempfile.TemporaryDirectory() as d:
            p=self.run_export(self.context(d),opener=Short)
            self.assertEqual(p.status,'failed:header_write');self.assertFalse(p.complete)
            self.assertEqual((p.bytes_written,Path(p.path).stat().st_size),(3,3));self.assertTrue(p.file_closed)

    def test_close_error_does_not_claim_complete(self):
        class Closing:
            def __init__(self,path,mode):self.file=open(path,mode)
            def write(self,data):return self.file.write(data)
            def close(self):self.file.close();raise OSError('simulated close failure')
        with tempfile.TemporaryDirectory() as d:
            p=self.run_export(self.context(d),opener=Closing)
            self.assertFalse(p.complete);self.assertEqual(p.status,'failed:close')
            self.assertEqual(p.close_error,'simulated close failure');self.assertFalse(p.file_closed)

    def test_own_directory_boundary_rejects_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.run_export(self.context(d,b'..\\outside'))
            self.assertFalse(p.complete);self.assertEqual(p.status,'failed:path_conversion')
            self.assertFalse(p.file_opened)

    def test_source_filename_C_string_termination(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.run_export(self.context(d,b'A\0ignored'))
            self.assertTrue(p.complete);self.assertEqual(Path(p.path).name,'A')

    def test_header_placeholder_and_conversion_default_flag_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=export_displayed_txt(self.context(d),'V','C','Aranan item ismini yazınız... 日',())
            self.assertTrue(p.complete)
            self.assertIn(b'Aranan item',Path(p.path).read_bytes())
            self.assertTrue(p.encoding_observations[0][3])
            self.assertFalse(Path(p.path).read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_context_requires_absolute_directory_and_explicit_codepages(self):
        with self.assertRaises(ValueError):self.context('relative')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):OwnedExportContext(d,b'A',(0,)*9,0,1254)


if __name__=='__main__':unittest.main()
