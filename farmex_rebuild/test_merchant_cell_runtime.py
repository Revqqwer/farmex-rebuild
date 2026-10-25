import sys,unittest
from merchant_cell_runtime import OwnedMerchantCells
from merchant_cell_actions import MerchantCellState
from merchant_result_rows import MerchantResultRow as R
from name_codec import WindowsNameCodec
from action_queue import QueueState,enqueue


def row(caption='Seller',x='825',y='520'):
    return R(7,caption,('Item','1','1.000','PM','GİT',x,y))


class OwnedMerchantCellRuntimeTests(unittest.TestCase):
    def test_no_selection_and_other_columns_skip_codec_clock(self):
        def forbidden():raise AssertionError('unreached input')
        s=OwnedMerchantCells()
        self.assertEqual(s.activate(None,4,codepage_reader=forbidden,clock=forbidden).status,'no_selected_row')
        self.assertEqual(s.activate(row(),3,codepage_reader=forbidden,clock=forbidden).status,'not_action_column')
        self.assertEqual(s.queue.records,())

    @unittest.skipUnless(sys.platform=='win32','Local Windows codec')
    def test_PM_uses_shared_own_queue_and_correct_wire(self):
        seed=enqueue(QueueState(),b'seed',4,0,1,10).state
        s=OwnedMerchantCells(seed)
        p=s.activate(row(),4,codec_factory=WindowsNameCodec,codepage_reader=lambda:1254,clock=lambda:123)
        self.assertTrue(p.complete)
        self.assertEqual(p.payload,b'\x35\x01\x06\x00Seller')
        self.assertEqual([r.payload for r in p.queue.records],[b'seed',p.payload])
        self.assertEqual(p.queue.records[-1].created_tick,123)
        self.assertEqual(p.record_index,7)
        self.assertFalse(p.delivery_verified or p.native_execution_verified or p.source_cell_frame_executed)

    @unittest.skipUnless(sys.platform=='win32','Local Windows codec')
    def test_PM_cstring_NUL_and_ANSI_codepage(self):
        p=OwnedMerchantCells().activate(row('ı\0ignored'),4,codec_factory=WindowsNameCodec,codepage_reader=lambda:1254,clock=lambda:1)
        self.assertEqual(p.payload,b'\x35\x01\x01\x00\xfd')
        self.assertEqual(p.conversion[0],1254)

    @unittest.skipUnless(sys.platform=='win32','Local Windows codec')
    def test_PM_copy_bound_and_invalid_CP_skip_clock(self):
        def forbidden():raise AssertionError('bad input must skip clock')
        s=OwnedMerchantCells()
        p=s.activate(row('x'*101),4,codec_factory=WindowsNameCodec,codepage_reader=lambda:1254,clock=forbidden)
        self.assertFalse(p.complete);self.assertEqual(p.status,'unresolved_source_stack_alias_copy')
        p=s.activate(row(),4,codec_factory=WindowsNameCodec,codepage_reader=lambda:0,clock=forbidden)
        self.assertFalse(p.complete);self.assertTrue(p.status.startswith('local_caption_conversion:'))
        self.assertEqual(s.queue.records,())

    @unittest.skipUnless(sys.platform=='win32','Local Windows codec')
    def test_own_queue_gate0_skips_clock_without_claiming_send(self):
        def forbidden():raise AssertionError('gate0 must skip clock')
        p=OwnedMerchantCells().activate(row(),4,codec_factory=WindowsNameCodec,codepage_reader=lambda:1254,
            clock=forbidden,admission_gate=0)
        self.assertTrue(p.complete);self.assertEqual(p.status,'not_enqueued')
        self.assertEqual(p.queue.records,())

    def test_GIT_prepares_measured_float_bits_and_does_not_require_codec(self):
        s=OwnedMerchantCells();s.state=MerchantCellState(7,8)
        p=s.activate(row(x='16777217',y='-2147483648'),5)
        self.assertTrue(p.complete)
        self.assertEqual(p.state,MerchantCellState(0,0))
        self.assertEqual(p.movement_push_order,(0xcf000000,0x4b800000))
        self.assertEqual(s.movements,((7,p.movement_push_order),))
        self.assertEqual(p.queue.records,())
        self.assertFalse(p.delivery_verified)

    def test_GIT_bad_text_preserves_stop_state_without_movement_intent(self):
        s=OwnedMerchantCells();s.state=MerchantCellState(7,8)
        p=s.activate(row(x='825.0'),5)
        self.assertFalse(p.complete)
        self.assertEqual(p.state,MerchantCellState(0,0))
        self.assertEqual(s.movements,())

    def test_contracts(self):
        with self.assertRaises(ValueError):OwnedMerchantCells('not queue')
        with self.assertRaises(ValueError):OwnedMerchantCells().activate('not row',4)
        with self.assertRaises(ValueError):OwnedMerchantCells().activate(row(),True)


if __name__=='__main__':unittest.main()
