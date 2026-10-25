import unittest
from route_gate_runtime import OwnedGateRecording
from route_gate_record import GateRecordObservation
from test_route_gate_record import observed
from route_npc_click import NpcValueCapture as C
from test_route_coordinate_click import Sink


class GateRuntimeTests(unittest.TestCase):
    def session(self,enabled=True):
        sink=Sink();flag=[enabled];session=OwnedGateRecording(lambda:sink,lambda:flag[0])
        return sink,flag,session

    def test_checkbox_owns_flag_and_disabled_direct_branch_needs_no_provider(self):
        sink,flag,s=self.session(False);calls=[]
        s.set_provider(lambda c:calls.append(c) or observed(recording_byte=1))
        self.assertEqual(s.dispatch(b'\x33').status,'recording_disabled')
        self.assertEqual(calls,[]);self.assertEqual(sink.rows,[])
        flag[0]=True;s.dispatch(b'\x33\x01\0\0\0')
        self.assertEqual(sink.rows,[['Gate Open',['1','-']]])

    def test_clock_shadow_is_committed_before_checkbox_read_even_disabled(self):
        sink,flag,s=self.session(False);seen=[]
        s.read_recording=lambda:seen.append(dict(s.clock_shadow)) or False
        s.set_provider(lambda c:observed(clock=C(7,True),recording_byte=1))
        self.assertEqual(s.dispatch(b'\x4b').status,'recording_disabled')
        self.assertEqual(seen,[{0x561f74:7,0x561f78:0}]);self.assertEqual(sink.rows,[])

    def test_checkbox_waits_for_clock_normal_return_and_is_read_fresh_after_provider(self):
        sink,flag,s=self.session(True);ready=[False];seen=[]
        s.read_recording=lambda:seen.append(True) or flag[0]
        def provider(c):
            if ready[0]:flag[0]=False
            return observed(clock=C(8,ready[0]))
        s.set_provider(provider);s.dispatch(b'\x4b\x01\0\0\0')
        self.assertEqual(seen,[]);self.assertEqual(s.clock_shadow,{})
        ready[0]=True;p=s.advance();self.assertEqual(p.status,'recording_disabled')
        self.assertEqual(seen,[True]);self.assertEqual(sink.rows,[])

    def test_no_implicit_provider_or_clock_and_late_formatter_keeps_one_row(self):
        sink,flag,s=self.session();p=s.dispatch(b'\x33\x01\0\0\0')
        self.assertFalse(p.done);self.assertEqual(sink.rows,[])
        s.reset('test');ready=[False]
        s.set_provider(lambda c:observed(format_returned=ready[0]))
        s.dispatch(b'\x33\x02\0\0\0');self.assertEqual(sink.rows,[['Gate Open',[]]])
        s.advance();self.assertEqual(len(sink.rows),1)
        ready[0]=True;self.assertTrue(s.advance().complete)
        self.assertEqual(sink.rows,[['Gate Open',['2','-']]])

    def test_reentrant_dispatch_is_fifo_and_does_not_replace_current_frame(self):
        sink,flag,s=self.session();entered=[False]
        def provider(c):
            if not entered[0]:entered[0]=True;s.dispatch(b'\x33\x02\0\0\0')
            return observed()
        s.set_provider(provider);s.dispatch(b'\x33\x01\0\0\0')
        self.assertEqual(sink.rows,[['Gate Open',['1','-']]]);self.assertEqual(len(s.pending),1)
        s.advance();self.assertEqual(sink.rows[-1],['Gate Open',['2','-']])

    def test_provider_generation_change_drops_stale_capture_without_row(self):
        sink,flag,s=self.session()
        def provider(c):s.reset('profile');return observed()
        s.set_provider(provider);generation=s.generation;s.dispatch(b'\x33\x01\0\0\0')
        self.assertEqual(sink.rows,[]);self.assertEqual(s.pending,[]);self.assertIsNone(s.result)
        self.assertIsNone(s.advance(generation))

    def test_provider_errors_are_pending_and_recoverable_without_duplicate_prefix(self):
        sink,flag,s=self.session();bad=[True]
        def provider(c):
            if bad[0]:raise OSError('capture unavailable')
            return observed()
        s.set_provider(provider);p=s.dispatch(b'\x33\x01\0\0\0')
        self.assertFalse(p.done);self.assertIn('unavailable',p.error);self.assertEqual(sink.rows,[])
        bad[0]=False;self.assertTrue(s.advance().complete);self.assertEqual(len(sink.rows),1)

    def test_invalid_provider_type_is_pending_and_clock_metadata_survives_reset(self):
        sink,flag,s=self.session(False);s.set_provider(lambda c:{})
        p=s.dispatch(b'\x4b');self.assertFalse(p.done);self.assertTrue(p.error)
        s.set_provider(lambda c:observed(clock=C(9,True)));s.dispatch(b'\x4b')
        s.reset('profile');self.assertEqual(s.clock_shadow,{0x561f74:9,0x561f78:0})


if __name__=='__main__':unittest.main()
