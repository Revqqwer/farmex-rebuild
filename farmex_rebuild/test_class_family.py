import unittest
from class_family import LEGAL_PATH, HEADS, LEGAL_HEADS, select_class_family, dispatch_class_family
from job_dispatcher import JobSnapshot, HelperReply
from alternate_dispatcher import AlternateSnapshot


class FamilyTests(unittest.TestCase):
    def choose(self, job='mage', legal=False, **changes):
        args=dict(blocked_74=False, normal_guard_45dc44=0)
        args.update(changes)
        return select_class_family(job, {LEGAL_PATH: legal}, **args)

    def test_all_five_source_head_pairs(self):
        for job in HEADS:
            self.assertEqual(self.choose(job).head, HEADS[job])
            self.assertEqual(self.choose(job, True).head, LEGAL_HEADS[job])

    def test_runtime_byte_overrides_ui_in_both_directions(self):
        self.assertEqual(self.choose(legal=True,runtime_byte=0).family,'normal')
        self.assertEqual(self.choose(runtime_byte=255).family,'legal')

    def test_outer_guard_stops_before_missing_ui(self):
        self.assertEqual(select_class_family('mage',{},blocked_74=True).status,'blocked')
        self.assertEqual(select_class_family('mage',{}).status,'needs_observation')

    def test_normal_guard_is_required_and_six_blocks(self):
        self.assertEqual(self.choose(normal_guard_45dc44=None).status,'needs_observation')
        self.assertEqual(self.choose(normal_guard_45dc44=6).status,'blocked')
        self.assertEqual(self.choose(legal=True,normal_guard_45dc44=6).status,'selected')

    def test_types_reject_bool_runtime_and_missing_legal(self):
        for byte in (True,-1,256):
            with self.assertRaises(ValueError):self.choose(runtime_byte=byte)
        with self.assertRaises(ValueError):select_class_family('mage',{},blocked_74=False)

    def test_blocked_selection_does_not_invoke_head(self):
        self.assertIsNone(dispatch_class_family('mage',self.choose(blocked_74=True),None))

    def test_real_normal_head_keeps_unknown_observation(self):
        result=dispatch_class_family('mage',self.choose(),JobSnapshot(1000))
        self.assertEqual(result.status,'needs_observation')

    def test_real_legal_head_stops_on_lock(self):
        result=dispatch_class_family('mage',self.choose(legal=True),
                                     AlternateSnapshot(1000,locked_561f7e=True))
        self.assertEqual(result.calls,())

    def test_legal_does_not_silently_accept_normal_snapshot(self):
        with self.assertRaises(ValueError):
            dispatch_class_family('mage',self.choose(legal=True),JobSnapshot(1000))

    def test_mismatched_class_selection_rejected(self):
        with self.assertRaises(ValueError):
            dispatch_class_family('priest',self.choose(),JobSnapshot(1000))
