import unittest
from delphi_list_text import plan_crlf_set_text as parse,plan_stable_get_text as text,plan_list_stream_bytes as stream

class DelphiListTextTests(unittest.TestCase):
    def text(self,rows,flags=4,lb='\r\n'):return text(rows,lb,flags,stable_same_invocation=True)
    def test_cr_lf_and_crlf_are_separators_in_default_branch(self):
        self.assertEqual(parse('a\rb\nc\r\nd','\r\n').rows,('a','b','c','d'))
    def test_empty_rows_and_trailing_separator_rules(self):
        for value,rows in (('',()),('\r\n',('',)),('a\r\n',('a',)),('\n\na',('','','a')),('a\r\n\r\n',('a',''))):
            self.assertEqual(parse(value,'\r\n').rows,rows)
    def test_nul_terminates_native_text_parse(self):
        self.assertEqual(parse('a\0ignored\r\nb','\r\n').rows,('a',))
        self.assertEqual(parse('\0a','\r\n').rows,())
    def test_case_space_duplicates_and_unicode_preserved(self):
        self.assertEqual(parse(' ABC \r\nabc\r\nabc\r\nİsim 😀','\r\n').rows,(' ABC ','abc','abc','İsim 😀'))
    def test_custom_delimiter_and_missing_fields_remain_unresolved(self):
        for lb in ('','\n','|'):self.assertFalse(parse('a|b',lb).complete)
        self.assertFalse(parse(None,'\r\n').complete)
    def test_get_text_trailing_flag_and_utf16_length(self):
        p=self.text(('a','😀'));self.assertEqual(p.text,'a\r\n😀\r\n');self.assertEqual(p.requested_utf16_units,7)
        p=self.text(('a','😀'),0);self.assertEqual(p.text,'a\r\n😀');self.assertEqual(p.requested_utf16_units,5)
    def test_get_text_uses_full_length_not_pchar_termination(self):
        p=self.text(('a\0b',));self.assertEqual(p.text,'a\0b\r\n');self.assertEqual(p.requested_utf16_units,5)
    def test_empty_no_trailing_negative_length_not_silently_fixed(self):
        self.assertEqual(self.text(()).text,'')
        p=self.text((),0);self.assertFalse(p.complete);self.assertEqual(p.requested_utf16_units,-2)
    def test_get_text_explicit_stability_and_known_flags(self):
        with self.assertRaises(ValueError):text(('a',),'\r\n',4)
        self.assertFalse(self.text(('a',),None).complete)
        with self.assertRaises(ValueError):self.text(('a',),True)
    def test_stream_preamble_flag_independent_of_trailing_line_flag(self):
        p=stream(0x1000,None,2,b'A',preamble_bytes=b'\xef\xbb\xbf')
        self.assertEqual(p.write_chunks,(b'\xef\xbb\xbf',b'A'));self.assertEqual(p.payload,b'\xef\xbb\xbfA')
        self.assertEqual(stream(0x1000,None,4,b'A').payload,b'A')
    def test_stream_defaults_only_when_explicit_pointer_zero(self):
        self.assertEqual(stream(0,0x2000,0,b'A').encoding_pointer_dword,0x2000)
        self.assertFalse(stream(None,0x2000,0,b'A').complete)
        self.assertFalse(stream(0,None,0,b'A').complete)
    def test_stream_unknown_preamble_and_empty_payload(self):
        self.assertFalse(stream(0x1000,None,2,b'A').complete)
        self.assertEqual(stream(0x1000,None,2,b'',preamble_bytes=b'').write_chunks,(b'',))
        self.assertFalse(stream(0x1000,None,0,None).complete)

if __name__=='__main__':unittest.main()
