import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_probe import RelogProbeFrame,RelogProbeBindingFrame,RelogProbeBindingObservation
import test_relog_gate as gate_fixture
import test_relog_controller as controller_fixture


def sample(**changes):
    values=dict(state_initial=0,state_increment=0,state_second=1,
                first_eax=0,second_eax=1,third_eax=0,fourth_eax=0,fifth_eax=0)
    values.update(changes)
    labels=['prologue','epilogue']+[x+s for x in ('first','second','third','fourth','fifth') for s in ('_before','','_after')]
    return JailObservation(True,values,{k:True for k in labels})


def parent(kind,**changes):
    if kind=='gate':o=gate_fixture.sample(install_attempted_byte=0,**changes);keys=('install_probe_eax','install_probe_local')
    else:o=controller_fixture.sample(bootstrap_done_byte=0,**changes);keys=('bootstrap_probe_eax','bootstrap_local_dword')
    return replace(o,values={k:v for k,v in o.values.items() if k not in keys})


class RelogProbeTests(unittest.TestCase):
    def test_entry_and_prologue_precede_all_reads(self):
        f=RelogProbeFrame();self.assertEqual(f.advance(JailObservation()).needed,('entry','004e2bc8'))
        p=f.advance(JailObservation(True));self.assertEqual(p.needed,('normal','prologue'));self.assertFalse(p.reads)

    def test_three_first_branch_results_and_low_al(self):
        for changes,code,labels in ((dict(first_eax=0x10001),1,['first']),
          (dict(second_eax=0x100),2,['first','second']),
          (dict(third_eax=0x123402),3,['first','second','third'])):
            with self.subTest(code=code):
                p=RelogProbeFrame().advance(sample(**changes));self.assertTrue(p.complete)
                self.assertEqual((p.output_code,p.return_al,p.return_eax),(code,1,None))
                actual=[label for _,_,label in p.calls if label in ('first','second','third','fourth','fifth')]
                self.assertEqual(actual,labels)

    def test_first_branch_failure_is_status91_not_elapsed_time(self):
        p=RelogProbeFrame().advance(sample());self.assertEqual((p.output_code,p.return_al,p.return_eax),(91,0,0))
        self.assertEqual(p.stores,((0x56ff3c,4,1),('source_local_dword',4,91)))

    def test_second_branch_results_and_failure92(self):
        for changes,code,success in ((dict(fourth_eax=2),4,1),(dict(fifth_eax=0x101),5,1),({},92,0)):
            p=RelogProbeFrame().advance(sample(state_initial=1,**changes))
            self.assertEqual((p.output_code,p.return_al),(code,success))
            self.assertEqual(p.stores[0],(0x56ff3c,4,0))
            self.assertFalse(any(label=='first' for _,_,label in p.calls))

    def test_second_state_read_is_fresh(self):
        p=RelogProbeFrame().advance(sample(state_initial=0xffffffff,state_second=1))
        self.assertEqual(p.output_code,92)
        self.assertEqual([x[2] for x in p.reads],['state_initial','state_second'])

    def test_invalid_state_leaves_output_unwritten(self):
        p=RelogProbeFrame().advance(sample(state_initial=1,state_second=2))
        self.assertTrue(p.complete);self.assertIsNone(p.output_code)
        self.assertEqual(p.return_eax,0);self.assertFalse(p.stores)
        self.assertEqual([label for _,_,label in p.calls],['prologue','epilogue'])

    def test_increment_reloads_and_wraps(self):
        p=RelogProbeFrame().advance(sample(state_increment=0xffffffff))
        self.assertEqual(p.stores[0],(0x56ff3c,4,0))
        p=RelogProbeFrame().advance(sample(state_increment=9));self.assertEqual(p.stores[0][2],10)

    def test_detector_eax_captured_before_after_call(self):
        f=RelogProbeFrame();o=sample(first_eax=1)
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'first_after':False}))
        self.assertEqual(p.needed,('normal','first_after'));self.assertIsNone(p.output_code)
        p=f.advance(sample(first_eax=0));self.assertEqual(p.output_code,1)

    def test_resume_preserves_state_store_and_waits_on_detector_return(self):
        f=RelogProbeFrame();o=sample()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'second':False}))
        self.assertEqual(p.needed,('normal','second'));self.assertEqual(p.stores,((0x56ff3c,4,1),))
        p=f.advance(o);self.assertEqual(len(p.stores),2)

    def test_epilogue_is_separate_after_output_store(self):
        o=sample();f=RelogProbeFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'epilogue':False}))
        self.assertFalse(p.complete);self.assertEqual(p.output_code,91)
        self.assertEqual(p.needed,('normal','epilogue'));self.assertTrue(f.advance(o).complete)

    def test_both_parents_derive91_and_reach_replacement(self):
        for kind,label in (('controller','bootstrap_replace'),('gate','install_replace')):
            o=parent(kind);o=replace(o,normal_returns={**o.normal_returns,label:False})
            p=RelogProbeBindingFrame(kind).advance(RelogProbeBindingObservation(o,sample()))
            self.assertTrue(p.probe.complete)
            self.assertEqual(p.parent.needed,('normal',label))

    def test_parent_return_receipt_still_required_after_child(self):
        o=parent('gate');o=replace(o,normal_returns={**o.normal_returns,'install_probe':False})
        f=RelogProbeBindingFrame('gate');p=f.advance(RelogProbeBindingObservation(o,sample()))
        self.assertTrue(p.probe.complete);self.assertEqual(p.parent.needed,('normal','install_probe'))
        p=f.advance(RelogProbeBindingObservation(parent('gate'),sample()));self.assertTrue(p.complete)

    def test_success_does_not_invent_upper_eax(self):
        o=parent('gate');f=RelogProbeBindingFrame('gate')
        p=f.advance(RelogProbeBindingObservation(o,sample(first_eax=1)))
        self.assertEqual(p.parent.needed,('value','install_probe_eax'))
        o=replace(o,values={**o.values,'install_probe_eax':0xabcde001})
        p=f.advance(RelogProbeBindingObservation(o,sample()));self.assertTrue(p.complete)
        self.assertFalse(any(label=='install_replace' for _,_,label in p.parent.calls))

    def test_invalid_state_requires_captured_caller_local(self):
        o=parent('gate');f=RelogProbeBindingFrame('gate')
        child=sample(state_initial=2,state_second=2)
        p=f.advance(RelogProbeBindingObservation(o,child))
        self.assertEqual(p.parent.needed,('value','install_probe_local'))
        self.assertIsNone(p.probe.output_code)
        o=replace(o,values={**o.values,'install_probe_local':0xffffffff})
        p=f.advance(RelogProbeBindingObservation(o,child));self.assertTrue(p.complete)
        self.assertFalse(any(label=='install_replace' for _,_,label in p.parent.calls))

    def test_conflicting_results_rejected_and_unreached_probe_not_created(self):
        o=parent('gate');o=replace(o,values={**o.values,'install_probe_local':90})
        with self.assertRaises(ValueError):RelogProbeBindingFrame('gate').advance(RelogProbeBindingObservation(o,sample()))
        o=parent('gate');o=replace(o,values={**o.values,'install_probe_eax':0})
        with self.assertRaises(ValueError):RelogProbeBindingFrame('gate').advance(RelogProbeBindingObservation(o,sample(first_eax=1)))
        f=RelogProbeBindingFrame('gate');p=f.advance(RelogProbeBindingObservation(gate_fixture.sample(),sample()))
        self.assertTrue(p.complete);self.assertIsNone(f.child)

    def test_typed_boundary_validation(self):
        with self.assertRaises(ValueError):RelogProbeBindingFrame('unknown')
        with self.assertRaises(ValueError):RelogProbeBindingObservation(parent={})
        with self.assertRaises(ValueError):RelogProbeFrame().advance({})
        with self.assertRaises(ValueError):RelogProbeBindingFrame('gate').advance(JailObservation())
