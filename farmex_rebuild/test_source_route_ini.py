import unittest,sys,tempfile
from pathlib import Path
from source_route_ini import *
from supply_routes import SupplyRouteLists,SupplyRouteState,route_codec_fixture,plan_supply_route_selection
from routes import RouteRunner

@unittest.skipUnless(sys.platform=='win32','Real owned Windows profile API fixture')
class SourceRouteIniTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'source route.R';self.codec=WindowsNameCodec(1254)
    def tearDown(self):self.temp.cleanup()
    def write(self,text):self.path.write_bytes(text.encode('ascii'));return str(self.path)
    def test_native_count_and_three_keys_are_zero_based_and_case_insensitive(self):
        path=self.write('[count]\nvalue=1\n[route]\nislem0=Koordinat\nsub10=12.5\nsub20=-3\nISLEM1=Ignored\n')
        p=read_source_route_ini(path)
        self.assertEqual(p.rows,((b'Koordinat',b'12.5',b'-3'),));self.assertTrue(p.changed)
        self.assertEqual(p.count_dword,1);self.assertFalse(p.independently_verified)
    def test_missing_file_default_count_zero_and_negative_preserve(self):
        self.assertEqual(read_source_route_ini(str(self.path)).status,'file_missing_preserve')
        for count in ('','0','-1'):
            p=read_source_route_ini(self.write('[Count]\nValue='+count+'\n'))
            self.assertFalse(p.changed);self.assertTrue(p.complete)
            self.assertEqual(p.rows,())
        self.assertEqual(p.count_dword,0xffffffff)
    def test_api_nsize255_truncates_to254_ansi_bytes_and_missing_keys_empty(self):
        p=read_source_route_ini(self.write('[Count]\nValue=1\n[ROUTE]\nISLEM0='+'A'*600+'\n'))
        self.assertEqual(len(p.rows[0][0]),254);self.assertEqual(p.rows[0][1:],(b'',b''))
    def test_local_row_budget_is_unresolved_and_does_not_claim_source_bound(self):
        p=read_source_route_ini(self.write('[Count]\nValue=3\n'),max_rows=2)
        self.assertFalse(p.complete);self.assertFalse(p.changed);self.assertEqual(p.status,'local_row_budget')
    def test_imports_coordinate_wait_and_npc_parameter_strings(self):
        path=self.write('[Count]\nValue=3\n[ROUTE]\nISLEM0=Koordinat\nSub10=1.5\nSub20=2.5\n'
            'ISLEM1=Bekle\nSub11=2\nSub21=ignored\nISLEM2=NPC\nSub12=Potion\nSub22=Extra\n')
        p=import_source_route(path,self.codec)
        self.assertTrue(p.complete);self.assertTrue(p.changed)
        self.assertEqual((p.steps[0].x,p.steps[0].y),(1.5,2.5));self.assertEqual(p.steps[1].seconds,2)
        self.assertEqual((p.steps[2].parameter1,p.steps[2].parameter2),('Potion','Extra'))
    def test_unsupported_or_bad_numeric_row_retains_only_uncommitted_prefix(self):
        for command in ('Unknown','Koordinat','Bekle'):
            path=self.write('[Count]\nValue=2\n[ROUTE]\nISLEM0=Bekle\nSub10=0\nISLEM1='+command+'\nSub11=bad\n')
            p=import_source_route(path,self.codec)
            self.assertFalse(p.complete);self.assertFalse(p.changed);self.assertEqual(len(p.steps),1)
            self.assertTrue(p.missing.startswith('row1:'))
    def test_selection_to_native_ini_to_existing_route_runner(self):
        self.write('[Count]\nValue=2\n[ROUTE]\nISLEM0=Koordinat\nSub10=10\nSub20=20\nISLEM1=Bekle\nSub11=0\n')
        prefix=self.codec.encode(str(self.path.parent)+'\\')[0];name=self.codec.encode(self.path.name)[0]
        obs=route_codec_fixture(name,prefix,self.codec,file_exists_byte=1)
        selected=plan_supply_route_selection(SupplyRouteLists((name,),(),True),'supply',SupplyRouteState(0,0),obs)
        imported=import_selected_source_route(selected,prefix,self.codec)
        self.assertTrue(imported.complete);runner=RouteRunner();runner.start(imported.steps)
        self.assertEqual(runner.tick(0).kind,'selected')
        self.assertEqual(runner.tick(1,distance=5).kind,'move')
        self.assertEqual(runner.tick(2,distance=2).kind,'step_complete')
        self.assertEqual(runner.tick(3).kind,'selected')
        self.assertEqual(runner.tick(4).kind,'waiting')
        self.assertEqual(runner.tick(5).kind,'step_complete')
        self.assertEqual(runner.tick(6).kind,'finished')
    def test_second_fresh_filename_controls_actual_load(self):
        from dataclasses import replace
        prefix=self.codec.encode(str(self.path.parent)+'\\')[0]
        self.write('[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=0\n')
        obs=route_codec_fixture(b'first.R',prefix,self.codec,file_exists_byte=1)
        obs=replace(obs,success_encoded=self.codec.encode(self.path.name)[0])
        selected=plan_supply_route_selection(SupplyRouteLists((b'first.R',),(),True),'supply',SupplyRouteState(0,0),obs)
        self.assertTrue(import_selected_source_route(selected,prefix,self.codec).complete)
    def test_missing_selection_and_missing_files_do_not_import_empty_route(self):
        selected=plan_supply_route_selection(SupplyRouteLists((),(),True),'supply',SupplyRouteState(0,0))
        p=import_selected_source_route(selected,b'C:\\',self.codec)
        self.assertFalse(p.complete);self.assertFalse(p.changed)
        p=import_source_route(str(self.path),self.codec)
        self.assertTrue(p.complete);self.assertFalse(p.changed)
    def test_relative_or_nul_paths_and_invalid_budgets_rejected(self):
        for path in ('relative.R','C:\\x\0.R'):
            with self.assertRaises(ValueError):read_source_route_ini(path)
        with self.assertRaises(ValueError):read_source_route_ini(str(self.path),max_rows=0)

if __name__=='__main__':unittest.main()
