import unittest
from dataclasses import replace
from upgrade_start import (UpgradeStartState,UpgradeStartObservation,UpgradeStartRow,
                           replay_upgrade_start,apply_upgrade_start)
from upgrade_scroll import UpgradeScrollObservation,UpgradeScrollSample
from operation_engine import UpgradeRunner


class UpgradeStartTests(unittest.TestCase):
    def observation(self, **kw):
        base=UpgradeStartObservation(1,True,True,True,
            UpgradeScrollObservation({14:UpgradeScrollSample(b'x',b'x')}),True,
            (3,3,3,3),{0:UpgradeStartRow(1,11),1:UpgradeStartRow(0,caption='invalid'),2:UpgradeStartRow(255,22)},
            {0:True,2:True})
        return replace(base,**kw)

    def test_start_order_first_scan_then_rows_then_mode(self):
        p=replay_upgrade_start(UpgradeStartState(2,(99,),5),self.observation())
        self.assertTrue(p.complete)
        self.assertEqual((p.state.mode,p.state.queue,p.state.scroll_index),(1,(11,22),0))
        self.assertEqual(p.calls[:6],(('SetEnabled:start',False),('SetEnabled:stop',True),
            ('004f7d28:end',),('004f7d04:begin',),('004f7d4c:erase_range',),('004f7040',)))
        self.assertFalse(p.independently_verified)

    def test_ui_gap_retains_input_and_exposes_only_reached_prefix(self):
        state=UpgradeStartState(2,(99,),5,True,False)
        p=replay_upgrade_start(state,self.observation(stop_ui_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.state,state)
        self.assertEqual(p.prospective_state.start_enabled,False)
        self.assertEqual(p.prospective_state.queue,(99,))
        self.assertEqual(len(p.calls),2)

    def test_clear_gap_does_not_reach_scroll_or_rows(self):
        p=replay_upgrade_start(UpgradeStartState(queue=(99,)),
            self.observation(vector_clear_returned=None,scroll_lookup=object()))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.queue,(99,))
        self.assertNotIn(('004f7040',),p.calls)

    def test_lookup_gap_and_cleanup_gap_show_distinct_prefix(self):
        state=UpgradeStartState(2,(99,),5)
        p=replay_upgrade_start(state,self.observation(scroll_lookup=None))
        self.assertEqual((p.state,p.prospective_state.queue,p.prospective_state.mode),(state,(),2))
        self.assertNotIn(('GetCount',0),p.calls)
        p=replay_upgrade_start(state,self.observation(scroll_cleanup_returned=None))
        self.assertEqual(p.prospective_state.scroll_index,0)
        self.assertNotIn(('GetCount',0),p.calls)

    def test_no_scroll_does_not_stop_start_helper(self):
        lookup=UpgradeScrollObservation({s:UpgradeScrollSample(b'x',b'other') for s in range(14,42)})
        p=replay_upgrade_start(UpgradeStartState(),self.observation(scroll_lookup=lookup))
        self.assertTrue(p.complete)
        self.assertEqual((p.state.mode,p.state.scroll_index,p.state.queue),(1,-1,(11,22)))

    def test_count_is_fresh_signed_and_can_shrink(self):
        p=replay_upgrade_start(UpgradeStartState(),self.observation(counts=(3,1),rows={0:UpgradeStartRow(1,11),1:object()}))
        self.assertEqual(p.state.queue,(11,))
        p=replay_upgrade_start(UpgradeStartState(),self.observation(counts=(-1,),rows={0:object()}))
        self.assertTrue(p.complete);self.assertEqual(p.state.queue,())
        p=replay_upgrade_start(UpgradeStartState(),self.observation(counts=(3,)))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.queue,(11,))

    def test_append_gap_keeps_prior_row_as_prospective_only(self):
        state=UpgradeStartState(queue=(99,))
        p=replay_upgrade_start(state,self.observation(append_returns={0:True}))
        self.assertFalse(p.complete);self.assertEqual(p.state.queue,(99,))
        self.assertEqual(p.prospective_state.queue,(11,))
        self.assertEqual(p.prospective_state.mode,0)

    def test_local_decimal_is_explicit_and_unchecked_caption_is_ignored(self):
        rows={0:UpgradeStartRow(1,caption='-1'),1:UpgradeStartRow(0,caption=object())}
        o=self.observation(rows=rows,counts=(2,2,2),append_returns={0:True})
        self.assertFalse(replay_upgrade_start(UpgradeStartState(),o).complete)
        p=replay_upgrade_start(UpgradeStartState(),replace(o,local_decimal=True))
        self.assertEqual(p.state.queue,(0xffffffff,))
        rows={0:UpgradeStartRow(1,caption='invalid')}
        p=replay_upgrade_start(UpgradeStartState(),replace(o,rows=rows,local_decimal=True))
        self.assertFalse(p.complete);self.assertIn('local decimal',p.missing)

    def test_stop_writes_mode_before_ui_and_keeps_queue(self):
        state=UpgradeStartState(1,(11,),2,False,True)
        p=replay_upgrade_start(state,UpgradeStartObservation(0))
        self.assertEqual((p.state.mode,p.prospective_state.mode,p.prospective_state.queue),(1,0,(11,)))
        p=replay_upgrade_start(state,UpgradeStartObservation(0,True,True))
        self.assertTrue(p.complete);self.assertEqual((p.state.mode,p.state.queue,p.state.scroll_index),(0,(11,),2))

    def test_apply_is_complete_snapshot_guarded_and_does_not_write_clock(self):
        runner=UpgradeRunner(source_clock=True);runner.queue_stamp_qword=123
        p=replay_upgrade_start(UpgradeStartState(),self.observation())
        apply_upgrade_start(runner,p)
        self.assertEqual((runner.state,runner.queue,runner.source_scroll_index,runner.queue_stamp_qword),
                         (1,(11,22),0,123))
        with self.assertRaises(ValueError):apply_upgrade_start(runner,p)
        with self.assertRaises(ValueError):
            apply_upgrade_start(UpgradeRunner(source_clock=True),replay_upgrade_start(UpgradeStartState(),UpgradeStartObservation(1)))
