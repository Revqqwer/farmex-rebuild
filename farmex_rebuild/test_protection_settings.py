import unittest
from dataclasses import replace
from protection_settings import *

def fixture():
    values={};normals={'prologue':True};texts={};ansi={};children={}
    for op in OPS:
        kind,slot,_=op[:3]
        if kind in ('flag','choice_else','enum'):
            slots=[s for s,_ in slot] if kind=='enum' else [slot]
            for source in slots:values['checked_'+label(source)]=0;normals['checked_'+label(source)]=True
        else:
            key=label(slot);texts[key]='not a lexical guess'
            for stage in ('init_','text_','text_cleanup_'):normals[stage+key]=True
            if kind=='number':
                normals['parser_outer_'+key]=True
                children[key]=SourceIntegerObservation(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True)
            else:
                ansi[key]=b'captured route'
                for stage in ('ansi_','assign_','ansi_cleanup_'):normals[stage+key]=True
    return ProtectionSettingsObservation(True,values,normals,texts,ansi,children)

class ProtectionSettingsTests(unittest.TestCase):
    def test_full_body_normal_path_and_four_fallback_defaults(self):
        p=ProtectionSettingsFrame().advance(fixture());self.assertTrue(p.complete)
        fields={a-0x5690f8:v for a,w,v in p.stores}
        self.assertEqual({k:fields[k] for k in (0xc,0x1c,0x2c,0x4c)}, {0xc:80,0x1c:60,0x2c:50,0x4c:30})
        self.assertEqual(fields[0xb4],2);self.assertEqual(p.next_address,0x46c18f)
        self.assertFalse(p.whole_producer_verified or p.native_execution_verified or p.live_compatibility_verified)
    def test_no_radio_match_performs_no_store_for_four_groups(self):
        p=ProtectionSettingsFrame().advance(fixture())
        self.assertEqual(p.unchanged_enum_offsets,(0x10,0x34,0x44,0x84))
        self.assertTrue(all(a-0x5690f8 not in p.unchanged_enum_offsets for a,w,v in p.stores))
    def test_radio_priority_is_source_order_not_numeric_enum_order(self):
        o=fixture();v=dict(o.values)
        for key in ('758','75c','7ec','7e4','7a0','7cc','800','808'):v['checked_'+key]=1
        p=ProtectionSettingsFrame().advance(replace(o,values=v));fields={a-0x5690f8:x for a,w,x in p.stores}
        self.assertEqual({k:fields[k] for k in (0x10,0x34,0x44,0x84)},{0x10:5,0x34:0,0x44:0,0x84:0})
    def test_nonconsecutive_notice_and_pm_values(self):
        o=fixture();v=dict(o.values);v.update(checked_7cc=255,checked_804=1)
        p=ProtectionSettingsFrame().advance(replace(o,values=v));fields={a-0x5690f8:x for a,w,x in p.stores}
        self.assertEqual(fields[0x44],4);self.assertEqual(fields[0x84],4)
    def test_raw_al_is_preserved_for_flags_and_tested_for_radios(self):
        o=fixture();v=dict(o.values);v.update(checked_b28=0x102,checked_748=0x100,checked_b10=0x100,checked_b14=1)
        f=ProtectionSettingsFrame();p=f.advance(replace(o,values=v));fields={a-0x5690f8:x for a,w,x in p.stores}
        self.assertEqual((fields[0x39],fields[8],fields[0xb4]),(2,0,2))
        self.assertNotIn('checked_b14',f.observation.values)
    def test_numeric_result_is_low32_without_unit_scaling(self):
        o=fixture();children=dict(o.integer_children)
        children['788']=SourceIntegerObservation(True,'normal',True,0x12345678ffffffff,cleanup_returned=True)
        p=ProtectionSettingsFrame().advance(replace(o,integer_children=children))
        self.assertIn((0x569114,4,0xffffffff),p.stores)
    def test_child_and_outer_parser_return_are_separate(self):
        o=fixture();n=dict(o.normal_returns);n['parser_outer_74c']=False
        f=ProtectionSettingsFrame();p=f.advance(replace(o,normal_returns=n))
        self.assertEqual(p.needed,('normal','parser_outer_74c'));self.assertEqual(len(p.stores),3)
        self.assertTrue(dict(p.children)['74c'].complete)
        p=f.advance(ProtectionSettingsObservation(normal_returns={'parser_outer_74c':True}))
        self.assertEqual(p.needed,('normal','text_cleanup_74c'));self.assertIn((0x569104,4,80),p.stores)
    def test_numeric_cleanup_gap_preserves_store_and_defers_later_getter(self):
        o=fixture();n=dict(o.normal_returns);n['text_cleanup_74c']=False
        f=ProtectionSettingsFrame();p=f.advance(replace(o,normal_returns=n))
        self.assertEqual(p.needed,('normal','text_cleanup_74c'));self.assertNotIn('checked_750',f.observation.values)
        v=dict(o.values);v['checked_750']=2
        p=f.advance(replace(o,values=v));self.assertTrue(p.complete);self.assertIn((0x569218,1,2),p.stores)
    def test_string_projection_precedes_cleanup_and_does_not_guess_encoding(self):
        o=fixture();n=dict(o.normal_returns);n['ansi_cleanup_760']=False
        f=ProtectionSettingsFrame();p=f.advance(replace(o,normal_returns=n))
        self.assertEqual(p.needed,('normal','ansi_cleanup_760'));self.assertEqual(p.string_assignments,((0x56911c,b'captured route'),))
        data=dict(o.ansi_bytes);data['760']=b'new contradictory bytes'
        p=f.advance(replace(o,ansi_bytes=data))
        self.assertTrue(p.complete);self.assertEqual(p.string_assignments[0],(0x56911c,b'captured route'))
        self.assertEqual([a-0x5690f8 for a,b in p.string_assignments],[0x24,0x3c,0x54,0x88])
    def test_entry_and_prologue_are_not_inferred_from_ready_fields(self):
        o=fixture();f=ProtectionSettingsFrame();p=f.advance(replace(o,entry_reached=False))
        self.assertEqual(p.needed,('entry','0046b928'));self.assertEqual(p.stores,())
        p=f.advance(ProtectionSettingsObservation(True));self.assertEqual(p.needed,('normal','prologue'))
    def test_numeric_child_gap_and_argument_text_are_retained(self):
        o=fixture();children=dict(o.integer_children);children['74c']=SourceIntegerObservation(True)
        f=ProtectionSettingsFrame();p=f.advance(replace(o,integer_children=children))
        self.assertEqual(p.needed,('child','74c'));self.assertEqual(f.frames['74c'].text,'not a lexical guess')
        texts=dict(o.texts);texts['74c']='changed'
        p=f.advance(replace(o,texts=texts));self.assertTrue(p.complete)
        self.assertEqual(f.frames['74c'].text,'not a lexical guess')
    def test_terminal_and_typed_inputs(self):
        f=ProtectionSettingsFrame();p=f.advance(fixture());self.assertIs(f.advance(ProtectionSettingsObservation()),p)
        with self.assertRaises(ValueError):ProtectionSettingsObservation(values={'checked_748':True})
        with self.assertRaises(ValueError):ProtectionSettingsObservation(ansi_bytes={'760':'text'})
        with self.assertRaises(ValueError):ProtectionSettingsObservation(integer_children={'74c':{}})

if __name__=='__main__':unittest.main()
