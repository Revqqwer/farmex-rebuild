import unittest
from dataclasses import replace
from npc_sell_filter import SellFilterObservation,select_sale_item


class SaleFilterTests(unittest.TestCase):
    def observation(self,**changes):
        return replace(SellFilterObservation(0,excluded_4e7c60=False,excluded_index_4e7be8=-1,
                       protect_grade_5622cf=False,list_index_41a5cc=1,list_checked_5622e1=True),**changes)

    def test_selected_regular_row_helper_order(self):
        r=select_sale_item(self.observation())
        self.assertEqual(r.status,'selected');self.assertEqual(r.calls,('004e7c60','004e7be8','0041a5cc'))

    def test_first_exclusion_short_circuits_all_later_observations(self):
        r=select_sale_item(SellFilterObservation(0,excluded_4e7c60=True))
        self.assertEqual(r.status,'skip');self.assertEqual(r.calls,('004e7c60',))

    def test_second_exclusion_uses_exact_minus1_sentinel(self):
        for index in (-2,0,1):
            self.assertEqual(select_sale_item(self.observation(excluded_index_4e7be8=index)).status,'skip')

    def test_list_index0_is_not_mode2_index0(self):
        self.assertEqual(select_sale_item(self.observation(list_index_41a5cc=0,list_checked_5622e1=None)).status,'skip')
        self.assertEqual(select_sale_item(SellFilterObservation(2,mode2_index_47677c=0,mode2_checked=True)).status,'selected')

    def test_mode2_does_not_read_nonmode2_exclusions_or_grade(self):
        r=select_sale_item(SellFilterObservation(2,mode2_index_47677c=1,mode2_checked=True))
        self.assertEqual(r.status,'selected');self.assertEqual(r.calls,('0047677c',))

    def test_mode2_negative_skips_without_checked_field(self):
        for index in (-1,-2):
            self.assertEqual(select_sale_item(SellFilterObservation(2,mode2_index_47677c=index)).status,'skip')

    def test_grade_threshold_equality_protects_but_type3_is_exception(self):
        for extension,typebyte,expected in ((105,2,'skip'),(104,2,'selected'),(105,3,'selected')):
            r=select_sale_item(self.observation(protect_grade_5622cf=True,minimum_grade_5622d0=5,
                                               extension_id=extension,type_byte=typebyte))
            self.assertEqual(r.status,expected)

    def test_lower_grade_does_not_require_unknown_type(self):
        r=select_sale_item(self.observation(protect_grade_5622cf=True,minimum_grade_5622d0=5,extension_id=104))
        self.assertEqual(r.status,'selected')

    def test_protection_disabled_ignores_unknown_grade_fields(self):
        self.assertEqual(select_sale_item(self.observation()).status,'selected')

    def test_unchecked_rows_skip_both_modes(self):
        self.assertEqual(select_sale_item(self.observation(list_checked_5622e1=False)).status,'skip')
        self.assertEqual(select_sale_item(SellFilterObservation(2,mode2_index_47677c=0,mode2_checked=False)).status,'skip')

    def test_missing_required_lookup_never_selects(self):
        self.assertEqual(select_sale_item(SellFilterObservation(2)).status,'needs_observation')
        self.assertEqual(select_sale_item(self.observation(list_checked_5622e1=None)).status,'needs_observation')

    def test_other_modes_follow_regular_branch(self):
        self.assertEqual(select_sale_item(self.observation(mode=1)).status,'selected')
