import sys,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from supply_route_start import *
from supply_routes import route_codec_fixture

class SupplyRouteStartTests(unittest.TestCase):
    def panel(self,supply=0,returning=0):return SupplyPanelConfiguration({0x588:supply,0x589:returning},{})
    def lists(self,supply=(),returning=()):return SupplyRouteLists(supply,returning,True)
    def obs(self,name=b'cycle.R',exists=1):
        return SupplyRouteObservation('cycle.R',name,b'C:\\Routes\\','C:\\Routes\\cycle.R',exists,name)
    def test_manual_conversion_is_required_even_when_cyclic_will_override(self):
        p=plan_panel_route_choice(self.panel(1),self.lists((b'cycle.R',)),'supply',SupplyRouteState(0,0),observation=self.obs())
        self.assertFalse(p.complete);self.assertEqual(p.state.supply_counter,0)
        self.assertEqual(p.status,'needs_manual_conversion')
    def test_disabled_cyclic_does_not_require_any_list_or_file_observation(self):
        lists=SupplyRouteLists((None,),(),False,('missing encoding',))
        p=plan_panel_route_choice(self.panel(),lists,'supply',SupplyRouteState(7,8),b'manual.R')
        self.assertTrue(p.complete);self.assertEqual(p.filename,b'manual.R')
        self.assertEqual(p.state,SupplyRouteState(7,8));self.assertIsNone(p.cyclic)
    def test_nonempty_cycle_overrides_manual_and_updates_only_matching_counter(self):
        p=plan_panel_route_choice(self.panel(returning=1),self.lists(returning=(b'cycle.R',)),
            'return',SupplyRouteState(7,0),b'manual.R',self.obs())
        self.assertEqual(p.filename,b'cycle.R');self.assertTrue(p.used_cyclic)
        self.assertEqual(p.state,SupplyRouteState(7,1))
    def test_empty_list_and_missing_file_fall_back_to_manual_without_erasing_counter_prefix(self):
        for lists,obs,counter in ((self.lists(),SupplyRouteObservation(),0),
                                 (self.lists((b'cycle.R',)),self.obs(exists=0),1)):
            p=plan_panel_route_choice(self.panel(1),lists,'supply',SupplyRouteState(0,0),b'manual.R',obs)
            self.assertEqual(p.filename,b'manual.R');self.assertEqual(p.status,'manual_route_fallback')
            self.assertEqual(p.state.supply_counter,counter)
    def test_incomplete_cycle_does_not_silently_fall_back_to_manual(self):
        p=plan_panel_route_choice(self.panel(1),self.lists((b'cycle.R',)),'supply',SupplyRouteState(0,0),b'manual.R')
        self.assertFalse(p.complete);self.assertEqual(p.filename,b'manual.R')
        self.assertEqual(p.status,'needs_route_observation')
    @unittest.skipUnless(sys.platform=='win32','Owned local Windows API fixture')
    def test_empty_final_name_is_source_stop_intent_without_file_read(self):
        p=plan_panel_route_choice(self.panel(),self.lists(),'supply',SupplyRouteState(0,0),b'')
        start=import_panel_route_choice(p,b'C:\\Routes\\',WindowsNameCodec(1254))
        self.assertTrue(start.stop_required);self.assertIsNone(start.imported);self.assertFalse(start.ready)
    @unittest.skipUnless(sys.platform=='win32','Owned local Windows API fixtures')
    def test_execution_zero_count_differs_from_editor_preserve(self):
        from source_route_ini import import_source_route
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'zero.R';file.write_bytes(b'[Count]\nValue=0\n')
            codec=WindowsNameCodec(1254);prefix=codec.encode(str(file.parent)+'\\')[0]
            choice=plan_panel_route_choice(self.panel(),self.lists(),'supply',SupplyRouteState(0,0),b'zero.R')
            start=import_panel_route_choice(choice,prefix,codec)
            editor=import_source_route(str(file),codec)
            self.assertTrue(start.stop_required);self.assertTrue(start.complete);self.assertFalse(start.ready)
            self.assertTrue(editor.complete);self.assertFalse(editor.changed)
    @unittest.skipUnless(sys.platform=='win32','Owned local Windows API fixtures')
    def test_missing_cycle_manual_fallback_imports_and_missing_manual_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'manual.R';file.write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=0\n')
            codec=WindowsNameCodec(1254);prefix=codec.encode(str(file.parent)+'\\')[0]
            obs=route_codec_fixture(b'missing.R',prefix,codec,file_exists_byte=0)
            p=plan_panel_route_choice(self.panel(1),self.lists((b'missing.R',)),'supply',SupplyRouteState(0,0),b'manual.R',obs)
            start=import_panel_route_choice(p,prefix,codec)
            self.assertTrue(start.ready);self.assertFalse(start.stop_required);self.assertEqual(p.state.supply_counter,1)
            file.unlink()
            start=import_panel_route_choice(p,prefix,codec)
            self.assertTrue(start.stop_required);self.assertFalse(start.ready)
    @unittest.skipUnless(sys.platform=='win32','Owned local Windows API fixtures')
    def test_unknown_row_is_unresolved_not_source_proven_stop(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'unknown.R';file.write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Unknown\n')
            codec=WindowsNameCodec(1254);prefix=codec.encode(str(file.parent)+'\\')[0]
            p=plan_panel_route_choice(self.panel(),self.lists(),'supply',SupplyRouteState(0,0),b'unknown.R')
            start=import_panel_route_choice(p,prefix,codec)
            self.assertFalse(start.complete);self.assertFalse(start.stop_required);self.assertFalse(start.ready)

if __name__=='__main__':unittest.main()
