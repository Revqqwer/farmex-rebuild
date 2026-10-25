import unittest
from unittest.mock import patch
from types import SimpleNamespace
from family_runner import FamilyRunner
from class_family import LEGAL_PATH,HEADS,LEGAL_HEADS
from job_dispatcher import JobSnapshot,JobState
from alternate_dispatcher import AlternateSnapshot,AlternateState

class FamilyRunnerTests(unittest.TestCase):
    def tick(self,runner,legal=False,job='mage',**changes):
        args=dict(blocked_74=False,normal_guard_45dc44=0)
        args.update(changes)
        return runner.tick(job,{LEGAL_PATH:legal},AlternateSnapshot(1000,locked_561f7e=True),**args)
    def test_five_ui_classes_route_to_matching_source_heads(self):
        runner=FamilyRunner()
        for job in HEADS:
            self.assertEqual(self.tick(runner,job=job).selection.head,HEADS[job])
            self.assertEqual(self.tick(runner,True,job).selection.head,LEGAL_HEADS[job])
    def test_runtime_byte_overrides_ui_both_ways(self):
        runner=FamilyRunner()
        self.assertEqual(self.tick(runner,True,runtime_byte=0).selection.family,'normal')
        self.assertEqual(self.tick(runner,False,runtime_byte=255).selection.family,'legal')
    def test_unknown_or_blocked_selection_retains_both_states(self):
        runner=FamilyRunner();before=(dict(runner.normal_states),dict(runner.legal_states))
        for change in ({'blocked_74':None},{'blocked_74':True},{'normal_guard_45dc44':6}):
            self.assertIsNone(self.tick(runner,**change).result)
        self.assertEqual((runner.normal_states,runner.legal_states),before)
    def test_normal_only_six_guard_does_not_block_legal(self):
        self.assertIsNotNone(self.tick(FamilyRunner(),True,normal_guard_45dc44=6).result)
    def test_family_states_and_class_states_are_independent(self):
        runner=FamilyRunner();normal=JobState(shared_last_ms=123);legal=AlternateState(last_ms=456)
        with patch('family_runner.dispatch_class_family') as dispatch:
            dispatch.return_value=SimpleNamespace(state=normal)
            self.tick(runner)
            dispatch.return_value=SimpleNamespace(state=legal)
            self.tick(runner,True)
            self.assertEqual(dispatch.call_args.kwargs['normal_state'],normal)
        self.assertEqual(runner.normal_states['mage'],normal)
        self.assertEqual(runner.legal_states['mage'],legal)
        self.assertEqual(runner.normal_states['priest'],JobState())
        self.assertEqual(runner.legal_states['priest'],AlternateState())
    def test_real_normal_head_keeps_missing_observation(self):
        result=FamilyRunner().tick('mage',{LEGAL_PATH:False},JobSnapshot(1000),blocked_74=False,normal_guard_45dc44=0)
        self.assertEqual(result.result.status,'needs_observation')
