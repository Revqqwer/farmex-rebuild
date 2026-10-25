import unittest
from jail_protection import JailObservation
from jail_preload import JailPreloadFrame

class JailPreloadTests(unittest.TestCase):
    def observation(self,values=None,blocked=()):
        v={'row0.count_initial_begin':0x1000,'row0.count_end':0x1004,'row0.count_sub_begin':0x1000,
           'row0.item_eax':7,'row0.element_begin':0x2000,'row0.caption_convert_eax':0x3000,
           'row0.caption_unicode_pointer':0x4000,'row0.title_pointer':0x5000,'row0.hwnd':8,
           'row0.pid_dword':9,'row0.handle':10,'row0.root_slot':0x6000,'row0.root_eax':0xfffffff0,
           'row0.size_offset':0x30,'row0.size_eax':15,'row0.pointer_offset':0x40,
           'row0.pointer_eax':0x7000,'row0.inline_offset':0x50,'row0.name_pointer':0x8000,
           'row0.name_unicode_pointer':0x9000,'row1.count_initial_begin':0}
        v.update(values or {})
        n={k:True for k in ('prologue','list_reset','scratch_init','final_cleanup','epilogue')}
        n.update({'row0.'+k:True for k in ('add','string_assign','caption_convert','caption','caption_cleanup',
          'checked','find_window','pid','open','root_read','size_read','pointer_read','name_init','name_read',
          'name_convert','name_assign','name_temp_cleanup','subitem','name_cleanup','failure_text',
          'failure_subitem','failure_cleanup')})
        n.update({k:False for k in blocked});return JailObservation(True,v,n)

    def test_empty_vector_and_explicit_entry(self):
        f=JailPreloadFrame();self.assertEqual(f.advance(JailObservation()).needed,('entry','0045b7d8'))
        p=f.advance(self.observation({'row0.count_initial_begin':0}))
        self.assertTrue(p.complete);self.assertEqual(p.iterations,0)
        self.assertEqual(p.ui_intents,(('virtual_reset_returned',),))

    def test_added_item_survives_missing_caption_conversion(self):
        p=JailPreloadFrame().advance(self.observation(blocked=('row0.caption_convert',)))
        self.assertEqual(p.needed,('normal','row0.caption_convert'))
        self.assertIn(('item_added',7),p.ui_intents)
        self.assertNotIn(('checked_set',7,1),p.ui_intents)

    def test_caption_and_checked_are_distinct_return_boundaries(self):
        f=JailPreloadFrame();p=f.advance(self.observation(blocked=('row0.caption_cleanup',)))
        self.assertIn(('caption_set',7,0x4000),p.ui_intents)
        self.assertNotIn(('checked_set',7,1),p.ui_intents)
        p=f.advance(self.observation(blocked=('row0.find_window',)))
        self.assertIn(('checked_set',7,1),p.ui_intents)

    def test_missing_window_preserves_checked_row_without_remote_read(self):
        p=JailPreloadFrame().advance(self.observation({'row0.hwnd':0}))
        self.assertTrue(p.complete);self.assertIn(('checked_set',7,1),p.ui_intents)
        self.assertNotIn('row0.root_slot',[r[2] for r in p.reads])
        self.assertFalse(any(c[2]=='row0.open' for c in p.calls))

    def test_zero_pid_still_opens_and_zero_handle_uses_failure_literal(self):
        p=JailPreloadFrame().advance(self.observation({'row0.pid_dword':0,'row0.handle':0}))
        self.assertTrue(p.complete)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.open'),(0,0,0x1fffff))
        self.assertIn(('subitem_literal_returned',7,b' - '),p.ui_intents)

    def test_inline_threshold_and_fresh_offset_with_wrapped_address(self):
        p=JailPreloadFrame().advance(self.observation())
        self.assertTrue(p.complete)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.size_read'),(0x20,10))
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.pointer_read'),(0x30,10))
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.name_read'),(15,0x40,10))

    def test_threshold16_uses_captured_pointer_without_inline_reload(self):
        for size in (16,0xffffffff):
            f=JailPreloadFrame();p=f.advance(self.observation({'row0.size_eax':size}))
            self.assertTrue(p.complete)
            self.assertNotIn('row0.inline_offset',f.values)
            self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.name_read'),(size,0x7000,10))

    def test_null_title_uses_source_nul_and_no_native_default_checked(self):
        p=JailPreloadFrame().advance(self.observation({'row0.title_pointer':0,'row0.hwnd':0}))
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.find_window'),(0x522210,0))
        self.assertEqual([i for i in p.ui_intents if i[0]=='checked_set'],[('checked_set',7,1)])

    def test_reached_only_values_and_idempotent_pending_ui_intent(self):
        f=JailPreloadFrame();p=f.advance(self.observation(blocked=('row0.name_init',)))
        self.assertNotIn('row0.inline_offset',f.values)
        self.assertEqual(f.advance(JailObservation()).ui_intents,p.ui_intents)
        p=f.advance(self.observation({'row0.inline_offset':0x60,'row0.item_eax':99}))
        self.assertTrue(p.complete)
        self.assertIn(('subitem_call_returned',7,0x9000),p.ui_intents)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.name_read'),(15,0x50,10))
        self.assertIs(f.advance(JailObservation()),p)

    def test_subitem_intent_survives_cleanup_gap(self):
        p=JailPreloadFrame().advance(self.observation(blocked=('row0.name_cleanup',)))
        self.assertEqual(p.needed,('normal','row0.name_cleanup'))
        self.assertIn(('subitem_call_returned',7,0x9000),p.ui_intents)
        self.assertEqual(p.iterations,0)
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified or p.whole_function_verified)

if __name__=='__main__':unittest.main()
