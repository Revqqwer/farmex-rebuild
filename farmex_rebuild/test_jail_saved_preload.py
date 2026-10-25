import unittest
from jail_selection import JailSelectionFrame,JailSelectionObservation
from jail_protection import JailObservation
from jail_saved_preload import SavedWindowPreload

class SavedPreloadTests(unittest.TestCase):
    def selection(self,rows=(b'\xd6rnek',)):
        # Drive the real producer instead of fabricating a complete plan.
        values={};normals={k:True for k in ('prologue','scratch_init','reset_end','reset_begin','reset_erase','final_cleanup','epilogue')}
        captures={}
        for i,b in enumerate(rows):
            p='row%d.'%i
            values.update({p+'count_eax':len(rows),p+'checked_eax':1,p+'size_eax':i,
               p+'capacity_eax':max(8,len(rows)),p+'end_pointer':0x2000+i*4,p+'insert_eax':0x2004+i*4})
            for stage in ('count','item','checked','text_prepare','text_get','ansi_convert','scratch_assign','ansi_cleanup','unicode_cleanup','size','capacity','insert'):
                normals[p+stage]=True
            captures[p+'title']=b
        values['row%d.count_eax'%len(rows)]=len(rows);normals['row%d.count'%len(rows)]=True
        return JailSelectionFrame().advance(JailSelectionObservation(JailObservation(True,values,normals),captures,()))

    def source(self,values=None,blocked=()):
        v={'row0.count_initial_begin':0x2000,'row0.count_end':0x2004,'row0.count_sub_begin':0x2000,
           'row0.item_eax':7,'row0.element_begin':0x2000,'row0.caption_convert_eax':0x3000,
           'row0.caption_unicode_pointer':0x4000,'row0.title_pointer':0x5000,'row0.hwnd':0,
           'row1.count_initial_begin':0x2000,'row1.count_end':0x2004,'row1.count_sub_begin':0x2000}
        v.update(values or {})
        n={k:True for k in ('prologue','list_reset','scratch_init','final_cleanup','epilogue')}
        n.update({'row0.'+k:True for k in ('add','string_assign','caption_convert','caption','caption_cleanup','checked','find_window')})
        n.update({k:False for k in blocked});return JailObservation(True,v,n)
    def bridge(self,rows=(b'\xd6rnek',),cp=1254):
        return SavedWindowPreload(self.selection(rows),vector_begin=0x2000,codepage=cp,stable_saved_rows=True)

    def test_real_save_then_preload_caption_and_checked_projection(self):
        b=self.bridge();p=b.advance(self.source())
        self.assertTrue(p.complete)
        self.assertEqual(p.captions,((0,7,0x4000,'Örnek'),))
        self.assertIn(('checked_set',7,1),p.source.ui_intents)
        self.assertFalse(p.source_RTL_conversion_verified or p.native_execution_verified or p.live_compatibility_verified)

    def test_contract_and_complete_selection_are_required(self):
        with self.assertRaises(ValueError):SavedWindowPreload(self.selection(),vector_begin=0x2000,codepage=1254)
        incomplete=JailSelectionFrame().advance(JailSelectionObservation())
        with self.assertRaises(ValueError):SavedWindowPreload(incomplete,vector_begin=0x2000,codepage=1254,stable_saved_rows=True)
        with self.assertRaises(ValueError):SavedWindowPreload(self.selection(),vector_begin=0,codepage=1254,stable_saved_rows=True)

    def test_missing_source_reads_are_not_synthesized(self):
        b=self.bridge();p=b.advance(JailObservation(True,normal_returns={'prologue':True,'list_reset':True,'scratch_init':True}))
        self.assertEqual(p.source.needed,('value','row0.count_initial_begin'))
        self.assertEqual(p.captions,())

    def test_inconsistent_fresh_bounds_are_rejected_when_reached(self):
        for label,value in (('row0.count_initial_begin',0),('row0.count_end',0x2008),
                            ('row0.count_sub_begin',0x2004),('row0.element_begin',0x1000)):
            b=self.bridge()
            with self.assertRaises(ValueError):b.advance(self.source({label:value}))
            self.assertIsNone(b.last)

    def test_caption_wait_and_cleanup_do_not_duplicate_projection(self):
        b=self.bridge();p=b.advance(self.source(blocked=('row0.caption',)))
        self.assertEqual(p.captions,())
        p=b.advance(self.source(blocked=('row0.caption_cleanup',)))
        self.assertEqual(p.captions,((0,7,0x4000,'Örnek'),))
        self.assertEqual(b.advance(JailObservation()).captions,p.captions)
        p=b.advance(self.source());self.assertTrue(p.complete)
        self.assertIs(b.advance(JailObservation()),p)

    def test_late_bounds_error_preserves_accepted_caption_prefix(self):
        b=self.bridge()
        with self.assertRaises(ValueError):b.advance(self.source({'row1.count_end':0x2008}))
        self.assertEqual(b.captions,[(0,7,0x4000,'Örnek')])
        self.assertIn(('checked_set',7,1),b.frame.advance(JailObservation()).ui_intents)

    def test_own_utf8_codec_and_empty_saved_vector(self):
        b=self.bridge(('Örnek'.encode('utf-8'),),65001)
        self.assertEqual(b.advance(self.source()).captions[0][3],'Örnek')
        b=SavedWindowPreload(self.selection(()),vector_begin=0,codepage=1254,stable_saved_rows=True)
        p=b.advance(JailObservation(True,{'row0.count_initial_begin':0},{k:True for k in ('prologue','list_reset','scratch_init','final_cleanup','epilogue')}))
        self.assertTrue(p.complete);self.assertEqual(p.captions,())

    def test_two_saved_rows_keep_slot_and_caption_order(self):
        o=self.source({'row0.count_end':0x2008,'row1.count_end':0x2008,
          'row1.item_eax':10,'row1.element_begin':0x2000,'row1.caption_convert_eax':0x3004,
          'row1.caption_unicode_pointer':0x4004,'row1.title_pointer':0x5004,'row1.hwnd':0,
          'row2.count_initial_begin':0x2000,'row2.count_end':0x2008,'row2.count_sub_begin':0x2000})
        n=dict(o.normal_returns)
        n.update({'row1.'+k:True for k in ('add','string_assign','caption_convert','caption','caption_cleanup','checked','find_window')})
        b=self.bridge((b'First',b'Second'));p=b.advance(JailObservation(True,o.values,n))
        self.assertTrue(p.complete)
        self.assertEqual(p.captions,((0,7,0x4000,'First'),(1,10,0x4004,'Second')))
        self.assertEqual([c[1][0] for c in p.source.calls if c[2].endswith('string_assign')],[0x2000,0x2004])

if __name__=='__main__':unittest.main()
