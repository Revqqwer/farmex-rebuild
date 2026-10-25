import unittest
from dataclasses import replace
from merchant_scan_collection import *

def empty_probes():return {i:MerchantProbe(0) for i in range(5001)}
def merchant(entity=42,kind=0,dist=9.5,**kw):
    args=dict(pointer=123,active_byte=1,x_float=1.9,y_float=-1.9,buy_byte=kind,distance_after_truncation=dist,entity_id_dword=entity);args.update(kw);return MerchantProbe(**args)

class MerchantTests(unittest.TestCase):
    def test_inclusive5000_and_distance_equality(self):
        p=empty_probes();p[5000]=merchant();d=collect_merchants(p,True,False)
        self.assertEqual(d.status,'collected');self.assertEqual(d.collected_count,1);self.assertEqual(d.state.queue,(MerchantRecord(42,123,0),))
    def test_initial_queue_cleared_visited_retained(self):
        st=MerchantCollectionState((MerchantRecord(7,1,0),),(42,),True)
        p=empty_probes();p[0]=merchant(42)
        d=collect_merchants(p,True,True,st)
        self.assertEqual(d.state.queue,());self.assertEqual(d.state.visited_ids,(42,));self.assertTrue(d.state.awaiting_merchant_reply)
    def test_low16_duplicate_suppression_inside_scan(self):
        p=empty_probes();p[0]=merchant(0x1002a);p[1]=merchant(42)
        d=collect_merchants(p,True,True);self.assertEqual(d.collected_count,1);self.assertEqual(d.state.visited_ids,(42,))
    def test_buy_type_exact_one_and_filter_matrix(self):
        for kind,buy in ((0,0),(1,1),(2,0),(255,0)):
            for normal_enabled,buy_enabled in ((False,False),(False,True),(True,False),(True,True)):
                p=empty_probes();p[0]=merchant(kind=kind)
                d=collect_merchants(p,normal_enabled,buy_enabled)
                expected=buy_enabled if buy else normal_enabled
                self.assertEqual(d.collected_count,int(expected))
                if expected:self.assertEqual(d.state.queue[0].buy_flag,buy)
    def test_distant_inactive_and_null_skip_unneeded_fields(self):
        p=empty_probes();p[0]=MerchantProbe(0);p[1]=MerchantProbe(123,active_byte=0);p[2]=merchant(dist=9.50001,entity_id_dword=None)
        self.assertEqual(collect_merchants(p,None,None).collected_count,0)
    def test_unknown_preserves_partial_queue(self):
        p={0:merchant()};d=collect_merchants(p,True,True)
        self.assertEqual(d.status,'needs_observation');self.assertEqual(d.stopped_probe,1);self.assertEqual(len(d.state.queue),1)
    def test_unknown_coordinate_and_overflow_failclosed(self):
        p=empty_probes();p[0]=merchant(x_float=None);self.assertEqual(collect_merchants(p,True,True).status,'needs_observation')
        p[0]=merchant(x_float=1e30);self.assertIn('overflow',collect_merchants(p,True,True).reason)
    def test_fifo_payload_and_steam_offsets(self):
        st=MerchantCollectionState((MerchantRecord(0x1234,100,0),MerchantRecord(55,200,1)),(0x1234,55))
        d=consume_merchant_head(st,True,True,2)
        self.assertEqual(d.request_bytes,bytes.fromhex('68113412'));self.assertEqual(d.target_pointer_offsets,(0x698,0x17c));self.assertTrue(d.state.awaiting_merchant_reply)
        self.assertEqual(d.state.queue,(MerchantRecord(55,200,1),))
        d=consume_merchant_head(d.state,True,True,1)
        self.assertEqual(d.request_bytes,bytes.fromhex('68513700'));self.assertEqual(d.target_pointer_offsets,(0x6ac,0x178))
    def test_disabled_record_popped_without_request_or_variant(self):
        st=MerchantCollectionState((MerchantRecord(4,9,0),),(4,),True)
        d=consume_merchant_head(st,False,None,None)
        self.assertEqual(d.status,'discarded_disabled_kind');self.assertEqual(d.state.queue,());self.assertIsNone(d.request_bytes);self.assertTrue(d.state.awaiting_merchant_reply)
    def test_empty_queue_and_recheck_bounds_exception(self):
        self.assertEqual(consume_merchant_head(MerchantCollectionState(),None,None).status,'queue_empty')
        st=MerchantCollectionState((MerchantRecord(4,9,0),))
        d=consume_merchant_head(st,True,True,1,0);self.assertEqual(d.status,'source_bounds_exception');self.assertEqual(d.state,st)
    def test_consumer_unknown_mode_keeps_head(self):
        st=MerchantCollectionState((MerchantRecord(4,9,1),))
        d=consume_merchant_head(st,True,None,1);self.assertEqual(d.status,'needs_observation');self.assertEqual(d.state,st)
        d=consume_merchant_head(st,True,True,None);self.assertEqual(d.status,'needs_observation');self.assertEqual(d.state,st)
    def test_vendor_export_not_fabricated(self):
        d=plan_vendor_txt_export((('SYNTHETIC','Item','1','100'),))
        self.assertEqual(d.status,'needs_vendor_format');self.assertEqual(d.row_count,1)
    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):MerchantProbe(True)
        with self.assertRaises(ValueError):MerchantProbe(0,active_byte=256)
        with self.assertRaises(ValueError):collect_merchants({5001:MerchantProbe(0)},True,True)
        with self.assertRaises(ValueError):MerchantRecord(65536,0,0)
        with self.assertRaises(ValueError):consume_merchant_head(MerchantCollectionState(),1,True)

if __name__=='__main__':unittest.main()
