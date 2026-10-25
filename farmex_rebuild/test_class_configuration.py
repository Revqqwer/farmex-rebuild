import copy
import json
from pathlib import Path
import unittest
from profiles import Profiles
from class_configuration import compile_priest, compile_warrior, compile_mage, compile_rogue, compile_kurian, _MAP
from priest_attack import PriestAttackSnapshot, PRIEST_ATTACK_ROWS, select_priest_attack
from job_dispatcher import WarriorSkillSnapshot, WARRIOR_ROWS, select_warrior_skill
from mage_attack import MageAttackSnapshot, MAGE_ATTACK_ROWS, select_mage_attack
from rogue_attack import RogueSnapshot, MELEE_ROWS, BOW_ROWS, SPECIAL_ROWS, select_rogue_melee
from combat_engine import MageSettings, MinorSettings, KurianSettings


class ClassConfigurationTests(unittest.TestCase):
    def setUp(self):
        profiles=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8')))
        self.values=copy.deepcopy(profiles.defaults)
        self.lists=copy.deepcopy(profiles.list_defaults)

    def path(self, job, suffix, kind='lists'):
        return next(p for p in _MAP[job][kind] if p.endswith('/'+suffix))

    def test_default_flags_cover_both_attack_engines(self):
        for compiler, rows in ((compile_priest,PRIEST_ATTACK_ROWS),(compile_warrior,WARRIOR_ROWS)):
            result=compiler(self.values,self.lists)
            self.assertTrue(all(result.flags[row.flag_offset] is False for row in rows))

    def test_warrior_ui_to_highest_priority(self):
        self.lists[self.path('warrior','lwWarriorFervor')][13]['checked']=True
        result=compile_warrior(self.values,self.lists)
        snapshot=WarriorSkillSnapshot(now_ms=12000,distance=1,configured_range=8,mp=500,
            flags=result.flags,raw_stats={'00462e34':75},last_ms_by_offset={0xf0:0},raw_skill_prefix_46256c=1)
        decision=select_warrior_skill(snapshot)
        self.assertEqual(decision.row.flag_offset,0xbd)

    def test_priest_ui_to_heal_attack(self):
        self.lists[self.path('priest','lwPriestHeal')][3]['checked']=True
        result=compile_priest(self.values,self.lists)
        snapshot=PriestAttackSnapshot(now_ms=3050,distance=8,configured_range=8,mp=120,
            flags=result.flags,raw_stats={'00462ddc':51},last_ms_by_offset={0x2c:0},locked_561f7e=False)
        self.assertEqual(select_priest_attack(snapshot).row.skill_number,0x227)

    def test_spirit_irregular_offsets(self):
        rows=self.lists[self.path('priest','lwPriestSpirit')]
        rows[0]['checked']=True; rows[2]['checked']=True; rows[11]['checked']=True
        flags=compile_priest(self.values,self.lists).flags
        self.assertTrue(flags[0x44]);self.assertTrue(flags[0x0f]);self.assertTrue(flags[0x12])
        self.assertFalse(flags[0x46])

    def test_unread_priest_support_rows_explicit(self):
        path=self.path('priest','lwPriestSupport')
        self.lists[path][17]['checked']=True
        result=compile_priest(self.values,self.lists)
        self.assertEqual(len(result.unresolved),3)
        self.assertIn('checked=True',result.unresolved[2])

    def test_self_party_heal_combo_tables(self):
        for suffix, offset in [('cmbSelfHeal',0xc8),('cmbPartyHeal',0xd4)]:
            paths=[p for p,s in _MAP['priest']['combos'].items() if s['offset']==offset]
            path=paths[0]
            for index, skill in enumerate((0,2,5,500,0x1fd,0x206,0x20f,0x218,0x221)):
                self.values[path]=index
                self.assertEqual(compile_priest(self.values,self.lists).parameters[offset],skill)
            self.values[path]=-1
            self.assertEqual(compile_priest(self.values,self.lists).parameters[offset],0)

    def test_unknown_combo_does_not_invent_previous_field(self):
        path=next(iter(_MAP['priest']['combos']))
        self.values[path]=999
        result=compile_priest(self.values,self.lists)
        self.assertNotIn(_MAP['priest']['combos'][path]['offset'],result.parameters)
        self.assertIn('retains previous',result.unresolved[-1])

    def test_warrior_raw_parameter_no_unsourced_ms_conversion(self):
        path=self.path('warrior','txtProvokeModeWait','integers')
        self.values[path]='32'
        self.assertEqual(compile_warrior(self.values,self.lists).parameters[0x1a0],32)

    def test_reordered_or_renamed_list_rejected(self):
        path=self.path('warrior','lwWarriorBasic')
        self.lists[path][0],self.lists[path][1]=self.lists[path][1],self.lists[path][0]
        with self.assertRaises(ValueError): compile_warrior(self.values,self.lists)

    def test_missing_or_extra_rows_rejected(self):
        path=self.path('priest','lwPriestHeal')
        self.lists[path].append(copy.deepcopy(self.lists[path][0]))
        with self.assertRaises(ValueError):compile_priest(self.values,self.lists)
        self.lists.pop(path)
        with self.assertRaises(ValueError):compile_priest(self.values,self.lists)

    def test_checked_and_checkbox_require_bool(self):
        self.lists[self.path('warrior','lwWarriorBasic')][0]['checked']=1
        with self.assertRaises(ValueError):compile_warrior(self.values,self.lists)
        self.lists[self.path('warrior','lwWarriorBasic')][0]['checked']=False
        self.values[next(iter(_MAP['warrior']['booleans']))]=1
        with self.assertRaises(ValueError):compile_warrior(self.values,self.lists)

    def test_decimal_policy_rejects_nondecimal_and_overflow(self):
        path=next(iter(_MAP['warrior']['integers']))
        for value in ('1.2','0x20','abc',str(1<<31),False):
            self.values[path]=value
            with self.assertRaises(ValueError):compile_warrior(self.values,self.lists)

    def test_result_does_not_mutate_inputs_and_maps_are_readonly(self):
        saved=copy.deepcopy(self.lists)
        result=compile_priest(self.values,self.lists)
        self.assertEqual(saved,self.lists)
        with self.assertRaises(TypeError):result.flags[0]=True

    def enable_offset(self,job,offset):
        for path,offsets in _MAP[job]['lists'].items():
            if offset in offsets:
                self.lists[path][offsets.index(offset)]['checked']=True
                return
        raise AssertionError('Unmapped source offset')

    def test_mage_62_and_rogue_all_rows_have_source_configuration(self):
        for compiler,rows in ((compile_mage,MAGE_ATTACK_ROWS),(compile_rogue,MELEE_ROWS+BOW_ROWS+SPECIAL_ROWS)):
            result=compiler(self.values,self.lists)
            self.assertTrue(all(result.flags[row.flag_offset] is False for row in rows))

    def test_mage_ui_to_attack_priority(self):
        row=MAGE_ATTACK_ROWS[0]
        self.enable_offset('mage',row.flag_offset)
        config=compile_mage(self.values,self.lists)
        snapshot=MageAttackSnapshot(now_ms=100000,distance=1,configured_range=8,mp=row.mp_minimum,
            flags=config.flags,raw_stats={row.stat_reader:row.stat_minimum},timer_values={row.timer_offset:0},
            locked_561f7e=False,raw_field_55403c_nonzero=False,raw_field_554020_nonzero=False)
        self.assertEqual(select_mage_attack(snapshot).row,row)

    def test_rogue_ui_to_melee_priority(self):
        row=MELEE_ROWS[0]
        self.enable_offset('rogue',row.flag_offset)
        config=compile_rogue(self.values,self.lists)
        snapshot=RogueSnapshot(now_ms=100000,distance=1,configured_range=12,mp=row.mp_minimum,
            flags=config.flags,raw_stats={row.stat_reader:row.stat_minimum},last_ms_by_offset={row.timer_offset:0})
        self.assertEqual(select_rogue_melee(snapshot).row,row)

    def test_mage_summary_flags_are_distinct_source_subsets(self):
        config=compile_mage(self.values,self.lists)
        self.assertFalse(config.flags[0]);self.assertFalse(config.flags[1])
        self.enable_offset('mage',0x12)
        config=compile_mage(self.values,self.lists)
        self.assertTrue(config.flags[0]);self.assertFalse(config.flags[1])
        self.enable_offset('mage',0x80)
        self.assertTrue(compile_mage(self.values,self.lists).flags[1])

    def test_mage_support_unread_final_row_is_explicit(self):
        config=compile_mage(self.values,self.lists)
        self.assertEqual(len(config.unresolved),1)
        self.assertIn('[18]',config.unresolved[0])

    def test_arrow_rain_requests_radio_update_without_mutating_input(self):
        path=self.path('rogue','charrowrain','booleans')
        self.values[path]=True
        saved=copy.deepcopy(self.values)
        config=compile_rogue(self.values,self.lists)
        self.assertEqual(list(config.ui_updates.values()),[True])
        self.assertTrue(next(iter(config.ui_updates)).endswith('/rdUseNormalSkill'))
        self.assertEqual(saved,self.values)

    def test_support_settings_fields_and_raw_interval(self):
        mage=compile_mage(self.values,self.lists)
        MageSettings(mage.flags[3],mage.parameters[4],mage.flags[8],mage.texts[0xc])
        rogue=compile_rogue(self.values,self.lists)
        MinorSettings(rogue.flags[0],rogue.parameters[4],rogue.parameters[8])
        self.assertEqual(rogue.parameters[8],150)
        kurian=compile_kurian(self.values,self.lists)
        KurianSettings(kurian.flags[0xdb],kurian.parameters[0xdc])
        self.assertEqual(len(kurian.flags),35)

    def test_mage_unicode_target_name_preserved_without_game_codec_guess(self):
        path=next(iter(_MAP['mage']['texts']))
        self.values[path]='İsimŞĞ'
        self.assertEqual(compile_mage(self.values,self.lists).texts[0xc],'İsimŞĞ')


if __name__=='__main__':unittest.main()
