import unittest
from dataclasses import replace
from source_name_mutation import NameMutationObservation as Obs,plan_name_mutation
from source_name_lists import (NameListsState,NameListRefreshObservation,NameListRefreshRow,
                               plan_name_list_refresh)

class NameMutationTests(unittest.TestCase):
    def refresh(self,**changes):
        values=dict(scratch_init_returned=True,black_reset_returned=True,white_reset_returned=True,
            black_after_reset=(),white_after_reset=(),black_rows=(NameListRefreshRow(0,0),),
            white_rows=(NameListRefreshRow(0,0),),final_cleanup_returned=True)
        values.update(changes)
        return plan_name_list_refresh(NameListsState(),NameListRefreshObservation(**values))
    def test_four_callers_use_correct_control_and_slot(self):
        for kind,action,caller,offset,slot in (
            ('white','clear',0x423cac,0x3d4,0x13c),('black','clear',0x423cd8,0x3f0,0x13c),
            ('white','remove',0x423d04,0x3d4,0x148),('black','remove',0x423d30,0x3f0,0x148)):
            p=plan_name_mutation(kind,action,('A',),Obs(True,(),self.refresh(),True))
            self.assertTrue(p.complete);self.assertEqual(p.caller,caller)
            self.assertEqual(p.steps[0],('virtual_call',kind,offset,slot));self.assertEqual(p.state,())
    def test_noop_and_empty_still_require_refresh_return(self):
        for rows in ((),('A','A')):
            p=plan_name_mutation('white','remove',rows,Obs(True,rows))
            self.assertFalse(p.complete);self.assertIn(('call',0x46c3b8,0x5690f8),p.steps)
            self.assertTrue(plan_name_mutation('white','remove',rows,Obs(True,rows,refresh_returned=True)).complete)
    def test_missing_mutation_receipt_does_not_reach_refresh(self):
        for receipt in (None,False):
            p=plan_name_mutation('black','clear',('A',),Obs(receipt,(),self.refresh(),True))
            self.assertFalse(p.complete);self.assertIsNone(p.refresh_execution)
            self.assertEqual(p.prospective,('A',));self.assertFalse(any(s[0]=='call' for s in p.steps))
    def test_return_does_not_invent_post_state(self):
        p=plan_name_mutation('white','clear',('A',),Obs(True,refresh_returned=True))
        self.assertFalse(p.complete);self.assertIn('post-mutation',p.missing)
    def test_refresh_completion_does_not_replace_independent_receipt(self):
        p=plan_name_mutation('black','remove',('A','A'),Obs(True,('A',),self.refresh()))
        self.assertFalse(p.complete);self.assertEqual(p.state,('A','A'))
        self.assertEqual(p.prospective,('A',));self.assertIsNotNone(p.refresh_execution)
    def test_incomplete_bound_refresh_blocks_even_with_receipt(self):
        refresh=self.refresh(final_cleanup_returned=None)
        p=plan_name_mutation('white','clear',('A',),Obs(True,(),refresh,True))
        self.assertFalse(p.complete);self.assertIn('bound refresh',p.missing)
        self.assertEqual(p.prospective,());self.assertFalse(p.native_execution_verified)
    def test_fresh_refresh_rows_not_assumed_equal_to_post_mutation(self):
        refresh=self.refresh(white_after_reset=(b'fresh',))
        p=plan_name_mutation('white','clear',('A',),Obs(True,(),refresh,True))
        self.assertTrue(p.complete);self.assertEqual(p.state,())
        self.assertEqual(p.refresh_execution.state.white,(b'fresh',))
    def test_input_contracts(self):
        for value in ([],(b'A',)):
            with self.assertRaises(ValueError):Obs(rows_after_mutation=value)
        with self.assertRaises(ValueError):Obs(mutation_returned=1)
        with self.assertRaises(ValueError):Obs(refresh_execution=True)
        with self.assertRaises(ValueError):plan_name_mutation('white','add',(),Obs())

if __name__=='__main__':unittest.main()
