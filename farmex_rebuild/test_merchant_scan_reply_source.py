import struct
import unittest
from dataclasses import replace
from item_lookup import BaseItemLookupObservation as B,ExtensionLookupObservation as E
from item_name import ItemNameObservation as N
from merchant_actor_metadata import MerchantActorObservation as A,MerchantCoordinateObservation as C
from merchant_item_metadata import MerchantItemObservation as I
from merchant_scan_reply_source import ScanReplySource,MerchantReplySourceFrame
from merchant_scan_reply_frame import ScanReplyObservation,MerchantScanReplyFrame
from merchant_reply import MerchantReplyState
from direct_chat_packets import QueueAttempt


def padded(data):return data+b'\0'+b'x'*(254-len(data))


def actor(**kw):
    args=dict(lookup_returned=True,actor_pointer=0x1000,x=C(0x10,True,True,825),
        y=C(0x14,True,True,0xffffffff),storage_offset_dword=0x18,storage_dword=4,
        initial_name_offset_dword=0x20,initial_name_dword=0,inline_name_offset_dword=0x30,
        readable=True,copied_bytes=padded(b'Seller'))
    args.update(kw);return A(**args)


def item(name=b'Bow',**kw):
    args=dict(base=B(first_variant_byte=1,function_target=0x9000,call_returned=True,result_eax=0x2000),
        resolver_type_raw=2,extension=E(0x4000,0x5000,0x9004,True,0x3000),
        name_category_byte=11,extension_id_dword=107,
        name=N(metadata_category=2,storage_dword=4,pointer_dword=0,bad_read_result=0,captured=padded(name)),
        stored_category_byte=12)
    args.update(kw);return I(**args)


def packet(count=1):
    return b'\x68\x23\x01\x34\x12'+struct.pack('<IHHI',123456,2,99,1000)*count+b'\0'*(12*(12-count))


class AsciiCodec:
    def __init__(self,cp):self.cp=cp
    def decode(self,data):return data.decode('ascii')


class ReplySourceTests(unittest.TestCase):
    def frame(self,data=None):return MerchantReplySourceFrame(packet() if data is None else data,codec_factory=AsciiCodec)

    def test_source_lookups_copies_derive_names_and_distinct_categories(self):
        f=self.frame();p=f.advance(ScanReplySource(actor(),{0:item()},1254))
        self.assertTrue(p.complete)
        record=p.results.records[0].display
        self.assertEqual((record.seller,record.item_name,record.x_04,record.y_08),('Seller','Bow(+7) (Reverse)',825,0xffffffff))
        self.assertEqual(record.filter_record.category_1c,12)
        self.assertEqual(record.filter_record.original_name_ansi,b'Bow(+7) (Reverse)')
        self.assertEqual(p.item_plans[0][1].name.family,'lookup')
        self.assertFalse(p.native_execution_verified or p.source_parser_return_verified)

    def test_actor_gate_prevents_all_item_and_codepage_consumption(self):
        p=self.frame().advance(ScanReplySource(actor(lookup_returned=False),{0:item()},1254))
        self.assertFalse(p.complete);self.assertEqual(p.item_plans,())
        self.assertEqual(dict(p.consumed_observations),{})

    def test_partial_actor_freezes_reached_x_but_not_unreached_y_eax(self):
        f=self.frame()
        p=f.advance(ScanReplySource(actor(y=C(0x14,True,False,11)),{0:item()},1254))
        self.assertEqual(p.actor_plan.coordinate_eax_prefix,(825,))
        self.assertNotIn(('actor','y','ftol_eax'),p.consumed_observations)
        p=f.advance(ScanReplySource(actor(actor_pointer=0x9999,x=C(99,True,True,99),
            y=C(99,True,True,0xfffffffe)),{0:item()},1254))
        self.assertTrue(p.complete)
        self.assertEqual((p.results.records[0].display.x_04,p.results.records[0].display.y_08),(825,0xfffffffe))
        self.assertEqual(p.consumed_observations[('actor','actor_pointer')],0x1000)

    def test_missing_copy_can_arrive_later_without_requiring_prior_fields_again(self):
        f=self.frame();a=actor(copied_bytes=None)
        p=f.advance(ScanReplySource(a,{0:item()},1254))
        self.assertFalse(p.complete);self.assertEqual(p.item_plans,())
        p=f.advance(ScanReplySource(A(copied_bytes=padded(b'Later')),{0:item()},1254))
        self.assertTrue(p.complete);self.assertEqual(p.results.records[0].display.seller,'Later')

    def test_short_item_copy_is_not_frozen_as_a_complete_range(self):
        f=self.frame();i=item()
        p=f.advance(ScanReplySource(actor(),{0:replace(i,name=replace(i.name,captured=b'Bo'))},1254))
        self.assertFalse(p.complete)
        self.assertNotIn(('item',0,'name','captured'),p.consumed_observations)
        self.assertNotIn(('item',0,'stored_category_byte'),p.consumed_observations)
        p=f.advance(ScanReplySource(items={0:I(name=N(captured=padded(b'Complete')),stored_category_byte=12)}))
        self.assertTrue(p.complete)
        self.assertEqual(p.results.records[0].display.item_name,'Complete(+7) (Reverse)')

    def test_base_branch_and_target_frozen_but_normal_false_and_eax_not_frozen(self):
        f=self.frame();i=item()
        b=replace(i.base,call_returned=False,result_eax=9)
        p=f.advance(ScanReplySource(actor(),{0:replace(i,base=b)},1254))
        self.assertNotIn(('item',0,'base','result_eax'),p.consumed_observations)
        p=f.advance(ScanReplySource(items={0:item(base=B(first_variant_byte=2,
            function_target=0,call_returned=True,result_eax=0x2000))}))
        self.assertTrue(p.complete)
        plan=p.item_plans[0][1]
        self.assertEqual((plan.base.target,plan.base.ecx),(0x9000,0))
        self.assertNotIn(('item',0,'base','second_variant_byte'),p.consumed_observations)

    def test_later_slot_remains_fresh_while_first_slot_metadata_waits(self):
        f=self.frame(packet(2));i=item()
        p=f.advance(ScanReplySource(actor(),{0:replace(i,name=replace(i.name,captured=None)),1:item(b'Old')},1254))
        self.assertFalse(p.complete)
        self.assertFalse(any(k[:2]==('item',1) for k in p.consumed_observations))
        p=f.advance(ScanReplySource(items={0:item(b'First'),1:item(b'Fresh')}))
        self.assertTrue(p.complete)
        self.assertEqual([r.display.item_name for r in p.results.records],['First(+7) (Reverse)','Fresh(+7) (Reverse)'])

    def test_completed_record_and_metadata_do_not_repeat_on_later_slot_gap(self):
        f=self.frame(packet(2));p=f.advance(ScanReplySource(actor(),{0:item()},1254))
        self.assertFalse(p.complete);self.assertEqual(len(p.results.records),1)
        p=f.advance(ScanReplySource(actor(copied_bytes=padded(b'Changed')),
            {0:item(b'Changed'),1:item(b'Second')},1254))
        self.assertTrue(p.complete);self.assertEqual(len(p.results.records),2)
        self.assertEqual([r.display.seller for r in p.results.records],['Seller','Seller'])
        self.assertEqual(p.results.records[0].display.item_name,'Bow(+7) (Reverse)')
        self.assertIs(f.advance(),p)

    def test_codepage_is_explicit_and_only_read_when_text_decode_reached(self):
        f=self.frame();p=f.advance(ScanReplySource(actor(),{0:item()}))
        self.assertFalse(p.complete);self.assertIn('Explicit source codepage',p.status)
        self.assertNotIn(('code_page',),p.consumed_observations)
        p=f.advance(ScanReplySource(items={0:item()},code_page=1254))
        self.assertTrue(p.complete);self.assertEqual(p.consumed_observations[('code_page',)],1254)

    def test_empty_names_need_no_codepage_and_rejected_reads_skip_copy_fields(self):
        i=item();i=replace(i,name=replace(i.name,bad_read_result=1,captured=None))
        p=self.frame().advance(ScanReplySource(actor(readable=False,copied_bytes=None),{0:i}))
        self.assertTrue(p.complete);self.assertNotIn(('code_page',),p.consumed_observations)
        self.assertNotIn(('actor','copied_bytes'),p.consumed_observations)
        self.assertNotIn(('item',0,'name','captured'),p.consumed_observations)

    def test_zero_base_result_does_not_invent_empty_item_or_helper_return(self):
        i=item();i=replace(i,base=replace(i.base,result_eax=0))
        p=self.frame().advance(ScanReplySource(actor(),{0:i},1254))
        self.assertFalse(p.complete);self.assertEqual(p.results.records,())
        self.assertIn('name:',p.status)

    def test_empty_reply_and_length_rejection_skip_source_production(self):
        for data in (packet(0),b'\x68\x23\x01'):
            p=self.frame(data).advance()
            self.assertTrue(p.complete);self.assertIsNone(p.actor_plan)
            self.assertEqual(p.item_plans,());self.assertEqual(dict(p.consumed_observations),{})

    def test_source_frame_still_requires_parser_and_finish_returns(self):
        f=MerchantScanReplyFrame(packet(),MerchantReplyState(scan_pending_byte=1))
        p=f.advance(ScanReplyObservation(source=ScanReplySource(actor(),{0:item()},1254)))
        self.assertEqual(p.status,'needs_parser_return');self.assertTrue(p.source_production.complete)
        self.assertEqual(p.queue.records,());self.assertEqual(p.state.scan_pending_byte,1)
        p=f.advance(ScanReplyObservation(parse_returned=True,finish_setup_returned=True,
            attempt=QueueAttempt(1,10,True),finish_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.state.scan_pending_byte,0)
        self.assertEqual(p.queue.records[0].payload,b'\x68\x27')

    def test_metadata_mode_cannot_bypass_an_inflight_source_gap(self):
        from merchant_scan_results import MerchantActorMetadata
        f=MerchantScanReplyFrame(packet(),MerchantReplyState(scan_pending_byte=1))
        f.advance(ScanReplyObservation(source=ScanReplySource()))
        with self.assertRaises(ValueError):f.advance(ScanReplyObservation(actor=MerchantActorMetadata('shortcut',1,2)))
        with self.assertRaises(ValueError):ScanReplyObservation(actor=MerchantActorMetadata('',1,2),source=ScanReplySource())


if __name__=='__main__':unittest.main()
