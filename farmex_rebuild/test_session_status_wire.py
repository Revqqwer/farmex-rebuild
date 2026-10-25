import unittest
from session_status_wire import (FIELDS, SessionStatusPrepared,
    build_session_status_wire, transform_status_bytes)

class SessionStatusWireTests(unittest.TestCase):
    def prepared(self, name=b'', **kw):
        values = dict.fromkeys(FIELDS, 0); values.update(kw)
        return SessionStatusPrepared(values, name)

    def build(self, p, count=None):
        return build_session_status_wire(p, entry_observed=True,
                                        transform_length_word=42+len(p.serialized_name) if count is None else count)

    def test_zero_message_even_wire_golden(self):
        p = self.build(self.prepared())
        self.assertTrue(p.complete)
        self.assertEqual(p.length_word, 42)
        self.assertEqual(p.plain_frame, bytes.fromhex('aa55263b02')+bytes(35)+b'\x55\xaa')
        self.assertEqual(p.wire_frame, bytes.fromhex('aa55263b705e')+bytes.fromhex('6e5e')*17+b'\x55\xaa')
        self.assertEqual(p.buffer_512[42:], bytes(470))
        self.assertFalse(p.full_builder_verified or p.native_execution_verified or p.live_compatibility_verified)

    def test_odd_name_wire_golden_and_independent_header_count(self):
        p = self.build(self.prepared(b'A', name_header_byte=255))
        self.assertEqual(p.length_word, 43)
        self.assertEqual(p.plain_frame[:8], bytes.fromhex('aa556b1f0200ff41'))
        self.assertEqual(p.wire_frame[:8], bytes.fromhex('aa556b1f5a4a578b'))
        self.assertEqual(p.wire_frame[-2:], b'\x55\xaa')

    def test_getter_low_bytes_and_dword_little_endian_layout(self):
        p = self.build(self.prepared(mode_byte=4, status_byte=0x34, getter_46209c=0x12345678,
            getter_462670=0x87654321, getter_46256c=0xff00, ratio_division_eax=0xfffffffe,
            getter_46258c=0x12345678, getter_4625ac=0x89abcdef,
            getter_4625d8=0xfedcba98, exclusive_byte=1))
        self.assertEqual(p.plain_frame[7:19], bytes.fromhex('0434782100fe785634120000'))
        self.assertEqual(p.plain_frame[19:31], bytes(12))
        self.assertEqual(p.plain_frame[31:40], bytes.fromhex('efcdab8998badcfe01'))

    def test_transform_preserves_guards_and_wraps_bytes(self):
        src = b'head'+bytes([255,254,253,252])+b'TR' + b'untouched'
        self.assertEqual(transform_status_bytes(src,10,0), b'head'+bytes([109,92,107,90])+b'TRuntouched')
        self.assertEqual(transform_status_bytes(src,10,1), b'head'+bytes([87,72,85,70])+b'TRuntouched')
        for count in (0,1,4,6,0x80000000,0xffffffff):
            self.assertEqual(transform_status_bytes(b'',count,0),b'')

    def test_fresh_global_length_is_not_assumed_local(self):
        prepared = self.prepared()
        gap = build_session_status_wire(prepared, entry_observed=True)
        self.assertFalse(gap.complete); self.assertEqual(gap.length_word,42)
        altered = self.build(prepared,43)
        self.assertEqual(altered.helper,'004f9564')
        # A changed count includes original trailer index40 in the body span.
        self.assertEqual(altered.wire_frame[-2:],bytes([0xad,0xaa]))
        self.assertEqual(altered.plain_frame[2:4],bytes.fromhex('263b'))

    def test_missing_entry_and_source_buffer_extent(self):
        self.assertFalse(build_session_status_wire(self.prepared()).complete)
        self.assertTrue(self.build(self.prepared(bytes(470))).complete)
        overflow = self.build(self.prepared(bytes(471)))
        self.assertFalse(overflow.complete); self.assertEqual(overflow.wire_frame,b'')
        self.assertFalse(self.build(self.prepared(),515).complete)
        self.assertTrue(self.build(self.prepared(),514).complete)

    def test_inputs_are_typed_and_immutable(self):
        values = dict.fromkeys(FIELDS,0); p = SessionStatusPrepared(values,b'')
        values['session_byte']=9; self.assertEqual(p.values['session_byte'],0)
        with self.assertRaises(TypeError): p.values['session_byte']=1
        for kw in ({'getter_46258c':True},{'exclusive_byte':2},{'session_byte':256}):
            with self.assertRaises(ValueError): self.prepared(**kw)
        with self.assertRaises(ValueError): self.prepared(bytearray())
        with self.assertRaises(ValueError): self.build(p,True)

if __name__ == '__main__': unittest.main()
