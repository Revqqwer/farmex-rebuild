import unittest
from upgrade_parameter_ui import read_parameter_text,remember_scroll_text,restore_scroll_text,SCROLL_PATH,WAIT_PATH


class Widget:
    def __init__(self,text):self.text=text
    def winfo_exists(self):return True
    def get(self):return self.text
    def set(self,text):self.text=text


class ParameterTextTests(unittest.TestCase):
    def setUp(self):
        self.values={SCROLL_PATH:0,WAIT_PATH:'20'}
        self.catalog=[dict(path=SCROLL_PATH,properties={'Items.Strings':['Scroll','Other']})]

    def test_actual_widget_text_precedes_profile_and_is_cached(self):
        cache={};widget=Widget('Actual')
        self.assertEqual(read_parameter_text('scroll',self.values,self.catalog,{SCROLL_PATH:widget},cache),'Actual')
        self.assertEqual(cache[SCROLL_PATH],(0,'Actual'))

    def test_hidden_combo_uses_known_text_or_valid_catalog_choice(self):
        self.assertEqual(read_parameter_text('scroll',self.values,self.catalog,{},{}),'Scroll')
        self.assertEqual(read_parameter_text('scroll',self.values,self.catalog,{},{SCROLL_PATH:(0,'Known')}),'Known')
        self.values[SCROLL_PATH]=1
        self.assertEqual(read_parameter_text('scroll',self.values,self.catalog,{},{SCROLL_PATH:(0,'Old')}),'Other')

    def test_unknown_hidden_minus_one_is_not_guessed_empty(self):
        self.values[SCROLL_PATH]=-1
        with self.assertRaises(ValueError):read_parameter_text('scroll',self.values,self.catalog,{},{})
        self.assertEqual(read_parameter_text('scroll',self.values,self.catalog,{},{SCROLL_PATH:(-1,'')}),'')

    def test_counted_custom_text_survives_owned_rerender_when_observed(self):
        self.values[SCROLL_PATH]=-1;cache={};widget=Widget('A\0B')
        remember_scroll_text(self.values,{SCROLL_PATH:widget},cache)
        replacement=Widget('');restore_scroll_text(replacement,self.values,cache)
        self.assertEqual(replacement.text,'A\0B')

    def test_edit_text_is_fresh_from_widget_or_hidden_value(self):
        widget=Widget('21');self.assertEqual(read_parameter_text('wait',self.values,self.catalog,{WAIT_PATH:widget},{}),'21')
        self.values[WAIT_PATH]='22';self.assertEqual(read_parameter_text('wait',self.values,self.catalog,{},{}),'22')

    def test_edit_variable_trace_uses_new_value_before_display_refresh(self):
        self.assertEqual(read_parameter_text('wait',self.values,self.catalog,
            {WAIT_PATH:Widget('20')},{},{WAIT_PATH:Widget('23')}),'23')


if __name__=='__main__':unittest.main()
