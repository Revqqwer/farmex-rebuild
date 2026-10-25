import unittest
from dataclasses import replace
from disconnect_settings import OPS,DisconnectSettingsFrame,DisconnectSettingsObservation
from source_integer import SourceIntegerObservation


def fixture():
    values={};normals={};texts={};ansi={};children={}
    for op in OPS:
        kind,slot,_=op[:3]
        if kind=='constant':continue
        key='%03x'%slot
        if kind in ('flag','index'):
            label=('checked_' if kind=='flag' else 'index_')+key
            values[label]=0;normals[label]=True
        else:
            texts[key]='captured text'
            for prefix in ('init_','text_','text_cleanup_'):normals[prefix+key]=True
            if kind=='number':
                normals['parser_outer_'+key]=True
                children[key]=SourceIntegerObservation(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True)
            else:
                ansi[key]=b'captured text'
                for prefix in ('ansi_','assign_','ansi_cleanup_'):normals[prefix+key]=True
    return DisconnectSettingsObservation(True,values,normals,texts,ansi,children)


class DisconnectSettingsTests(unittest.TestCase):
    def test_explicit_mid_function_entry_without_fake_prologue(self):
        p=DisconnectSettingsFrame().advance(DisconnectSettingsObservation())
        self.assertEqual(p.needed,('entry','00457d02'));self.assertFalse(p.calls)
        p=DisconnectSettingsFrame().advance(fixture())
        self.assertTrue(p.complete);self.assertEqual(p.next_address,0x4580ac)
        self.assertFalse(any(label=='prologue' for _,_,label in p.calls))

    def test_fourteen_fields_and_unconditional_manual_route_flag(self):
        p=DisconnectSettingsFrame().advance(fixture())
        self.assertEqual(len(p.stores),11);self.assertEqual(len(p.string_assignments),4)
        self.assertIn((0x562194+0x9a,1,1),p.stores)
        self.assertIn((0x562194+0x94,4,30),p.stores)

    def test_checkbox_low_al_vs_combo_full_dword(self):
        o=fixture();v={**o.values,'checked_828':0x102,'index_83c':0xffffffff,'index_eb8':0x12345678}
        p=DisconnectSettingsFrame().advance(replace(o,values=v))
        self.assertIn((0x56221e,1,2),p.stores)
        self.assertIn((0x562224,4,0xffffffff),p.stores)
        self.assertIn((0x56223c,4,0x12345678),p.stores)

    def test_unread_wait_and_manual_checkboxes_not_consumed(self):
        f=DisconnectSettingsFrame();o=fixture()
        o=replace(o,values={**o.values,'checked_830':0xffffffff,'checked_848':0xffffffff})
        p=f.advance(o);self.assertTrue(p.complete)
        self.assertNotIn('checked_830',f.observation.values);self.assertNotIn('checked_848',f.observation.values)
        self.assertIn((0x56222e,1,1),p.stores)

    def test_numeric_low32_without_clamp_or_seconds_scaling(self):
        o=fixture();child=SourceIntegerObservation(True,'normal',True,0x12345678ffffffff,cleanup_returned=True)
        p=DisconnectSettingsFrame().advance(replace(o,integer_children={'834':child}))
        self.assertIn((0x562228,4,0xffffffff),p.stores)

    def test_parser_child_and_outer_return_separate(self):
        o=fixture();f=DisconnectSettingsFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'parser_outer_834':False}))
        self.assertEqual(p.needed,('normal','parser_outer_834'))
        self.assertTrue(p.children[0][1].complete);self.assertEqual(len(p.stores),4)
        self.assertTrue(f.advance(o).complete)

    def test_route_uses_captured_text_bytes_not_index(self):
        o=fixture();o=replace(o,ansi_bytes={**o.ansi_bytes,'84c':b'route_actual_text'})
        p=DisconnectSettingsFrame().advance(o)
        self.assertIn((0x562230,b'route_actual_text'),p.string_assignments)

    def test_string_prefix_and_assign_cleanup_boundaries(self):
        o=fixture();f=DisconnectSettingsFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'assign_854':False}))
        self.assertEqual(p.needed,('normal','assign_854'));self.assertEqual(len(p.string_assignments),1)
        self.assertFalse(any(a==0x562194+0xa8 for a,_,_ in p.stores))
        p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(len(p.string_assignments),4)

    def test_completed_prefix_not_replaced_by_later_input(self):
        o=fixture();f=DisconnectSettingsFrame()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'index_83c':False}))
        old=p.stores
        o=replace(o,values={**o.values,'checked_828':1,'checked_82c':1})
        p=f.advance(o);self.assertEqual(p.stores[:3],old)

    def test_context_wrap_and_scope_flags(self):
        p=DisconnectSettingsFrame(context=0xffffff80).advance(fixture())
        self.assertEqual(p.stores[0],(0xa,1,0))
        self.assertFalse(p.whole_producer_verified or p.native_execution_verified or p.live_compatibility_verified)
