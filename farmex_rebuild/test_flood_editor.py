import unittest
from flood_editor import *

class FloodEditorTests(unittest.TestCase):
    def test_add_channel_message_delay_and_allow_duplicate_empty_message(self):
        a=edit_flood('add',(),channels=('Party',),channel_index=0,message='',delay_text='5')
        b=edit_flood('add',a.rows,channels=('Party',),channel_index=0,message='',delay_text='+0005')
        self.assertEqual(b.rows,(FloodRow('Party',('','5')),)*2);self.assertEqual(b.selected_index,1)

    def test_low_dword_signed_threshold_and_long_decimal(self):
        for text in ('4','-1','2147483648','4294967300'):
            p=edit_flood('add',(),channels=('Clan',),channel_index=0,delay_text=text)
            self.assertFalse(p.changed);self.assertEqual(p.status,'delay_rejected')
        p=edit_flood('add',(),channels=('Clan',),channel_index=0,delay_text='4294967301')
        self.assertEqual(p.rows[0].subitems[1],'5')
        self.assertEqual(flood_delay('  +5'),5)
        self.assertEqual(flood_delay('5 '),10)

    def test_rtl_formats_and_invalid_fallback_ten_discard_partial_result(self):
        for text in ('','$','1.5','x','９','9223372036854775808','-9223372036854775809','5 '):
            with self.subTest(text=text):self.assertEqual(flood_delay(text),10)
        for text in ('$10','0x10','x10'):self.assertEqual(flood_delay(text),16)
        self.assertEqual(flood_delay('0'*2000+'5'),5)
        self.assertEqual(flood_delay('5\0tail'),5)

    def test_remove_only_selected_and_preserve_all_other_fields(self):
        rows=(FloodRow('A',('1','2','extra'),True),FloodRow('B',('3','4')),FloodRow('C',()))
        result=edit_flood('selected',rows,selected_index=1)
        self.assertEqual(result.rows,(rows[0],rows[2]));self.assertEqual(rows[1].caption,'B')
        for index in (None,-1,3):self.assertFalse(edit_flood('selected',rows,selected_index=index).changed)

    def test_clear_and_roundtrip_rows_without_aliasing(self):
        data=[dict(caption='Türkçe',subitems=['mesaj','10'],checked=True)]
        rows=read_rows(data);written=write_rows(rows);written[0]['subitems'][0]='changed'
        self.assertEqual(data[0]['subitems'][0],'mesaj');self.assertEqual(rows[0].subitems[0],'mesaj')
        self.assertTrue(edit_flood('clear',rows).changed);self.assertFalse(edit_flood('clear',()).changed)

    def test_explicit_limits_and_types(self):
        self.assertFalse(edit_flood('clear',()).source_native_equivalence_verified)
        self.assertFalse(edit_flood('clear',()).live_compatibility_verified)
        for kw in ({'channel_index':-1},{'channel_index':True},{'channels':['All Chat'],'channel_index':0}):
            with self.assertRaises(ValueError):edit_flood('add',(),**kw)
        with self.assertRaises(ValueError):read_rows([{'caption':'A','subitems':(),'checked':False}])

if __name__=='__main__':unittest.main()
