import unittest
from dataclasses import replace
from merchant_quick_source import (QuickItemSource as I,QuickActorSource as A,QuickSourceSnapshot,
    produce_quick_item,produce_quick_actor,produce_quick_sources)
from merchant_quick_table import prepare_quick_table
from merchant_actor_metadata import MerchantActorObservation as Actor,MerchantCoordinateObservation as C
from item_lookup import BaseItemLookupObservation as B,ExtensionLookupObservation as E


def item(**kw):
    values=dict(base=B(first_variant_byte=1,function_target=0x9000,call_returned=True,result_eax=0x2000),
        resolver_eax=0x123402,extension=E(0x4000,0x5000,0x9004,True,0x3000),name_category_eax=2,
        extension_id_eax=15,name_storage_eax=4,name_data_eax=0,readable=True,
        captured_bytes=b'Bow\0'.ljust(255,b'\0'),stored_category_eax=5)
    values.update(kw);return I(**values)


def actor(**kw):
    values=dict(actor=Actor(True,0x1000,C(0x10,True,True,0xffffffff),C(0x20,True,True,520),
        0x24,4,8,0,12,True,b'Seller\0'.ljust(255,b'\0')),
        active_offset=1,active_eax=1,first_buy_offset=4,first_buy_eax=0,second_buy_offset=5,second_buy_eax=0,
        entity_offset=8,entity_eax=7,slot_base_word=0x100,slot_ids=(10,0,0,0),items={0:item()})
    values.update(kw);return A(**values)


def all_sources():return dict.fromkeys(range(1,5001),A(actor=Actor(lookup_returned=True,actor_pointer=0)))


class QuickItemSourceTests(unittest.TestCase):
    def test_lookup_name_family_and_normal_lookup_keys(self):
        for category in (0,2,5,11):
            p=produce_quick_item(123456,item(name_category_eax=category))
            self.assertTrue(p.complete);self.assertEqual((p.base.key,p.extension.key),(123000,456))
            self.assertIn(('read_dword','name_storage',0x201c),p.steps)
            self.assertEqual(p.text_request.address,0x200c);self.assertEqual(p.metadata.base_name_ansi,b'Bow')

    def test_extension_name_family_includes_category_one(self):
        for category in (1,3,12):
            p=produce_quick_item(1,item(name_category_eax=category))
            self.assertTrue(p.complete);self.assertIn(('read_dword','name_storage',0x3018),p.steps)
            self.assertEqual(p.text_request.address,0x3008)

    def test_lookup_normals_are_not_inferred_from_EAX(self):
        o=item();p=produce_quick_item(1,replace(o,base=replace(o.base,call_returned=False)))
        self.assertFalse(p.complete);self.assertEqual(p.steps,())
        q=produce_quick_item(1,replace(o,extension=replace(o.extension,call_returned=None)))
        self.assertFalse(q.complete);self.assertFalse(any(s[1]=='name_category' for s in q.steps))

    def test_inline_data_read_still_required_and_pointer_copy_uses_count(self):
        p=produce_quick_item(1,item(name_data_eax=None));self.assertEqual(p.status,'needs_name_data_eax')
        q=produce_quick_item(1,item(name_storage_eax=16,name_data_eax=0x8000,captured_bytes=b'N\0'.ljust(16,b'x')))
        self.assertTrue(q.complete);self.assertEqual((q.text_request.address,q.text_request.byte_count),(0x8000,16))

    def test_readability_and_native_copy_boundary_remain_distinct(self):
        p=produce_quick_item(1,item(readable=False,captured_bytes=None));self.assertTrue(p.complete)
        self.assertEqual(p.metadata.base_name_ansi,b'')
        q=produce_quick_item(1,item(readable=None,captured_bytes=None));self.assertFalse(q.complete)
        r=produce_quick_item(1,item(name_storage_eax=513,name_data_eax=0x8000));self.assertFalse(r.complete)
        self.assertEqual(r.status,'copy:unresolved_native_buffer_overflow')

    def test_missing_stored_category_retains_only_observed_metadata(self):
        p=produce_quick_item(1,item(stored_category_eax=None))
        self.assertFalse(p.complete);self.assertEqual(p.metadata.base_name_ansi,b'Bow')
        self.assertIsNone(p.metadata.stored_category_byte)

    def test_null_base_does_not_fabricate_empty_item(self):
        o=item();p=produce_quick_item(1,replace(o,base=replace(o.base,result_eax=0),resolver_eax=None))
        self.assertFalse(p.complete);self.assertEqual(p.steps,(('read_byte','resolver',4),))

    def test_low_AL_categories_and_independent_record_category(self):
        p=produce_quick_item(1,item(name_category_eax=0xabcd000b,stored_category_eax=0x1234000c))
        self.assertTrue(p.complete)
        self.assertEqual((p.metadata.name_category_byte,p.metadata.stored_category_byte),(11,12))
        self.assertFalse(p.native_execution_verified)


class QuickActorSourceTests(unittest.TestCase):
    def test_lookup_gate_and_empty_result_do_not_consume_actor_fields(self):
        p=produce_quick_actor(1,A(actor=Actor(lookup_returned=False,actor_pointer=0)))
        self.assertFalse(p.complete);self.assertIsNone(p.actor_values.pointer)
        q=produce_quick_actor(1,A(actor=Actor(lookup_returned=True,actor_pointer=0)))
        self.assertTrue(q.complete);self.assertEqual(len(q.steps),1)

    def test_low_AL_active_gate(self):
        p=produce_quick_actor(1,A(actor=Actor(True,0x1000),active_offset=1,active_eax=0x100))
        self.assertTrue(p.complete);self.assertEqual(p.status,'inactive_actor');self.assertIsNone(p.actor_values.seller_ansi)

    def test_fresh_buy_offsets_and_full_actor_copy_to_values(self):
        p=produce_quick_actor(1,actor(first_buy_eax=0x100,second_buy_eax=0x101))
        self.assertTrue(p.complete);self.assertEqual(p.direction_byte,1)
        self.assertIn(('read','first_buy',0x1004),p.steps);self.assertIn(('read','second_buy',0x1005),p.steps)
        self.assertEqual(p.actor_values.seller_ansi,b'Seller')
        self.assertEqual(p.actor_values.items[0].base_name_ansi,b'Bow')

    def test_coordinate_returns_are_independent(self):
        o=actor();a=o.actor
        p=produce_quick_actor(1,replace(o,actor=replace(a,x=replace(a.x,float_reader_returned=False))))
        self.assertFalse(p.complete);self.assertNotIn(('ftol','x'),p.steps)
        q=produce_quick_actor(1,replace(o,actor=replace(a,y=replace(a.y,ftol_returned=False))))
        self.assertFalse(q.complete);self.assertEqual(q.actor_values.x_ftol_eax,0xffffffff)
        self.assertIsNone(q.actor_values.y_ftol_eax)

    def test_fresh_inline_name_offset_and_unused_data_read(self):
        p=produce_quick_actor(1,actor());self.assertEqual(p.text_request.address,0x100c)
        self.assertIn(('read','seller_data',0x1008),p.steps)
        o=actor();q=produce_quick_actor(1,replace(o,actor=replace(o.actor,initial_name_dword=None)))
        self.assertFalse(q.complete);self.assertIsNone(q.text_request)

    def test_all_cached_IDs_precede_item_production(self):
        p=produce_quick_actor(1,actor(slot_ids=(10,0,0,None),items={}))
        self.assertFalse(p.complete);self.assertEqual(p.item_plans,())
        self.assertEqual(p.actor_values.slot_ids,(10,0,0))

    def test_late_item_gap_keeps_produced_prefix(self):
        p=produce_quick_actor(1,actor(slot_ids=(10,11,0,0)))
        self.assertFalse(p.complete);self.assertEqual(len(p.item_plans),2)
        self.assertEqual(p.actor_values.items[0].base_name_ansi,b'Bow')
        self.assertIsNone(p.actor_values.items[1].name_category_byte)

    def test_unknown_flag_stops_after_first_metadata_before_later_slot(self):
        p=produce_quick_actor(1,actor(first_buy_eax=2,second_buy_eax=2,slot_ids=(10,11,0,0),items={0:item(),1:item()}))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_initial_or_prior_direction_byte')
        self.assertEqual(len(p.item_plans),1)


class QuickSourceCompositionTests(unittest.TestCase):
    def test_full_source_to_table_without_manual_final_names(self):
        class Codec:
            def __init__(self,cp):pass
            def decode(self,value):return value.decode('ascii')
        data=all_sources();data[1]=actor();p=prepare_quick_table(QuickSourceSnapshot(data,1254),codec_factory=Codec)
        self.assertTrue(p.complete);self.assertTrue(p.source_production.complete)
        self.assertEqual(p.display_records[0].item_name,'Bow(+5)')
        self.assertEqual(p.display_records[0].filter_record.original_name_ansi,b'Bow(+5)')

    def test_partial_source_holds_decode_and_preserves_raw_records(self):
        def fail(cp):raise AssertionError('decode before source complete')
        p=prepare_quick_table(QuickSourceSnapshot({1:actor()},1254),codec_factory=fail)
        self.assertFalse(p.complete);self.assertEqual(len(p.quick_values.records),1)
        self.assertEqual(p.source_production.status,'needs_actor_source:2')

    def test_carry_across_source_actors_and_stop_before_unknown_later_actor(self):
        data=all_sources();data[1]=actor(first_buy_eax=1,second_buy_eax=1)
        data[2]=actor(first_buy_eax=2,second_buy_eax=0)
        p=produce_quick_sources(QuickSourceSnapshot(data,1254))
        self.assertTrue(p.complete);self.assertEqual(p.direction_byte,1)
        q=produce_quick_sources(QuickSourceSnapshot({1:actor(first_buy_eax=2,second_buy_eax=2),2:actor()},1254))
        self.assertFalse(q.complete);self.assertEqual(len(q.actor_plans),1)

    def test_source_snapshot_contract_and_missing_lookup_is_unknown(self):
        p=produce_quick_sources(QuickSourceSnapshot({}))
        self.assertFalse(p.complete);self.assertEqual(dict(p.actors),{})
        with self.assertRaises(ValueError):QuickSourceSnapshot({0:actor()})
        with self.assertRaises(ValueError):produce_quick_item(0,item())


if __name__=='__main__':unittest.main()
