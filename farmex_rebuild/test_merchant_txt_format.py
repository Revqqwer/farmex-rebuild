import unittest
from dataclasses import replace
from merchant_txt_format import (build_txt_header,build_txt_path,MerchantTxtAnsiRow as Row,project_txt_bytes)


class MerchantTxtTests(unittest.TestCase):
    def row(self,index=0,**kw):
        args=dict(seller_ansi=b'Seller',item_ansi=b'Item(+7)',amount_ansi=b'2',price_ansi=b'1.000')
        args.update(kw);return Row(index,**args)

    def test_header_uses_current_control_text_without_filtering_placeholder(self):
        self.assertEqual(build_txt_header('Selling Merchant','Tümü','Aranan item ismini yazınız...'),
            'Selling Merchant - Tümü - Filtre : Aranan item ismini yazınız... \n')
        self.assertEqual(build_txt_header('','',''),' -  - Filtre :  \n')

    def test_path_uses_explicit_helper_outputs_without_sanitizing(self):
        self.assertEqual(build_txt_path(b'C:\\Data',b'A/B',b'time'),b'C:\\Data\\A/B Merchant Tarama time.txt')
        self.assertEqual(build_txt_path(b'',b'',b''),b'\\ Merchant Tarama .txt')

    def test_row_order_literals_and_CRLF(self):
        p=project_txt_bytes(b'Header \n',(self.row(),))
        self.assertTrue(p.complete)
        self.assertEqual(p.insertion_chunks,(b'Header \n',b'1 - Sat\xfdc\xfd : Seller Item : Item(+7) Adet : 2 Fiyat : 1.000 \n'))
        self.assertEqual(p.projected_CRT_text_bytes,b''.join(p.insertion_chunks).replace(b'\n',b'\r\n'))
        self.assertFalse(p.file_written);self.assertFalse(p.source_ostream_executed)

    def test_c_string_boundary_applies_to_each_insertion(self):
        p=project_txt_bytes(b'H\0hidden\n',(self.row(seller_ansi=b'A\0B'),self.row(1)))
        self.assertEqual(p.insertion_chunks[0],b'H')
        self.assertEqual(p.insertion_chunks[1],b'1 - Sat\xfdc\xfd : A')
        self.assertTrue(p.insertion_chunks[2].startswith(b'2 - '))

    def test_missing_values_stop_in_source_getter_order(self):
        for field in ('price_ansi','amount_ansi','item_ansi','seller_ansi'):
            p=project_txt_bytes(b'H',(self.row(),replace(self.row(1),**{field:None}),self.row(2)))
            self.assertFalse(p.complete);self.assertEqual(p.needed,(1,field))
            self.assertEqual(len(p.insertion_chunks),2)
            self.assertEqual(p.read_order[-1],(1,field))
            self.assertFalse(any(i==2 for i,name in p.read_order))

    def test_missing_header_preserves_unknown_instead_of_encoding(self):
        p=project_txt_bytes(None,(self.row(),))
        self.assertFalse(p.complete);self.assertEqual(p.insertion_chunks,())
        self.assertEqual(p.read_order,())
        with self.assertRaises(ValueError):project_txt_bytes('Header',())

    def test_counter_signed_wrap_and_empty_rows(self):
        for index,prefix in ((0,'1'),(0x7fffffff,'-2147483648'),(0xffffffff,'0')):
            self.assertTrue(project_txt_bytes(b'',(self.row(index),)).insertion_chunks[1].startswith(prefix.encode()+b' - '))
        p=project_txt_bytes(b'Only header\n',());self.assertTrue(p.complete)
        self.assertEqual(p.projected_CRT_text_bytes,b'Only header\r\n')

    def test_raw_ANSI_not_reencoded_and_no_BOM_invented(self):
        p=project_txt_bytes(b'\xfe\xffH\r\n',(self.row(item_ansi=b'\x80\xff'),))
        self.assertTrue(p.projected_CRT_text_bytes.startswith(b'\xfe\xffH\r\r\n'))
        self.assertIn(b'Item : \x80\xff',p.projected_CRT_text_bytes)
        self.assertFalse(project_txt_bytes(b'H',()).projected_CRT_text_bytes.startswith(b'\xef\xbb\xbf'))

    def test_input_contract_rejects_unicode_row_and_mutable_snapshot(self):
        with self.assertRaises(ValueError):self.row(seller_ansi='Seller')
        with self.assertRaises(ValueError):project_txt_bytes(b'H',[self.row()])
        with self.assertRaises(ValueError):Row(-1)


if __name__=='__main__':unittest.main()
