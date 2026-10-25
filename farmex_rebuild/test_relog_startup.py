import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_startup import RelogStartupFrame,RelogStartupChildrenFrame,RelogStartupChildrenObservation
from detector_code_state import CURRENT,LEGACY
import test_callback_replacement as replacement_fixture
import test_detector_code_state as state_fixture


def sample(**changes):
    values={'ready0.slot':0x100,'ready0.root_eax':0x200,'ready0.offset':0x10,'ready0.object_eax':0x300,
      'ready1.slot':0x400,'ready1.root_eax':0x500,'ready1.offset':0x20,'ready1.object_eax':0x600,
      'install.slot':0x700,'install.root_eax':0x800,'install.offset':0x30,'install.object_eax':0x900,
      'install.table_eax':0xfffffff0,'install.slot_offset':0x30,'install.slot_fresh':0x7777,
      'next_slot_base':0x2000,'next_slot_offset':0x40}
    values.update(changes)
    labels=('prologue','ready0.root','ready0.object','ready0.sleep','ready1.root','ready1.object','ready1.sleep',
      'prepare','prepare_second','prepare_third','prepare_fourth','install.root','install.object','install.table',
      'replace','config','code_state','finish_first','finish_second','epilogue')
    return JailObservation(True,values,{k:True for k in labels})


def bound(parent=None,code=None,replacement=None):
    return RelogStartupChildrenObservation(parent or sample(),replacement or replacement_fixture.child(),
                                           code or state_fixture.sample(1))


class RelogStartupTests(unittest.TestCase):
    def test_entry_and_prologue(self):
        f=RelogStartupFrame(CURRENT)
        self.assertEqual(f.advance(JailObservation()).needed,('entry','00424924'))
        self.assertEqual(f.advance(JailObservation(True)).needed,('normal','prologue'))

    def test_first_ready_check_has_no_sleep(self):
        p=RelogStartupFrame(CURRENT).advance(sample())
        self.assertTrue(p.complete);self.assertEqual(p.ready_iterations,1)
        self.assertFalse(any(h=='SleepEx' for h,_,_ in p.calls))

    def test_zero_ready_sleeps_and_repeats_fresh_chain(self):
        p=RelogStartupFrame(CURRENT).advance(sample(**{'ready0.object_eax':0}))
        self.assertTrue(p.complete);self.assertEqual(p.ready_iterations,2)
        sleep=next(c for c in p.calls if c[0]=='SleepEx');self.assertEqual(sleep[1],(0,1))
        root=next(c for c in p.calls if c[2]=='ready1.root');self.assertEqual(root[1],(0x400,))
        obj=next(c for c in p.calls if c[2]=='ready1.object');self.assertEqual(obj[1],(0x520,))

    def test_no_fictional_loop_limit_or_ready_object_reuse(self):
        p=RelogStartupFrame(CURRENT).advance(sample(**{'ready0.object_eax':0,'ready1.object_eax':0}))
        self.assertEqual(p.needed,('value','ready2.slot'));self.assertFalse(p.stores)

    def test_install_chain_is_fresh_and_wraps_offset(self):
        p=RelogStartupFrame(CURRENT).advance(sample(**{'install.root_eax':0xfffffff0}))
        self.assertIn(('0045dc44',(0x20,),'install.object'),p.calls)
        self.assertIn(('0045dc44',(0x900,),'install.table'),p.calls)
        self.assertEqual(p.stores,((0x554210,4,0x20),(0x554214,4,0x2040)))

    def test_zero_install_object_still_reaches_table_and_replacement(self):
        p=RelogStartupFrame(CURRENT).advance(sample(**{'install.object_eax':0}))
        self.assertTrue(p.complete)
        self.assertIn(('0045dc44',(0,),'install.table'),p.calls)
        self.assertIn(('0046b8fc',(0x412adc,0x7777,0x554220),'replace'),p.calls)

    def test_store_then_fresh_slot_reload(self):
        o=sample();f=RelogStartupFrame(CURRENT)
        o=replace(o,values={k:v for k,v in o.values.items() if k!='install.slot_fresh'})
        p=f.advance(o);self.assertEqual(p.needed,('value','install.slot_fresh'))
        self.assertEqual(p.stores,((0x554210,4,0x20),))
        p=f.advance(sample(**{'install.slot_fresh':0x8888}))
        self.assertIn(('0046b8fc',(0x412adc,0x8888,0x554220),'replace'),p.calls)

    def test_config_then_code_state_then_future_slot(self):
        f=RelogStartupFrame(CURRENT);o=sample()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'config':False}))
        self.assertEqual(p.needed,('normal','config'));self.assertEqual(len(p.stores),1)
        self.assertFalse(any(label=='code_state' for _,_,label in p.calls))
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'code_state':False}))
        self.assertEqual(p.calls[-1],('004e2a88',(1,),'code_state'));self.assertEqual(len(p.stores),1)
        p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(len(p.stores),2)

    def test_future_base_is_direct_value_not_a_dereference(self):
        p=RelogStartupFrame(CURRENT).advance(sample(next_slot_base=0xfffffff0,next_slot_offset=0x30))
        self.assertEqual(p.stores[-1],(0x554214,4,0x20))
        self.assertEqual([r[0] for r in p.reads if r[2].startswith('next_')],[0x553f68,0x554204])

    def test_version_specific_prepare_and_code_helpers(self):
        for sha,a,b in ((CURRENT,'004e30c8','004e2a88'),(LEGACY,'004e30ac','004e2a6c')):
            p=RelogStartupFrame(sha).advance(sample())
            self.assertIn((a,(),'prepare'),p.calls);self.assertIn((b,(1,),'code_state'),p.calls)

    def test_children_derive_args_and_preserve_source_order(self):
        f=RelogStartupChildrenFrame(CURRENT);p=f.advance(bound())
        self.assertTrue(p.complete)
        c=f.frames['replace'];self.assertEqual((c.saved_cell,c.target_slot,c.replacement),(0x554220,0x7777,0x412adc))
        c=f.frames['code_state'];self.assertEqual((c.source_sha256,c.mode),(CURRENT,1))
        self.assertEqual(tuple(p.children),('replace','code_state'))
        with self.assertRaises(TypeError):p.children['other']=None

    def test_unreached_children_absent(self):
        o=sample();o=replace(o,normal_returns={**o.normal_returns,'prepare':False})
        f=RelogStartupChildrenFrame(CURRENT);p=f.advance(bound(o))
        self.assertFalse(p.complete);self.assertFalse(f.frames)

    def test_child_completion_does_not_imply_outer_return(self):
        o=sample();o=replace(o,normal_returns={**o.normal_returns,'replace':False})
        f=RelogStartupChildrenFrame(CURRENT);p=f.advance(bound(o))
        self.assertTrue(p.children['replace'].complete)
        self.assertEqual(p.needed,('parent',('normal','replace')));self.assertNotIn('code_state',f.frames)
        p=f.advance(bound());self.assertTrue(p.complete)

    def test_child_gaps_retain_parent_prefix_and_never_skip_to_code_state(self):
        o=replacement_fixture.child();o=replace(o,normal_returns={**o.normal_returns,'copy4':False})
        f=RelogStartupChildrenFrame(CURRENT);p=f.advance(bound(replacement=o))
        self.assertEqual(p.needed,('replace',('normal','copy4')))
        self.assertEqual(p.parent.stores,((0x554210,4,0x20),));self.assertNotIn('code_state',f.frames)
        p=f.advance(bound());self.assertTrue(p.complete)

    def test_code_state_child_must_complete_before_future_slot(self):
        f=RelogStartupChildrenFrame(CURRENT);p=f.advance(bound(code=state_fixture.sample(0)))
        self.assertEqual(p.needed,('code_state',('normal','byte0.read')))
        self.assertEqual(len(p.parent.stores),1);self.assertTrue(p.children['replace'].complete)
        code=state_fixture.complete_fixture(CURRENT,1,0)
        p=f.advance(bound(code=code));self.assertTrue(p.complete)
        self.assertEqual(len(p.children['code_state'].byte_write_intents),5660)

    def test_final_epilogue_separate_and_invalid_types_rejected(self):
        o=sample();f=RelogStartupFrame(CURRENT)
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'epilogue':False}))
        self.assertEqual(len(p.stores),2);self.assertFalse(p.complete)
        self.assertTrue(f.advance(o).complete)
        with self.assertRaises(ValueError):RelogStartupFrame('unknown')
        with self.assertRaises(ValueError):RelogStartupChildrenObservation(parent={})
        with self.assertRaises(ValueError):RelogStartupChildrenFrame(CURRENT).advance(JailObservation())
