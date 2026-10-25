import unittest
from loot_name_cache import *

class LootNameCacheTests(unittest.TestCase):
    def names(self,first='Fork',last=''):return (first,'','','','','','',last)
    def test_exact_utf16_case_and_space_sensitive(self):
        rows=(LootCacheRow('Fork',1),LootCacheRow('fork',0),LootCacheRow(' Fork',0))
        p=update_loot_name_cache(self.names(),rows)
        self.assertEqual(p.state.values,(1,None,None,None,None,None,None,None))
        self.assertEqual(p.writes,((1,0,1),))
    def test_equivalent_utf16_surrogate_representations_match(self):
        p=update_loot_name_cache(self.names('\U0001f600'),(LootCacheRow('\ud83d\ude00',1),))
        self.assertEqual(p.state.values[0],1)
    def test_duplicates_last_row_wins_and_raw_take_requires_exact1(self):
        rows=(LootCacheRow('Fork',1),LootCacheRow('Fork',255),LootCacheRow('Fork',1))
        p=update_loot_name_cache(self.names(),rows)
        self.assertEqual(p.writes,((1,0,1),(2,0,0),(3,0,1)))
    def test_no_match_and_empty_names_preserve_stale_unknown_bytes(self):
        st=LootCacheState((255,0,1,None,None,None,None,1))
        p=update_loot_name_cache(self.names('Unknown',''),(LootCacheRow('',1),),st)
        self.assertEqual(p.state,st);self.assertEqual(p.writes,())
        self.assertTrue(update_loot_name_cache(self.names('',''),(),st,source_count=100).complete)
    def test_each_of_eight_slots_updates_independently(self):
        names=tuple('item%d'%i for i in range(8))
        rows=tuple(LootCacheRow(name,i%2) for i,name in enumerate(names))
        self.assertEqual(update_loot_name_cache(names,rows).state.values,tuple(i%2 for i in range(8)))
    def test_signed_source_count_and_missing_row_prefix(self):
        rows=(LootCacheRow('Fork',1),)
        self.assertEqual(update_loot_name_cache(self.names(),rows,source_count=0xffffffff).writes,())
        p=update_loot_name_cache(self.names(),rows,source_count=2)
        self.assertFalse(p.complete);self.assertEqual(p.state.values[0],1)
        self.assertEqual(p.reason,'source cache row2')
    def test_panel_topla_column_not_checkbox_or_row_ordinal(self):
        lists={LOOT_LIST_PATH:[{'caption':'Fork','checked':False,'subitems':['EVET','HAYIR','HAYIR','HAYIR','999']},
                              {'caption':'Other','checked':True,'subitems':['HAYIR','EVET','EVET','EVET','1']}]}
        rows=compile_loot_name_cache(lists)
        self.assertEqual(rows,(LootCacheRow('Fork',1),LootCacheRow('Other',0)))
        self.assertEqual(lists[LOOT_LIST_PATH][0]['subitems'][-1],'999')
    def test_invalid_panel_tokens_and_raw_state_rejected(self):
        with self.assertRaises(ValueError):compile_loot_name_cache({LOOT_LIST_PATH:[{'caption':'Fork','subitems':['Evet']}]})
        with self.assertRaises(ValueError):LootCacheRow('Fork',True)
        with self.assertRaises(ValueError):LootCacheState((0,)*7)
    def test_preconversion_guard_is_separate_from_unicode_equality(self):
        guards=(True,False,False,False,False,False,False,False)
        p=update_loot_name_cache(self.names(''),(LootCacheRow('',1),),input_nonempty=guards)
        self.assertEqual(p.state.values[0],1)
        p=update_loot_name_cache(self.names(),(LootCacheRow('Fork',1),),input_nonempty=(False,)*8)
        self.assertEqual(p.state,LootCacheState())

class LootCacheCompositionTests(unittest.TestCase):
    def setUp(self):
        self.fields={4:3,0x18:1,0x1c:7,0x21:0,0x20:0,0x11:0,0x14:0}
        self.items=(123,0,0,0,0,0,0,0)
        self.names=('Fork','','','','','','','')
        self.obs=LootListObservation({0:LootMetadataObservation(1,1,2,7,0)})
    def test_metadata_cache_and_mask_compose_without_raw_cache_override(self):
        p=classify_loot_with_name_cache(self.items,self.fields,self.obs,self.names,(LootCacheRow('Fork',1),))
        self.assertEqual(p.cache_state.values[0],1);self.assertEqual(p.classification.attempt_slots,(0,))
    def test_unknown_lookup_stops_before_cache_state_changes(self):
        p=classify_loot_with_name_cache(self.items,self.fields,LootListObservation(),self.names,(LootCacheRow('Fork',1),))
        self.assertIsNone(p.cache);self.assertEqual(p.cache_state,LootCacheState())
        self.assertEqual(p.classification.reason,'slot0:lookup')
    def test_no_match_with_unknown_old_cache_does_not_become_false(self):
        p=classify_loot_with_name_cache(self.items,self.fields,self.obs,self.names,())
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.classification.reason,'slot0:cache_byte')
        p=classify_loot_with_name_cache(self.items,self.fields,self.obs,self.names,(),cache_state=LootCacheState((1,)*8))
        self.assertEqual(p.classification.attempt_slots,(0,))
    def test_cached_record_skips_name_matching_entirely(self):
        st=LootListState(1,0,(1,0,0,0,0,0,0,0))
        p=classify_loot_with_name_cache(self.items,self.fields,LootListObservation(),None,None,record_state=st)
        self.assertIsNone(p.cache);self.assertEqual(p.classification.attempt_slots,(0,))
    def test_null_lookup_cannot_produce_a_name_cache_match(self):
        obs=LootListObservation({0:LootMetadataObservation(lookup=0)})
        p=classify_loot_with_name_cache(self.items,self.fields,obs,self.names,(LootCacheRow('Fork',1),))
        self.assertEqual(p.cache.writes,());self.assertEqual(p.cache_state,LootCacheState())
        self.assertEqual(p.classification.state.discarded,1)
