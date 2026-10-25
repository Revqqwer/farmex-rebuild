import unittest
from jail_protection import JailObservation
from jail_discovery import JailDiscoveryFrame,JailRefreshFrame,JailRefreshObservation

class JailDiscoveryTests(unittest.TestCase):
    def observation(self,values=None,blocked=()):
        p='process0.'
        v={'snapshot_handle':1,'first_eax':1,p+'search_eax':0,p+'pid':2,p+'handle':3,
           p+'identity_address':4,p+'identity_pointer':5,p+'duplicate0.count_eax':0,
           p+'exclude_eax':1,p+'item_eax':6,p+'identity_unicode_pointer':7,
           p+'root_slot':0x100,p+'root_eax':0xfffffff0,p+'size_offset':0x20,
           p+'size_eax':15,p+'pointer_offset':0x30,p+'pointer_eax':0x200,
           p+'inline_offset':0x40,p+'name_pointer':0x300,p+'name_unicode_pointer':0x400,p+'next_eax':0}
        v.update(values or {})
        n={k:True for k in ('initial_text','snapshot','first','final_cleanup','epilogue')}
        n.update({p+k:True for k in ('executable','search','open','identity_read','identity_convert',
           'duplicate0.count','duplicate0.title','duplicate0.compare','duplicate0.cleanup',
           'duplicate1.count','exclude','add','caption','root_read','size_read','pointer_read',
           'name_init','name_read','name_convert','name_assign','name_temp_cleanup','subitem',
           'name_cleanup','identity_cleanup','next','executable_cleanup')})
        n.update({k:False for k in blocked})
        return JailObservation(True,v,n)

    def test_entry_snapshot_error_and_no_native_call(self):
        f=JailDiscoveryFrame();self.assertEqual(f.advance(JailObservation()).needed,('entry','0045bac8'))
        p=f.advance(self.observation({'snapshot_handle':0xffffffff}))
        self.assertTrue(p.complete);self.assertEqual(p.ui_intents,())
        self.assertNotIn('first',[c[2] for c in p.calls])
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified or p.whole_function_verified)

    def test_search_minus_one_skips_identity_and_still_advances(self):
        p=JailDiscoveryFrame().advance(self.observation({'process0.search_eax':0xffffffff}))
        self.assertTrue(p.complete);self.assertEqual(p.iterations,1)
        self.assertNotIn('process0.open',[c[2] for c in p.calls])

    def test_zero_open_handle_is_not_invented_skip(self):
        p=JailDiscoveryFrame().advance(self.observation({'process0.handle':0}))
        self.assertTrue(p.complete)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='process0.identity_read'),(0xff,4,0))
        self.assertIn(('item_added',6),p.ui_intents)

    def test_negative_signed_duplicate_count_skips_row_getter(self):
        p=JailDiscoveryFrame().advance(self.observation({'process0.duplicate0.count_eax':0xffffffff}))
        self.assertTrue(p.complete)
        self.assertNotIn('process0.duplicate0.title',[c[2] for c in p.calls])

    def test_duplicate_result_is_tested_after_cleanup_and_cannot_be_changed(self):
        f=JailDiscoveryFrame()
        p=f.advance(self.observation({'process0.duplicate0.count_eax':1,'process0.duplicate0.compare_eax':0x102},
                                    blocked=('process0.duplicate0.cleanup',)))
        self.assertEqual(p.needed,('normal','process0.duplicate0.cleanup'))
        self.assertNotIn('process0.exclude_eax',f.values)
        p=f.advance(self.observation({'process0.duplicate0.compare_eax':0}))
        self.assertTrue(p.complete)
        self.assertEqual(p.ui_intents,())
        self.assertNotIn('process0.duplicate1.count_eax',f.values)

    def test_duplicate_still_evaluates_exclusion_before_skip(self):
        p=JailDiscoveryFrame().advance(self.observation({'process0.duplicate0.count_eax':1,
            'process0.duplicate0.compare_eax':1},blocked=('process0.exclude',)))
        self.assertEqual(p.needed,('normal','process0.exclude'))
        self.assertEqual(p.ui_intents,())

    def test_no_match_reloads_count_and_uses_saved_low_al(self):
        p=JailDiscoveryFrame().advance(self.observation({'process0.duplicate0.count_eax':2,
          'process0.duplicate0.compare_eax':0x100,'process0.duplicate1.count_eax':1}))
        self.assertTrue(p.complete)
        self.assertIn(('item_added',6),p.ui_intents)
        self.assertIn('process0.duplicate1.count',[c[2] for c in p.calls])

    def test_exclusion_low_al_zero_skips_add(self):
        p=JailDiscoveryFrame().advance(self.observation({'process0.exclude_eax':0x100}))
        self.assertTrue(p.complete);self.assertEqual(p.ui_intents,())

    def test_add_and_caption_prefix_before_character_reads(self):
        p=JailDiscoveryFrame().advance(self.observation(blocked=('process0.root_read',)))
        self.assertEqual(p.needed,('normal','process0.root_read'))
        self.assertEqual(p.ui_intents,(('item_added',6),('caption_set',6,7)))
        self.assertFalse(any('checked' in c[2] for c in p.calls))

    def test_inline_and_indirect_name_paths_preserve_fresh_offset(self):
        for size,address in ((15,0x30),(16,0x200),(0xffffffff,0x200)):
            f=JailDiscoveryFrame();p=f.advance(self.observation({'process0.size_eax':size}))
            self.assertTrue(p.complete)
            self.assertEqual(next(c[1] for c in p.calls if c[2]=='process0.name_read'),(size,address,3))
            self.assertEqual('process0.inline_offset' in f.values,size<16)

    def test_next_precedes_executable_cleanup_and_subitem_prefix_survives(self):
        f=JailDiscoveryFrame();p=f.advance(self.observation(blocked=('process0.name_cleanup',)))
        self.assertIn(('subitem_call_returned',6,0x400),p.ui_intents)
        self.assertNotIn('process0.next_eax',f.values)
        p=f.advance(self.observation())
        labels=[c[2] for c in p.calls]
        self.assertLess(labels.index('process0.next'),labels.index('process0.executable_cleanup'))
        self.assertEqual(len([i for i in p.ui_intents if i[0]=='item_added']),1)
        self.assertIs(f.advance(JailObservation()),p)

    def preload_empty(self):
        return JailObservation(values={'row0.count_initial_begin':0},normal_returns={
          k:True for k in ('prologue','list_reset','scratch_init','final_cleanup','epilogue')})

    def test_refresh_cannot_skip_preload_with_early_outer_return(self):
        f=JailRefreshFrame()
        p=f.advance(JailRefreshObservation(JailObservation(True,normal_returns={'prologue':True,'preload_return':True}),
                                          discovery=self.observation()))
        self.assertEqual(p.needed,('preload',('normal','prologue')))
        self.assertIsNone(f.discovery)

    def test_refresh_requires_outer_return_after_completed_preload(self):
        f=JailRefreshFrame()
        p=f.advance(JailRefreshObservation(JailObservation(True,normal_returns={'prologue':True}),
                                          self.preload_empty(),self.observation()))
        self.assertTrue(p.preload.complete)
        self.assertEqual(p.needed,('outer_normal','preload_return'))
        self.assertIsNone(f.discovery)
        p=f.advance(JailRefreshObservation(JailObservation(normal_returns={'preload_return':True}),
                                          discovery=self.observation({'snapshot_handle':0xffffffff})))
        self.assertTrue(p.complete)
        self.assertEqual(p.ui_intents,(('virtual_reset_returned',),))
        self.assertIs(f.advance(JailRefreshObservation()),p)

    def test_refresh_preserves_preload_intents_and_discovery_needs(self):
        f=JailRefreshFrame()
        p=f.advance(JailRefreshObservation(JailObservation(True,normal_returns={'prologue':True,'preload_return':True}),
                                          self.preload_empty()))
        self.assertEqual(p.needed,('discovery',('normal','initial_text')))
        self.assertEqual(p.ui_intents,(('virtual_reset_returned',),))
        with self.assertRaises(ValueError):JailRefreshObservation(discovery={})

if __name__=='__main__':unittest.main()
