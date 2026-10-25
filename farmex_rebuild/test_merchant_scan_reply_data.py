import struct
import unittest
from merchant_scan_reply_data import decode_merchant_scan_data as decode


def packet(direction, first=None, tail=b''):
    header = b'\x68\x23\x01' if direction else b'\x68\x05\x01\xff'
    empty = b'\0' * (12 if direction else 16)
    return header + struct.pack('<H',0x1234) + (empty if first is None else first) + empty * 11 + tail


class MerchantScanDataTests(unittest.TestCase):
    def test_minimum_gate_before_any_reads(self):
        for payload in (b'',b'\x68\x23\x01',b'\0'*148):
            p=decode(payload)
            self.assertTrue(p.complete)
            self.assertEqual((p.status,p.reads,p.slots,p.cursor),('source_length_rejected',(),(),0))
            self.assertFalse(p.source_length_gate_passed)

    def test_sell_and_buy_offsets_and_twelve_empty_slots(self):
        for direction,length in ((0,198),(1,149)):
            data=packet(direction);self.assertEqual(len(data),length)
            p=decode(data)
            self.assertTrue(p.complete)
            self.assertEqual((p.direction,p.entity_id,len(p.slots),p.cursor),(direction,0x1234,12,length))
            self.assertTrue(all(r.item_id==0 for r in p.slots))
            self.assertEqual(p.reads[1],(3 if direction else 4,2))

    def test_nonempty_buy_words_price_and_following_cursor(self):
        p=decode(packet(1,struct.pack('<IHHI',12345,7,99,0xffffffff)))
        r=p.slots[0]
        self.assertEqual((r.item_id,r.word_a,r.word_b,r.price),(12345,7,99,0xffffffff))
        self.assertIsNone(r.sell_extra_dword)
        self.assertIsNone(r.extension)
        self.assertEqual(p.reads[6],(17,4))

    def test_sell_extra_zero_and_unsigned_fields(self):
        p=decode(packet(0,struct.pack('<IHHII',1,65535,65534,0x80000000,0)))
        r=p.slots[0]
        self.assertEqual((r.word_a,r.word_b,r.price,r.sell_extra_dword),(65535,65534,0x80000000,0))
        self.assertIsNone(r.extension)
        self.assertEqual(p.cursor,198)

    def test_variable_extension_preserves_bytes_and_next_slot(self):
        body=struct.pack('<IHHIIH',1,2,3,4,5,3)+b'A\0B'+struct.pack('<IHB',6,7,8)
        p=decode(packet(0,body))
        self.assertTrue(p.complete)
        self.assertEqual((p.slots[0].extension.data,p.slots[0].extension.dword,p.slots[0].extension.word,p.slots[0].extension.byte),(b'A\0B',6,7,8))
        self.assertEqual(p.cursor,210)
        self.assertEqual(len(p.slots),12)

    def test_zero_length_extension_does_not_skip_tail_fields(self):
        body=struct.pack('<IHHIIHIHB',1,2,3,4,5,0,6,7,8)
        p=decode(packet(0,body))
        self.assertEqual(p.slots[0].extension.data,b'')
        self.assertEqual(p.slots[0].extension.byte,8)

    def test_source_minimum_gate_does_not_guarantee_sell_frame(self):
        p=decode(packet(0)[:149])
        self.assertFalse(p.complete)
        self.assertEqual((p.status,len(p.slots),p.stopped_slot),('truncated:item_id',9,9))
        self.assertEqual((p.cursor,p.reads[-1]),(154,(150,4)))

    def test_final_empty_skip_is_not_an_extra_memory_read(self):
        data=packet(0)[:186]
        p=decode(data)
        self.assertTrue(p.complete)
        self.assertEqual(p.cursor,198)
        self.assertEqual(p.reads[-1],(182,4))

    def test_extension_truncation_preserves_reached_fields(self):
        body=struct.pack('<IHHIIH',1,2,3,4,5,65535)
        p=decode(packet(0,body))
        self.assertFalse(p.complete)
        self.assertEqual(p.status,'truncated:extension_data')
        self.assertEqual(p.stopped_slot,0)
        self.assertEqual(dict(p.reached_fields)['extension_length'],65535)
        self.assertEqual(p.slots,())

    def test_dispatcher_guards_and_metadata_are_not_synthesized(self):
        data=bytearray(packet(1,tail=b'ignored'))
        data[0]=0;data[2]=0
        p=decode(bytes(data))
        self.assertTrue(p.complete)
        self.assertEqual(p.direction,1)
        self.assertFalse(p.native_execution_verified or p.result_records_verified or p.live_compatibility_verified)
        with self.assertRaises(ValueError):decode(data)


if __name__=='__main__':unittest.main()
