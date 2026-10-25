import unittest
from dataclasses import replace
from jail_protection import JailObservation
from profile_string import ProfileStringFrame


def frame():return ProfileStringFrame(section=1,key=2,path=3,default=4,output=5)


def sample(**changes):
    values={name+s:v for name,v in (('path',0x100),('default',0x200),('key',0x300),('section',0x400))
            for s in ('_test_pointer','_value_pointer')}
    values.update(buffer_construct_eax=0x500,output_slot_return=0x600,saved_fs=0x1234)
    values.update(changes)
    labels=('prologue','default_convert','path_convert','key_convert','section_convert','profile_api','buffer_construct',
            'output_assign','temp_cleanup','section_cleanup','key_cleanup','path_cleanup','default_cleanup','fs_restore','epilogue')
    return JailObservation(True,values,{n:True for n in labels})


class ProfileStringTests(unittest.TestCase):
    def test_entry_and_prologue_before_all_conversions(self):
        f=frame();self.assertEqual(f.advance(JailObservation()).needed,('entry','0045f228'))
        p=f.advance(JailObservation(True));self.assertEqual(p.needed,('normal','prologue'));self.assertFalse(p.reads)

    def test_formal_conversion_order_and_slots(self):
        p=frame().advance(sample());self.assertTrue(p.complete)
        self.assertEqual([label for _,_,label in p.calls][1:5],['default_convert','path_convert','key_convert','section_convert'])
        self.assertIn(('00504ef8',(('source_formal_slot',24),('source_formal_slot',24)),'default_convert'),p.calls)
        self.assertEqual(p.formal_arguments,(1,2,3,4,5))

    def test_full_api_push_order_and_capacity(self):
        p=frame().advance(sample())
        self.assertIn(('GetPrivateProfileStringA',(0x100,255,'source_profile_stack_buffer',0x200,0x300,0x400),'profile_api'),p.calls)

    def test_null_formals_select_four_empty_literals(self):
        o=sample(**{n+'_test_pointer':0 for n in ('path','default','key','section')})
        o=replace(o,values={k:v for k,v in o.values.items() if not k.endswith('_value_pointer')})
        p=frame().advance(o);self.assertTrue(p.complete)
        self.assertIn(('GetPrivateProfileStringA',(0x52348a,255,'source_profile_stack_buffer',0x523489,0x523488,0x523487),'profile_api'),p.calls)

    def test_fresh_test_and_value_reads_can_differ(self):
        p=frame().advance(sample(path_value_pointer=0))
        self.assertIn(('GetPrivateProfileStringA',(0,255,'source_profile_stack_buffer',0x200,0x300,0x400),'profile_api'),p.calls)

    def test_api_count_not_consumed_or_returned(self):
        for count in (0,254,0xffffffff):
            p=frame().advance(sample(profile_api_eax=count))
            self.assertTrue(p.complete);self.assertEqual(p.return_eax,0x600)
            self.assertFalse(any(r[2]=='profile_api_eax' for r in p.reads))

    def test_api_normal_then_buffer_construct_value_are_separate(self):
        o=sample();f=frame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'profile_api':False}))
        self.assertEqual(p.needed,('normal','profile_api'));self.assertFalse(p.assignment_intents)
        o=replace(o,values={k:v for k,v in o.values.items() if k!='buffer_construct_eax'})
        p=f.advance(o);self.assertEqual(p.needed,('value','buffer_construct_eax'))

    def test_assignment_intent_not_memory_success(self):
        o=sample();p=frame().advance(replace(o,normal_returns={**o.normal_returns,'output_assign':False}))
        self.assertEqual(p.assignment_intents,((5,0x500),));self.assertIsNone(p.return_eax)
        self.assertFalse(p.assignment_effects_verified)

    def test_return_captured_before_temp_and_formal_cleanup(self):
        o=sample();f=frame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'temp_cleanup':False}))
        self.assertEqual(p.return_eax,0x600);self.assertFalse(p.complete)
        p=f.advance(sample(output_slot_return=0));self.assertTrue(p.complete);self.assertEqual(p.return_eax,0x600)

    def test_fs_and_frame_return_separate(self):
        o=sample();f=frame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'fs_restore':False}))
        self.assertEqual(p.needed,('normal','fs_restore'))
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'epilogue':False}))
        self.assertEqual(p.needed,('normal','epilogue'));self.assertTrue(f.advance(o).complete)

    def test_raw_argument_and_source_guards(self):
        for bad in (True,-1,1<<32):
            with self.assertRaises(ValueError):ProfileStringFrame(section=1,key=2,path=3,default=4,output=bad)
        with self.assertRaises(ValueError):ProfileStringFrame(section=1,key=2,path=3,default=4,output=5,source_sha256='unknown')
