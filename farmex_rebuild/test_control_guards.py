import json,unittest
from pathlib import Path
from dataclasses import replace
from profiles import Profiles
from control_guards import *

class ControlGuardTests(unittest.TestCase):
    def config(self,np=0,coins=0,level=0,threshold=100,level_limit=54):
        raw=threshold&0xffffffffffffffff
        return ControlGuardConfiguration({0xbf:np,0xc0:coins,0xc8:raw&0xffffffff,0xcc:raw>>32,0xd0:level,0xd4:level_limit})
    def obs(self,**kw):return replace(ControlGuardObservation(stop_returned=True,town_returned=True),**kw)

    def test_actual_profile_defaults_compile_without_mutation(self):
        catalog=json.loads(Path(__file__).with_name('ui_model.json').read_text(encoding='utf-8'))
        p=Profiles(catalog);values=dict(p.defaults)
        c=compile_control_guards(values)
        self.assertEqual(c.fields[0xc8],1000000);self.assertEqual(c.fields[0xcc],0)
        self.assertEqual(c.fields[0xd4],54)
        self.assertTrue(all(path in values for path in CONTROL_GUARD_INPUTS))

    def test_disabled_queries_are_not_required_and_later_function_is_unclaimed(self):
        p=plan_control_guards(self.config(),ControlGuardObservation())
        self.assertTrue(p.complete);self.assertFalse(p.source_return_planned)
        self.assertEqual(p.calls,());self.assertEqual(p.next_address,0x459071)

    def test_np_priority_and_stop_before_town(self):
        p=plan_control_guards(self.config(1,1,1),self.obs(np_462718=0))
        self.assertEqual(p.status,'np_zero_stop_town')
        self.assertEqual(p.calls,(('00462718',()),('0040ae0c',(0x561f34,0)),('00465678',())))
        self.assertFalse(p.native_execution_verified)

    def test_missing_normal_returns_preserve_ordered_call_prefix(self):
        p=plan_control_guards(self.config(np=1),self.obs(np_462718=0,stop_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.calls[-1][0],'0040ae0c')
        p=plan_control_guards(self.config(np=1),self.obs(np_462718=0,town_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.calls[-1][0],'00465678')

    def test_missing_query_is_not_zero(self):
        p=plan_control_guards(self.config(np=1),ControlGuardObservation())
        self.assertEqual(p.missing,'00462718 DWORD return')
        self.assertEqual(p.calls,(('00462718',()),))

    def test_coin_equal_is_inclusive_and_higher_passes(self):
        for coins,status in ((99,'coins_at_or_below_stop_town'),(100,'coins_at_or_below_stop_town'),(101,'entry_guards_passed')):
            self.assertEqual(plan_control_guards(self.config(coins=1),self.obs(coins_46258c=coins)).status,status)

    def test_signed64_threshold_compares_to_zero_extended_coin_dword(self):
        for threshold,trigger in ((-1,False),(-(1<<63),False),(1<<32,True),((1<<63)-1,True)):
            p=plan_control_guards(self.config(coins=1,threshold=threshold),self.obs(coins_46258c=0xffffffff))
            self.assertEqual(p.source_return_planned,trigger)

    def test_level_exact_equality_not_greater_or_equal(self):
        for level,trigger in ((53,False),(54,True),(55,False)):
            p=plan_control_guards(self.config(level=1),self.obs(level_462670=level))
            self.assertEqual(p.source_return_planned,trigger)

    def test_nonzero_threshold_high_short_circuits_unobserved_low_word(self):
        for high,trigger in ((1,True),(0x7fffffff,True),(0x80000000,False),(0xffffffff,False)):
            fields=dict(self.config(coins=1).fields);fields[0xcc]=high;fields.pop(0xc8)
            p=plan_control_guards(ControlGuardConfiguration(fields),self.obs(coins_46258c=0))
            self.assertTrue(p.complete);self.assertEqual(p.source_return_planned,trigger)

    def test_compiler_signed64_coin_and_low32_level(self):
        values={path:False for path in FLAG_PATHS}
        values.update({ROOT+'txtCoinControlValue':' -1 ',ROOT+'txtLevelKontrol':'4294967350'})
        c=compile_control_guards(values)
        self.assertEqual((c.fields[0xc8],c.fields[0xcc]),(0xffffffff,0xffffffff))
        self.assertEqual(c.fields[0xd4],54)
        values[ROOT+'txtCoinControlValue']='invalid'
        with self.assertRaises(ValueError):compile_control_guards(values)

    def test_query_chain_np_nonzero_coin_high_then_level(self):
        p=plan_control_guards(self.config(1,1,1),self.obs(np_462718=1,coins_46258c=101,level_462670=54))
        self.assertEqual([c[0] for c in p.calls],['00462718','0046258c','00462670','0040ae0c','00465678'])

if __name__=='__main__':unittest.main()
