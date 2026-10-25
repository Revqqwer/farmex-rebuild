import unittest
from dataclasses import replace,FrozenInstanceError
from route_coordinate_click import *
from current_coordinates import GuardedFloatSample
from test_current_coordinates import sample


class Sink:
    def __init__(self,fail=None):self.rows=[];self.events=[];self.fail=fail
    def add_row(self):
        self.events.append('add');row=['',[]];self.rows.append(row);return row
    def validate(self,row):
        if not any(r is row for r in self.rows):raise ValueError('own row invalidated')
    def set_caption(self,row,text):self.events.append('caption');row[0]=text
    def add_subitem(self,row,text):
        phase='sub%d'%(len(row[1])+1);self.events.append(phase)
        if phase==self.fail:raise OSError('own setter failed')
        row[1].append(text)


class CoordinateClickTests(unittest.TestCase):
    def test_add_caption_precedes_missing_coordinate_capture_without_fake_zero(self):
        sink=Sink();f=CoordinateClickFrame(sink);p=f.advance()
        self.assertFalse(p.done);self.assertEqual(sink.rows,[['Koordinat',[]]])
        self.assertEqual(sink.events,['add','caption']);self.assertEqual(p.coordinates.axes[0].needed,('root_address_dword',))

    def test_both_axes_before_first_parameter_and_no_duplicate_setters(self):
        sink=Sink();f=CoordinateClickFrame(sink)
        p=f.advance(CoordinateClickInput(sample(eax=0xffffffff)))
        self.assertEqual(sink.rows,[['Koordinat',[]]]);self.assertFalse(p.done)
        p=f.advance(CoordinateClickInput(y=sample(root_address=0x200,root=0x2000,eax=5)))
        self.assertTrue(p.complete);self.assertTrue(p.done);self.assertEqual(sink.rows,[['Koordinat',['-1','5']]])
        self.assertIs(f.advance(),p);self.assertEqual(sink.events,['add','caption','sub1','sub2'])

    def test_second_setter_failure_retains_first_parameter_and_is_terminal(self):
        sink=Sink('sub2');f=CoordinateClickFrame(sink)
        p=f.advance(CoordinateClickInput(sample(eax=1),sample(eax=2)))
        self.assertTrue(p.done);self.assertFalse(p.complete);self.assertEqual(sink.rows,[['Koordinat',['1']]])
        self.assertIs(f.advance(),p)

    def test_invalid_reached_capture_is_pending_and_can_resume_without_new_row(self):
        sink=Sink();f=CoordinateClickFrame(sink)
        bad=replace(sample(),float_sample=GuardedFloatSample(99,1,0))
        p=f.advance(CoordinateClickInput(bad));self.assertFalse(p.done);self.assertTrue(p.error)
        p=f.advance(CoordinateClickInput(sample(),sample(eax=8)))
        self.assertTrue(p.complete);self.assertEqual(len(sink.rows),1);self.assertEqual(sink.events.count('add'),1)

    def test_invalidated_target_does_not_write_into_replacement_row(self):
        sink=Sink();f=CoordinateClickFrame(sink);f.advance();sink.rows[:]=[['replacement',[]]]
        p=f.advance(CoordinateClickInput(sample(),sample()))
        self.assertTrue(p.done);self.assertFalse(p.complete);self.assertEqual(sink.rows,[['replacement',[]]])
        self.assertIsNone(f.axes.x.observation.root_address_dword)

    def test_cancel_is_terminal_even_after_hold(self):
        sink=Sink();f=CoordinateClickFrame(sink);f.advance();p=f.cancel('own profile change')
        self.assertIs(f.hold('late provider failure'),p);self.assertIs(f.advance(CoordinateClickInput(sample(),sample())),p)
        self.assertEqual(sink.rows,[['Koordinat',[]]])

    def test_reentrant_sink_advance_does_not_add_another_row(self):
        sink=Sink();f=CoordinateClickFrame(sink);original=sink.add_row
        def add():f.advance();return original()
        sink.add_row=add;f.advance();self.assertEqual(len(sink.rows),1)

    def test_capture_type_and_context_are_explicit(self):
        with self.assertRaises(ValueError):CoordinateClickInput(x={})
        f=CoordinateClickFrame(Sink());p=f.advance({});self.assertFalse(p.done);self.assertTrue(p.error)
        context=CoordinateCaptureContext(1,2,'x',('root_address_dword',))
        with self.assertRaises(FrozenInstanceError):context.axis='y'


if __name__=='__main__':unittest.main()
