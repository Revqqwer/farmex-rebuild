import unittest
from name_list_controls import edit_name_list as edit,LIST_PATHS,TEXT_PATHS,BUTTON_ACTIONS

class NameListControlTests(unittest.TestCase):
    def test_add_empty_and_exact_duplicate_do_not_mutate(self):
        for text in ('','abc'):
            p=edit('white','add',('abc',),text=text);self.assertFalse(p.changed);self.assertEqual(p.rows,('abc',))
    def test_add_preserves_case_space_order_and_unicode(self):
        p=edit('black','add',('abc','abc'),text=' ABC ')
        self.assertEqual(p.rows,('abc','abc',' ABC '));self.assertEqual(p.index,2)
        p=edit('white','add',(),text='İsim ŞĞ');self.assertEqual(p.rows,('İsim ŞĞ',));self.assertFalse(p.native_execution_verified)
    def test_utf16_surrogate_equivalent_is_duplicate_without_normalization(self):
        self.assertFalse(edit('white','add',('\U0001f600',),text='\ud83d\ude00').changed)
        self.assertTrue(edit('white','add',('\u00e9',),text='e\u0301').changed)
    def test_remove_selected_occurrence_not_all_duplicates(self):
        p=edit('white','remove',('a','b','a'),selected_index=2);self.assertEqual(p.rows,('a','b'));self.assertEqual(p.index,2)
    def test_remove_missing_or_invalid_selection_is_noop(self):
        for i in (None,-1,2):self.assertFalse(edit('black','remove',('a',),selected_index=i).changed)
    def test_clear_repeated_and_add_after_clear(self):
        p=edit('white','clear',('a','b'));self.assertTrue(p.changed);self.assertEqual(p.rows,())
        self.assertFalse(edit('white','clear',p.rows).changed)
        self.assertTrue(edit('white','add',p.rows,text='a').changed)
    def test_paths_and_action_types(self):
        self.assertEqual(set(LIST_PATHS),set(TEXT_PATHS));self.assertEqual(len(BUTTON_ACTIONS),4)
        with self.assertRaises(ValueError):edit('wrong','add',(),text='x')
        with self.assertRaises(ValueError):edit('white','add',[],text='x')
        with self.assertRaises(ValueError):edit('white','remove',('a',),selected_index=True)
        with self.assertRaises(ValueError):edit('white','add',(),text=None)

if __name__=='__main__':unittest.main()
