import unittest
from dataclasses import replace
from jail_protection import JailObservation
from jail_selection import JailSelectionObservation,JailSelectionFrame

class JailSelectionTests(unittest.TestCase):
    def observation(self,values=None,blocked=(),reset=()):
        v={'row0.count_eax':1,'row0.checked_eax':1,'row0.size_eax':0,
           'row0.capacity_eax':2,'row0.end_pointer':0x1000,'row0.insert_eax':0x1004,'row1.count_eax':1}
        v.update(values or {})
        n={k:True for k in ('prologue','scratch_init','reset_end','reset_begin','reset_erase','final_cleanup','epilogue')}
        n.update({'row0.'+k:True for k in ('count','item','checked','text_prepare','text_get','ansi_convert',
           'scratch_assign','ansi_cleanup','unicode_cleanup','size','capacity','slow_end','insert')})
        n['row1.count']=True;n.update({k:False for k in blocked})
        return JailSelectionObservation(JailObservation(True,v,n),{'row0.title':b'Window A'},reset)

    def test_reset_normal_does_not_invent_empty_vector(self):
        f=JailSelectionFrame(initial_rows=(b'old',))
        p=f.advance(self.observation(reset=None))
        self.assertEqual(p.needed,('reset','after_reset'))
        self.assertEqual(p.rows,(b'old',))
        p=f.advance(JailSelectionObservation(after_reset=(b'captured',)))
        self.assertEqual(p.rows,(b'captured',))
        self.assertEqual(p.needed,('normal','row0.count'))

    def test_only_checked_rows_and_signed_fresh_count(self):
        for values in ({'row0.count_eax':0xffffffff},{'row0.checked_eax':0x100}):
            p=JailSelectionFrame().advance(self.observation(values))
            self.assertTrue(p.complete)
            self.assertEqual(p.rows,())
            self.assertNotIn('row0.text_get',[c[2] for c in p.calls])

    def test_fast_insert_projects_returned_end(self):
        p=JailSelectionFrame().advance(self.observation({'row0.checked_eax':0x102}))
        self.assertTrue(p.complete)
        self.assertEqual(p.rows,(b'Window A',))
        self.assertEqual(p.stores,((0x5691cc,4,0x1004),))
        self.assertEqual(next(c[0] for c in p.calls if c[2]=='row0.insert'),'00409fbc')

    def test_full_capacity_selects_slow_insert_without_end_store(self):
        p=JailSelectionFrame().advance(self.observation({'row0.size_eax':2}))
        self.assertTrue(p.complete)
        self.assertEqual(p.stores,())
        self.assertEqual(next(c[0] for c in p.calls if c[2]=='row0.insert'),'0040a01c')
        p=JailSelectionFrame().advance(self.observation({'row0.size_eax':0xffffffff,'row0.capacity_eax':1}))
        self.assertEqual(next(c[0] for c in p.calls if c[2]=='row0.insert'),'0040a01c')

    def test_missing_insert_and_returned_end_do_not_append(self):
        f=JailSelectionFrame()
        p=f.advance(self.observation(blocked=('row0.insert',)))
        self.assertEqual(p.rows,())
        p=f.advance(JailSelectionObservation(source=JailObservation(normal_returns={'row0.insert':True})))
        self.assertEqual(p.needed,('value','row0.insert_eax'))
        self.assertEqual(p.rows,())
        self.assertEqual(p.stores,())

    def test_prefix_survives_later_cleanup_and_terminal_frame_is_stable(self):
        f=JailSelectionFrame()
        p=f.advance(self.observation(blocked=('final_cleanup',)))
        self.assertEqual(p.rows,(b'Window A',))
        self.assertEqual(p.needed,('normal','final_cleanup'))
        self.assertEqual(f.advance(JailSelectionObservation()).stores,p.stores)
        p=f.advance(JailSelectionObservation(source=JailObservation(normal_returns={'final_cleanup':True,'epilogue':True})))
        self.assertTrue(p.complete)
        self.assertIs(f.advance(JailSelectionObservation()),p)

    def test_reached_only_bytes_and_count_do_not_cache_future_data(self):
        f=JailSelectionFrame();p=f.advance(self.observation(blocked=('row0.ansi_convert',)))
        self.assertEqual(p.needed,('normal','row0.ansi_convert'))
        self.assertEqual(dict(f.observation.ansi_bytes),{})
        self.assertNotIn('row1.count_eax',f.observation.source.values)
        o=self.observation({'row1.count_eax':0xffffffff})
        p=f.advance(replace(o,ansi_bytes={'row0.title':b'Changed before reached'}))
        self.assertTrue(p.complete)
        self.assertEqual(p.rows,(b'Changed before reached',))

    def test_source_order_and_context_wrap(self):
        p=JailSelectionFrame(context=0xffffff80).advance(self.observation())
        labels=[c[2] for c in p.calls]
        self.assertLess(labels.index('row0.unicode_cleanup'),labels.index('row0.size'))
        self.assertLess(labels.index('row0.size'),labels.index('row0.capacity'))
        self.assertEqual(p.stores,((0x54,4,0x1004),))
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified or p.whole_function_verified)

    def test_unicode_cleanup_gap_prevents_vector_append(self):
        p=JailSelectionFrame().advance(self.observation(blocked=('row0.unicode_cleanup',)))
        self.assertEqual(p.rows,())
        self.assertNotIn('row0.size',[c[2] for c in p.calls])

    def test_typed_bytes_and_entry_required(self):
        p=JailSelectionFrame().advance(JailSelectionObservation())
        self.assertEqual(p.needed,('entry','0046ce04'))
        b={'x':b'a'};o=JailSelectionObservation(ansi_bytes=b);b['x']=b'b'
        self.assertEqual(o.ansi_bytes['x'],b'a')
        with self.assertRaises(ValueError):JailSelectionObservation(ansi_bytes={'x':'a'})
        with self.assertRaises(ValueError):JailSelectionObservation(after_reset=[b'a'])
        with self.assertRaises(ValueError):JailSelectionFrame(context=True)

if __name__=='__main__':unittest.main()
