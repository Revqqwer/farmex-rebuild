import unittest
from operation_engine import UpgradeRunner
from upgrade_parameter_frame import UpgradeParameterState
from upgrade_start_frame import UpgradeStartFrame, UpgradeStartFrameObservation as Observation
from upgrade_scroll_frame import UpgradeScrollFrame
from upgrade_scroll import UpgradeScrollObservation, UpgradeScrollSample
from mining_slot_name import SlotNameObservation


class Sink:
    def __init__(self, rows=()):
        self.rows=list(rows);self.events=[]
    def set_enabled(self,name,value):self.events.append((name,value))
    def count(self):return len(self.rows)
    def checked(self,index):return self.rows[index][0]
    def caption(self,index):return self.rows[index][1]


def scan(hit=14):
    return UpgradeScrollObservation({slot:UpgradeScrollSample(b'Scroll',b'Scroll' if slot==hit else b'other')
                                     for slot in range(14,42)})


def receipts(**overrides):
    values=dict(gate_byte=1,start_ui_returned=True,stop_ui_returned=True,
                vector_end_returned=True,vector_begin_returned=True,vector_erase_returned=True,
                scroll_conversion_returned=True,scroll_lookup=scan(),scroll_lookup_returned=True,
                scroll_cleanup_returned=True,caption_returns={0:True,1:True,2:True},
                caption_cleanup_returns={0:True,1:True,2:True},append_returns={0:True,1:True,2:True})
    values.update(overrides)
    return Observation(**values)


class UpgradeStartFrameTests(unittest.TestCase):
    def frame(self,method='start',rows=(),parameters=None):
        runner=UpgradeRunner(source_clock=True)
        runner.state=2;runner.queue=(99,);runner.source_scroll_index=7
        runner.queue_stamp_qword=123;runner.armor_stamp_qword=456
        sink=Sink(rows)
        return UpgradeStartFrame(method,runner,parameters or UpgradeParameterState(b'Scroll',1254),sink),runner,sink

    def test_closed_gate_preserves_all_effects(self):
        f,r,s=self.frame()
        self.assertTrue(f.advance(Observation(gate_byte=0)).complete)
        self.assertEqual((r.state,r.queue,r.source_scroll_index,s.events),(2,(99,),7,[]))

    def test_stop_mode_precedes_ui_and_preserves_queue_and_clocks(self):
        f,r,s=self.frame('stop')
        p=f.advance(Observation(gate_byte=1))
        self.assertEqual((r.state,r.queue,s.events,p.needed),(0,(99,),[('start',True)],(None,'start_ui_returned')))
        self.assertEqual(f.advance(receipts()).status,'stopped')
        self.assertEqual((r.queue,r.source_scroll_index,r.queue_stamp_qword,r.armor_stamp_qword),((99,),7,123,456))
        self.assertEqual(s.events,[('start',True),('stop',False)])

    def test_start_commits_selected_caption_dwords_and_keeps_clocks(self):
        f,r,s=self.frame(rows=((True,'$FFFFFFFF'),(False,'invalid'),(True,'27')))
        self.assertEqual(f.advance(receipts()).status,'started')
        self.assertEqual((r.state,r.queue,r.source_scroll_index),(1,(0xffffffff,27),0))
        self.assertEqual((r.queue_stamp_qword,r.armor_stamp_qword),(123,456))
        self.assertEqual(s.events,[('start',False),('stop',True)])

    def test_queue_clear_waits_for_erase_return_and_does_not_change_mode(self):
        f,r,s=self.frame(parameters=UpgradeParameterState())
        p=f.advance(receipts(vector_erase_returned=None))
        self.assertEqual((r.queue,r.state,p.needed),((99,),2,(None,'vector_erase_returned')))
        p=f.advance(Observation(vector_erase_returned=True))
        self.assertEqual((r.queue,r.state,p.needed),((),2,('cached_scroll_bytes',)))
        self.assertEqual(len(s.events),2)

    def test_no_scroll_match_still_starts_with_empty_queue(self):
        f,r,s=self.frame()
        self.assertTrue(f.advance(receipts(scroll_lookup=scan(None))).complete)
        self.assertEqual((r.state,r.queue,r.source_scroll_index),(1,(),-1))

    def test_caption_cleanup_and_append_gaps_keep_prefix_without_duplicate(self):
        f,r,s=self.frame(rows=((True,'4'),(True,'5')))
        p=f.advance(receipts(caption_cleanup_returns={}))
        self.assertEqual((r.queue,p.needed),((),('caption_cleanup_returns',0)))
        s.rows[0]=(True,'999')
        p=f.advance(Observation(caption_cleanup_returns={0:True}))
        self.assertEqual((r.queue,p.needed),((),('append_returns',0)))
        p=f.advance(Observation(append_returns={0:True}))
        self.assertEqual((r.queue,p.needed),((4,),('caption_returns',1)))
        self.assertEqual(f.advance(receipts()).status,'started')
        self.assertEqual(r.queue,(4,5))
        f.advance(receipts())
        self.assertEqual(r.queue,(4,5))

    def test_invalid_caption_does_not_invent_default_or_complete_start(self):
        f,r,s=self.frame(rows=((True,'4'),(True,'bad')))
        p=f.advance(receipts())
        self.assertFalse(p.complete)
        self.assertEqual(p.needed[:2],('caption_exception_outcome',1))
        self.assertEqual((r.queue,r.state),((4,),2))

    def test_row_count_is_fresh_after_append(self):
        f,r,s=self.frame(rows=((True,'4'),(True,'5')))
        f.advance(receipts(append_returns={}))
        s.rows.pop()
        self.assertEqual(f.advance(Observation(append_returns={0:True})).status,'started')
        self.assertEqual(r.queue,(4,))

    def test_cancel_preserves_known_prefix_and_ignores_late_receipts(self):
        f,r,s=self.frame()
        f.advance(Observation(gate_byte=1))
        f.cancel('profile_change')
        self.assertEqual(f.advance(receipts()).status,'cancelled')
        self.assertEqual((r.queue,s.events),((99,),[('start',False)]))

    def test_cached_scroll_bytes_freeze_while_codepage_is_missing(self):
        parameters=UpgradeParameterState(b'Scroll\0tail')
        f,r,s=self.frame(parameters=parameters)
        p=f.advance(receipts())
        self.assertEqual(p.needed,('cached_scroll_codepage',))
        parameters.scroll_bytes=b'changed';parameters.scroll_codepage=1254
        self.assertTrue(f.advance(receipts()).complete)
        self.assertEqual(f.scroll_text,'Scroll\0tail')

    def test_empty_cached_scroll_needs_no_codepage(self):
        f,r,s=self.frame(parameters=UpgradeParameterState(b''))
        self.assertTrue(f.advance(receipts()).complete)
        self.assertEqual(f.scroll_text,'')

    def test_own_inflight_worker_guard_does_not_mutate_runner(self):
        r=UpgradeRunner(source_clock=True);r.source_pending=object();r.state=2;r.queue=(9,)
        with self.assertRaises(ValueError):UpgradeStartFrame('stop',r,UpgradeParameterState(),Sink())
        self.assertEqual((r.state,r.queue),(2,(9,)))

    def test_scroll_freezes_reached_values_and_ignores_unreached_data(self):
        f=UpgradeScrollFrame()
        self.assertFalse(f.advance(UpgradeScrollObservation({14:UpgradeScrollSample(b'')})).complete)
        empty=SlotNameObservation(global_553e80=1,offset_5540a8=4,offset_5540ac=8,root=2,inventory=3,record=0)
        p=f.advance(UpgradeScrollObservation({14:UpgradeScrollSample(b'changed',slot_name_inputs=empty),15:object()}))
        self.assertEqual((p.complete,p.relative_index,p.visited_slots),(True,0,(14,)))

    def test_lower_scroll_reads_resume_without_requiring_prior_snapshot(self):
        f=UpgradeScrollFrame()
        f.advance(UpgradeScrollObservation({14:UpgradeScrollSample(b'',slot_name_inputs=SlotNameObservation(global_553e80=1,root=2))}))
        p=f.advance(UpgradeScrollObservation({14:UpgradeScrollSample(slot_name_inputs=SlotNameObservation(offset_5540a8=4,inventory=3,offset_5540ac=8,record=0))}))
        self.assertEqual((p.complete,p.relative_index),(True,0))


if __name__=='__main__':unittest.main()
