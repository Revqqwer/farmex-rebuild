import json,unittest
from pathlib import Path
from mining_configuration import *
from mining_engine import (MiningRunner,MiningExecutionState,MiningSnapshot,OreSlotState,
    OreSlotSnapshot,process_ore_slot,crash_wait_complete,signed_duration_product)
from profiles import Profiles

class MiningConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf8')))
    def setUp(self):self.values=dict(self.profiles.defaults)
    def compile(self,**kw):return compile_mining_panel(self.values,**kw)
    def test_26_scalar_paths_exist_and_default_modes_numbers(self):
        self.assertEqual(len(MINING_PANEL_INPUTS),26);self.assertTrue(set(MINING_PANEL_INPUTS)<=set(self.values))
        p=self.compile();self.assertEqual((p.fields[0x5ff8],p.fields[0x6048]),(1,1))
        self.assertEqual((p.fields[0x602c],p.fields[0x6030],p.fields[0x6040]),(3,1,30))
        self.assertIsNone(p.manual_route_ansi);self.assertTrue(p.missing)
        with self.assertRaises(TypeError):p.fields[0x602c]=0
    def test_radio_nested_priority_is_first_true_not_last(self):
        for paths,offset in ((START_MODES,0x5ff8),(SPEED_MODES,0x6048)):
            for path in paths:self.values[path]=True
            self.assertEqual(self.compile().fields[offset],1)
            self.values[paths[0]]=False;self.assertEqual(self.compile().fields[offset],2)
            self.values[paths[1]]=False;self.assertEqual(self.compile().fields[offset],3)
    def test_no_radio_retains_observed_raw_previous_or_remains_unknown(self):
        for path in START_MODES+SPEED_MODES:self.values[path]=False
        p=self.compile();self.assertNotIn(0x5ff8,p.fields);self.assertNotIn(0x6048,p.fields)
        p=self.compile(previous_start_mode=0,previous_speed_mode=0xffffffff)
        self.assertEqual((p.fields[0x5ff8],p.fields[0x6048]),(0,0xffffffff))
    def test_signed64_numbers_preserve_low_dword_without_clamp(self):
        for value,expected in (('-1',0xffffffff),('4294967297',1),('9223372036854775807',0xffffffff)):
            self.values[ORE+'txtGoCrashWait']=value;self.assertEqual(self.compile().fields[0x602c],expected)
        for value in ('9223372036854775808','1.000','0x10',''):
            self.values[ORE+'txtGoCrashWait']=value
            with self.assertRaises(ValueError):self.compile()
    def test_each_flag_changes_only_its_source_field(self):
        base=self.compile()
        for path,offset in FLAG_PATHS.items():
            old=self.values[path];self.values[path]=not old;p=self.compile()
            self.assertEqual(p.fields[offset],int(not old))
            self.assertEqual({k:v for k,v in p.fields.items() if k!=offset},
                {k:v for k,v in base.fields.items() if k!=offset})
            self.values[path]=old
    def test_manual_filename_is_explicit_ansi_not_combo_index(self):
        self.assertTrue(self.compile().missing)
        p=self.compile(manual_route_ansi=b'\xddtem.R')
        self.assertEqual(p.status,'compiled_mining_fields');self.assertEqual(p.manual_route_ansi,b'\xddtem.R')
        with self.assertRaises(ValueError):self.compile(manual_route_ansi='İtem.R')
    def test_runner_wait_enable_and_strict_minute_boundary_consume_panel(self):
        self.values[ORE+'chGoCrashWait']=True;self.values[ORE+'txtGoCrashWait']='1'
        runner=MiningRunner(mining_runner_configuration(self.compile()));state=MiningExecutionState(route_active=True)
        self.assertEqual(runner.tick(state,MiningSnapshot(),60000).state.phase,0)
        self.assertEqual(runner.tick(state,MiningSnapshot(),60001).state.phase,1)
        self.values[ORE+'chGoCrashWait']=False
        runner.config=mining_runner_configuration(self.compile())
        self.assertEqual(runner.tick(state,MiningSnapshot(),0).state.phase,1)
    def test_pitman_override_6035_avoids_unneeded_comparison_observation(self):
        self.values[ORE+'chPitmanFollow']=True;runner=MiningRunner(mining_runner_configuration(self.compile()))
        p=runner.tick(MiningExecutionState(phase=1,route_active=True),MiningSnapshot(),0)
        self.assertEqual(p.required_observations,('helper_479988_result',))
    def test_vip_604c_not_magic_hammer_stop_6039_controls_phase5(self):
        self.values[ORE+'chMiningVipStorage']=False;self.values[REPAIR+'chMiningMHBotStop']=True
        state=MiningExecutionState(phase=5,route_active=True)
        runner=MiningRunner(mining_runner_configuration(self.compile()))
        self.assertEqual(runner.tick(state,MiningSnapshot(),0).state.phase,6)
        self.values[ORE+'chMiningVipStorage']=True;runner.config=mining_runner_configuration(self.compile())
        p=runner.tick(state,MiningSnapshot(),0)
        self.assertTrue(p.state.auxiliary_flag);self.assertEqual(p.intents[0].name,'begin_storage_operation_5')
    def test_ore_speed_and_ws_projection_compose_with_existing_slot_model(self):
        self.values[ORE+'txtOreCrashSpeed']='2';self.values[ORE+'chOreCrashWS']=True
        settings=mining_ore_settings(self.compile());self.assertEqual((settings.interval_seconds,settings.ws_enabled),(2,True))
        state=OreSlotState();snapshot=OreSlotSnapshot(True,True,True)
        self.assertEqual(process_ore_slot(state,snapshot,1999,settings.interval_seconds,settings.ws_enabled).intents,())
        p=process_ore_slot(state,snapshot,2000,settings.interval_seconds,settings.ws_enabled)
        self.assertEqual([i.name for i in p.intents],['ws_action_465f30_first','ore_crash_request_attempt'])
        self.assertEqual(p.state.item_index,15) # Local attempt only, no server receipt.
    def test_source_duration_product_overflow_is_signed_not_arbitrary_precision(self):
        self.assertEqual(signed_duration_product(0xffffffff,60000),-60000)
        self.assertTrue(crash_wait_complete(True,0xffffffff,0,0))
        self.assertFalse(crash_wait_complete(True,0x40000000,0,0))
        self.assertTrue(crash_wait_complete(True,0x40000000,0,1))
        p=process_ore_slot(OreSlotState(),OreSlotSnapshot(True,request_helper_45dc44_zero=True),0,0xffffffff)
        self.assertEqual(p.state.item_index,15)
    def test_invalid_raw_duration_and_profile_types_rejected(self):
        for value in (-1,True,0x100000000):
            with self.assertRaises(ValueError):signed_duration_product(value,1000)
        self.values[ORE+'chPitmanFollow']=1
        with self.assertRaises(ValueError):self.compile()

if __name__=='__main__':unittest.main()
