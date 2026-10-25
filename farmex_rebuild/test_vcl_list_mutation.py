import unittest
from dataclasses import replace
from vcl_list_mutation import VclMutationObservation as Obs,VclDeleteSample as Sample,plan_vcl_mutation as plan
from source_name_mutation import NameMutationObservation,plan_name_mutation

class VclMutationTests(unittest.TestCase):
    def single(self,**kw):
        fields=dict(multi_select_byte=0,first_index_returned=True,first_index_dword=0,
            second_index_returned=True,second_index_dword=1,samples=(Sample(1,delete_returned=True,rows_after_delete=('A',)),))
        fields.update(kw);return Obs(**fields)
    def test_two_fresh_indices_and_second_minus_one_not_guarded(self):
        p=plan('remove',('A','B'),self.single());self.assertTrue(p.complete)
        self.assertEqual(p.delete_indices,(1,));self.assertEqual(p.state,('A',))
        p=plan('remove',('A',),self.single(second_index_dword=0xffffffff,
            samples=(Sample(0xffffffff,delete_returned=True,rows_after_delete=('A',)),)))
        self.assertTrue(p.complete);self.assertEqual(p.delete_indices,(0xffffffff,))
    def test_first_minus_one_skips_second_read_and_delete(self):
        p=plan('remove',('A',),Obs(multi_select_byte=0,first_index_returned=True,first_index_dword=0xffffffff))
        self.assertTrue(p.complete);self.assertEqual(p.delete_indices,());self.assertEqual(p.state,('A',))
    def test_multi_selection_descends_and_preserves_supplied_effects(self):
        p=plan('remove',('A','B','A'),Obs(multi_select_byte=255,count_returned=True,count_dword=3,
            samples=(Sample(2,True,1,True,('A','B')),Sample(1,True,0),Sample(0,True,255,True,('B',)))))
        self.assertTrue(p.complete);self.assertEqual(p.delete_indices,(2,0));self.assertEqual(p.state,('B',))
    def test_signed_count_decrement_and_wrap(self):
        for count in (0,0xffffffff):
            p=plan('remove',('A',),Obs(multi_select_byte=1,count_returned=True,count_dword=count))
            self.assertTrue(p.complete);self.assertEqual(p.delete_indices,())
        p=plan('remove',(),Obs(multi_select_byte=1,count_returned=True,count_dword=0x80000000,
            samples=(Sample(0x7fffffff,True,0),)),iteration_budget=1)
        self.assertFalse(p.complete);self.assertIn('budget',p.missing)
    def test_missing_selection_prefix_does_not_complete_loop(self):
        p=plan('remove',('A','B'),Obs(multi_select_byte=1,count_returned=True,count_dword=2,
            samples=(Sample(1,True,1,True,('A',)),)))
        self.assertFalse(p.complete);self.assertEqual(p.state,('A','B'));self.assertEqual(p.prospective,('A',))
    def test_native_return_does_not_invent_delete_effect(self):
        for field in ('delete_returned','rows_after_delete'):
            o=self.single(samples=(replace(Sample(1,delete_returned=True,rows_after_delete=('A',)),**{field:None}),))
            p=plan('remove',('A','B'),o);self.assertFalse(p.complete)
            self.assertEqual(p.prospective,('A','B'))
    def test_selection_nonreturn_does_not_use_al_or_delete(self):
        p=plan('remove',('A',),Obs(multi_select_byte=1,count_returned=True,count_dword=1,
            samples=(Sample(0,False,1,True,()),)))
        self.assertFalse(p.complete);self.assertEqual(p.delete_indices,())
    def test_clear_calls_items_virtual_without_selection(self):
        p=plan('clear',('A',),Obs(clear_returned=True,rows_after_clear=()))
        self.assertTrue(p.complete);self.assertEqual(p.steps[0],('Items_virtual',0x48))
        self.assertFalse(plan('clear',('A',),Obs(clear_returned=True)).complete)
    def test_parent_bound_identity_and_independent_return(self):
        v=plan('remove',('A','B'),self.single())
        o=NameMutationObservation(mutation_execution=v,refresh_returned=True)
        self.assertFalse(plan_name_mutation('white','remove',('A','B'),o).complete)
        p=plan_name_mutation('white','remove',('A','B'),replace(o,mutation_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.state,('A',))
        with self.assertRaises(ValueError):plan_name_mutation('white','clear',('A','B'),o)
        with self.assertRaises(ValueError):plan_name_mutation('white','remove',('wrong',),o)
        with self.assertRaises(ValueError):plan_name_mutation('white','remove',('A','B'),replace(o,rows_after_mutation=()))
        incomplete=plan('remove',('A','B'),self.single(second_index_returned=None))
        self.assertFalse(plan_name_mutation('white','remove',('A','B'),replace(o,mutation_execution=incomplete,mutation_returned=True)).complete)
    def test_reached_order_and_types(self):
        with self.assertRaises(ValueError):plan('remove',('A','B'),self.single(samples=(Sample(0),)))
        with self.assertRaises(ValueError):Obs(multi_select_byte=True)
        with self.assertRaises(ValueError):Sample(0,selected_al=256)
        with self.assertRaises(ValueError):Obs(samples=[])
        with self.assertRaises(ValueError):plan('clear',(),Obs(),iteration_budget=0)

if __name__=='__main__':unittest.main()
