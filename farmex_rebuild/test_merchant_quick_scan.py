import unittest
from dataclasses import replace
from merchant_quick_scan import QuickActorObservation as A,QuickItemObservation as M,project_quick_scan,format_quick_item_name


def actor(**kw):
    args=dict(pointer=0x1000,active_eax=1,buy_first_eax=0,buy_second_eax=0,entity_id_eax=123,
              x_ftol_eax=0xffffffff,y_ftol_eax=7,seller_ansi=b'Seller',slot_base_word=0x100,
              slot_ids=(1,0,0,0),items={0:M(2,5,0xffffffff,b'Item')})
    args.update(kw);return A(**args)


def complete_actors(**unused):return {i:A(pointer=0) for i in range(1,5001)}


class QuickScanTests(unittest.TestCase):
    def test_exact_inclusive_lookup_range_and_unknown_not_empty(self):
        p=project_quick_scan(complete_actors());self.assertTrue(p.complete)
        self.assertEqual(p.steps[0],('lookup',1));self.assertEqual(p.steps[-1],('lookup',5000))
        self.assertTrue(p.rebuild_requested);self.assertEqual(p.records,())
        q=project_quick_scan({});self.assertEqual(q.needed,('lookup',1));self.assertFalse(q.rebuild_requested)

    def test_zero_pointer_and_low_byte_active_gate_skip_actor_fields(self):
        p=project_quick_scan({1:A(pointer=0),2:A(pointer=5,active_eax=0x100)})
        self.assertEqual(p.needed,('lookup',3));self.assertEqual(p.records,())

    def test_four_cached_slots_on_last_actor_and_zero_record_amounts(self):
        actors=complete_actors();actors[5000]=actor(slot_ids=(1,2,3,4),items={
            0:M(0,1,1,b'Zero'),1:M(1,2,2,b'One'),2:M(11,11,13,b'Eleven'),3:M(12,12,14,b'Twelve')})
        p=project_quick_scan(actors);self.assertTrue(p.complete)
        self.assertEqual([r.item_name_ansi for r in p.records],[b'Zero',b'One',b'Eleven(+3) (Reverse)',b'Twelve (Reverse)'])
        self.assertTrue(all((r.amount_dword,r.alternate_amount_dword,r.price_dword,r.final_flag)==(0,0,0,0) for r in p.records))

    def test_quick_suffix_categories_and_name_family_are_independent(self):
        for category in range(16):
            expected=b'N'
            if category in (2,5,11):expected+=b'(+5)'
            if category in (11,12):expected+=b' (Reverse)'
            self.assertEqual(format_quick_item_name(category,b'N',0xffffffff),expected)
            self.assertEqual(M(category).name_family,'lookup' if category in (0,2,5,11) else 'extension')

    def test_double_read_flag_keeps_prior_byte_and_does_not_normalize(self):
        p=project_quick_scan({1:actor(buy_first_eax=2,buy_second_eax=2)},initial_direction_byte=255)
        self.assertEqual(p.records[0].direction_byte,255)
        q=project_quick_scan({1:actor(buy_first_eax=0x100,buy_second_eax=0x101)})
        self.assertEqual(q.records[0].direction_byte,1)

    def test_unknown_direction_is_not_filled_with_zero(self):
        p=project_quick_scan({1:actor(buy_first_eax=2,buy_second_eax=2)})
        self.assertEqual(p.needed,(1,0,'initial_or_prior_direction_byte'));self.assertEqual(p.records,())
        q=project_quick_scan({1:actor(buy_first_eax=2,buy_second_eax=2,slot_ids=(0,0,0,0))})
        self.assertEqual(q.needed,('lookup',2));self.assertIsNone(q.direction_byte)

    def test_direction_carries_across_actors_without_valid_overwrite(self):
        p=project_quick_scan({1:actor(buy_first_eax=1,buy_second_eax=1),2:actor(buy_first_eax=2,buy_second_eax=0)})
        self.assertEqual([r.direction_byte for r in p.records],[1,1])
        q=project_quick_scan({1:actor(buy_first_eax=1,buy_second_eax=1),2:actor(buy_first_eax=0,buy_second_eax=2)})
        self.assertEqual([r.direction_byte for r in q.records],[1,0])

    def test_second_read_missing_preserves_first_store_but_stops(self):
        p=project_quick_scan({1:actor(buy_second_eax=None)},initial_direction_byte=7)
        self.assertEqual(p.direction_byte,0);self.assertEqual(p.needed,(1,'buy_second_eax'))
        self.assertFalse(any(s[0]=='read_cached_id' for s in p.steps))

    def test_all_four_ID_reads_precede_first_metadata_lookup(self):
        p=project_quick_scan({1:actor(slot_ids=(1,0,0,None),items={})})
        self.assertEqual(p.needed,(1,'slot_id',3));self.assertEqual(p.records,())

    def test_word_slot_offset_wraps_before_adding_actor_pointer(self):
        p=project_quick_scan({1:actor(slot_base_word=0xfffc,slot_ids=(0,0,0,0))})
        reads=[s[3] for s in p.steps if s[0]=='read_cached_id']
        self.assertEqual(reads,[0x10ffc,0x1000,0x1004,0x1008])

    def test_fresh_stored_category_and_raw_coordinates_preserved(self):
        p=project_quick_scan({1:actor(items={0:M(2,12,0xffffffff,b'I\0X')})})
        r=p.records[0];self.assertEqual((r.category_byte,r.extension_digit,r.x_dword,r.y_dword),(12,5,0xffffffff,7))
        self.assertEqual(r.item_name_ansi,b'I\0X(+5)')

    def test_late_metadata_gap_preserves_records_without_requesting_rebuild(self):
        p=project_quick_scan({1:actor(slot_ids=(1,2,0,0))})
        self.assertEqual(len(p.records),1);self.assertEqual(p.needed,(1,'metadata',1))
        self.assertFalse(p.rebuild_requested);self.assertFalse(p.source_helper_returns_verified)

    def test_unused_entity_read_and_seller_are_still_demanded(self):
        p=project_quick_scan({1:actor(entity_id_eax=None)})
        self.assertEqual(p.needed,(1,'entity_id_eax'))
        q=project_quick_scan({1:actor(seller_ansi=None,slot_ids=(0,0,0,0))})
        self.assertEqual(q.needed,(1,'seller_ansi'))

    def test_typed_bounds_and_no_lookup_zero(self):
        with self.assertRaises(ValueError):project_quick_scan({0:A(pointer=0)})
        with self.assertRaises(ValueError):project_quick_scan({},initial_direction_byte=True)
        with self.assertRaises(ValueError):A(slot_ids=(0,)*5)


if __name__=='__main__':unittest.main()
