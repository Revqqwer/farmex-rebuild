import unittest,sys
from dataclasses import replace
from supply_routes import *

class SupplyRouteTests(unittest.TestCase):
    def lists(self,*supply,returning=()):return SupplyRouteLists(tuple(supply),tuple(returning),True)
    def obs(self,name=b'a',exists=1):return SupplyRouteObservation('a',name,b'C:\\Routes\\','C:\\Routes\\a',exists,name)
    def test_empty_list_returns_empty_without_counter_change_or_observations(self):
        state=SupplyRouteState(0xffffffff,5)
        p=plan_supply_route_selection(self.lists(), 'supply',state)
        self.assertEqual(p.filename,b'');self.assertEqual(p.state,state);self.assertTrue(p.complete)
    def test_cyclic_selection_advances_and_wraps_separate_global_counters(self):
        state=SupplyRouteState(0,1);lists=self.lists(b'a',b'b',returning=(b'x',b'y'))
        p=plan_supply_route_selection(lists,'supply',state,self.obs())
        self.assertEqual((p.selected_index,p.state.supply_counter,p.state.return_counter),(0,1,1))
        q=plan_supply_route_selection(lists,'supply',p.state,self.obs(b'b'))
        self.assertEqual((q.selected_index,q.state.supply_counter),(1,2))
        r=plan_supply_route_selection(lists,'supply',q.state,self.obs())
        self.assertEqual((r.selected_index,r.state.supply_counter),(0,1))
        back=plan_supply_route_selection(lists,'return',r.state,self.obs(b'y'))
        self.assertEqual((back.selected_index,back.state.supply_counter,back.state.return_counter),(1,1,2))
    def test_high_positive_counter_resets_but_negative_dword_does_not_modulo(self):
        lists=self.lists(b'a',b'b')
        p=plan_supply_route_selection(lists,'supply',SupplyRouteState(0x7fffffff,0),self.obs())
        self.assertEqual((p.selected_index,p.state.supply_counter),(0,1))
        for raw in (0xffffffff,0x80000000):
            p=plan_supply_route_selection(lists,'supply',SupplyRouteState(raw,0),self.obs())
            self.assertFalse(p.complete);self.assertEqual(p.status,'unresolved_source_counter')
            self.assertEqual(p.state.supply_counter,raw)
    def test_counter_reset_before_decode_and_increment_after_decode(self):
        lists=self.lists(b'a');state=SupplyRouteState(10,0)
        p=plan_supply_route_selection(lists,'supply',state)
        self.assertEqual(p.state.supply_counter,0);self.assertIn('ANSI->Unicode',p.missing)
        p=plan_supply_route_selection(lists,'supply',state,SupplyRouteObservation(decoded_name='a'))
        self.assertEqual(p.state.supply_counter,1);self.assertIn('first Unicode->ANSI',p.missing)
    def test_missing_file_consumes_slot_and_returns_empty_not_next_entry(self):
        p=plan_supply_route_selection(self.lists(b'a',b'b'),'supply',SupplyRouteState(0,0),self.obs(exists=0))
        self.assertEqual((p.filename,p.selected_index,p.state.supply_counter),(b'',0,1))
        self.assertEqual(p.status,'route_file_missing');self.assertTrue(p.complete)
    def test_nonzero_fileexists_byte_and_fresh_return_conversion(self):
        o=replace(self.obs(),file_exists_byte=255,success_encoded=b'different')
        p=plan_supply_route_selection(self.lists(b'a'),'supply',SupplyRouteState(0,0),o)
        self.assertEqual(p.filename,b'different');self.assertEqual(p.candidate_path,b'C:\\Routes\\a')
        self.assertFalse(p.independently_verified)
    def test_fileexists_required_after_path_conversion_and_failed_path_skips_success_encode(self):
        base=self.obs();lists=self.lists(b'a');state=SupplyRouteState(0,0)
        for attr in ('prefix','path_unicode','file_exists_byte'):
            p=plan_supply_route_selection(lists,'supply',state,replace(base,**{attr:None}))
            self.assertFalse(p.complete);self.assertEqual(p.state.supply_counter,1)
        p=plan_supply_route_selection(lists,'supply',state,replace(base,file_exists_byte=0,success_encoded=None))
        self.assertTrue(p.complete);self.assertEqual(p.filename,b'')
        p=plan_supply_route_selection(lists,'supply',state,replace(base,success_encoded=None))
        self.assertFalse(p.complete);self.assertIn('fresh successful',p.missing)
    def test_concat_is_raw_without_separator_trim_or_case_normalization(self):
        o=SupplyRouteObservation(' x ',b' x ',b'prefix', 'explicit observed path',1,b' x ')
        p=plan_supply_route_selection(self.lists(b' x '),'supply',SupplyRouteState(0,0),o)
        self.assertEqual(p.candidate_path,b'prefix x ');self.assertEqual(p.filename,b' x ')
    def test_profile_nonempty_names_require_explicit_conversion_not_python_utf8_guess(self):
        profile={LIST_PATHS['supply']:[{'caption':'İtem','checked':False}],LIST_PATHS['return']:[]}
        lists=compile_supply_route_lists(profile)
        self.assertFalse(lists.complete);self.assertEqual(lists.supply,(None,))
        p=plan_supply_route_selection(lists,'supply',SupplyRouteState(0,0),self.obs())
        self.assertEqual(p.status,'needs_route_list_conversion');self.assertEqual(p.state.supply_counter,0)
        empty=compile_supply_route_lists({path:[] for path in LIST_PATHS.values()})
        self.assertTrue(empty.complete)
    @unittest.skipUnless(sys.platform=='win32','Owned Windows API fixture')
    def test_profile_codec_preserves_order_duplicates_and_ignores_checked(self):
        profile={LIST_PATHS['supply']:[{'caption':'İtem','checked':False},{'caption':'İtem'}],
            LIST_PATHS['return']:[{'caption':' Back '}]}
        lists=compile_supply_route_lists(profile,codec=WindowsNameCodec(1254))
        self.assertTrue(lists.complete);self.assertEqual(lists.supply,(b'\xddtem',b'\xddtem'))
        self.assertEqual(lists.returning,(b' Back ',))
    @unittest.skipUnless(sys.platform=='win32','Owned Windows API fixture')
    def test_explicit_codec_chain_reaches_fileexists_plan(self):
        for cp in (1254,65001):
            codec=WindowsNameCodec(cp);name=codec.encode('İtem')[0]
            o=route_codec_fixture(name,b'C:\\Routes\\',codec,file_exists_byte=1)
            p=plan_supply_route_selection(self.lists(name),'supply',SupplyRouteState(0,0),o)
            self.assertTrue(p.complete);self.assertEqual(p.file_exists_path,'C:\\Routes\\İtem')
            self.assertEqual(p.filename,name)
    def test_invalid_observation_types_rejected(self):
        for raw in (True,-1,0x100000000):
            with self.assertRaises(ValueError):SupplyRouteState(raw,0)
        with self.assertRaises(ValueError):SupplyRouteObservation(prefix='C:')
        with self.assertRaises(ValueError):SupplyRouteObservation(file_exists_byte=True)

if __name__=='__main__':unittest.main()
