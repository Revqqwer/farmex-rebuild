import unittest
from quest_row import QuestRow
from quest_compare import QuestCompareFrame,QuestCompareObservation as Observation,plan_quest_alpha_sort,sort_quest_rows_owned


def receipts(**changes):
    result={label:True for label,helper in QuestCompareFrame.STEPS if helper is not None}
    result.update(changes);return result


def row(level,caption='0',name='Quest'):return QuestRow(caption,(level,name))


class QuestCompareTests(unittest.TestCase):
    def test_compares_numeric_first_subitems_ignoring_caption_and_name(self):
        f=QuestCompareFrame(row('9','999','Z'),row('27','1','A'),use_owned_integer_model=True)
        p=f.advance(Observation(receipts()))
        self.assertEqual((p.complete,p.signed_result,p.result_written),(True,-18,True))
        self.assertFalse(p.sorting_verified)

    def test_dword_subtraction_wrap_is_not_normalized_to_sign(self):
        f=QuestCompareFrame(row('a'),row('b'))
        p=f.advance(Observation(receipts(),0x80000000,1))
        self.assertEqual((p.result_dword,p.signed_result),(0x7fffffff,0x7fffffff))

    def test_missing_second_parse_keeps_previous_result_and_cached_first(self):
        f=QuestCompareFrame(row('5'),row('2'),previous_result=77)
        p=f.advance(Observation(receipts(),5))
        self.assertEqual((p.result_dword,p.result_written,p.needed),(77,False,('second_parse_dword',)))
        p=f.advance(Observation(receipts(),999,2))
        self.assertEqual(p.result_dword,3)

    def test_result_write_precedes_second_then_first_cleanup(self):
        f=QuestCompareFrame(row('5'),row('2'),use_owned_integer_model=True)
        p=f.advance(Observation(receipts(second_cleanup=False)))
        self.assertEqual((p.complete,p.result_dword,p.result_written),(False,3,True))
        p=f.advance(Observation({'second_cleanup':True}))
        self.assertEqual(p.needed,('first_cleanup',))
        self.assertEqual(p.result_dword,3)
        self.assertTrue(f.advance(Observation(receipts())).complete)

    def test_first_getter_gap_does_not_reach_parser_or_second_getter(self):
        f=QuestCompareFrame(row('5'),row('2'))
        p=f.advance(Observation(receipts(first_text_span=False),5,2))
        self.assertEqual(p.needed,('first_text_span',))
        self.assertEqual(f.calls,[('SubItems.Strings[0]','first_text_span')])

    def test_owned_invalid_integer_does_not_become_zero(self):
        f=QuestCompareFrame(row('bad'),row('2'),previous_result=99,use_owned_integer_model=True)
        p=f.advance(Observation(receipts()))
        self.assertEqual((p.status,p.result_dword,p.result_written),('needs_native_StrToInt_exception_path',99,False))
        self.assertFalse(any(label=='second_text_span' for _,label in f.calls))

    def test_missing_subitem_does_not_become_zero_or_name(self):
        f=QuestCompareFrame(QuestRow('9'),row('2'),use_owned_integer_model=True)
        p=f.advance(Observation(receipts()))
        self.assertEqual((p.status,p.needed,p.result_written),('needs_owned_subitem',('first',0),False))

    def test_parser_normal_return_is_separate_from_captured_eax(self):
        f=QuestCompareFrame(row('5'),row('2'))
        p=f.advance(Observation(receipts(first_parse=False),5,2))
        self.assertEqual(p.needed,('first_parse',));self.assertFalse(p.result_written)
        p=f.advance(Observation(receipts(),5,2))
        self.assertTrue(p.complete)
        self.assertEqual(len(f.calls),len(f.STEPS)-1)

    def test_equal_levels_write_zero_and_terminal_resume_does_not_repeat(self):
        f=QuestCompareFrame(row('5','0'),row('5','1'),use_owned_integer_model=True)
        p=f.advance(Observation(receipts()))
        self.assertEqual(p.result_dword,0);self.assertTrue(p.result_written)
        self.assertIs(f.advance(),p)

    def test_alpha_sort_handle_and_result_do_not_certify_order(self):
        self.assertFalse(plan_quest_alpha_sort().complete)
        self.assertEqual(plan_quest_alpha_sort(False).result_bool,False)
        p=plan_quest_alpha_sort(True,123,1)
        self.assertEqual((p.message,p.send_requested,p.result_bool),(0x1030,True,True))
        self.assertFalse(p.sorted_order_verified)

    def test_owned_sort_orders_level_numerically_and_keeps_equal_input_order(self):
        rows=(row('27','a'),row('5','b'),row('5','c'),row('100','d'))
        p=sort_quest_rows_owned(rows)
        self.assertEqual((p.complete,p.permutation),(True,(1,2,0,3)))
        self.assertEqual(tuple(r.caption for r in p.rows),('b','c','a','d'))
        self.assertEqual(tuple(r.caption for r in rows),('a','b','c','d'))
        self.assertFalse(p.sorting_verified)

    def test_owned_sort_does_not_guess_outside_byte_level_domain(self):
        for text in ('-1','256','$80000000'):
            with self.subTest(text=text):
                p=sort_quest_rows_owned((row(text),))
                self.assertFalse(p.complete);self.assertIsNone(p.rows)
                self.assertEqual(p.status,'outside_producer_level_domain')

    def test_owned_sort_invalid_integer_and_missing_subitem_are_incomplete(self):
        self.assertFalse(sort_quest_rows_owned((row('bad'),)).complete)
        self.assertEqual(sort_quest_rows_owned((QuestRow('9'),)).status,'needs_subitem')

    def test_owned_empty_sort_has_explicit_empty_permutation(self):
        p=sort_quest_rows_owned(())
        self.assertEqual((p.complete,p.rows,p.permutation),(True,(),()))


if __name__=='__main__':unittest.main()
