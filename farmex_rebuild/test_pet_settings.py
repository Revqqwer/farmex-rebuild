import unittest
from dataclasses import replace
from pet_settings import PetSettingsFrame,PetSettingsObservation,plan_pet_settings
from source_integer import SourceIntegerObservation

def captured(**changes):
    values={'checked_f18':1,'checked_f28':0,'checked_f24':1,'checked_f20':0,'checked_f14':1}
    normals={key:True for key in values}
    normals.update({key+'_f1c':True for key in ('init','text','parser_outer','text_cleanup')})
    o=PetSettingsObservation(entry_reached=True,values=values,normal_returns=normals,
        texts={'f1c':'10'},integer_children={'f1c':SourceIntegerObservation(
        text_copy_returned=True,route='normal',parser_returned=True,parser_qword=10,cleanup_returned=True)})
    return replace(o,**changes)

class PetSettingsTests(unittest.TestCase):
    def test_four_fields_and_bounded_exit(self):
        p=plan_pet_settings(captured())
        self.assertTrue(p.complete);self.assertEqual(p.next_address,0x40a4b0)
        self.assertEqual(p.stores,((0x5620dc,1,1),(0x5620e0,4,2),(0x5620e4,1,1),(0x5620e8,4,10)))
        self.assertFalse(p.whole_producer_verified)
    def test_nonzero_low_byte_and_attack_priority(self):
        o=captured();v={**o.values,'checked_f18':0x100,'checked_f28':0x102,'checked_f24':1,'checked_f20':1,'checked_f14':0x102}
        p=plan_pet_settings(replace(o,values=v))
        self.assertEqual([s[2] for s in p.stores],[0,1,2,10])
        self.assertFalse(any(c[2]=='checked_f24' for c in p.calls))
    def test_no_radio_does_not_write_default_mode(self):
        o=captured();v={**o.values,'checked_f28':0,'checked_f24':0,'checked_f20':0}
        p=plan_pet_settings(replace(o,values=v))
        self.assertEqual(p.unchanged_enum_offsets,(0x1ac,))
        self.assertNotIn(0x5620e0,[s[0] for s in p.stores])
    def test_catch_default_and_no_percent_clamp(self):
        o=captured();child=SourceIntegerObservation(text_copy_returned=True,route='catch_landing',catch_landing_returned=True,cleanup_returned=True)
        self.assertEqual(plan_pet_settings(replace(o,integer_children={'f1c':child})).stores[-1][2],10)
        child=replace(o.integer_children['f1c'],parser_qword=0xffffffffffffffff)
        self.assertEqual(plan_pet_settings(replace(o,integer_children={'f1c':child})).stores[-1][2],0xffffffff)
    def test_outer_return_and_cleanup_are_separate(self):
        o=captured();n={**o.normal_returns,'parser_outer_f1c':False}
        p=plan_pet_settings(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertEqual(len(p.stores),3)
        n={**o.normal_returns,'text_cleanup_f1c':False}
        p=plan_pet_settings(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertEqual(len(p.stores),4)
    def test_frame_does_not_replace_consumed_mode(self):
        o=captured();n={**o.normal_returns,'init_f1c':False};frame=PetSettingsFrame()
        p=frame.advance(replace(o,normal_returns=n));self.assertEqual(p.stores[1][2],2)
        p=frame.advance(replace(o,values={**o.values,'checked_f28':1,'checked_f24':0}))
        self.assertTrue(p.complete);self.assertEqual(p.stores[1][2],2)

if __name__=='__main__':unittest.main()
