import unittest
from flood_compilation import *

class Codec:
    def __init__(self,page):self.page=page
    def encode(self,text):return text.encode('cp1254' if self.page==1254 else 'utf-8'),False if self.page==1254 else None

class FloodCompilationTests(unittest.TestCase):
    def test_order_checked_ignored_extra_columns_and_byte_layout(self):
        rows=(FloodRow('Party',('hello','5'),False),FloodRow('Clan',('Türkçe','10','ignored'),True))
        p=compile_flood_rows(rows,1254,codec_factory=Codec)
        self.assertTrue(p.complete)
        self.assertEqual(p.rows,(MessageListRow(b'Party',b'hello',5000,0),MessageListRow(b'Clan',b'T\xfcrk\xe7e',10000,1)))
        self.assertEqual(len(p.conversions),4)

    def test_source_producer_has_no_add_minimum_gate(self):
        rows=tuple(FloodRow('All Chat',('',text)) for text in ('0','-1','4','4294967301'))
        p=compile_flood_rows(rows,1254,codec_factory=Codec)
        self.assertEqual([r.delay_dword for r in p.rows],[0,0xfffffc18,4000,5000])

    def test_invalid_delay_default_ten_and_low32_millisecond_wrap(self):
        rows=tuple(FloodRow('Party',('M',text)) for text in ('bad','5 ','$10','$ffffffffffffffff'))
        p=compile_flood_rows(rows,1254,codec_factory=Codec)
        self.assertEqual(p.fallback_rows,(0,1));self.assertEqual([r.delay_dword for r in p.rows],[10000,10000,16000,0xfffffc18])

    def test_nul_bytes_preserved_and_utf8_policy_explicit(self):
        p=compile_flood_rows((FloodRow('Party',('a\0ğ','5\0bad')),),65001,codec_factory=Codec)
        self.assertEqual(p.rows[0].message_bytes,b'a\x00\xc4\x9f');self.assertEqual(p.rows[0].delay_dword,5000)
        self.assertIsNone(p.conversions[1][3])

    def test_later_missing_cell_retains_only_completed_prefix(self):
        rows=(FloodRow('Party',('a','5')),FloodRow('Clan',('missing delay',)))
        p=compile_flood_rows(rows,1254,codec_factory=Codec)
        self.assertFalse(p.complete);self.assertEqual(p.failed_row,1);self.assertEqual(len(p.rows),1)
        self.assertEqual(len(p.conversions),2)

    def test_conversion_failure_does_not_fabricate_row_or_drop_prior_prefix(self):
        class Failing(Codec):
            def encode(self,text):
                if text=='fail':raise OSError('owned conversion failure')
                return super().encode(text)
        p=compile_flood_rows((FloodRow('Party',('ok','5')),FloodRow('Clan',('fail','10'))),1254,codec_factory=Failing)
        self.assertFalse(p.complete);self.assertEqual(len(p.rows),1)
        self.assertEqual(p.conversions[-1][:2],(1,'channel'))

    def test_empty_compile_needs_no_codec_and_input_snapshot_immutable(self):
        def unavailable(page):raise AssertionError('empty list must not initialize codec')
        p=compile_flood_rows((),1254,codec_factory=unavailable)
        self.assertTrue(p.complete);self.assertEqual(p.rows,())
        row=FloodRow('Party',('a','5'));p=compile_flood_rows((row,),1254,codec_factory=Codec)
        self.assertEqual(p.snapshot,(row,))

    def test_local_container_has_no_invented_sixtyfour_row_limit(self):
        rows=tuple(FloodRow('Party',('m',str(i))) for i in range(1000))
        p=compile_flood_rows(rows,1254,codec_factory=Codec)
        self.assertTrue(p.complete);self.assertEqual(len(p.rows),1000);self.assertEqual(p.rows[-1].source_index,999)

    def test_invalid_codec_contract_and_flags(self):
        class Bad(Codec):
            def encode(self,text):return b'ok',1
        p=compile_flood_rows((FloodRow('P',('M','5')),),1254,codec_factory=Bad)
        self.assertFalse(p.complete);self.assertEqual(p.rows,())
        self.assertFalse(p.native_codec_equivalence_verified);self.assertFalse(p.native_vector_verified);self.assertFalse(p.live_compatibility_verified)
        with self.assertRaises(ValueError):compile_flood_rows([],1254)
        with self.assertRaises(ValueError):compile_flood_rows((),0)

    def test_value_projection_matches_independent_captured_source_frame(self):
        from message_list_producer import MessageListFrame,MessageListObservation
        from source_integer import SourceIntegerObservation
        # Raw native result/ANSI captures are fixed independently of compiler.
        for text,qword in (('-1',0xffffffffffffffff),('4294967301',4294967301)):
            p='row0.'
            names=('count','channel_init','channel_get','channel_ansi','channel_unicode_cleanup',
                   'message_init','message_get','message_ansi','message_unicode_cleanup','delay_init','delay_get',
                   'parser_outer','delay_unicode_cleanup','record_channel_init','record_message_init',
                   'record_channel_assign','record_message_assign','size','capacity','fast_append',
                   'record_message_cleanup','record_channel_cleanup','original_message_cleanup','original_channel_cleanup')
            normals={p+n:True for n in names};normals.update({n:True for n in ('clear_end_iterator','clear_begin_iterator','clear_range','row1.count')})
            values={p+'count_eax':1,p+'size_eax':0,p+'capacity_eax':1,p+'end_dword':0x1000,'row1.count_eax':1}
            o=MessageListObservation(True,values,normals,{p+'channel':'Party',p+'message':'hello',p+'delay':text},
                {p+'channel':b'Party',p+'message':b'hello'},
                {p+'delay_integer':SourceIntegerObservation(True,'normal',True,qword,cleanup_returned=True)})
            source=MessageListFrame().advance(o)
            own=compile_flood_rows((FloodRow('Party',('hello',text)),),1254,codec_factory=Codec)
            self.assertTrue(source.complete);self.assertEqual(own.rows,source.rows)

if __name__=='__main__':unittest.main()
