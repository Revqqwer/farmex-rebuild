import unittest
from dataclasses import replace
from merchant_actor_metadata import MerchantActorObservation as O, MerchantCoordinateObservation as C, plan_merchant_actor_metadata as actor, project_merchant_reply_values as project
from merchant_result_filter import MerchantFilterSelection as S


def observed():
    return O(True,0x1000,C(0x10,True,True,825),C(0x14,True,True,0xffffffff),0x18,4,0x20,0,0x30,True,b'Seller\0'+b'x'*248)


class MerchantActorMetadataTests(unittest.TestCase):
    def test_inline_uses_fresh_offset_but_does_not_skip_initial_read(self):
        p=actor(0xffff,observed(),lambda b:b.decode('ascii'))
        self.assertTrue(p.complete)
        self.assertEqual((p.metadata.seller,p.metadata.x_dword,p.metadata.y_dword),('Seller',825,0xffffffff))
        self.assertEqual((p.text_request.address,p.text_request.byte_count,p.text_request.indirect),(0x1030,255,False))
        self.assertIn(('0045dc44',0x1020),p.steps)
        self.assertEqual(p.steps[0],('00464a10',0xffff))

    def test_pointer_branch_does_not_consume_inline_offset(self):
        o=replace(observed(),storage_dword=16,initial_name_dword=0x9000,inline_name_offset_dword=None,copied_bytes=b'Seller\0'+b'x'*9)
        p=actor(1,o,lambda b:b.decode('ascii'))
        self.assertTrue(p.complete)
        self.assertEqual((p.text_request.address,p.text_request.byte_count),(0x9000,16))
        self.assertNotIn(('global:second',0x553fe8),p.steps)

    def test_unsigned_storage_high_bit_does_not_select_inline(self):
        p=actor(1,replace(observed(),storage_dword=0x80000000,readable=True,copied_bytes=None))
        self.assertEqual(p.status,'name_copy:unresolved_native_buffer_overflow')
        self.assertTrue(p.text_request.indirect)

    def test_read_rejected_empty_name_is_separate_from_missing_capture(self):
        p=actor(1,replace(observed(),readable=False,copied_bytes=None))
        self.assertTrue(p.complete)
        self.assertEqual(p.metadata.seller,'')
        self.assertFalse(actor(1,replace(observed(),copied_bytes=None)).complete)

    def test_missing_actor_does_not_invent_zero_coordinates(self):
        p=actor(1,O(True,0))
        self.assertEqual(p.status,'unresolved_missing_actor_coordinate_locals')
        self.assertEqual(p.coordinate_eax_prefix,())
        self.assertIsNone(p.metadata)

    def test_coordinate_normal_and_eax_observations_are_separate(self):
        p=actor(1,replace(observed(),y=C(0x14,True,None,0)))
        self.assertEqual(p.coordinate_eax_prefix,(825,))
        self.assertEqual(p.status,'needs_y_ftol_normal_return')
        p=actor(1,replace(observed(),x=C(0x10,True,True,None)))
        self.assertEqual(p.status,'needs_x_ftol_eax')

    def test_decoder_missing_preserves_captured_ansi(self):
        p=actor(1,observed())
        self.assertEqual(p.status,'needs_explicit_own_name_decoder')
        self.assertEqual(p.text_copy.ansi_bytes,b'Seller')
        self.assertFalse(p.native_execution_verified or p.native_text_conversion_verified)

    def test_exact512_unterminated_copy_stays_unresolved(self):
        p=actor(1,replace(observed(),storage_dword=512,initial_name_dword=0x9000,copied_bytes=b'x'*512))
        self.assertEqual(p.status,'name_copy:unresolved_native_string_overread')

    def test_full_actor_item_and_row_composition(self):
        from test_merchant_item_metadata import packet,observed as item
        p=project(packet(),observed(),{0:item()},S('Buying Merchant','all',1),lambda b:b.decode('ascii'))
        self.assertTrue(p.complete)
        row=p.lookup_results.results.rows.rows[0]
        self.assertEqual(row.caption,'Seller')
        self.assertEqual(row.subitems[0],'Bow(+7) (Reverse)')
        self.assertEqual(row.subitems[-2:],('825','-1'))
        self.assertFalse(p.source_parser_return_verified or p.native_execution_verified)

    def test_contracts(self):
        with self.assertRaises(ValueError):actor(65536)
        with self.assertRaises(ValueError):C(float_reader_returned=1)
        with self.assertRaises(ValueError):O(copied_bytes=bytearray())


if __name__=='__main__':unittest.main()
