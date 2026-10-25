import unittest
from dataclasses import replace
from route_resume import RouteResumeState as State,RouteResumeObservation as Read
from route_resume_paths import RouteResumePathObservation as Obs,plan_route_resume_path as plan,WRITES
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte

def sample(value):
    return Read(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,value))

class RouteResumePathTests(unittest.TestCase):
    def timed(self,**kw):
        values=dict(condition=sample(0),tail=sample(1),tick_dword=150,stamp_qword=100,
                    limit_dword=50,compare_span_returned=True,comparison_al=0)
        values.update(kw);return Obs(**values)
    def test_strict_wait_and_equal_due_boundary(self):
        wait=plan('timed',State(1,0),self.timed(tick_dword=149,tail=Read(),compare_span_returned=None))
        self.assertTrue(wait.complete);self.assertEqual(wait.status,'timed_wait_no_tail')
        self.assertEqual(wait.state,State(1,0));self.assertIsNone(wait.tail);self.assertEqual(wait.writes,())
        due=plan('timed',State(1,0),self.timed())
        self.assertTrue(due.complete);self.assertEqual(due.state,State(0,1));self.assertEqual(due.writes,WRITES)
    def test_first_nonzero_skips_unreached_clock_and_flag(self):
        for kind in ('timed','optional'):
            with self.subTest(kind=kind):
                d=plan(kind,State(3,0),Obs(sample(1),sample(0)))
                self.assertTrue(d.complete);self.assertIsNone(d.elapsed_signed);self.assertEqual(d.writes,WRITES)
    def test_first_nonzero_then_tail_nonzero_preserves_entry(self):
        d=plan('timed',State(3,7),Obs(sample(1),sample(2)))
        self.assertEqual(d.state,State(3,7));self.assertEqual(d.writes,())
    def test_tail_zero_repeats_writes_after_due_prefix(self):
        d=plan('timed',State(1,0),self.timed(tail=sample(0)))
        self.assertEqual(d.writes,WRITES+WRITES)
    def test_missing_tail_does_not_reuse_first_read_or_commit_prefix(self):
        d=plan('timed',State(1,0),self.timed(tail=Read()))
        self.assertFalse(d.complete);self.assertEqual(d.state,State(1,0))
        self.assertEqual(d.prospective_state,State(0,1));self.assertEqual(d.writes,WRITES)
        self.assertIn('common tail',d.missing)
    def test_string_span_and_saved_al_and_notification_are_separate(self):
        for kw,part in ((dict(compare_span_returned=None),'comparison/string'),
                        (dict(comparison_al=None),'comparison AL'),
                        (dict(comparison_al=1),'00459fb0')):
            with self.subTest(kw=kw):
                d=plan('timed',State(1,0),self.timed(**kw))
                self.assertFalse(d.complete);self.assertEqual(d.writes,());self.assertIn(part,d.missing)
        d=plan('timed',State(1,0),self.timed(comparison_al=255,notification_returned=True))
        self.assertTrue(d.complete)
    def test_optional_flag_zero_skips_helper_but_requires_fresh_tail(self):
        d=plan('optional',State(1,0),Obs(sample(0),sample(1),optional_flag_byte=0))
        self.assertTrue(d.complete);self.assertEqual(d.writes,WRITES)
    def test_optional_nonzero_requires_normal_helper_return(self):
        o=Obs(sample(0),sample(1),optional_flag_byte=2)
        d=plan('optional',State(1,0),o)
        self.assertFalse(d.complete);self.assertEqual(d.writes,());self.assertIn('0047789c',d.missing)
        self.assertTrue(plan('optional',State(1,0),replace(o,optional_helper_returned=True)).complete)
    def test_signed_limit_and_full_qword_elapsed_cases(self):
        cases=((0,1,0,False,-1,0),(0,1,0xffffffff,True,-1,-1),
               (0xffffffff,0,0x7fffffff,True,0xffffffff,0x7fffffff),
               (0,1<<32,0,False,-(1<<32),0),
               (0,(1<<64)-1,1,True,1,1),
               (0,0x8000000000000000,0x80000000,False,-(1<<63),-(1<<31)))
        for tick,stamp,limit,due,elapsed,signed_limit in cases:
            with self.subTest(tick=tick,stamp=stamp,limit=limit):
                d=plan('timed',State(1,0),self.timed(tick_dword=tick,stamp_qword=stamp,limit_dword=limit))
                self.assertTrue(d.complete);self.assertEqual(d.elapsed_signed,elapsed);self.assertEqual(d.limit_signed,signed_limit)
                self.assertEqual(bool(d.writes),due)
    def test_missing_each_reached_scalar_stops_before_writes(self):
        for field in ('tick_dword','stamp_qword','limit_dword'):
            d=plan('timed',State(1,0),replace(self.timed(),**{field:None}))
            self.assertFalse(d.complete);self.assertEqual(d.writes,())
        d=plan('optional',State(1,0),Obs(sample(0),sample(1)))
        self.assertFalse(d.complete);self.assertEqual(d.writes,())
    def test_missing_first_read_is_not_success(self):
        d=plan('timed',State(1,0),Obs(tail=sample(0)))
        self.assertFalse(d.complete);self.assertEqual(d.writes,());self.assertIsNone(d.tail)
    def test_types(self):
        for kw in (dict(tick_dword=True),dict(limit_dword=-1),dict(stamp_qword=1<<64),
                   dict(comparison_al=256),dict(optional_helper_returned=1)):
            with self.assertRaises(ValueError):Obs(**kw)
        with self.assertRaises(ValueError):plan('guessed',State(1,0),Obs())

if __name__=='__main__':unittest.main()
