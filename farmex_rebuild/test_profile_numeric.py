import unittest
from dataclasses import replace
from profile_numeric import ProfileNumericFrame
from jail_protection import JailObservation


def sample(api=0,**extra):
    values=dict(path_test_pointer=0x100,path_value_pointer=0x900,key_test_pointer=0x200,key_value_pointer=0x800,
                section_test_pointer=0x300,section_value_pointer=0x700,profile_api_eax=api,saved_fs=0x1234)
    values.update(extra)
    return JailObservation(True,values,{n:True for n in ('prologue','path_convert','key_convert','section_convert',
      'profile_api','section_cleanup','key_cleanup','path_cleanup','fs_restore','epilogue')})


def frame(kind='boolean',default=0):return ProfileNumericFrame(kind,section=1,key=2,path=3,default=default)


class ProfileNumericTests(unittest.TestCase):
    def test_entry_and_prologue(self):
        f=frame();self.assertEqual(f.advance(JailObservation()).needed,('entry','0045f508'))
        self.assertEqual(f.advance(JailObservation(True)).needed,('normal','prologue'))

    def test_boolean_normalizes_full_api_result(self):
        for raw,result in ((0,0),(1,1),(2,1),(256,1),(0xffffffff,1)):
            self.assertEqual(frame().advance(sample(raw)).return_eax,result)

    def test_dword_retains_all_bits(self):
        for raw in (0,1,256,0xffffffff):self.assertEqual(frame('dword').advance(sample(raw)).return_eax,raw)

    def test_boolean_default_byte_vs_dword_default(self):
        for kind,default in (('boolean',1),('dword',0x101)):
            p=frame(kind,0x101).advance(sample())
            self.assertIn(('GetPrivateProfileIntA',(0x900,default,0x800,0x700),'profile_api'),p.calls)

    def test_converted_formals_are_fresh_after_all_conversions(self):
        o=sample();f=frame();o=replace(o,normal_returns={**o.normal_returns,'section_convert':False})
        p=f.advance(o);self.assertFalse(p.reads);self.assertEqual(p.needed,('normal','section_convert'))
        p=f.advance(sample(path_value_pointer=0x999));self.assertTrue(p.complete)
        self.assertIn(('GetPrivateProfileIntA',(0x999,0,0x800,0x700),'profile_api'),p.calls)

    def test_kind_specific_formal_path_slots_and_alias_arguments(self):
        for kind,slot in (('boolean',16),('dword',20)):
            p=frame(kind).advance(sample())
            self.assertIn(('00504ef8',(('source_formal_slot',slot),('source_formal_slot',slot)),'path_convert'),p.calls)
            self.assertEqual(p.formal_arguments,(1,2,3,0))

    def test_null_converted_pointers_select_empty_literals(self):
        for kind,base in (('boolean',0x52348f),('dword',0x523492)):
            o=sample(path_test_pointer=0,key_test_pointer=0,section_test_pointer=0)
            o=replace(o,values={k:v for k,v in o.values.items() if not k.endswith('_value_pointer')})
            p=frame(kind).advance(o);self.assertTrue(p.complete)
            self.assertIn(('GetPrivateProfileIntA',(base+2,0,base+1,base),'profile_api'),p.calls)

    def test_capture_before_cleanup_and_separate_fs_return(self):
        f=frame();o=sample(256)
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'section_cleanup':False}))
        self.assertEqual(p.return_eax,1);self.assertFalse(p.complete)
        p=f.advance(replace(sample(0),normal_returns={**o.normal_returns,'fs_restore':False}))
        self.assertEqual(p.return_eax,1);self.assertEqual(p.needed,('normal','fs_restore'))
        p=f.advance(sample());self.assertTrue(p.complete);self.assertEqual(p.return_eax,1)

    def test_api_return_required_before_value_consumption(self):
        o=sample();p=frame().advance(replace(o,normal_returns={**o.normal_returns,'profile_api':False}))
        self.assertIsNone(p.return_eax);self.assertEqual(p.needed,('normal','profile_api'))

    def test_raw_argument_validation(self):
        for bad in (True,-1,1<<32):
            with self.assertRaises(ValueError):frame(default=bad)
        with self.assertRaises(ValueError):frame('other')
        with self.assertRaises(ValueError):ProfileNumericFrame('boolean',section=1,key=2,path=3,default=0,source_sha256='unknown')
