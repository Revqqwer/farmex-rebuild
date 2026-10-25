import unittest
from merchant_search_field import plan_search_focus as plan,PLACEHOLDER,GRAY_TEXT
from merchant_result_filter import MerchantResultRecord as R,MerchantFilterSelection as S,filter_merchant_results


class MerchantSearchFieldTests(unittest.TestCase):
    def test_enter_only_replaces_exact_placeholder_and_sets_black(self):
        p=plan(PLACEHOLDER,GRAY_TEXT,'enter')
        self.assertTrue(p.changed)
        self.assertEqual((p.text,p.color,p.rebuild_requested),('',0,False))
        self.assertFalse(plan(PLACEHOLDER.upper(),GRAY_TEXT,'enter').changed)

    def test_enter_nonplaceholder_leaves_color_and_text(self):
        p=plan('sword',GRAY_TEXT,'enter')
        self.assertEqual((p.changed,p.text,p.color),(False,'sword',GRAY_TEXT))

    def test_exit_empty_restores_placeholder_gray_then_requests_rebuild(self):
        p=plan('',0,'exit')
        self.assertTrue(p.changed and p.rebuild_requested)
        self.assertEqual((p.text,p.color),(PLACEHOLDER,GRAY_TEXT))

    def test_exit_nonempty_has_no_rebuild_and_no_trimming(self):
        for value in ('sword',' ','\0'):
            p=plan(value,0,'exit')
            self.assertFalse(p.changed or p.rebuild_requested)
            self.assertEqual(p.text,value)

    def test_color_gate_bypasses_placeholder_and_does_not_mean_font_style(self):
        record=R(0,1,1,1)
        self.assertTrue(filter_merchant_results((record,),S('Selling Merchant','Tümü',GRAY_TEXT,28)).complete)
        self.assertEqual(filter_merchant_results((record,),S('Selling Merchant','Tümü',0,28)).status,'needs_normalized_search')

    def test_utf16_equality_preserves_units_and_embedded_nul(self):
        self.assertTrue(plan('\ud83d\ude00',GRAY_TEXT,'enter','\U0001f600').changed)
        self.assertFalse(plan(PLACEHOLDER+'\0',GRAY_TEXT,'enter').changed)

    def test_contracts(self):
        with self.assertRaises(ValueError):plan('',-1,'exit')
        with self.assertRaises(ValueError):plan('',0,'other')
        with self.assertRaises(ValueError):plan(None,0,'enter')


if __name__=='__main__':unittest.main()
