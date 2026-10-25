import unittest,sys,tempfile
from pathlib import Path
from global_route_choices import *
from supply_route_start import import_panel_route_choice
from profiles import Profiles
import json

class GlobalRouteChoiceTests(unittest.TestCase):
    def state(self):return SupplyRouteState(9,7)
    def obs(self,name=b'cycle.R',exists=1):return SupplyRouteObservation('cycle.R',name,b'C:\\MineCheck\\','C:\\MineCheck\\cycle.R',exists,name)
    def mine(self,**kwargs):
        return plan_global_route_choice('Mine',{ROUTE_GLOBALS['Mine']:b'manual.R'},self.state(),**kwargs)
    def test_seven_direct_kinds_use_exact_globals_without_other_observations(self):
        expected={'SMerchant':0x5698bc,'BMerchant':0x569908,'AntiCR':0x56911c,'Enemy':0x569134,
            'Notice':0x56914c,'PMKONTROL':0x569180,'Relog':0x562230}
        for kind,address in expected.items():
            self.assertEqual(ROUTE_GLOBALS[kind],address)
            p=plan_global_route_choice(kind,{address:b' x\xff.R '},self.state())
            self.assertTrue(p.complete);self.assertEqual(p.filename,b' x\xff.R ')
            self.assertEqual(p.state,self.state());self.assertIsNone(p.cyclic)
    def test_missing_global_is_not_empty_and_exact_source_kind_required(self):
        p=plan_global_route_choice('Relog',{},self.state())
        self.assertFalse(p.complete);self.assertIsNone(p.filename)
        with self.assertRaises(ValueError):plan_global_route_choice('relog',{},self.state())
        with self.assertRaises(ValueError):plan_global_route_choice('Relog',{0x562230:'name'},self.state())
    def test_mine_change_is_independent_required_byte_and_zero_skips_list_counter(self):
        self.assertEqual(self.mine().status,'needs_mining_change_observation')
        p=self.mine(mine_change_byte=0)
        self.assertTrue(p.complete);self.assertEqual(p.filename,b'manual.R');self.assertIsNone(p.mine_counter)
    def test_empty_mine_list_needs_no_counter_but_unknown_list_does(self):
        self.assertEqual(self.mine(mine_change_byte=1).status,'needs_mining_list_observation')
        p=self.mine(mine_change_byte=1,mine_names=())
        self.assertTrue(p.complete);self.assertEqual(p.filename,b'manual.R');self.assertIsNone(p.mine_counter)
        self.assertEqual(self.mine(mine_change_byte=1,mine_names=(b'cycle.R',)).status,'needs_mining_counter_observation')
    def test_third_counter_advances_and_wraps_without_touching_supply_return(self):
        for current,expected_index,next_value in ((0,0,1),(1,1,2),(2,0,1)):
            p=self.mine(mine_change_byte=255,mine_names=(b'cycle.R',b'other.R'),mine_counter=current,observation=self.obs())
            self.assertTrue(p.complete);self.assertEqual(p.mine_counter,next_value)
            self.assertEqual(p.cyclic.selected_index,expected_index);self.assertEqual(p.state,self.state())
    def test_missing_file_fallback_consumes_mining_slot(self):
        p=self.mine(mine_change_byte=1,mine_names=(b'cycle.R',),mine_counter=0,observation=self.obs(exists=0))
        self.assertEqual(p.status,'mining_manual_fallback');self.assertEqual(p.filename,b'manual.R');self.assertEqual(p.mine_counter,1)
    def test_negative_counter_and_missing_conversion_preserve_known_prefix(self):
        p=self.mine(mine_change_byte=1,mine_names=(b'cycle.R',),mine_counter=0xffffffff,observation=self.obs())
        self.assertFalse(p.complete);self.assertEqual(p.mine_counter,0xffffffff)
        p=self.mine(mine_change_byte=1,mine_names=(b'cycle.R',),mine_counter=0,observation=SupplyRouteObservation(decoded_name='cycle.R'))
        self.assertFalse(p.complete);self.assertEqual(p.mine_counter,1);self.assertEqual(p.state,self.state())
    @unittest.skipUnless(sys.platform=='win32','Owned local Windows codec/API fixtures')
    def test_mining_check_prefix_and_final_load_prefix_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);check=root/'check';load=root/'load';check.mkdir();load.mkdir()
            (check/'cycle.R').write_bytes(b'not a route file')
            (load/'cycle.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=0\n')
            codec=WindowsNameCodec(1254);prefix=codec.encode(str(check)+'\\')[0]
            p=self.mine(mine_change_byte=1,mine_names=(b'cycle.R',),mine_counter=0,
                observation=SupplyRouteObservation('cycle.R',b'cycle.R',prefix,str(check/'cycle.R'),1,b'cycle.R'))
            loaded=import_panel_route_choice(p,codec.encode(str(load)+'\\')[0],codec)
            self.assertTrue(loaded.ready);self.assertEqual(loaded.imported.steps[0].command,'Bekle')
            self.assertNotEqual(p.cyclic.candidate_path,codec.encode(str(load/'cycle.R'))[0])
    @unittest.skipUnless(sys.platform=='win32','Owned local Windows codec fixture')
    def test_mining_profile_checkbox_and_list_ignore_checked_and_keep_duplicates(self):
        model=json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf8'));profiles=Profiles(model)
        values=dict(profiles.defaults);lists={p:list(rows) for p,rows in profiles.list_defaults.items()}
        values[MINE_CHANGE_PATH]=True;lists[MINE_LIST_PATH]=[{'caption':'İtem.R','checked':False},{'caption':'İtem.R'}]
        p=compile_mining_route_inputs(values,lists,WindowsNameCodec(1254))
        self.assertEqual(p.change_byte,1);self.assertEqual(p.names,(b'\xddtem.R',b'\xddtem.R'))

if __name__=='__main__':unittest.main()
