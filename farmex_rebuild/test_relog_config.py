import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_config import RelogConfigFrame,COMMON,USKO,STEAM


def sample(mode=2,copy=False,**changes):
    values={'mode_byte':mode,'saved_fs':0x1234,'id_alloc_eax':0x3000,'pw_alloc_eax':0x4000,
            'id_compare_eax':int(copy),'pw_compare_eax':int(copy)}
    labels=['prologue','fs_restore','epilogue','id_alloc','pw_alloc','id_empty','id_compare',
            'pw_empty','pw_compare','id_empty_cleanup','pw_empty_cleanup','id_cleanup','pw_cleanup',
            'id_length.metadata','pw_length.metadata','id_copy','pw_copy']
    for label,_,_,_,_ in COMMON+USKO+STEAM:
        values.update({label+'.handle':0x1000,label+'.key_pointer':0x100,label+'.section_pointer':0x200,label+'.eax':0})
        labels.extend(label+s for s in ('.key','.section','.read','.section_cleanup','.key_cleanup'))
    for label in ('captcha_detail','id','pw'):
        values.update({label+'.handle':0x1000,label+'.default_pointer':0x300,label+'.key_pointer':0x100,
                       label+'.section_pointer':0x200,label+'.output_eax':0x500})
        labels.extend(label+s for s in ('.default','.key','.section','.output_prepare','.read','.convert',
                      '.assign','.ansi_cleanup','.output_cleanup','.section_cleanup','.key_cleanup','.default_cleanup'))
    values.update({'id_length.pointer':0x111,'id_length.metadata_eax':0xfffffff8,'id_length.length':5,
      'pw_length.pointer':0x222,'pw_length.metadata_eax':0x600,'pw_length.length':6,
      'id_copy_source.test':0x111,'id_copy_source.value':0x777,'pw_copy_source.test':0x222,'pw_copy_source.value':0x888,
      'id_copy.length':9,'pw_copy.length':10,'id_copy.destination':0x900,'pw_copy.destination':0xa00})
    values.update(changes)
    return JailObservation(True,values,{k:True for k in labels})


class RelogConfigTests(unittest.TestCase):
    def test_entry_and_prologue_before_all_reads(self):
        f=RelogConfigFrame();self.assertEqual(f.advance(JailObservation()).needed,('entry','00412f48'))
        p=f.advance(JailObservation(True));self.assertEqual(p.needed,('normal','prologue'));self.assertFalse(p.reads)

    def test_all_non_one_modes_use_steam(self):
        for mode in (0,2,255):
            p=RelogConfigFrame().advance(sample(mode))
            self.assertTrue(p.complete);self.assertEqual(p.branch,'STEAMLOGIN')
            self.assertFalse(any(h=='VirtualAlloc' for h,_,_ in p.calls))
            self.assertEqual(len(p.stores),7)

    def test_byte_truncation_and_dword_preservation(self):
        p=RelogConfigFrame().advance(sample(**{'captcha_enabled.eax':0x123402,'captcha_service.eax':0xffffffff,
                                              'steam_enabled.eax':0x100,'steam_server.eax':0xffffffff}))
        self.assertIn((0x561ed0,1,2),p.stores);self.assertIn((0x561ed4,4,0xffffffff),p.stores)
        self.assertIn((0x50b2d8,1,0),p.stores);self.assertIn((0x50b2cc,4,0xffffffff),p.stores)

    def test_fresh_handle_and_distinct_wrapper_push_order(self):
        p=RelogConfigFrame().advance(sample(**{'captcha_enabled.handle':0x11,'captcha_service.handle':0x22}))
        self.assertIn(('0045f508',(0,0x11,0x100,0x200),'captcha_enabled.read'),p.calls)
        self.assertIn(('0045f5f4',(0x22,0,0x100,0x200),'captcha_service.read'),p.calls)

    def test_scalar_store_precedes_cleanup_but_requires_read_return(self):
        o=sample();f=RelogConfigFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'captcha_enabled.read':False}))
        self.assertFalse(p.stores);self.assertEqual(p.needed,('normal','captcha_enabled.read'))
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'captcha_enabled.section_cleanup':False}))
        self.assertEqual(p.stores,((0x561ed0,1,0),));self.assertEqual(p.needed,('normal','captcha_enabled.section_cleanup'))

    def test_detail_query_assignment_and_cleanup_are_separate(self):
        o=sample();f=RelogConfigFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'captcha_detail.assign':False}))
        self.assertFalse(p.string_assignments);self.assertIsNone(p.branch)
        self.assertIn(('0045f228',(0x300,0x1000,0x100,0x200,0x500),'captcha_detail.read'),p.calls)
        p=f.advance(o);self.assertEqual(p.string_assignments,((0x561ed8,('source_ansi_output','captcha_detail')),))

    def test_usko_allocations_are_not_gated_by_login_flags(self):
        p=RelogConfigFrame().advance(sample(1))
        self.assertTrue(p.complete);self.assertEqual(p.branch,'USKO')
        self.assertEqual(sum(h=='VirtualAlloc' for h,_,_ in p.calls),2)
        self.assertIn(('VirtualAlloc',(0x40,0x1000,0x32,0),'id_alloc'),p.calls)
        self.assertIn((0x553c5c,4,0x3000),p.stores);self.assertIn((0x553c60,4,0x4000),p.stores)
        self.assertFalse(p.copy_intents)

    def test_id_compare_short_circuits_pw_and_keeps_lengths_untouched(self):
        p=RelogConfigFrame().advance(sample(1,**{'id_compare_eax':0x100}))
        self.assertFalse(any(label=='pw_compare' for _,_,label in p.calls))
        self.assertFalse(any(dest in (0x50b2c4,0x50b2c8) for dest,_,_ in p.stores))
        self.assertFalse(p.copy_intents)

    def test_pw_compare_false_skips_both_lengths_and_copies(self):
        p=RelogConfigFrame().advance(sample(1,True,**{'pw_compare_eax':0x100}))
        self.assertFalse(p.copy_intents)
        self.assertFalse(any(dest in (0x50b2c4,0x50b2c8) for dest,_,_ in p.stores))

    def test_metadata_length_addresses_and_fresh_copy_values(self):
        p=RelogConfigFrame().advance(sample(1,True))
        self.assertTrue(p.complete);self.assertIn((0,4,'id_length.length'),p.reads)
        self.assertIn((0x608,4,'pw_length.length'),p.reads)
        self.assertIn((0x50b2c4,4,5),p.stores);self.assertIn((0x50b2c8,4,6),p.stores)
        self.assertEqual(p.copy_intents,((0x900,0x777,9),(0xa00,0x888,10)))
        self.assertIn(('_memcpy',(9,0x777,0x900),'id_copy'),p.calls)

    def test_null_locals_and_fallback_literals(self):
        p=RelogConfigFrame().advance(sample(1,True,**{'id_length.pointer':0,'pw_length.pointer':0,
          'id_copy_source.test':0,'pw_copy_source.test':0}))
        self.assertIn((0x50b2c4,4,0),p.stores);self.assertIn((0x50b2c8,4,0),p.stores)
        self.assertFalse(any(label in ('id_length.metadata','pw_length.metadata') for _,_,label in p.calls))
        self.assertEqual(p.copy_intents,((0x900,0x50b3db,9),(0xa00,0x50b3dc,10)))

    def test_zero_allocation_and_oversize_copy_remain_inert_source_intents(self):
        p=RelogConfigFrame().advance(sample(1,True,**{'id_alloc_eax':0,'id_copy.destination':0,'id_copy.length':0xffffffff}))
        self.assertTrue(p.complete);self.assertIn((0x553c5c,4,0),p.stores)
        self.assertEqual(p.copy_intents[0],(0,0x777,0xffffffff))
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

    def test_compare_result_captured_before_cleanup_resume(self):
        o=sample(1,True);f=RelogConfigFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'pw_empty_cleanup':False}))
        self.assertEqual(p.needed,('normal','pw_empty_cleanup'));self.assertFalse(p.copy_intents)
        p=f.advance(sample(1,False));self.assertTrue(p.complete);self.assertEqual(len(p.copy_intents),2)

    def test_copy_prefix_survives_missing_native_return(self):
        o=sample(1,True);f=RelogConfigFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'id_copy':False}))
        self.assertEqual(p.copy_intents,((0x900,0x777,9),));self.assertEqual(p.needed,('normal','id_copy'))
        self.assertFalse(any(label=='pw_copy' for _,_,label in p.calls))
        p=f.advance(o);self.assertEqual(len(p.copy_intents),2)

    def test_fs_restore_and_epilogue_are_distinct(self):
        o=sample();f=RelogConfigFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'fs_restore':False}))
        self.assertEqual(p.needed,('normal','fs_restore'));self.assertFalse(p.complete)
        self.assertEqual(p.calls[-1],('source_FS_restore_span',(0x1234,),'fs_restore'))
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'epilogue':False}))
        self.assertEqual(p.needed,('normal','epilogue'));self.assertTrue(f.advance(o).complete)

    def test_raw_observation_validation_and_unreached_inputs(self):
        with self.assertRaises(ValueError):RelogConfigFrame('unknown')
        with self.assertRaises(ValueError):RelogConfigFrame().advance({})
        with self.assertRaises(ValueError):sample(mode=256)
        o=sample();keys={k:v for k,v in o.values.items() if not k.startswith(('id_','pw_','id.','pw.','usko_'))}
        p=RelogConfigFrame().advance(replace(o,values=keys));self.assertTrue(p.complete)
