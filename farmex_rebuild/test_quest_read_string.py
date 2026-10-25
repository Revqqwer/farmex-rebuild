import unittest
from dataclasses import replace
from quest_read_string import QuestReadStringFrame,QuestReadStringObservation as Observation


def capture(raw=b'abc',bad=0,constructor=None):
    return Observation(bad,raw,constructor,{k:True for k in ('entry','guard','copy_prefix','copy','constructor','assign_prefix','assign','cleanup','epilogue')})


class QuestReadStringTests(unittest.TestCase):
    def frame(self,count=3,owned=True):return QuestReadStringFrame(0x1234,count,b'old',use_owned_cstring_model=owned)
    def labels(self,p):return [label for label,_,_ in p.calls]

    def test_readable_copy_constructor_assignment_and_destination_return(self):
        p=self.frame().advance(capture())
        self.assertTrue(p.complete);self.assertEqual(p.destination_ansi,b'abc')
        self.assertEqual(p.return_target,'owned_destination')
        self.assertEqual(p.local_buffer[:4],b'abc\0');self.assertEqual(len(p.local_buffer),512)
        self.assertFalse(p.native_execution_verified)

    def test_bad_read_nonzero_takes_empty_branch_without_copy_or_overflow(self):
        p=self.frame(0xffffffff).advance(capture(raw=object(),bad=0x100))
        self.assertTrue(p.complete);self.assertEqual(p.destination_ansi,b'')
        self.assertIsNone(p.local_buffer);self.assertNotIn('copy',self.labels(p))

    def test_guard_is_required_before_bytes_and_result(self):
        o=capture(raw=object());normal=dict(o.normal_returns);normal['guard']=False
        p=self.frame().advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,('normal','guard'));self.assertEqual(p.destination_ansi,b'old')

    def test_guard_return_and_eax_are_separate_and_cached(self):
        f=self.frame();p=f.advance(replace(capture(),bad_read_eax=None))
        self.assertEqual(p.needed,('value','bad_read_eax'))
        o=capture();normal=dict(o.normal_returns);normal['guard']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.complete);self.assertEqual(self.labels(p).count('guard'),1)

    def test_short_copy_waits_without_truncating_count(self):
        f=self.frame(4);p=f.advance(capture(b'ab'))
        self.assertEqual(p.needed,('bytes',4));self.assertEqual(p.local_buffer,b'\0'*512)
        self.assertEqual(f.advance(capture(b'abcd')).destination_ansi,b'abcd')

    def test_copy_prefix_precedes_outer_return_and_does_not_resample_bytes(self):
        f=self.frame();o=capture();normal=dict(o.normal_returns);normal['copy']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.local_buffer[:3],b'abc');self.assertEqual(p.destination_ansi,b'old')
        p=f.advance(capture(b'XYZ'))
        self.assertEqual(p.destination_ansi,b'abc');self.assertEqual(self.labels(p).count('copy'),1)

    def test_copy_prefix_receipt_is_not_inferred_from_outer_return(self):
        o=capture();normal=dict(o.normal_returns);del normal['copy_prefix']
        p=self.frame().advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,('normal','copy_prefix'));self.assertEqual(p.local_buffer,b'\0'*512)

    def test_embedded_nul_and_template_tail_terminate_own_cstring(self):
        for raw,count,expected in ((b'a\0b',3,b'a'),(b'ab',2,b'ab'),(b'',0,b'')):
            p=self.frame(count).advance(capture(raw))
            self.assertTrue(p.complete);self.assertEqual(p.destination_ansi,expected)

    def test_zero_count_still_calls_copy_and_required_lifetimes(self):
        p=self.frame(0).advance(capture(raw=object()))
        self.assertTrue(p.complete)
        self.assertIn('copy',self.labels(p));self.assertIn('constructor',self.labels(p))

    def test_512_byte_boundary_and_unterminated_source(self):
        p=self.frame(512).advance(capture(b'a'*511+b'\0'))
        self.assertTrue(p.complete);self.assertEqual(len(p.destination_ansi),511)
        f=self.frame(512);p=f.advance(capture(b'a'*512))
        self.assertFalse(p.complete);self.assertEqual(p.status,'unresolved_unterminated_source_buffer')
        self.assertEqual(p.destination_ansi,b'old')
        # An explicit completed constructor value can describe an observed
        # normal return; it does not invent bytes beyond our local buffer.
        p=f.advance(capture(constructor=b'captured'))
        self.assertTrue(p.complete);self.assertEqual(p.destination_ansi,b'captured')

    def test_readable_overflow_is_unresolved_before_copy_even_with_captures(self):
        p=self.frame(513).advance(capture(b'a'*513,constructor=b'captured'))
        self.assertEqual(p.status,'unresolved_source_stack_overflow')
        self.assertNotIn('copy',self.labels(p));self.assertEqual(p.destination_ansi,b'old')

    def test_default_mode_requires_explicit_constructor_output(self):
        f=self.frame(owned=False);p=f.advance(capture())
        self.assertEqual(p.needed,('value','constructor_ansi'));self.assertEqual(p.destination_ansi,b'old')
        p=f.advance(capture(constructor=b'post-constructor'))
        self.assertEqual(p.destination_ansi,b'post-constructor')

    def test_assignment_prefix_survives_outer_return_gap_and_changed_capture(self):
        f=self.frame();o=capture();normal=dict(o.normal_returns);normal['assign']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.destination_assigned);self.assertEqual(p.destination_ansi,b'abc')
        p=f.advance(capture(constructor=b'different'))
        self.assertEqual(p.destination_ansi,b'abc');self.assertEqual(self.labels(p).count('assign'),1)

    def test_assignment_requires_prefix_before_value_changes(self):
        o=capture();normal=dict(o.normal_returns);normal['assign_prefix']=False
        p=self.frame().advance(replace(o,normal_returns=normal))
        self.assertEqual(p.destination_ansi,b'old');self.assertFalse(p.destination_assigned)

    def test_cleanup_and_epilogue_gaps_preserve_assignment_without_completing(self):
        for role in ('cleanup','epilogue'):
            f=self.frame();o=capture();normal=dict(o.normal_returns);normal[role]=False
            p=f.advance(replace(o,normal_returns=normal))
            self.assertEqual(p.destination_ansi,b'abc');self.assertFalse(p.complete)
            self.assertEqual(p.temporary_ansi,b'abc' if role=='cleanup' else None)
            self.assertIsNone(p.return_target)
            p=f.advance(o);self.assertTrue(p.complete);self.assertIsNone(p.temporary_ansi);self.assertIs(f.advance(),p)

    def test_guard_change_cannot_switch_the_taken_branch_on_retry(self):
        f=self.frame();o=capture();normal=dict(o.normal_returns);normal['constructor']=False
        f.advance(replace(o,normal_returns=normal))
        p=f.advance(capture(b'xyz',bad=1))
        self.assertEqual((p.branch,p.destination_ansi),('readable',b'abc'))

    def test_raw_types_and_immutable_snapshots_are_required(self):
        with self.assertRaises(ValueError):self.frame().advance(capture(raw=bytearray(b'abc')))
        with self.assertRaises(ValueError):self.frame().advance(capture(bad=True))
        with self.assertRaises(ValueError):QuestReadStringFrame(-1,1)


if __name__=='__main__':unittest.main()
