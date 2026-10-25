import json,unittest
from jail_selection_trial import *

class JailSelectionTrialTests(unittest.TestCase):
    def setUp(self):
        self.lists={JAIL_LIST_PATH:[dict(caption='Örnek',checked=True,subitems=['char']),
          dict(caption='skip',checked=False,subitems=[]),dict(caption='Third',checked=True,subitems=[])]}
        self.cp=1254;self.trial=JailSelectionTrial(lambda:({},self.lists),lambda:({},self.cp))
    def data(self):return json.loads(example_selection_sample(self.trial.current_snapshot()))

    def test_default_waits_and_snapshot_ignores_subitems(self):
        p=self.trial.step('{}');self.assertEqual(p.needed,('entry','0046ce04'))
        snap=self.trial.current_snapshot();self.lists[JAIL_LIST_PATH][0]['subitems']=['other']
        self.assertEqual(snap,self.trial.current_snapshot())

    def test_selected_captions_only_and_unselected_bad_capture_not_parsed(self):
        d=self.data();d['ansi_hex']['row1.title']='bad HEX'
        p=self.trial.step(json.dumps(d));self.assertTrue(p.complete)
        self.assertEqual(self.trial.saved_rows,(WindowsNameCodec(1254).encode('Örnek')[0],b'Third'))
        self.assertNotIn('row1.title',self.trial.frame.observation.ansi_bytes)

    def test_cleanup_gap_resumes_same_frame_without_duplicate(self):
        d=self.data();d['normal_returns']['row0.unicode_cleanup']=False
        p=self.trial.step(json.dumps(d));self.assertEqual(p.needed,('normal','row0.unicode_cleanup'))
        self.assertEqual(self.trial.saved_rows,())
        frame=self.trial.frame;d['normal_returns']['row0.unicode_cleanup']=True
        p=self.trial.step(json.dumps(d));self.assertTrue(p.complete)
        self.assertIs(self.trial.frame,frame);self.assertEqual(len(self.trial.saved_rows),2)
        self.assertIs(self.trial.step(json.dumps(d)),p)

    def test_checked_caption_and_codepage_edits_reject_stale_sample(self):
        for change in ('checked','caption','codepage'):
            self.setUp();d=self.data();self.trial.step(json.dumps(d))
            if change=='checked':self.lists[JAIL_LIST_PATH][0]['checked']=False
            elif change=='caption':self.lists[JAIL_LIST_PATH][0]['caption']='new'
            else:self.cp=65001
            with self.assertRaises(ValueError):self.trial.step(json.dumps(d))
            self.assertIsNone(self.trial.last)

    def test_count_and_checked_cannot_override_panel(self):
        for label,value in (('row0.count_eax',0),('row0.checked_eax',0),('row0.checked_eax',True)):
            self.setUp();d=self.data();d['values'][label]=value
            with self.assertRaises(ValueError):self.trial.step(json.dumps(d))

    def test_late_invalid_hex_preserves_accepted_rows_and_clears_last(self):
        d=self.data();d['ansi_hex']['row2.title']='xx'
        with self.assertRaises(ValueError):self.trial.step(json.dumps(d))
        self.assertIsNone(self.trial.last)
        self.assertEqual(self.trial.saved_rows,(WindowsNameCodec(1254).encode('Örnek')[0],))

    def test_new_snapshot_retains_saved_state_until_explicit_reset_observation(self):
        self.trial.step(json.dumps(self.data()));old=self.trial.saved_rows
        self.lists[JAIL_LIST_PATH][0]['checked']=False
        self.trial.step('{}');self.assertEqual(self.trial.saved_rows,old)
        self.trial.step(json.dumps(self.data()));self.assertEqual(self.trial.saved_rows,(b'Third',))

    def test_empty_and_explicit_windows_utf8_policy(self):
        self.cp=65001;self.trial.step(json.dumps(self.data()))
        self.assertEqual(self.trial.saved_rows[0],'Örnek'.encode('utf-8'))
        self.lists[JAIL_LIST_PATH]=[];self.trial.step(json.dumps(self.data()))
        self.assertEqual(self.trial.saved_rows,())
        with self.assertRaises(ValueError):selection_snapshot({JAIL_LIST_PATH:[{'caption':'a','checked':1}]},1254)

if __name__=='__main__':unittest.main()
