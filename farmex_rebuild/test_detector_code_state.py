import unittest
from dataclasses import replace
from detector_code_state import DetectorCodeStateFrame,transform_owned_bytes,CURRENT,LEGACY,REGIONS
from jail_protection import JailObservation


def sample(state=0,**values):
    return JailObservation(True,dict(state=state,**values),
                           {k:True for k in ('prologue','protect','epilogue')})


def complete_fixture(sha,mode,state):
    n=REGIONS[sha][1]-REGIONS[sha][0]
    values={'state':state};normals={k:True for k in ('prologue','protect','epilogue')}
    for i in range(n):
        values['byte%d.eax'%i]=0xabcd0000|((i*17)&255)
        normals['byte%d.read'%i]=normals['byte%d.write'%i]=True
    return JailObservation(True,values,normals)


class DetectorCodeStateTests(unittest.TestCase):
    def test_entry_and_prologue_boundaries(self):
        f=DetectorCodeStateFrame(CURRENT,1)
        self.assertEqual(f.advance(JailObservation()).needed,('entry','004e2a88'))
        self.assertEqual(f.advance(JailObservation(True)).needed,('normal','prologue'))

    def test_identical_raw_state_skips_protect_even_for_unknown_mode(self):
        for mode in (0,1,2,0xffffffff):
            p=DetectorCodeStateFrame(CURRENT,mode).advance(sample(mode))
            self.assertTrue(p.complete);self.assertFalse(p.stores);self.assertFalse(p.byte_write_intents)
            self.assertEqual([l for _,_,l in p.calls],['prologue','epilogue'])

    def test_unknown_mode_still_calls_protect_when_state_differs(self):
        p=DetectorCodeStateFrame(CURRENT,2).advance(sample(0))
        self.assertTrue(p.complete);self.assertFalse(p.stores);self.assertFalse(p.byte_write_intents)
        self.assertEqual(p.calls[1],('VirtualProtect',('source_old_protection_local',0x40,5660,0x4e1464),'protect'))

    def test_protect_return_value_not_required(self):
        p=DetectorCodeStateFrame(CURRENT,1).advance(sample())
        self.assertEqual(p.needed,('normal','byte0.read'))
        self.assertEqual(p.calls[-1],('0045dbdc',(0x4e1464,),'byte0.read'))

    def test_reader_then_full_eax_then_writer_return_are_separate(self):
        f=DetectorCodeStateFrame(CURRENT,1);o=sample()
        o=replace(o,normal_returns={**o.normal_returns,'byte0.read':True})
        p=f.advance(o);self.assertEqual(p.needed,('value','byte0.eax'));self.assertFalse(p.byte_write_intents)
        o=replace(o,values={**o.values,'byte0.eax':0xabcdefe0})
        p=f.advance(o);self.assertEqual(p.needed,('normal','byte0.write'))
        self.assertEqual(p.byte_write_intents,((0x4e1464,1,8,0xabcdef08),))
        self.assertEqual(p.calls[-1],('0045de4c',(0xabcdef08,0x4e1464),'byte0.write'))

    def test_prefix_is_retained_and_state_not_stored_early(self):
        o=sample(**{'byte0.eax':0,'byte1.eax':0xff})
        o=replace(o,normal_returns={**o.normal_returns,'byte0.read':True,'byte0.write':True,'byte1.read':True})
        f=DetectorCodeStateFrame(CURRENT,0);o=replace(o,values={**o.values,'state':1})
        p=f.advance(o);self.assertEqual(p.needed,('normal','byte1.write'))
        self.assertEqual([w[2] for w in p.byte_write_intents],[0xd8,0xbf]);self.assertFalse(p.stores)
        p=f.advance(o);self.assertEqual(len(p.byte_write_intents),2)

    def test_full_current_and_legacy_loop_bounds(self):
        for sha,n in ((CURRENT,5660),(LEGACY,5632)):
            for mode in (0,1):
                p=DetectorCodeStateFrame(sha,mode).advance(complete_fixture(sha,mode,1-mode))
                self.assertTrue(p.complete);self.assertEqual(len(p.byte_write_intents),n)
                self.assertEqual(p.byte_write_intents[-1][0],REGIONS[sha][1]-1)
                self.assertEqual(p.stores,((0x56ff38,4,mode),))
                # Source has one outer protection call and no restoration call.
                self.assertEqual(sum(h=='VirtualProtect' for h,_,_ in p.calls),1)
                self.assertFalse(p.byte_effects_verified)

    def test_final_state_precedes_separate_epilogue(self):
        o=complete_fixture(CURRENT,1,0);f=DetectorCodeStateFrame(CURRENT,1)
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'epilogue':False}))
        self.assertFalse(p.complete);self.assertEqual(p.stores,((0x56ff38,4,1),))
        self.assertEqual(p.needed,('normal','epilogue'));self.assertTrue(f.advance(o).complete)

    def test_owned_arithmetic_known_vectors_and_immutability(self):
        raw=bytes([0,0,0xff,0xff,0xd8,0xc0]);encoded=transform_owned_bytes(raw,1)
        self.assertEqual(encoded,bytes([0x28,0x40,0x27,0x3f,0,0]))
        self.assertEqual(raw,bytes([0,0,0xff,0xff,0xd8,0xc0]))
        self.assertEqual(transform_owned_bytes(encoded,0),raw)

    def test_owned_roundtrip_all_byte_values_both_modes(self):
        raw=bytes(range(256))*2
        for mode in (0,1):self.assertEqual(transform_owned_bytes(transform_owned_bytes(raw,mode),1-mode),raw)

    def test_raw_reader_upper_bits_preserved_by_add_al(self):
        o=complete_fixture(CURRENT,0,1)
        p=DetectorCodeStateFrame(CURRENT,0).advance(o)
        self.assertTrue(all(w[3]&0xffffff00==0xabcd0000 for w in p.byte_write_intents))

    def test_reject_unknown_identity_and_nonraw_arguments(self):
        for sha,mode in (('unknown',0),(CURRENT,True),(CURRENT,-1),(CURRENT,1<<32)):
            with self.assertRaises(ValueError):DetectorCodeStateFrame(sha,mode)
        for data,mode in ((bytearray(),0),(b'',True),(b'',2)):
            with self.assertRaises(ValueError):transform_owned_bytes(data,mode)
