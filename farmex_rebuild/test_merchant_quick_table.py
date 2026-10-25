import sys,unittest
from merchant_quick_scan import QuickActorObservation as A,QuickItemObservation as M
from merchant_quick_table import QuickScanSnapshot,prepare_quick_table
from test_merchant_quick_scan import actor,complete_actors


def snapshot(**kw):
    actors=complete_actors();actors[1]=actor(**kw)
    return QuickScanSnapshot(actors,1254)


class QuickTableTests(unittest.TestCase):
    def test_missing_provider_does_not_invent_empty_scan(self):
        p=prepare_quick_table(None)
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_quick_scan_provider')
        self.assertIsNone(p.quick_values)

    def test_partial_values_prevent_final_decode(self):
        def fail(cp):raise AssertionError('not reached')
        p=prepare_quick_table(QuickScanSnapshot({1:actor()},1254),codec_factory=fail)
        self.assertFalse(p.complete);self.assertEqual(p.quick_values.needed,('lookup',2))
        self.assertEqual(len(p.quick_values.records),1);self.assertEqual(p.display_records,())

    def test_empty_complete_scan_needs_no_codec(self):
        def fail(cp):raise AssertionError('not reached')
        p=prepare_quick_table(QuickScanSnapshot(complete_actors()),codec_factory=fail)
        self.assertTrue(p.complete);self.assertEqual(p.display_records,())

    def test_nonempty_scan_requires_explicit_codepage(self):
        s=snapshot();p=prepare_quick_table(QuickScanSnapshot(s.actors))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_explicit_codepage')
        self.assertEqual(len(p.quick_values.records),1)

    @unittest.skipUnless(sys.platform=='win32','Own Windows decoding')
    def test_original_bytes_and_zero_fields_reach_display_records(self):
        p=prepare_quick_table(snapshot(seller_ansi=b'Sat\xfdc\xfd',items={0:M(11,12,15,b'K\xfdl\xfdc')}))
        self.assertTrue(p.complete);r=p.display_records[0]
        self.assertEqual((r.seller,r.item_name),('Satıcı','Kılıc(+5) (Reverse)'))
        self.assertEqual(r.filter_record.original_name_ansi,b'K\xfdl\xfdc(+5) (Reverse)')
        self.assertEqual((r.price_14,r.filter_record.amount_20,r.filter_record.alternate_amount_24),(0,0,0))
        self.assertEqual((r.x_04,r.y_08),(0xffffffff,7));self.assertFalse(p.native_execution_verified)

    def test_decoder_error_retains_owned_prefix_without_complete_table(self):
        class Codec:
            def __init__(self,cp):pass
            def decode(self,value):
                if value==b'FAIL':raise ValueError('explicit decode gap')
                return value.decode('ascii')
        s=snapshot(slot_ids=(1,2,0,0),items={0:M(1,1,0,b'Good'),1:M(1,1,0,b'FAIL')})
        p=prepare_quick_table(s,codec_factory=Codec)
        self.assertFalse(p.complete);self.assertEqual(p.failed_record,1)
        self.assertEqual(len(p.quick_values.records),2);self.assertEqual(len(p.display_records),1)
        self.assertEqual(p.status,'own_decode_failed')

    def test_snapshot_is_immutable_and_initial_raw_flag_preserved(self):
        data=complete_actors();data[1]=actor(buy_first_eax=2,buy_second_eax=2)
        s=QuickScanSnapshot(data,1254,255);data.clear()
        class Codec:
            def __init__(self,cp):pass
            def decode(self,value):return value.decode('ascii')
        p=prepare_quick_table(s,codec_factory=Codec)
        self.assertTrue(p.complete);self.assertEqual(p.display_records[0].filter_record.direction_0c,255)
        with self.assertRaises(TypeError):s.actors[1]=A(pointer=0)

    def test_snapshot_and_codepage_contract(self):
        with self.assertRaises(ValueError):QuickScanSnapshot({},0)
        with self.assertRaises(ValueError):prepare_quick_table({})


if __name__=='__main__':unittest.main()
