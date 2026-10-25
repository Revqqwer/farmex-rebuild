import json,unittest
from pathlib import Path
from loot_configuration import *
from profiles import Profiles
from operation_engine import LootRecord,LootSnapshot,loot_step

class LootConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8')))
    def setUp(self):self.values=dict(self.profiles.defaults)
    def mode(self,choice):
        for i,path in enumerate(MODE_PATHS,1):self.values[path]=i==choice
    def compile(self,**kwargs):return compile_loot_panel(self.values,**kwargs)
    def test_last_radio_wins_and_no_radio_requires_prior_field(self):
        for path in MODE_PATHS:self.values[path]=True
        self.assertEqual(self.compile().settings.mode,LootMode.LIST)
        self.mode(0)
        self.assertEqual(self.compile().status,'needs_previous_mode')
        self.assertEqual(self.compile(previous_mode=LootMode.COINS).settings.mode,LootMode.COINS)
    def test_three_source_mode_values_are_not_reordered(self):
        for mode in LootMode:
            self.mode(mode.value);self.assertEqual(self.compile().fields[4],mode.value)
    def test_price_dot_removal_and_dword_storage(self):
        self.mode(1);self.values[FILTER+'txtLootNpcPrice']='10.000'
        self.assertEqual(self.compile().fields[0x14],10000)
        self.values[FILTER+'txtLootNpcPrice']='4294967297'
        self.assertEqual(self.compile().fields[0x14],1)
        self.values[FILTER+'txtLootUpgrade']='-1'
        self.assertEqual(self.compile().fields[0x1c],0xffffffff)
    def test_invalid_types_and_numbers_fail_without_mutating_profile(self):
        for path,value in ((GENERAL+'chAutoLoot',1),(MODE_PATHS[0],'true'),
                (GENERAL+'txtLootBeforeWait','1.5'),(FILTER+'txtLootNpcPrice','1.2'),
                (FILTER+'txtLootUpgrade','2147483648')):
            values=dict(self.values);values[path]=value;before=dict(values)
            with self.assertRaises(ValueError):compile_loot_panel(values)
            self.assertEqual(values,before)
    def test_enabled_flag_blocks_even_unresolved_list(self):
        self.mode(3);self.values[GENERAL+'chAutoLoot']=False
        c=self.compile();record=LootRecord('fixture',0,item_phase=True)
        self.assertEqual(loot_step(c.settings,LootSnapshot(1000,(record,))).status,'blocked')
    def test_wait_bridge_preserves_strict_age_boundary(self):
        self.mode(1);self.values.update({GENERAL+'chAutoLoot':True,GENERAL+'chLootBeforeWait':True,GENERAL+'txtLootBeforeWait':'1000'})
        record=LootRecord('fixture',0,item_ids=(1,0,0,0,0,0,0,0),item_phase=True)
        settings=self.compile().settings
        self.assertEqual(loot_step(settings,LootSnapshot(1000,(record,))).intents,())
        self.assertEqual(len(loot_step(settings,LootSnapshot(1001,(record,))).intents),1)
    def test_list_mode_never_treats_row_ordinals_as_item_ids(self):
        self.mode(3);self.values[GENERAL+'chAutoLoot']=True
        c=self.compile();self.assertEqual(c.settings.listed_ids,())
        record=LootRecord('fixture',0,item_ids=(1,0,0,0,0,0,0,0),item_phase=True)
        p=loot_step(c.settings,LootSnapshot(1000,(record,)))
        self.assertEqual(p.status,'needs_item_classifier');self.assertEqual(p.intents,())
    def test_filter_flags_are_captured_separately_from_engine_consumption(self):
        self.mode(1)
        for path in FLAG_PATHS:self.values[path]=True
        c=self.compile()
        for offset in FLAG_PATHS.values():self.assertEqual(c.fields[offset],1)
        self.assertFalse(c.settings.extended_filters) # ALL ignores these source LIST filter gates.
