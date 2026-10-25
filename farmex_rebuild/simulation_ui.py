"""Interactive, explicitly simulated inputs for the implemented decision engines."""
import tkinter as tk
import json
from tkinter import ttk
from follow_trial import FollowTrial,example_follow_sample
from monster_stone_trial import MonsterStoneTrial,example_ms_activation,describe_ms_trial
from ms_achievement_trial import AchievementTrial,example_achievement_sample,describe_achievement_trial
from allocation_panel_trial import AllocationPanelTrial,compile_allocation_panel,example_allocation_sample,describe_allocation_panel
from event_join_trial import EventJoinTrial,event_snapshot,example_event_sample,describe_event_trial
from transformation_trial import TransformationTrial,transformation_snapshot,example_transformation_sample,describe_transformation_trial
from tp_protection_trial import TPProtectionTrial,tp_snapshot,example_tp_sample,describe_tp_trial
from protection_panel_trial import ProtectionSettingsTrial,example_protection_sample,describe_protection_trial
from disconnect_panel_trial import DisconnectSettingsTrial,example_disconnect_sample,describe_disconnect_trial
from genie_settings_trial import GenieSettingsTrial,example_genie_settings_sample,describe_genie_settings_trial
from control_settings_trial import ControlSettingsTrial,example_control_settings_sample,describe_control_settings_trial
from item_break_settings_trial import ItemBreakSettingsTrial,example_item_break_settings_sample,describe_item_break_settings_trial
from jail_selection_trial import JailSelectionTrial,example_selection_sample,describe_selection_trial
from dc_panel_trial import DCPanelTrial,example_dc_sample,describe_dc_trial
from party_invitation_trial import PartyInvitationTrial,example_invitation_sample
from chat_party_trial import ChatPartyTrial,example_chat_party_sample,EXAMPLE_CHAT_HEX
from chat_commands_trial import ChatCommandsTrial,example_chat_commands_sample,example_detailed_commands_sample,EXAMPLE_COMMAND_HEX
from chat_skills_trial import ChatSkillsTrial,example_chat_skills_sample,EXAMPLE_SKILL_HEX
from dataclasses import fields as dataclass_fields, is_dataclass, replace
from collections.abc import Mapping
from enum import Enum
from operation_engine import (LootRecord, LootSettings, LootSnapshot, loot_step,
    UpgradeRunner, UpgradeRow, UpgradeSnapshot, MerchantRunner, MerchantSettings,
    MerchantKind, MerchantRow, MerchantSnapshot,OperationDecision)
from merchant_setup import BuySetupObservation,MerchantInventoryObservation
from merchant_preparation import BUY_LIST_PATH,BuyPreparationRow,BuyPreparationObservation
from merchant_open import BuyOpenState,BuyOpenObservation
from merchant_open_frame import BuyOpenCallerState,BuyOpenFrame
from merchant_open_clock import BuyOpenClockSample
from merchant_monitor import BuyMonitorObservation
from merchant_sell_preparation import SELL_LIST_PATH,SellPreparationState,replay_sell_preparation
from merchant_sell_setup import SellSetupObservation
from merchant_sell_selection import SellSelectionObservation
from merchant_sell_cost import SellCostObservation,plan_sell_cost
from merchant_sell_prepare_wait import parse_sell_prepare_wait
from merchant_sell_coin_alarm import plan_sell_coin_alarm
from merchant_sell_failure import parse_sell_failure,parse_bank_error_returns
from merchant_buy_failure import parse_buy_failure
from merchant_configuration import (compile_buy_merchant_panel,buy_merchant_settings_from_panel,
    compile_sell_merchant_panel,sell_merchant_settings_from_panel,sell_coin_alarm_from_panel)
from merchant_reply import (MerchantReplyState,MerchantReplyObservation,
    plan_merchant_reply,merchant_snapshot_from_reply)
from support_engine import GuardConfig, GuardSnapshot, evaluate_guards, CrashSnapshot, abyss_crash_decision
from policies import weight_supply_due, stock_supply_due, MessageSequence, MessageRow
from combat_engine import (Vitals, PartyMember, SupportSnapshot, PriestSettings, MinorSettings, KurianSettings,
    MageSettings, priest_heal, rogue_minor, kurian_heal, mage_tp)
from mining_engine import MiningRunner, MiningRunnerConfig, MiningExecutionState, MiningSnapshot,OreSlotState,OreSlotSnapshot
from mining_configuration import MiningPanelConfiguration,compile_mining_panel,mining_runner_configuration,mining_ore_settings
from route_catalog import ROUTE_COMBO_PATHS
from global_route_choices import ROUTE_GLOBALS,compile_panel_route_name
from mining_pipeline import MiningPipelineState,MiningPipelineObservation
from mining_slot_name import SlotNameObservation
from mining_requests import GOLD_NAME,ORE_NAME
from mining_frame import MiningFrameState,MiningFrameObservation,replay_mining_frame
from mining_callback import MiningCallbackState,MiningCallbackObservation,replay_mining_callback
from mining_effects import MiningEffectObservation
from mining_transitions import MiningCandidateSlot
from priest_attack import PriestAttackSnapshot, PRIEST_ATTACK_ROWS, select_priest_attack
from alternate_dispatcher import AlternateSnapshot, AlternateState, dispatch_alternate
from job_dispatcher import HelperReply, WarriorSkillSnapshot, WARRIOR_ROWS, select_warrior_skill
from class_configuration import compile_class_configuration
from support_configuration import support_settings_from_config
from combat_configuration import compile_bot_combat
from attack_configuration import (rogue_volley_ranges, rogue_alternate_bow_ranges,
    RogueAlternateBowRanges, warrior_provoke_settings, WarriorProvokeSettings)
from rogue_alternate_bow import AlternateBowObservation,plan_alternate_bow
from rogue_combo import ComboObservation
from rogue_chain import RogueChainState,replay_rogue_chain
from attack_lock import AttackLockState,LockCallbackObservation,plan_callback_attack_unlock,apply_lock_write_plans
from combo_configuration import ComboPanelConfiguration,compile_combo_panel
from loot_configuration import LootPanelConfiguration,compile_loot_panel
from upgrade_configuration import compile_upgrade_panel,upgrade_runner_from_panel,selected_upgrade_scroll_text
from upgrade_scroll import UpgradeScrollObservation,UpgradeScrollSample
from upgrade_start import UpgradeStartState,UpgradeStartRow,UpgradeStartObservation,replay_upgrade_start,apply_upgrade_start
from upgrade_packets import UpgradePacketObservation
from upgrade_execution import UpgradeExecution,ArmorExecutionInputs
from upgrade_armor import ArmorPacketObservation,ArmorFreeSlotObservation,VENDORS as ARMOR_VENDORS
from armor_start import (COMBO_PATH as ARMOR_COMBO_PATH,ArmorStartObservation,replay_armor_start,
    capture_armor_start_state,apply_armor_start)
from npc_lookup import NpcCandidate
from loot_pipeline import LootRecordProducer,replay_loot_pipeline
from loot_packets import plan_loot_intents
from supply_configuration import compile_supply_panel,weight_percent_dword,plan_supply_weight
from supply_stock import compile_supply_list,SupplyStockObservation,plan_supply_stock
from control_guards import compile_control_guards,ControlGuardObservation,plan_control_guards
from control_continuation import compile_control_continuation,ControlContinuationObservation,replay_control_chain
from party_help import compile_party_help,PartyHelpState
from control_alarms import compile_control_alarms,LootActivityState
from control_frame import ControlFrameConfiguration,ControlFrameState,ControlFrameObservation,replay_control_frame
from control_capture import parse_control_sample
from control_callback import ControlCallbackState,ControlCallbackInputs,replay_control_callback
from callback_interlude import CallbackInterludeState,replay_callback_interlude
from callback_capture import parse_interlude_sample
from loot_classifier import LootListState,LootListObservation,LootMetadataObservation,plan_loot_list
from loot_name_cache import (LOOT_LIST_PATH,LootCacheState,LootCacheRow,compile_loot_name_cache,
    classify_loot_with_name_cache)
from item_name import ItemNameObservation,plan_item_name
from name_codec import WindowsNameCodec,convert_name_chain
from kurian_attack import (KURIAN_ATTACK_ROWS,KURIAN_SPECIAL_ROWS,select_kurian_attack,
    select_kurian_special,KurianCycleState,KurianCycleSnapshot,replay_kurian_cycle)
from warrior_alternate import ProvokeState,ProvokeSnapshot,PROVOKE_ROWS,replay_warrior_provoke
from family_runner import FamilyRunner
from target_configuration import compile_target_configuration
from target_resolver import TargetResolver,ResolverCandidate,ResolverSnapshot,CurrentTargetObservation
from target_branches import TargetBranchObservation,LeaderTargetObservation,plan_target_branch
from mage_attack import MageAttackSnapshot, MAGE_ATTACK_ROWS, select_mage_attack
from rogue_attack import (RogueSnapshot, MELEE_ROWS, BOW_ROWS, SPECIAL_ROWS,
    select_rogue_melee, select_rogue_bow, select_rogue_special, plan_rogue_volley)
from quest_engine import QuestRecord, QuestSnapshot, plan_take_quest
from action_queue import QueueState, QueueSample, CallbackQueueGate, enqueue, drain
from repair_engine import RepairObservation, repair_step
from repair_inventory import RepairSlot, RepairInventoryObservation, STARTUP_SLOTS
from enchant_engine import EnchantObservation, enchant_step
from npc_sell_engine import NpcSaleState,NpcSaleObservation,npc_sale_step
from npc_sell_filter import SellFilterObservation
from npc_sell_packets import NpcSellRecord,SellCacheSlot,VENDORS
from npc_buy_engine import NpcBuyState,NpcBuyObservation,NpcBuyRouteRow,npc_buy_step
from npc_buy_packets import NpcBuyRecord,NpcBuyPacketObservation,BUY_VENDORS


class EnginePage:
    # Settings previews remain separate from the worker decision cases below.
    CASES = ('Kontrol Ayarları', 'Genie Ayarları', 'DC / Relog Ayarları', 'DC Koruma', 'DC–Hapis Listesi', 'Koruma Ayarları', 'TP Koruma', 'Transformation', 'Etkinlik Katılımı', 'Stat/Skill Ayarları', 'Achieve MS', 'Monster Stone', 'Takip', 'Party Daveti', 'Chat/PM Party', 'Chat Komutları', 'Chat Yetenek İsteği', 'Upgrade', 'Armor Alımı', 'Sell Merchant', 'Buy Merchant', 'Loot', 'Kontrol', 'Item Kır',
             'Tedarik', 'Flood', 'Priest', 'Priest Saldırı', 'Rogue Minor', 'Kurian', 'Mage TP',
             'Mage Alternatif', 'Kurian Alternatif', 'Warrior Alternatif',
             'Priest Alternatif', 'Rogue Alternatif', 'Warrior Saldırı', 'Mage Saldırı',
             'Rogue Yakın', 'Rogue Yay', 'Rogue Özel', 'Rogue Çoklu', 'Görev Alma', 'Maden',
             'NPC Onarım', 'NPC Enchant', 'NPC Satış', 'NPC Satın Alma', 'Eylem Kuyruğu', 'Warrior Provoke', 'Sınıf Ailesi', 'Hedef Seçimi', 'Rogue Alternatif Yay', 'Rogue Combo Zinciri', 'Kurian Saldırı', 'Kurian Özel', 'Kurian Döngü', 'Loot Filtre')
    CASES = ('Item Kırma Ayarları',) + CASES
    def __init__(self, frame, configuration_reader=None, configuration_writer=None,route_configuration_reader=None,
                 bank_route_reader=None,bank_route_consumer=None,buy_bank_route_reader=None,buy_bank_route_consumer=None):
        self.configuration_reader = configuration_reader
        self.configuration_writer = configuration_writer
        self.route_configuration_reader=route_configuration_reader
        self.bank_route_reader=bank_route_reader;self.bank_route_consumer=bank_route_consumer
        self.buy_bank_route_reader=buy_bank_route_reader;self.buy_bank_route_consumer=buy_bank_route_consumer
        top = ttk.Frame(frame, padding=8)
        top.pack(fill='x')
        ttk.Label(top, text='Yerel deneme • Oyuna işlem gönderilmez').pack(side='left')
        self.case = tk.StringVar(value='Upgrade')
        choice = ttk.Combobox(top, values=self.CASES, textvariable=self.case, state='readonly', width=18)
        choice.pack(side='left', padx=12)
        choice.bind('<<ComboboxSelected>>', lambda _: self.reset())
        self.inputs = {}
        self.input_labels = {}
        self.input_titles = {}
        fields = [('hp', 'HP', 30), ('hp_max', 'Maksimum HP', 100), ('mp', 'MP', 1100),
                  ('threshold', 'Eşik (%)', 50), ('item_id', 'Deneme eşya/beceri ID', 1),
                  ('quantity', 'Stok / pazar adet', 2), ('price', 'Pazar fiyatı / coin', 100),
                  ('wait', 'Bekleme (saniye; maden için dakika)', 2), ('distance', 'Hedef / NPC mesafesi', 5)]
        settings = ttk.Frame(frame, padding=8)
        settings.pack(fill='x')
        self.follow_trial=FollowTrial(self.configuration_reader)
        self.ms_trial=MonsterStoneTrial(self.configuration_reader,self.configuration_writer)
        self.allocation_trial=AllocationPanelTrial(self.configuration_reader)
        self.protection_trial=ProtectionSettingsTrial(self.configuration_reader,self.route_configuration_reader)
        self.disconnect_trial=DisconnectSettingsTrial(self.configuration_reader,self.route_configuration_reader)
        self.genie_settings_trial=GenieSettingsTrial(self.configuration_reader)
        self.control_settings_trial=ControlSettingsTrial(self.configuration_reader)
        self.item_break_settings_trial=ItemBreakSettingsTrial(self.configuration_reader)
        self.item_break_settings_controls=ttk.Frame(settings)
        self.item_break_settings_controls.grid(row=45,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.item_break_settings_controls,text='Item Kır sekmesindeki etkinleştirme, hız ve Abyss seçimini yerel olarak önizler.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.item_break_settings_sample=tk.StringVar(value='{}')
        ttk.Entry(self.item_break_settings_controls,textvariable=self.item_break_settings_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.item_break_settings_controls,text='Panel ayarlarını önizle',command=self.item_break_settings_example).grid(row=2,column=0,sticky='w')
        self.control_settings_controls=ttk.Frame(settings)
        self.control_settings_controls.grid(row=44,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.control_settings_controls,text='Kontrol sekmesindeki sınır, saat ve party ayarlarını yerel olarak önizler.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.control_settings_sample=tk.StringVar(value='{}')
        ttk.Entry(self.control_settings_controls,textvariable=self.control_settings_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.control_settings_controls,text='Panel ayarlarını önizle',command=self.control_settings_example).grid(row=2,column=0,sticky='w')
        self.genie_settings_controls=ttk.Frame(settings)
        self.genie_settings_controls.grid(row=43,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.genie_settings_controls,text='Kontrol sekmesindeki doğrulanmış beş Genie ayarını yerel olarak önizler.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.genie_settings_sample=tk.StringVar(value='{}')
        ttk.Entry(self.genie_settings_controls,textvariable=self.genie_settings_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.genie_settings_controls,text='Panel ayarlarını önizle',command=self.genie_settings_example).grid(row=2,column=0,sticky='w')
        self.disconnect_controls=ttk.Frame(settings)
        self.disconnect_controls.grid(row=42,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.disconnect_controls,text='Kontrol sekmesindeki DC ve otomatik giriş ayarlarını yerel olarak önizler.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.disconnect_sample=tk.StringVar(value='{}')
        ttk.Entry(self.disconnect_controls,textvariable=self.disconnect_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.disconnect_controls,text='Panel ayarlarını önizle',command=self.disconnect_example).grid(row=2,column=0,sticky='w')
        self.jail_selection_trial=JailSelectionTrial(self.configuration_reader,self.route_configuration_reader)
        self.dc_trial=DCPanelTrial(self.configuration_reader)
        self.dc_controls=ttk.Frame(settings)
        self.dc_controls.grid(row=41,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.dc_controls,text='Koruma bölümündeki DC seçimlerini ve gönderim çağrı planını yerelde dener.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.dc_sample=tk.StringVar(value='{}')
        ttk.Entry(self.dc_controls,textvariable=self.dc_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.dc_controls,text='Panele bağlı boş kaynak örneği',command=self.dc_example).grid(row=2,column=0,sticky='w')
        self.jail_selection_controls=ttk.Frame(settings)
        self.jail_selection_controls.grid(row=40,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.jail_selection_controls,text='DC–Hapis penceresindeki seçili başlıkları yerel kayıt modelinde dener.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.jail_selection_sample=tk.StringVar(value='{}')
        ttk.Entry(self.jail_selection_controls,textvariable=self.jail_selection_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.jail_selection_controls,text='Seçili başlıklardan sentetik örnek',command=self.jail_selection_example).grid(row=2,column=0,sticky='w')
        self.protection_controls=ttk.Frame(settings)
        self.protection_controls.grid(row=39,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.protection_controls,text='Koruma bölümündeki 50 kaynak alanını yerel ayar modelinde dener. Dönüşüm örneği seçili rota kod sayfasını kullanır.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.protection_sample=tk.StringVar(value='{}')
        ttk.Entry(self.protection_controls,textvariable=self.protection_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.protection_controls,text='Panelden sentetik derleme örneği',command=self.protection_example).grid(row=2,column=0,sticky='w')
        self.tp_trial=TPProtectionTrial(self.configuration_reader)
        self.tp_controls=ttk.Frame(settings)
        self.tp_controls.grid(row=38,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.tp_controls,text='Koruma > Karakter TP Olursa ayarları ve yerel olay denemesi. Durdurma/DC çağrıları yalnız planlanır.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.tp_packet=tk.StringVar(value='27 01 0a');self.tp_sample=tk.StringVar(value='{}')
        ttk.Label(self.tp_controls,text='Olay HEX').grid(row=1,column=0,sticky='w')
        ttk.Entry(self.tp_controls,textvariable=self.tp_packet,width=55).grid(row=1,column=1,sticky='ew')
        ttk.Entry(self.tp_controls,textvariable=self.tp_sample,width=110).grid(row=2,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.tp_controls,text='Panele ve olaya göre sentetik örnek',command=self.tp_example).grid(row=3,column=0,sticky='w')
        self.transformation_trial=TransformationTrial(self.configuration_reader)
        self.transformation_controls=ttk.Frame(settings)
        self.transformation_controls.grid(row=37,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.transformation_controls,text='Genel > Transformation ayar öneki ve açık yardımcı çağrısı denemesi. Periyodik kullanım doğrulanmadı; oyuna işlem gönderilmez.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.transformation_sample=tk.StringVar(value='{}')
        ttk.Entry(self.transformation_controls,textvariable=self.transformation_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.transformation_controls,text='Panelden sentetik ayar ve açık çağrı örneği',command=self.transformation_example).grid(row=2,column=0,sticky='w')
        self.event_trial=EventJoinTrial(self.configuration_reader)
        self.event_controls=ttk.Frame(settings)
        self.event_controls.grid(row=36,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.event_controls,text='Genel > Etkinlik seçeneklerini yerel kuyrukta dener. Oyuna katılım isteği gönderilmez.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.event_sample=tk.StringVar(value='{}')
        ttk.Entry(self.event_controls,textvariable=self.event_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.event_controls,text='Seçimlere göre sentetik örnek',command=self.event_example).grid(row=2,column=0,sticky='w')
        self.allocation_controls=ttk.Frame(settings)
        self.allocation_controls.grid(row=35,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.allocation_controls,text='Diğer > Otomatik Stat/Skill listelerini yerel ayar satırlarına dönüştürür. Satır üretimi puan dağıtımı değildir; oyuna işlem gönderilmez.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.allocation_sample=tk.StringVar(value='{}')
        ttk.Entry(self.allocation_controls,textvariable=self.allocation_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.allocation_controls,text='Mevcut satırlara sentetik gözlem örneği',command=self.allocation_example).grid(row=2,column=0,sticky='w')
        self.achievement_trial=AchievementTrial()
        self.achievement_controls=ttk.Frame(settings)
        self.achievement_controls.grid(row=34,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.achievement_controls,text='Achieve MS: 11 sıralı istek girişimini kendi kuyruğunda dener. Ödül kazanımı sunucudan doğrulanmadı.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.achievement_sample=tk.StringVar(value='{}')
        ttk.Entry(self.achievement_controls,textvariable=self.achievement_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.achievement_controls,text='11 istek için sentetik örneği doldur',command=lambda:self.achievement_sample.set(example_achievement_sample())).grid(row=2,column=0,sticky='w')
        self.ms_controls=ttk.Frame(settings)
        self.ms_controls.grid(row=33,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.ms_controls,text='Monster Stone panelindeki seçim ve alarm ayarlarını kullanır. Etkinleştirme adımlarını yerel olarak dener; oyun işleyicisini çalıştırmaz.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.ms_sample=tk.StringVar(value='{}')
        ttk.Entry(self.ms_controls,textvariable=self.ms_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.ms_controls,text='Sentetik dönüş örneğini doldur',command=lambda:self.ms_sample.set(example_ms_activation())).grid(row=2,column=0,sticky='w')
        self.party_trial=PartyInvitationTrial(self.configuration_reader)
        self.chat_party_trial=ChatPartyTrial(self.configuration_reader)
        self.chat_commands_trial=ChatCommandsTrial(self.configuration_reader)
        self.chat_skills_trial=ChatSkillsTrial(self.configuration_reader)
        self.chat_skills_controls=ttk.Frame(settings)
        self.chat_skills_controls.grid(row=32,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.chat_skills_controls,text='Job > Mage/Rogue/Priest chat yetenek ayarlarını kullanır. Mesajdan bekleyen istek üretimini dener; oyunda yetenek kullanmaz. Aynı girdide devam eder; Sıfırla yeni deneme başlatır.',wraplength=950).grid(row=0,column=0,columnspan=3,sticky='w')
        self.chat_skills_packet=tk.StringVar(value='10');self.chat_skills_sample=tk.StringVar(value='{}');self.chat_skills_codepage=tk.StringVar(value='1254')
        self.chat_skills_example_family=tk.StringVar(value='Mage')
        ttk.Label(self.chat_skills_controls,text='Mesaj HEX').grid(row=1,column=0,sticky='w')
        ttk.Entry(self.chat_skills_controls,textvariable=self.chat_skills_packet,width=75).grid(row=1,column=1,sticky='ew')
        ttk.Combobox(self.chat_skills_controls,textvariable=self.chat_skills_codepage,values=('1254','65001'),state='readonly',width=8).grid(row=1,column=2)
        ttk.Entry(self.chat_skills_controls,textvariable=self.chat_skills_sample,width=110).grid(row=2,column=0,columnspan=3,sticky='ew')
        ttk.Combobox(self.chat_skills_controls,textvariable=self.chat_skills_example_family,values=('Mage','Rogue','Priest'),state='readonly',width=10).grid(row=3,column=0,sticky='w')
        ttk.Button(self.chat_skills_controls,text='Sentetik “go” mesajı ve sınıf gözlemi',command=self.chat_skills_example).grid(row=3,column=1,sticky='w')
        self.chat_commands_controls=ttk.Frame(settings)
        self.chat_commands_controls.grid(row=31,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.chat_commands_controls,text='Diğer > Chat Komutlarına Göre İşlem Yap ayarlarını kullanır. Komut dalına girildiği varsayılan yerel deneme; oyunda eylem yürütmez. Aynı mesajda devam eder; Sıfırla yeni deneme başlatır.',wraplength=950).grid(row=0,column=0,columnspan=3,sticky='w')
        self.chat_commands_packet=tk.StringVar(value='10');self.chat_commands_sample=tk.StringVar(value='{}');self.chat_commands_codepage=tk.StringVar(value='1254')
        ttk.Label(self.chat_commands_controls,text='Mesaj HEX').grid(row=1,column=0,sticky='w')
        ttk.Entry(self.chat_commands_controls,textvariable=self.chat_commands_packet,width=75).grid(row=1,column=1,sticky='ew')
        ttk.Combobox(self.chat_commands_controls,textvariable=self.chat_commands_codepage,values=('1254','65001'),state='readonly',width=8).grid(row=1,column=2)
        ttk.Entry(self.chat_commands_controls,textvariable=self.chat_commands_sample,width=110).grid(row=2,column=0,columnspan=3,sticky='ew')
        ttk.Button(self.chat_commands_controls,text='Sentetik “go” mesajı',command=self.chat_commands_example).grid(row=3,column=0,sticky='w')
        self.chat_commands_detailed=tk.BooleanVar(value=False)
        ttk.Checkbutton(self.chat_commands_controls,text='Ayrıntılı yardımcı denemesi',variable=self.chat_commands_detailed).grid(row=4,column=0,sticky='w')
        ttk.Button(self.chat_commands_controls,text='Ayrıntılı sentetik örnek',command=self.chat_commands_detailed_example).grid(row=3,column=1,sticky='w')
        self.chat_party_controls=ttk.Frame(settings)
        self.chat_party_controls.grid(row=30,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.chat_party_controls,text='Chat/PM: Diğer > Party Davet Ayarları komutunu ve isim listesini kullanır. Davet dalına ulaşıldığı varsayılan yerel deneme; oyuna mesaj göndermez. Aynı girdide devam eder; Sıfırla yeni deneme başlatır.',wraplength=950).grid(row=0,column=0,columnspan=3,sticky='w')
        self.chat_party_packet=tk.StringVar(value='10');self.chat_party_sample=tk.StringVar(value='{}');self.chat_party_codepage=tk.StringVar(value='1254')
        ttk.Label(self.chat_party_controls,text='Mesaj HEX').grid(row=1,column=0,sticky='w')
        ttk.Entry(self.chat_party_controls,textvariable=self.chat_party_packet,width=75).grid(row=1,column=1,sticky='ew')
        ttk.Combobox(self.chat_party_controls,textvariable=self.chat_party_codepage,values=('1254','65001'),state='readonly',width=8).grid(row=1,column=2)
        ttk.Entry(self.chat_party_controls,textvariable=self.chat_party_sample,width=110).grid(row=2,column=0,columnspan=3,sticky='ew')
        ttk.Button(self.chat_party_controls,text='Sentetik Alice “add” mesajı',command=self.chat_party_example).grid(row=3,column=0,sticky='w')
        self.party_controls=ttk.Frame(settings)
        self.party_controls.grid(row=29,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.party_controls,text='Party: Diğer > Party Davet Ayarları panelini kullanır. Yalnız captured veri denemesi; yanıt gönderilmez.',wraplength=950).grid(row=0,column=0,columnspan=3,sticky='w')
        self.party_packet=tk.StringVar(value='2f02');self.party_sample=tk.StringVar(value='{}');self.party_codepage=tk.StringVar(value='1254')
        ttk.Label(self.party_controls,text='Captured HEX').grid(row=1,column=0,sticky='w')
        ttk.Entry(self.party_controls,textvariable=self.party_packet,width=75).grid(row=1,column=1,sticky='ew')
        ttk.Combobox(self.party_controls,textvariable=self.party_codepage,values=('1254','65001'),state='readonly',width=8).grid(row=1,column=2)
        ttk.Entry(self.party_controls,textvariable=self.party_sample,width=110).grid(row=2,column=0,columnspan=3,sticky='ew')
        ttk.Button(self.party_controls,text='Sentetik Alice daveti örneği',command=self.party_example).grid(row=3,column=0,sticky='w')
        self.follow_controls=ttk.Frame(settings)
        self.follow_controls.grid(row=28,column=0,columnspan=6,sticky='ew')
        ttk.Label(self.follow_controls,text='Takip: Genel > Takip panelini kullanır. Gözlemler boşsa bekler; oyuna hareket göndermez.',wraplength=950).grid(row=0,column=0,columnspan=2,sticky='w')
        self.follow_sample=tk.StringVar(value='{}')
        ttk.Entry(self.follow_controls,textvariable=self.follow_sample,width=110).grid(row=1,column=0,columnspan=2,sticky='ew')
        ttk.Button(self.follow_controls,text='Sentetik örneği doldur',command=lambda:self.follow_sample.set(example_follow_sample())).grid(row=2,column=0,sticky='w')
        ttk.Label(self.follow_controls,text='Örnek: X10/Y20; liderde Y20, isim modunda Y24. Gerçek oyun verisi değildir.',wraplength=800).grid(row=2,column=1,sticky='w')
        for row, (name, label, default) in enumerate(fields):
            variable = tk.StringVar(value=str(default))
            self.inputs[name] = variable
            self.input_titles[name]=label
            self.input_labels[name]=ttk.Label(settings,text=label)
            self.input_labels[name].grid(row=row // 3,column=(row % 3)*2,sticky='w',padx=5,pady=4)
            ttk.Entry(settings, textvariable=variable, width=10).grid(row=row // 3, column=(row % 3) * 2 + 1, padx=5)
        self.ready = tk.BooleanVar(value=True)
        self.full = tk.BooleanVar(value=False)
        self.ready_control=ttk.Checkbutton(settings,text='Deneme işlem kapısı açık / loot kutusu açık',variable=self.ready)
        self.ready_control.grid(row=3,column=0,columnspan=3,sticky='w')
        ttk.Checkbutton(settings, text='Çanta dolu', variable=self.full).grid(row=3, column=3, columnspan=3, sticky='w')
        self.use_class_panel = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings, text='Bağlı motor denemelerinde panel ayarlarını kullan',
                        variable=self.use_class_panel).grid(row=4, column=0, columnspan=6, sticky='w')
        self.upgrade_scroll_controls=ttk.Frame(settings)
        self.upgrade_scroll_controls.grid(row=18,column=0,columnspan=6,sticky='w')
        self.upgrade_scroll_fixture=tk.BooleanVar(value=False)
        self.upgrade_scroll_slot=tk.StringVar(value='2')
        ttk.Checkbutton(self.upgrade_scroll_controls,text='Upgrade/Armor için örnek başlangıç/çanta gözlemleri',
                        variable=self.upgrade_scroll_fixture).pack(side='left')
        self.upgrade_slot_label=ttk.Label(self.upgrade_scroll_controls,text='Scroll çanta yuvası (0–27; -1=yok)')
        self.upgrade_slot_label.pack(side='left',padx=5)
        ttk.Entry(self.upgrade_scroll_controls,textvariable=self.upgrade_scroll_slot,width=5).pack(side='left')
        self.upgrade_queue_gate=tk.StringVar(value='1')
        ttk.Label(self.upgrade_scroll_controls,text='Kuyruk bağlantısı (0:kapalı)').pack(side='left',padx=5)
        ttk.Entry(self.upgrade_scroll_controls,textvariable=self.upgrade_queue_gate,width=4).pack(side='left')
        self.armor_extra=ttk.Frame(settings)
        self.armor_extra.grid(row=19,column=0,columnspan=6,sticky='w')
        self.armor_second_gate=tk.StringVar(value='1')
        ttk.Label(self.armor_extra,text='İkinci kuyruk bağlantısı (0:kapalı)').pack(side='left')
        ttk.Entry(self.armor_extra,textvariable=self.armor_second_gate,width=4).pack(side='left',padx=5)
        ttk.Label(self.armor_extra,text='NPC/konum gözlemleri örnektir; oyunda arama yapılmaz.').pack(side='left',padx=5)
        self.buy_merchant_controls=ttk.Frame(settings)
        self.buy_merchant_controls.grid(row=20,column=0,columnspan=6,sticky='w')
        self.buy_merchant_fixture=tk.BooleanVar(value=False)
        ttk.Checkbutton(self.buy_merchant_controls,text='Alış pazarı için örnek hazırlık/çanta gözlemleri',
                        variable=self.buy_merchant_fixture).pack(side='left')
        self.buy_merchant_coins=tk.StringVar(value='1000')
        self.buy_merchant_free=tk.StringVar(value='12')
        self.buy_merchant_threshold=tk.StringVar(value='0')
        for title,variable in (('Coin',self.buy_merchant_coins),('Boş yuva (0–28)',self.buy_merchant_free),
                               ('Boş yuva eşiği',self.buy_merchant_threshold)):
            ttk.Label(self.buy_merchant_controls,text=title).pack(side='left',padx=4)
            ttk.Entry(self.buy_merchant_controls,textvariable=variable,width=8).pack(side='left')
        self.buy_reply_controls=ttk.Frame(settings)
        self.buy_reply_controls.grid(row=21,column=0,columnspan=6,sticky='w')
        self.buy_reply_fixture=tk.BooleanVar(value=False)
        self.buy_reply_hex=tk.StringVar(value='68 28 01 00 00 00')
        self.buy_reply_actor=tk.StringVar(value='1')
        ttk.Checkbutton(self.buy_reply_controls,text='Yanıt örneğiyle bekle (yeni denemede)',
                        variable=self.buy_reply_fixture).pack(side='left')
        ttk.Label(self.buy_reply_controls,text='Hex').pack(side='left',padx=4)
        ttk.Entry(self.buy_reply_controls,textvariable=self.buy_reply_hex,width=23).pack(side='left')
        ttk.Label(self.buy_reply_controls,text='Yerel DWORD kimlik').pack(side='left',padx=4)
        ttk.Entry(self.buy_reply_controls,textvariable=self.buy_reply_actor,width=10).pack(side='left')
        ttk.Button(self.buy_reply_controls,text='Aşama 4: yerel örneği işle',
                   command=self.apply_merchant_reply).pack(side='left',padx=4)
        self.sell_preparation_controls=ttk.Frame(settings)
        self.sell_preparation_controls.grid(row=22,column=0,columnspan=6,sticky='w')
        self.sell_preparation_fixture=tk.BooleanVar(value=False)
        ttk.Checkbutton(self.sell_preparation_controls,text='Satış listesi hazırlayıcısını bağla (yeni denemede)',
                        variable=self.sell_preparation_fixture).pack(side='left')
        self.sell_setup_cost=tk.StringVar(value='0');self.sell_setup_matches=tk.StringVar(value='0')
        self.sell_setup_coins=tk.StringVar(value='1000')
        for title,variable in (('Örnek helper maliyeti QWORD',self.sell_setup_cost),
                               ('Helper eşleşme sayısı',self.sell_setup_matches),('Coin DWORD',self.sell_setup_coins)):
            ttk.Label(self.sell_preparation_controls,text=title).pack(side='left',padx=4)
            ttk.Entry(self.sell_preparation_controls,textvariable=variable,width=9).pack(side='left')
        self.sell_cost_controls=ttk.Frame(settings)
        self.sell_cost_controls.grid(row=23,column=0,columnspan=6,sticky='w')
        self.sell_cost_fixture=tk.BooleanVar(value=False)
        self.sell_cost_items=tk.StringVar(value='[]');self.sell_cost_quantities=tk.StringVar(value='[]')
        ttk.Checkbutton(self.sell_cost_controls,text='Envanter örneklerinden maliyet hesapla (hazırlık modunda)',
                        variable=self.sell_cost_fixture).pack(side='left')
        ttk.Label(self.sell_cost_controls,text='Taze item EAX dizisi (JSON)').pack(side='left',padx=4)
        ttk.Entry(self.sell_cost_controls,textvariable=self.sell_cost_items,width=22).pack(side='left')
        ttk.Label(self.sell_cost_controls,text='Adet EAX dizisi (JSON)').pack(side='left',padx=4)
        ttk.Entry(self.sell_cost_controls,textvariable=self.sell_cost_quantities,width=15).pack(side='left')
        self.sell_wait_controls=ttk.Frame(settings)
        self.sell_wait_controls.grid(row=24,column=0,columnspan=6,sticky='w')
        self.sell_wait_fixture=tk.BooleanVar(value=False)
        self.sell_wait_json=tk.StringVar(value='{}')
        ttk.Checkbutton(self.sell_wait_controls,text='Satış yanıtı beklemesini örnekle (yeni denemede)',
                        variable=self.sell_wait_fixture).pack(side='left')
        ttk.Label(self.sell_wait_controls,text='Aşama 3 gözlemi (JSON)').pack(side='left',padx=4)
        ttk.Entry(self.sell_wait_controls,textvariable=self.sell_wait_json,width=52).pack(side='left')
        self.sell_failure_controls=ttk.Frame(settings)
        self.sell_failure_controls.grid(row=26,column=0,columnspan=6,sticky='w')
        self.sell_failure_fixture=tk.BooleanVar(value=False)
        self.sell_failure_json=tk.StringVar(value='{}')
        ttk.Checkbutton(self.sell_failure_controls,text='SELL başarısızlık gözlemlerini bağla (yeni denemede)',
                        variable=self.sell_failure_fixture).pack(side='left')
        ttk.Entry(self.sell_failure_controls,textvariable=self.sell_failure_json,width=72).pack(side='left',padx=4)
        self.buy_failure_controls=ttk.Frame(settings)
        self.buy_failure_controls.grid(row=27,column=0,columnspan=6,sticky='w')
        self.buy_failure_fixture=tk.BooleanVar(value=False);self.buy_failure_json=tk.StringVar(value='{}')
        ttk.Checkbutton(self.buy_failure_controls,text='BUY başarısızlık gözlemlerini bağla (yeni denemede)',variable=self.buy_failure_fixture).pack(side='left')
        ttk.Entry(self.buy_failure_controls,textvariable=self.buy_failure_json,width=72).pack(side='left',padx=4)
        self.sell_coin_controls=ttk.Frame(settings)
        self.sell_coin_controls.grid(row=25,column=0,columnspan=6,sticky='w')
        self.sell_coin_current=tk.StringVar(value='');self.sell_coin_return=tk.BooleanVar(value=False)
        ttk.Label(self.sell_coin_controls,text='Panel coin alarmı için güncel coin örneği (boş: bilinmiyor)').pack(side='left')
        ttk.Entry(self.sell_coin_controls,textvariable=self.sell_coin_current,width=12).pack(side='left',padx=4)
        ttk.Checkbutton(self.sell_coin_controls,text='Alarm işlemi normal döndü (örnek)',variable=self.sell_coin_return).pack(side='left')
        self.enchant_zone=tk.StringVar(value='Moradon')
        self.enchant_zone_label=ttk.Label(settings,text='Deneme bölgesi')
        self.enchant_zone_label.grid(row=5,column=0,sticky='w')
        self.enchant_zone_choice=ttk.Combobox(settings,textvariable=self.enchant_zone,
            values=('Moradon','Luferson','EMC','Karus Eslant','Human Eslant'),state='readonly')
        self.enchant_zone_choice.grid(row=5,column=1,columnspan=3,sticky='w')
        self.family_controls=ttk.Frame(settings)
        self.family_controls.grid(row=6,column=0,columnspan=6,sticky='w')
        self.family_job=tk.StringVar(value='mage')
        self.family_runtime=tk.StringVar(value='Panel adayı')
        self.family_normal_guard=tk.StringVar(value='0')
        for text,var,choices in (('Deneme sınıfı',self.family_job,('mage','rogue','priest','warrior','kurian')),
            ('Sentetik mode BYTE',self.family_runtime,('Panel adayı','0','1','255')),
            ('Normal helper sonucu',self.family_normal_guard,('0','6','Bilinmiyor'))):
            ttk.Label(self.family_controls,text=text).pack(side='left',padx=4)
            ttk.Combobox(self.family_controls,textvariable=var,values=choices,state='readonly',width=13).pack(side='left')
        self.target_controls=ttk.Frame(settings)
        self.target_controls.grid(row=7,column=0,columnspan=6,sticky='w')
        self.target_pool=tk.StringVar(value='Panel')
        ttk.Label(self.target_controls,text='Havuz seçici: panel veya sentetik override (0:ikisi,1:A atla,2:B atla)').pack(side='left')
        ttk.Combobox(self.target_controls,textvariable=self.target_pool,values=('Panel','0','1','2'),state='readonly',width=8).pack(side='left',padx=5)
        self.loot_name_controls=ttk.Frame(settings)
        self.loot_name_controls.grid(row=8,column=0,columnspan=6,sticky='w')
        self.loot_name=tk.StringVar(value='Fork')
        ttk.Label(self.loot_name_controls,text='Deneme isim metni (sentetik)').pack(side='left')
        ttk.Entry(self.loot_name_controls,textvariable=self.loot_name,width=30).pack(side='left',padx=5)
        self.loot_codepage=tk.StringVar(value='1254')
        ttk.Label(self.loot_name_controls,text='Deneme kod sayfası').pack(side='left')
        ttk.Combobox(self.loot_name_controls,textvariable=self.loot_codepage,values=('1254','65001'),state='readonly',width=8).pack(side='left')
        self.loot_source_fixture=tk.BooleanVar(value=False)
        ttk.Checkbutton(self.loot_name_controls,text='Ana Loot için sentetik producer',variable=self.loot_source_fixture).pack(side='left',padx=5)
        self.mining_controls=ttk.Frame(settings)
        self.mining_controls.grid(row=9,column=0,columnspan=6,sticky='w')
        self.mining_fixture=tk.BooleanVar(value=False)
        self.mining_ws_zero=tk.BooleanVar(value=True);self.mining_request_zero=tk.BooleanVar(value=True)
        for title,var in (('Sentetik maden helper örneği',self.mining_fixture),
            ('İlk helper sonucu 0',self.mining_ws_zero),('İkinci helper sonucu 0',self.mining_request_zero)):
            ttk.Checkbutton(self.mining_controls,text=title,variable=var).pack(side='left',padx=4)
        self.mining_name_controls=ttk.Frame(settings)
        self.mining_name_controls.grid(row=10,column=0,columnspan=6,sticky='w')
        self.mining_name_fixture=tk.BooleanVar(value=False)
        self.mining_name_kind=tk.StringVar(value='Ore')
        ttk.Checkbutton(self.mining_name_controls,text='Sentetik taze slot adı ve yerel kuyruk (bağlantı kapısı=1)',
            variable=self.mining_name_fixture).pack(side='left',padx=4)
        ttk.Combobox(self.mining_name_controls,textvariable=self.mining_name_kind,
            values=('Ore','Gold','Boş yuva','Diğer'),state='readonly',width=12).pack(side='left')
        self.mining_scheduler_controls=ttk.Frame(settings)
        self.mining_scheduler_controls.grid(row=11,column=0,columnspan=6,sticky='w')
        self.mining_scheduler_fixture=tk.BooleanVar(value=False)
        self.mining_dead=tk.BooleanVar(value=False)
        ttk.Checkbutton(self.mining_scheduler_controls,text='Sentetik üst maden döngüsü',
            variable=self.mining_scheduler_fixture).pack(side='left',padx=4)
        ttk.Checkbutton(self.mining_scheduler_controls,text='Ölüm kapısı örneği',
            variable=self.mining_dead).pack(side='left',padx=4)
        self.mining_speed_controls=ttk.Frame(settings)
        self.mining_speed_controls.grid(row=12,column=0,columnspan=6,sticky='w')
        self.mining_speed_fixture=tk.BooleanVar(value=False)
        self.mining_speed_success=tk.BooleanVar(value=True)
        self.mining_speed_family=tk.StringVar(value='Rogue')
        ttk.Checkbutton(self.mining_speed_controls,text='Sentetik hız becerisi (istatistik100, actor1)',
            variable=self.mining_speed_fixture).pack(side='left',padx=4)
        ttk.Combobox(self.mining_speed_controls,textvariable=self.mining_speed_family,
            values=('Rogue','Warrior','Diğer'),state='readonly',width=10).pack(side='left')
        ttk.Checkbutton(self.mining_speed_controls,text='Swift çağrısı başarılı örneği',
            variable=self.mining_speed_success).pack(side='left',padx=4)
        self.mining_callback_fixture=tk.BooleanVar(value=False)
        ttk.Checkbutton(self.mining_speed_controls,text='Callback kilit çözme örneği',
            variable=self.mining_callback_fixture).pack(side='left',padx=4)
        self.mining_maintenance_controls=ttk.Frame(settings)
        self.mining_maintenance_controls.grid(row=13,column=0,columnspan=6,sticky='w')
        self.mining_maintenance_active=tk.BooleanVar(value=False)
        self.mining_maintenance_fixture=tk.BooleanVar(value=False)
        self.mining_maintenance_case=tk.StringVar(value='Boş')
        ttk.Checkbutton(self.mining_maintenance_controls,text='Bakım döngüsü etkin örneği',variable=self.mining_maintenance_active).pack(side='left',padx=4)
        ttk.Checkbutton(self.mining_maintenance_controls,text='Sentetik bakım verisi',variable=self.mining_maintenance_fixture).pack(side='left',padx=4)
        ttk.Combobox(self.mining_maintenance_controls,textvariable=self.mining_maintenance_case,
            values=('Boş','Kazma','Hammer','Hammer yok','Dolu','Onarım EMC','Onarım Luferson','Onarım Moradon'),state='readonly',width=18).pack(side='left')
        self.mining_post_controls=ttk.Frame(settings)
        self.mining_post_controls.grid(row=14,column=0,columnspan=6,sticky='w')
        self.mining_post_route=tk.BooleanVar(value=True)
        self.mining_post_lock=tk.StringVar(value='Bilinmiyor')
        ttk.Checkbutton(self.mining_post_controls,text='Bakım sonrası rota açık örneği',variable=self.mining_post_route).pack(side='left',padx=4)
        ttk.Label(self.mining_post_controls,text='Bakım sonrası kilit BYTE örneği').pack(side='left')
        ttk.Combobox(self.mining_post_controls,textvariable=self.mining_post_lock,values=('Bilinmiyor','0','1'),state='readonly',width=12).pack(side='left',padx=4)
        self.mining_effect_controls=ttk.Frame(settings)
        self.mining_effect_controls.grid(row=15,column=0,columnspan=6,sticky='w')
        self.mining_effect_fixture=tk.BooleanVar(value=False)
        self.mining_effect_candidates=tk.StringVar(value='Yok')
        self.mining_effect_region=tk.StringVar(value='Moradon')
        ttk.Checkbutton(self.mining_effect_controls,text='Sentetik başlatma/dönüş ve varsayılan rota',variable=self.mining_effect_fixture).pack(side='left',padx=4)
        ttk.Combobox(self.mining_effect_controls,textvariable=self.mining_effect_candidates,values=('Yok','Satış','Banka','İkisi'),state='readonly',width=10).pack(side='left',padx=4)
        ttk.Combobox(self.mining_effect_controls,textvariable=self.mining_effect_region,values=('EMC','EMCR','LFC','LFCR','Moradon'),state='readonly',width=12).pack(side='left',padx=4)
        self.control_guard_controls=ttk.Frame(settings)
        self.control_guard_controls.grid(row=16,column=0,columnspan=6,sticky='w')
        self.control_guard_data=tk.BooleanVar(value=False)
        self.control_guard_stop_return=tk.BooleanVar(value=False)
        self.control_guard_town_return=tk.BooleanVar(value=False)
        for title,var in (('Örnek NP/coin/level gözlemi',self.control_guard_data),
                          ('Örnek stop helper normal döndü',self.control_guard_stop_return),
                          ('Örnek Town helper normal döndü',self.control_guard_town_return)):
            ttk.Checkbutton(self.control_guard_controls,text=title,variable=var).grid(row=0,column=len(self.control_guard_controls.winfo_children()),sticky='w')
        ttk.Label(self.control_guard_controls,text='Panel seçimi NP→coin→level girişini kullanır;devam ayrıca açılır. Gerçek stop/Town/alarm veya süreç kapatma yapılmaz.',wraplength=950).grid(row=1,column=0,columnspan=4,sticky='w')
        self.control_follow_enabled=tk.BooleanVar(value=False)
        self.control_follow_alarm_return=tk.BooleanVar(value=False)
        self.control_follow_mode=tk.StringVar(value='Bilinmiyor')
        self.control_follow_hour=tk.StringVar();self.control_follow_minute=tk.StringVar();self.control_follow_handle=tk.StringVar()
        self.control_follow_counts=tk.StringVar();self.control_follow_matches=tk.StringVar(value='{}')
        ttk.Checkbutton(self.control_guard_controls,text='Saat/party devamını modelle',variable=self.control_follow_enabled).grid(row=2,column=0,sticky='w')
        ttk.Combobox(self.control_guard_controls,textvariable=self.control_follow_mode,values=('Bilinmiyor','0','1','2','3'),state='readonly',width=12).grid(row=2,column=1,sticky='w')
        ttk.Checkbutton(self.control_guard_controls,text='Örnek alarm helper normal döndü',variable=self.control_follow_alarm_return).grid(row=2,column=2,columnspan=2,sticky='w')
        time_controls=ttk.Frame(self.control_guard_controls);time_controls.grid(row=3,column=0,columnspan=4,sticky='w')
        for label,var in (('Örnek saat',self.control_follow_hour),('Dakika',self.control_follow_minute),('Örnek process handle',self.control_follow_handle)):
            ttk.Label(time_controls,text=label).pack(side='left',padx=4)
            ttk.Entry(time_controls,textvariable=var,width=12).pack(side='left')
        ttk.Label(self.control_guard_controls,text='Her count sorgusu için sırayla DWORD (virgülle):').grid(row=4,column=0,sticky='w')
        ttk.Entry(self.control_guard_controls,textvariable=self.control_follow_counts,width=24).grid(row=4,column=1,sticky='w')
        ttk.Label(self.control_guard_controls,text='Priest karşılaştırmaları JSON:').grid(row=4,column=2,sticky='w')
        ttk.Entry(self.control_guard_controls,textvariable=self.control_follow_matches,width=24).grid(row=4,column=3,sticky='w')
        self.control_frame_enabled=tk.BooleanVar(value=False)
        self.control_frame_json=tk.StringVar(value='{}')
        ttk.Checkbutton(self.control_guard_controls,text='Birleşik kontrol / yardım / alarm modeli',variable=self.control_frame_enabled).grid(row=5,column=0,columnspan=2,sticky='w')
        ttk.Label(self.control_guard_controls,text='Kaynak gözlem JSON (başlangıç state yalnız sıfırlamada alınır):').grid(row=5,column=2,columnspan=2,sticky='w')
        ttk.Entry(self.control_guard_controls,textvariable=self.control_frame_json,width=110).grid(row=6,column=0,columnspan=4,sticky='we')
        self.mining_control_controls=ttk.Frame(settings)
        self.mining_control_controls.grid(row=17,column=0,columnspan=6,sticky='w')
        self.mining_control_enabled=tk.BooleanVar(value=False)
        self.mining_control_guard_json=tk.StringVar(value='{}')
        self.mining_control_timer_lock=tk.StringVar()
        self.mining_control_post_lock=tk.StringVar()
        self.mining_control_segment_return=tk.BooleanVar(value=False)
        self.mining_control_post_mode=tk.StringVar()
        ttk.Checkbutton(self.mining_control_controls,text='Callback içinde panel kontrol modelini kullan',variable=self.mining_control_enabled).grid(row=0,column=0,columnspan=2,sticky='w')
        for row,title,var in (
            (1,'Kontrol giriş gözlemi JSON',self.mining_control_guard_json),
            (2,'Kontrol sonrası kilit JSON',self.mining_control_timer_lock),
            (3,'Ara bölüm sonrası kilit JSON',self.mining_control_post_lock)):
            ttk.Label(self.mining_control_controls,text=title).grid(row=row,column=0,sticky='w')
            ttk.Entry(self.mining_control_controls,textvariable=var,width=80).grid(row=row,column=1,sticky='we')
        ttk.Checkbutton(self.mining_control_controls,text='Örnek ara bölüm normal döndü',variable=self.mining_control_segment_return).grid(row=4,column=0,sticky='w')
        ttk.Entry(self.mining_control_controls,textvariable=self.mining_control_post_mode,width=12).grid(row=4,column=1,sticky='w')
        ttk.Label(self.mining_control_controls,text='Yanındaki değer ara bölüm sonrası mode DWORD örneğidir. Boş kilit/mode bilinmeyendir. Saat/party/yardım/alarm gözlemleri yukarıdaki kontrol alanlarından alınır.',wraplength=950).grid(row=5,column=0,columnspan=2,sticky='w')
        self.mining_interlude_enabled=tk.BooleanVar(value=False)
        self.mining_interlude_json=tk.StringVar(value='{}')
        ttk.Checkbutton(self.mining_control_controls,text='Ara bölümün kaynak modelini kullan (kontrol modelini de açar)',variable=self.mining_interlude_enabled).grid(row=6,column=0,columnspan=2,sticky='w')
        ttk.Label(self.mining_control_controls,text='Ara bölüm gözlem JSON; clock/helper sonuçları ayrı, başlangıç state bir kez alınır:').grid(row=7,column=0,columnspan=2,sticky='w')
        ttk.Entry(self.mining_control_controls,textvariable=self.mining_interlude_json,width=110).grid(row=8,column=0,columnspan=2,sticky='we')
        buttons = ttk.Frame(frame, padding=8)
        buttons.pack(fill='x')
        ttk.Button(buttons, text='Denemeyi sıfırla', command=self.reset).pack(side='left')
        ttk.Button(buttons, text='+1000 ms ilerlet', command=self.tick).pack(side='left', padx=5)
        ttk.Button(buttons, text='+60000 ms ilerlet', command=lambda: self.tick(60000)).pack(side='left')
        self.output = tk.Text(frame, height=20, wrap='word')
        self.output.pack(fill='both', expand=True, padx=8, pady=8)
        self.reset()

    def numbers(self):
        return {key: int(variable.get()) for key, variable in self.inputs.items()}

    def control_follow_observation(self):
        def optional(variable):
            text=variable.get().strip()
            return None if not text else int(text)
        text=self.control_follow_counts.get().strip()
        counts=tuple(None if not part.strip() else int(part.strip()) for part in text.split(',')) if text else ()
        comparisons=json.loads(self.control_follow_matches.get())
        if not isinstance(comparisons,dict):raise ValueError('İndeksli Priest karşılaştırma JSON nesnesi gerekli')
        matches={int(key):value for key,value in comparisons.items()}
        mode=self.control_follow_mode.get()
        return ControlContinuationObservation(optional(self.control_follow_hour),optional(self.control_follow_minute),
            None if mode=='Bilinmiyor' else int(mode),optional(self.control_follow_handle),counts,matches,
            True if self.control_guard_stop_return.get() else None,
            True if self.control_guard_town_return.get() else None,
            True if self.control_follow_alarm_return.get() else None)

    def mining_control_inputs(self):
        if not self.use_class_panel.get() or self.configuration_reader is None:
            raise ValueError('Callback kontrol bağı için panel kaynağı seçilmeli')
        panel=self.configuration_reader()[0]
        entry_config=compile_control_guards(panel)
        entry_data=json.loads(self.mining_control_guard_json.get())
        if not isinstance(entry_data,dict):raise ValueError('Kontrol giriş gözlem nesnesi gerekli')
        entry_observation=ControlGuardObservation(**entry_data)
        entry=plan_control_guards(entry_config,entry_observation)
        follow_config=follow_observation=help_config=alarm_config=help_observation=alarm_observation=None
        if entry.complete and not entry.source_return_planned:
            follow_config=compile_control_continuation(panel)
            follow_observation=self.control_follow_observation()
            chain=replay_control_chain(entry_config,entry_observation,follow_config,follow_observation)
            follow=chain.continuation
            if (chain.complete and follow is not None
                    and not follow.source_return_planned and not follow.termination_call_planned):
                sample=parse_control_sample(self.control_frame_json.get())
                if not self.mining_control_seeded:
                    self.mining_control_state=sample.initial_state or ControlFrameState(PartyHelpState(),LootActivityState())
                    self.mining_control_seeded=True
                help_config=compile_party_help(panel,observed_ansi=sample.observed_ansi)
                alarm_config=compile_control_alarms(panel)
                help_observation=sample.party_help;alarm_observation=sample.alarms
        return ControlCallbackInputs(
            ControlFrameConfiguration(entry_config,follow_config,help_config,alarm_config),
            ControlFrameObservation(entry_observation,follow_observation,help_observation,alarm_observation))

    def mining_lock_observation(self,variable):
        text=variable.get().strip()
        if not text:return None
        data=json.loads(text)
        if not isinstance(data,dict) or set(data)!={'byte','duration_ms','started_ms'}:
            raise ValueError('Kilit JSON byte/duration_ms/started_ms alanlarını içermeli')
        return AttackLockState(**data)

    def mining_effect_observation(self,tick):
        if not self.mining_effect_fixture.get():return None
        candidates=self.mining_effect_candidates.get();region=self.mining_effect_region.get()
        if candidates not in ('Yok','Satış','Banka','İkisi') or region not in ('EMC','EMCR','LFC','LFCR','Moradon'):
            raise ValueError('Geçerli başlatma/dönüş örneği gerekli')
        def slots(enabled):
            return {i:MiningCandidateSlot(0,int(enabled)) if i==14 else MiningCandidateSlot(0xffffffff) for i in range(14,42)}
        returning=dict(region_1_equal=int(region in ('EMC','EMCR')),region_2_equal=int(region in ('LFC','LFCR')),
            region_3_equal=int(region=='Moradon'),distance_first_ftol=20 if region.endswith('R') else 10,
            distance_second_ftol=10 if region.endswith('R') else 20,distance_fpu_ah=0x40,
            use_constructor_defaults=1,**{'returned:004eb9f4':True,'returned:004ebca0':True})
        return MiningEffectObservation(
            start=dict(gate_4631a8=0,name_first_equal=1,name_second_equal=0,free_slot_463a8c=0,
                fresh_slot6_name=b'Mattock',start_tick=tick,**{'returned:0046526c':True}),
            returning=returning,sell_slots=slots(candidates in ('Satış','İkisi')),bank_slots=slots(candidates in ('Banka','İkisi')))

    def write(self, text):
        self.output.configure(state='normal')
        self.output.insert('end', text + '\n')
        self.output.see('end')
        self.output.configure(state='disabled')

    def panel_route_sample(self,kind,*,ansi=False):
        """Reached own panel Text; None means no provider, never inferred empty."""
        if kind not in ROUTE_GLOBALS:raise ValueError('Known route filename producer required')
        if self.route_configuration_reader is None:return None
        sample=self.route_configuration_reader()
        if type(sample) is not tuple or len(sample)!=2 or not isinstance(sample[0],Mapping):
            raise ValueError('Own route Text snapshot and explicit codepage required')
        texts,codepage=sample
        if ansi:return compile_panel_route_name(kind,texts,WindowsNameCodec(codepage))[ROUTE_GLOBALS[kind]]
        text=texts.get(ROUTE_COMBO_PATHS[kind])
        if type(text) is not str:raise ValueError('Seçilen rota için panel Text gözlemi gerekli')
        return text

    def sell_failure_observation(self,text):
        self.sell_bank_handoff_last=None
        o=parse_sell_failure(text)
        def route_inputs():
            if self.bank_route_reader is None:return None
            inputs=self.bank_route_reader()
            if inputs is None:return None
            return replace(inputs,**parse_bank_error_returns(text))
        return replace(o,route_inputs_factory=route_inputs)

    def buy_failure_observation(self,text):
        self.buy_bank_handoff_last=None
        o=parse_buy_failure(text)
        def route_inputs():
            if self.buy_bank_route_reader is None:return None
            inputs=self.buy_bank_route_reader()
            if inputs is None:return None
            return replace(inputs,**parse_bank_error_returns(text))
        return replace(o,route_inputs_factory=route_inputs)

    def reset(self):
        self.dc_trial.reset()
        self.jail_selection_trial.reset()
        self.protection_trial.reset()
        self.disconnect_trial.reset()
        self.genie_settings_trial.reset()
        self.control_settings_trial.reset()
        self.item_break_settings_trial.reset()
        self.tp_trial.reset()
        self.transformation_trial.reset()
        self.event_trial.reset()
        self.allocation_trial.reset()
        self.achievement_trial.reset()
        self.ms_trial.reset()
        self.follow_trial.reset()
        self.party_trial.reset()
        self.chat_party_trial.reset()
        self.chat_commands_trial.reset()
        self.chat_skills_trial.reset()
        self.buy_merchant_compiled=None
        self.sell_merchant_compiled=None
        self.sell_preparation_enabled=False
        self.sell_cost_enabled=False
        self.sell_wait_enabled=False
        self.sell_failure_enabled=False;self.sell_bank_handoff_last=None
        self.buy_failure_enabled=False;self.buy_bank_handoff_last=None
        self.merchant_reply_state=None;self.merchant_reply_last=None;self.merchant_reply_enabled=False
        self.upgrade_compiled=None;self.upgrade=None
        self.upgrade_start_plan=None
        self.armor_start_plan=None
        self.upgrade_execution=None;self.upgrade_execution_last=None
        self.control_guard_last=None;self.control_guard_compiled=None
        self.control_chain_last=None;self.control_continuation_last=None
        self.control_frame_last=None;self.control_frame_seeded=False
        self.control_frame_state=ControlFrameState(PartyHelpState(),LootActivityState())
        self.target_resolver=None
        self.target_previous_mode=None
        self.family_runner=FamilyRunner()
        self.provoke_state=ProvokeState()
        self.action_queue = QueueState()
        self.action_queue_initialized = False
        self.action_queue_send_plans = 0
        self.action_queue_drops = 0
        self.now_ms = 0
        self.last_crash_ms = 0
        self.last_self_ms = 0
        self.last_minor_ms = 0
        self.alternate_state = AlternateState()
        self.rogue_chain_state = RogueChainState()
        self.attack_lock_state = AttackLockState()
        self.kurian_cycle_state = KurianCycleState()
        self.loot_previous_mode = None
        self.mining_previous_start=None
        self.mining_previous_speed=None
        self.mining_ore_state=OreSlotState()
        self.mining_name_request_last=None
        self.mining_queue_last=None
        self.mining_request_queue=QueueState()
        self.mining_local_complete=False
        self.mining_frame_last=None
        self.mining_callback_last=None
        self.mining_control_state=ControlFrameState(PartyHelpState(),LootActivityState())
        self.mining_control_seeded=False
        self.mining_interlude_state=CallbackInterludeState()
        self.mining_interlude_seeded=False
        self.mining_pipeline_last=None
        self.mining_last=None
        self.mining_scheduler_times={0x553df0:0,0x553df8:0,0x553e00:0}
        self.mining_speed_values={0x553de8:0,0x561f7e:0,0x561f80:0,0x561f84:0}
        self.mining_maintenance_values={0x553de0:0,0x5690d0:0,0x5690b8:0}
        self.mining_repair_route_last=None
        self.loot_list_state = LootListState()
        self.loot_cache_state = LootCacheState()
        self.loot_pending = None
        self.loot_bundle_ids = {}
        self.loot_packet_last = None
        self.priest_attack_timers = {r.timer_offset: 0 for r in PRIEST_ATTACK_ROWS
                                    if r.timer_offset is not None}
        self.warrior_attack_timers = {r.timer_read_offset: 0 for r in WARRIOR_ROWS
                                     if r.timer_read_offset is not None}
        self.mage_attack_timers = {r.timer_offset: 0 for r in MAGE_ATTACK_ROWS
                                  if r.timer_offset is not None}
        self.rogue_attack_timers = {r.timer_offset: 0 for r in MELEE_ROWS + BOW_ROWS + SPECIAL_ROWS
                                   if r.timer_offset is not None}
        self.rogue_attack_timers.update({0x2c: 0, 0x30: 0, 0x34: 0})
        self.initialized = False
        titles=dict(self.input_titles)
        ready_title='Deneme işlem kapısı açık / loot kutusu açık'
        if self.case.get()=='Armor Alımı':
            titles.update(item_id='İlk Armor combo indeksi (örnek)',price='Deneme NPC DWORD',threshold='İkinci combo indeksi (örnek)',
                          hp='NPC X __ftol DWORD',hp_max='NPC Y __ftol DWORD')
            ready_title='Helper ve temizleme normal döndü (sentetik)'
        elif self.case.get()=='NPC Onarım':
            titles.update(hp='Dayanıklılık',hp_max='Maksimum dayanıklılık')
            ready_title='Onarım yanıtı alındı (sentetik)'
        elif self.case.get()=='NPC Enchant':
            titles.update(hp='Seviye',item_id='Rota seçeneği (0–4)')
            ready_title='NPC hedefte (sentetik)'
        elif self.case.get()=='NPC Satış':
            titles.update(hp='Örnek dayanıklılık',quantity='Eşya stok adedi')
            ready_title='Satış için seçili (sentetik)'
        elif self.case.get()=='NPC Satın Alma':
            titles.update(hp='Mevcut ağırlık',hp_max='Ağırlık sınırı',mp='Mevcut coin',
                          threshold='Mevcut eşya adedi',quantity='İstenen toplam adet',
                          price='Birim coin',distance='Birim ağırlık')
            ready_title='Satın alma satırı seçili (sentetik)'
        elif self.case.get()=='Eylem Kuyruğu':
            ready_title='Bağlantı kapısı açık (sentetik)'
        elif self.case.get()=='Tedarik':
            titles.update(hp='Deneme mevcut ağırlık',hp_max='Deneme azami ağırlık',
                item_id='Deneme envanter eşya ID',quantity='Deneme yığın adedi')
            ready_title='Ağırlık dalına erişildi (sentetik)'
        elif self.case.get()=='Kontrol':
            titles.update(item_id='Deneme NP DWORD',price='Deneme coin DWORD',hp='Deneme level DWORD')
        elif self.case.get()=='Maden':
            titles.update(quantity='Örnek ore sayısı (0–28)',distance='Örnek maden/NPC mesafesi',item_id='Örnek hedef ID')
            ready_title='Ad karşılaştırmaları eşleşir (sentetik)'
        elif self.case.get()=='Warrior Provoke':
            titles.update(wait='Provoke pencere (saniye)',quantity='Başlangıç beklemesi (saniye)',
                          price='Beceri beklemesi (saniye)')
            ready_title='Native helper nonzero döner (sentetik)'
        elif self.case.get()=='Sınıf Ailesi':
            ready_title='Dış aile kapısı açık (sentetik)'
        elif self.case.get()=='Hedef Seçimi':
            titles.update(item_id='A havuzu deneme hedef ID',distance='Deneme integer mesafe')
            ready_title='Aday visibility kapısı açık (sentetik)'
        elif self.case.get()=='Loot Filtre':
            titles.update(quantity='Ham kategori BYTE (0–255)',threshold='Ham upgrade DWORD',price='Ham NPC fiyat DWORD')
            ready_title='Metadata lookup nonzero (sentetik)'
        for name,label in self.input_labels.items():label.configure(text=titles[name])
        self.ready_control.configure(text=ready_title)
        for widget in (self.enchant_zone_label,self.enchant_zone_choice):
            if self.case.get()=='NPC Enchant':widget.grid()
            else:widget.grid_remove()
        if self.case.get()=='Takip':self.follow_controls.grid()
        else:self.follow_controls.grid_remove()
        if self.case.get()=='Monster Stone':self.ms_controls.grid()
        else:self.ms_controls.grid_remove()
        if self.case.get()=='Achieve MS':self.achievement_controls.grid()
        else:self.achievement_controls.grid_remove()
        if self.case.get()=='Koruma Ayarları':self.protection_controls.grid()
        else:self.protection_controls.grid_remove()
        if self.case.get()=='DC / Relog Ayarları':self.disconnect_controls.grid()
        else:self.disconnect_controls.grid_remove()
        if self.case.get()=='Genie Ayarları':self.genie_settings_controls.grid()
        else:self.genie_settings_controls.grid_remove()
        if self.case.get()=='Kontrol Ayarları':self.control_settings_controls.grid()
        else:self.control_settings_controls.grid_remove()
        if self.case.get()=='Item Kırma Ayarları':self.item_break_settings_controls.grid()
        else:self.item_break_settings_controls.grid_remove()
        if self.case.get()=='DC–Hapis Listesi':self.jail_selection_controls.grid()
        else:self.jail_selection_controls.grid_remove()
        if self.case.get()=='DC Koruma':self.dc_controls.grid()
        else:self.dc_controls.grid_remove()
        if self.case.get()=='TP Koruma':self.tp_controls.grid()
        else:self.tp_controls.grid_remove()
        if self.case.get()=='Transformation':self.transformation_controls.grid()
        else:self.transformation_controls.grid_remove()
        if self.case.get()=='Etkinlik Katılımı':self.event_controls.grid()
        else:self.event_controls.grid_remove()
        if self.case.get()=='Stat/Skill Ayarları':self.allocation_controls.grid()
        else:self.allocation_controls.grid_remove()
        if self.case.get()=='Party Daveti':self.party_controls.grid()
        else:self.party_controls.grid_remove()
        if self.case.get()=='Chat/PM Party':self.chat_party_controls.grid()
        else:self.chat_party_controls.grid_remove()
        if self.case.get()=='Chat Komutları':self.chat_commands_controls.grid()
        else:self.chat_commands_controls.grid_remove()
        if self.case.get()=='Chat Yetenek İsteği':self.chat_skills_controls.grid()
        else:self.chat_skills_controls.grid_remove()
        if self.case.get()=='Sınıf Ailesi':self.family_controls.grid()
        else:self.family_controls.grid_remove()
        if self.case.get()=='Hedef Seçimi':self.target_controls.grid()
        else:self.target_controls.grid_remove()
        if self.case.get() in ('Upgrade','Armor Alımı'):self.upgrade_scroll_controls.grid()
        else:self.upgrade_scroll_controls.grid_remove()
        self.upgrade_slot_label.configure(text='Boş yuva (0–27; -1:bulunamadı)' if self.case.get()=='Armor Alımı'
                                           else 'Scroll çanta yuvası (0–27; -1=yok)')
        if self.case.get()=='Armor Alımı':self.armor_extra.grid()
        else:self.armor_extra.grid_remove()
        if self.case.get()=='Buy Merchant':
            self.buy_merchant_controls.grid();self.buy_reply_controls.grid()
            self.buy_failure_controls.grid()
        else:
            self.buy_merchant_controls.grid_remove();self.buy_reply_controls.grid_remove()
            self.buy_failure_controls.grid_remove()
        if self.case.get()=='Sell Merchant':
            self.sell_preparation_controls.grid();self.sell_cost_controls.grid();self.sell_wait_controls.grid();self.sell_coin_controls.grid()
            self.sell_failure_controls.grid()
        else:
            self.sell_preparation_controls.grid_remove();self.sell_cost_controls.grid_remove();self.sell_wait_controls.grid_remove();self.sell_coin_controls.grid_remove()
            self.sell_failure_controls.grid_remove()
        if self.case.get() in ('Kontrol','Maden'):self.control_guard_controls.grid()
        else:self.control_guard_controls.grid_remove()
        if self.case.get() in ('Loot','Loot Filtre'):self.loot_name_controls.grid()
        else:self.loot_name_controls.grid_remove()
        for widget in (self.mining_controls,self.mining_name_controls,self.mining_scheduler_controls,self.mining_speed_controls,self.mining_maintenance_controls,self.mining_post_controls,self.mining_effect_controls,self.mining_control_controls):
            if self.case.get()=='Maden':widget.grid()
            else:widget.grid_remove()
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.configure(state='disabled')
        self.write(self.case.get() + ': yeni yerel deneme. Canlı oyun sonucu değildir.')
        if self.case.get()=='Buy Merchant':
            self.write('Hazırlık/çanta örneği varsayılan kapalıdır. Açıldığında liste temizliği, string/append dönüşleri ve taze 28 yuva ID sonucu sentetiktir. Panel seçeneği açıkken alış listesinin tüm satırları; kapalıyken tek deneme satırı kaynak sırayla çevrilir. Sayı dönüşümü decimal alt küme, fiyat ANSI örneği ASCII ile sınırlıdır. Eşik yeni denemede alınır; eşya satın alınmaz.')
        if self.case.get()=='Kontrol':
            self.write('Panel seçimi NP/coin/level bayrak ve eşiklerini kullanır. Gözlemler/helper dönüşleri ve saat/party devamı ayrı/default-off örneklerdir. Devamda mode,saat,dakika,handle ve her count sorgusu açık gözlemdir;boşlar bilinmeyendir. Sonraki buff/loot/item alarm dalları kapsam dışıdır. Gerçek oyun okuma/stop/Town/alarm/süreç kapatma yapılmaz.')
        if self.case.get()=='Maden':
            self.write('Üst döngü, helper ve taze isim örnekleri ayrı ve varsayılan kapalıdır. Üst örnekte aktif kapısı1, ölüm zamanı1ms, pazar/otomatik maden kapıları0; helper normal dönüşleri varsayılır. Ölümden sonra gönderim/dirilme onayı üretilmez. İsim/kuyruk örneği kendi sabit adresleri ve bağlantı kapısı1 kullanır. Gerçek oyun gözlemi değildir.')
            self.write('Hız örneği ayrıca açılır ve panel hız seçimini kullanır. Rogue için kendi class101/istatistik100/actor1/boş buff değerleri vardır; Warrior kaynak yolundaki başlatılmamış stack kimlikleri doldurulmaz. Callback örneği kapalıyken Swift kilidi kendi state üzerinde kalır. Sıfırla kendi kilidini temizler.')
            self.write('Callback kilit çözme örneği ayrıca açılabilir: readiness1/connection1,VIP kendi bakım stateinden,Inn/worker0,normal helper dönüşleri,mode2 ve ara bölümün lock değiştirmediği kapalı dünya örneğidir. Gerçek callback/queue/ağ etkileri yürütülmez;başka modlar burada modellenmez.')
            self.write('Bakım örneği gerçek veri değildir: sorgu/helper sonuçları senaryodan,karar bayrakları panelden alınır. Bakım sonrası rota/kilit bağımsız örnek gözlemlerdir. Onarım rotaları açık constructor-default örneğidir;canlı vector aynı varsayılmaz. NPC/stop/depo etkileri ve ACK yürütülmez;depo aktif örneği sıfırlamaya kadar kalabilir.')
            self.write('Başlatma/dönüş örneği ayrıca açılır:kazma adı/boş slot kendi örneği,adaylar ayrı28slot sınıflandırma snapshotlarıdır. Bilinen faz/index/başlangıç yazımları yalnız kendi statee uygulanır. Dönüş tercihi panelden veadaylardan seçilir;rotalar constructor-default örneğidir. Ekipman/NPC/rota gönderimi veya ACK yürütülmez.')
        if self.case.get() == 'Priest Saldırı':
            self.write('Deneme: 16 aday seçili, raw statlar 100, menzil 8. MP ve mesafe girişleri kullanılır; kapı kapalıysa kilitlidir.')
        if self.case.get().endswith(' Alternatif'):
            self.write('Deneme: hazır ve aynı hedef; destek yardımcılarının yerel dönüşü false, sonraki kilit false. Gerçek oyun yanıtı değildir.')
        if self.case.get() in ('Warrior Saldırı', 'Mage Saldırı', 'Rogue Yakın',
                               'Rogue Yay', 'Rogue Özel', 'Rogue Çoklu'):
            self.write('Deneme: tüm adaylar seçili, statlar 100, menzil ayarı 8; MP ve mesafe girişten. Panel seçeneği işaretleri kaynak eşlemesinden alır. Canlı veri değildir.')
        if self.case.get() == 'Görev Alma':
            self.write('Deneme: örnek NPC ve b"deneme" scripti; gerçek görev kaydı değildir. Mesafe ve lookup sayısı girişten alınır. Kuyruk planları oyuna gönderilmez.')
        if self.case.get() == 'Rogue Alternatif Yay':
            self.write('Deneme: helper dönüşleri0, statlar100 sentetik. Yalnız seçim parametresi0; gönderim çağrılmaz. Panel seçeneği +10/+14/+18 mesafelerini ve W/S Combo kutularını kullanır; kapalıysa W/S1/0 örneği. Canlı gözlem değildir.')
        if self.case.get() == 'Rogue Combo Zinciri':
            self.write('Deneme: callback kilit süresi→alternatif baş→combo→yay seçicisi yerel zinciri; raw yol1, actor gate sıfır, destek dönüşleri false ve native dönüş1 sentetik. Panel seçeneği W/S Combo ve hedefe koş bayraklarını kullanır; kapalıysa1/0/0 örneği. Kilit BYTE/süreler korunur; başlangıç0/0/0, helper tamamlanmaları ve saatler sentetiktir. Çağrı/yazımlar yalnız plandır.')
        if self.case.get() in ('Kurian Saldırı','Kurian Özel','Kurian Döngü'):
            self.write('Deneme: panel sınıf listeleri/aktif menzil; döngüde R Atak ve W/S Combo panelden. Panel seçeneği kapalıysa tüm adaylar, menzil8 ve R açık/W/S kapalı örneği. Stat100, uygunluk helper false, gönderim helper true ve hazırlık DWORD0 sentetiktir. MP/mesafe girişten; işlem kapısı kilit gözlemidir. Çağrı/yazımlar yalnız plandır.')
        if self.case.get()=='Loot':
            self.write('Deneme: tek sentetik kutu/ilk yuvada girişteki eşya ID. Panel enable/mod/bekleme kullanılır. LIST için sentetik producer seçeneği isim baytı→codec→cache→mask zincirini besler; kapalıysa veri beklenir. Eksik geçiş aynı başlangıç snapshotıyla tutulur, yeni callback başlatılmaz. Denemeyi sıfırla yerel beklemeyi temizler. Gerçek kutu/oyun sonucu değildir.')
        if self.case.get()=='Loot Filtre':
            self.write('Deneme: aynı eşya ID ilk/son yuvada; lookup/metadata, adresler ve yakalanmış buffer sentetik. Açık kod sayfası1254/65001 ile yerel Windows dönüşümü kullanılır; bu oyun codepage doğrulaması değildir. Panel LIST ve TOPLA sütunu cache üretir. İsim metninden deneme ANSI bufferı kurulur; gerçek ID→bellek okuyucu yoktur. Sınıflandırılmış maske korunur; yeni deneme için sıfırla. Oyuna native çağrı yoktur.')
        if self.case.get() == 'Mage TP':
            self.write('Deneme: iki kişilik sentetik party, TP uygunluk kapısı ve raw stat 10. '
                       'Parti hedefinin yaş kapısı korunur; gerçek parti/stat okuması değildir.')
        if self.case.get() == 'Warrior Provoke':
            self.write('Deneme: caller önkoşulları, raw state0 ve stat100 sentetik. '
                       'Helper dönüşü kutudan; panel seçimi açıkken Provoke flag ve beklemeler panelden alınır. '
                       'Yerel helper sonucu sunucu onayı değildir.')
        if self.case.get()=='Sınıf Ailesi':
            self.write('Deneme: aile seçimi panel radio değerinden veya açık sentetik BYTE girdisinden. '
                       'Sınıf kullanıcı seçimi; durum/stat/hedef ve helper dönüşleri sentetiktir. '
                       'Normal ve Legal timer durumları ayrı tutulur. Gerçek runtime override ölçülmez.')
        if self.case.get()=='Hedef Seçimi':
            self.write('Deneme: seçim radio/mesafe/süre/liste/koş-merkez ayarları panelden. '
                       'İki sentetik A/B aday, visibility ve current ID0 kullanılır; havuzlar oyun nesne sınıfı sayılmaz. '
                       'İsim/ID ve otomatik resolver; manuel/Auto Z/başkana göre helper-yazım planları vardır. '
                       'Başkan dalında party/lookup/HP ve FCOM durumu da sentetiktir; hedef oyuna yazılmaz.')
        if self.case.get() == 'Eylem Kuyruğu':
            self.write('Deneme: ilk adımda örnek görevin üç kaydı eklenir; beklemeler 500/1000/1500 ms. '
                       'Sonraki adımlarda bağlantı kutusu gönderim planı veya gönderilmeden silinme yolunu seçer. '
                       'Helper dönüşü sentetiktir; sunucu onayı oluşmaz.')
        if self.case.get()=='NPC Onarım':
            self.write('Deneme: aynı NPC, örnek slotlarda aynı eşya ve dayanıklılık; cache seçimleri sentetiktir. Yanıt kutusu yalnız yerel beklemeyi etkiler. Gerçek eşya onarılmaz.')
        if self.case.get()=='NPC Enchant':
            self.write('Deneme: örnek NPC, seçilen bölge/seviye ve rota seçeneğiyle aşamalar ilerler. Enchant uygulanmaz; yalnız yerel işlem planı oluşur.')
        if self.case.get()=='NPC Satış':
            self.write('Deneme: örnek Sundries NPC, aynı eşya ile dolu örnek slotlar ve sentetik cache. Seçim kutusu kapalıysa eşyalar atlanır; 14 seçili eşya toplu işlem planı oluşturur. Gerçek eşya satılmaz.')
        if self.case.get()=='NPC Satın Alma':
            self.write('Deneme: örnek Sundries NPC ve tek satın alma satırı. Mevcut adet istenen toplamdan çıkarılır; ağırlık ve coin sınırları kullanılır. Gerçek eşya alınmaz.')

    def apply_merchant_reply(self):
        # Sequential phase4 fixture only. Never capture, send, or advance the clock.
        if (self.case.get()!='Buy Merchant' or not self.initialized or
                not self.merchant_reply_enabled or self.merchant.phase!=4):
            self.write('Yanıt örneği için seçeneği açıp yeni denemeyi aşama 4\'e ilerletin; oyun bağlantısı yoktur.')
            return
        try:
            payload=bytes.fromhex(self.buy_reply_hex.get())
            actor=int(self.buy_reply_actor.get(),0)
            plan=plan_merchant_reply(self.merchant_reply_state,payload,
                MerchantReplyObservation(scan_active_byte=0,local_actor_dword=actor,tick_dword=self.now_ms&0xffffffff))
            self.merchant_reply_last=plan
            if plan.complete:self.merchant_reply_state=plan.state
            self.write('Yalnız yerel yanıt örneği; sunucu onayı değildir: '+self.describe(plan))
        except ValueError as error:
            self.write('Yanıt örneği geçersiz: '+str(error))

    def buy_preparation_sample(self):
        return self.merchant_preparation_sample(BUY_LIST_PATH)

    def merchant_preparation_sample(self,list_path):
        if self.use_class_panel.get():
            if self.configuration_reader is None:raise ValueError('Alış listesi panel kaynağı bağlanmadı')
            entries=self.configuration_reader()[1].get(list_path)
            if type(entries) is not list:raise ValueError('Alış pazarı panel listesi gerekli')
        else:
            entries=[{'caption':str(row.item_id),'subitems':['Deneme eşyası',str(row.quantity),str(row.price)]}
                     for row in self.merchant.settings.rows]
        rows={}
        for index,row in enumerate(entries):
            if not isinstance(row,Mapping):raise ValueError('Alış listesi satır nesnesi gerekli')
            sub=row.get('subitems',[])
            if type(sub) is not list:raise ValueError('Alış alt sütunları gerekli')
            quantity=sub[1] if len(sub)>1 else None;price=sub[2] if len(sub)>2 else None
            ansi=price.encode('ascii') if type(price) is str and price.isascii() else None
            rows[index]=BuyPreparationRow(item_text=row.get('caption'),quantity_text=quantity,price_text=price,
                price_ansi=ansi,item_cleanup_returned=True,quantity_cleanup_returned=True,ansi_returned=True,
                price_ansi_cleanup_returned=True,price_unicode_cleanup_returned=True)
        count=len(rows)
        return BuyPreparationObservation(clear_returned=self.ready.get(),counts=(count,)*(count+1),rows=rows,
            sizes={index:index for index in rows},capacities={index:max(count,12) for index in rows},
            append_returns={index:True for index in rows},local_decimal=True)

    def panel_configuration(self, job):
        if self.configuration_reader is None:raise ValueError('Panel ayar kaynağı bağlanmadı')
        values, lists = self.configuration_reader()
        settings = compile_class_configuration(job, values, lists)
        if settings.ui_updates:
            if self.configuration_writer is None:
                raise ValueError('Sınıf arayüz etkisi için panel yazıcısı bağlı değil')
            self.configuration_writer(settings.ui_updates)
        if settings.unresolved:
            self.write('Panel eşlemesinde açık kalan alanlar: ' + '; '.join(settings.unresolved))
        return settings

    def attack_flags(self, job, rows):
        if self.use_class_panel.get():return self.panel_configuration(job).flags
        return {row.flag_offset: True for row in rows}

    def bot_combat_settings(self):
        if self.configuration_reader is None:raise ValueError('Panel ayar kaynağı bağlanmadı')
        values,_=self.configuration_reader()
        self.bot_combat=compile_bot_combat(values)
        return self.bot_combat

    def build_loot_name_fixture(self,values):
        """Owned buffer/addresses and explicit local codec, never game reads."""
        page=int(self.loot_codepage.get());codec=WindowsNameCodec(page)
        data,self.loot_fixture_used_default=codec.encode(self.loot_name.get())
        inline=len(data)<16
        captured=data+b'\0'*(255-len(data)) if inline else data
        pointer=int.from_bytes((data+b'\0'*4)[:4],'little') if inline else 0x9000
        self.loot_name_plan=plan_item_name(values['item_id'],ItemNameObservation(
            metadata_category=values['quantity'],storage_dword=len(data),pointer_dword=pointer,
            bad_read_result=0,captured=captured),provided_lookup=0x1000,provided_metadata=0x2000)
        if self.loot_name_plan.ansi_bytes is None:return None,False
        self.loot_name_conversion=convert_name_chain(self.loot_name_plan.ansi_bytes,page)
        return self.loot_name_conversion.compare_unicode,self.loot_name_conversion.preconversion_nonempty

    def upgrade_scroll_observation(self):
        relative=int(self.upgrade_scroll_slot.get())
        if not -1<=relative<=27:raise ValueError('Deneme scroll yuvası -1..27 olmalı')
        key=self.upgrade_compiled.scroll_text.encode('ascii')
        return UpgradeScrollObservation({slot:UpgradeScrollSample(key,
            key if slot==relative+14 and relative>=0 else b'owned nonmatching item')
            for slot in range(14,42)})

    def setup(self, values):
        case = self.case.get()
        if case == 'Upgrade':
            if self.use_class_panel.get():
                if self.configuration_reader is None:raise ValueError('Panel ayar kaynağı bağlanmadı')
                panel_values,panel_lists=self.configuration_reader()
                from pathlib import Path
                catalog=json.loads((Path(__file__).absolute().parent/'ui_model.json').read_text(encoding='utf-8'))
                self.upgrade_compiled=compile_upgrade_panel(panel_values,panel_lists,
                    scroll_text=selected_upgrade_scroll_text(panel_values,catalog),defer_rows=True)
                self.upgrade=upgrade_runner_from_panel(self.upgrade_compiled)
                rows=self.upgrade_compiled.raw_start_rows
                self.upgrade_start_plan=replay_upgrade_start(UpgradeStartState(),UpgradeStartObservation(1,
                    start_ui_returned=True,stop_ui_returned=True,vector_clear_returned=True,
                    scroll_lookup=self.upgrade_scroll_observation() if self.upgrade_scroll_fixture.get() else None,
                    scroll_cleanup_returned=True,counts=(len(rows),)*(len(rows)+1),
                    rows={i:UpgradeStartRow(int(row['checked']),caption=row.get('caption')) for i,row in enumerate(rows)},
                    append_returns={i:True for i in range(len(rows))},local_decimal=True))
                if not self.upgrade_start_plan.complete:
                    self.write('Upgrade başlangıcı gözlem bekliyor: '+self.upgrade_start_plan.missing)
                    return
                apply_upgrade_start(self.upgrade,self.upgrade_start_plan)
                self.upgrade.queue_stamp_qword=0 # Explicit owned fixture; source start does not write a clock.
                self.upgrade_execution=UpgradeExecution(self.upgrade)
                self.write('Upgrade: panel beklemesi milisaniye; yalnız işaretli ana sütunlar kuyruğa alındı. '
                           'İşlem kapısı, scroll envanter indeksi, başlangıç stamp0 ve helper dönüşü/taze tick sentetik; gerçek upgrade yapılmaz.')
            else:
                self.upgrade = UpgradeRunner(interval_ms=values['wait'] * 1000)
                self.upgrade.start([UpgradeRow(values['item_id'], True)])
        elif case=='Armor Alımı':
            if not self.upgrade_scroll_fixture.get():
                self.write('Armor: mode2/çanta örnek gözlemleri kapalı; başlangıç bekliyor.')
                return
            self.upgrade=UpgradeRunner(source_clock=True)
            if self.use_class_panel.get():
                if self.configuration_reader is None:raise ValueError('Panel ayar kaynağı bağlanmadı')
                panel_values,_=self.configuration_reader()
                first=second=panel_values.get(ARMOR_COMBO_PATH)
            else:first,second=values['item_id'],values['threshold']
            def source_dword(value):
                if value is None:return None
                if type(value) is not int or not -0x80000000<=value<=0xffffffff:
                    raise ValueError('Gözlenen signed32/rawDWORD örneği gerekli')
                return value&0xffffffff
            self.armor_start_plan=replay_armor_start(capture_armor_start_state(self.upgrade),ArmorStartObservation(
                filter_ready_returned=True,lookup_candidates=(NpcCandidate(7,values['price'],b'[Armor Merchant]'),),
                traversal_complete=True,npc_pointer_dword=0x7000,x_offset_dword=4,y_offset_dword=8,
                x_ftol_dword=source_dword(values['hp']),y_ftol_dword=source_dword(values['hp_max']),
                distance_ftol_dword=source_dword(values['distance']),first_combo_dword=source_dword(first),
                second_combo_dword=source_dword(second),bag_flag_byte=int(self.full.get()),
                message_returns={n:True for n in ('npc_missing','too_far','item_missing','bag_full')},
                message_cleanup_returns={n:True for n in ('npc_missing','too_far','item_missing','bag_full')}))
            if not self.armor_start_plan.complete:
                self.write('Armor başlangıcı gözlem bekliyor: '+self.armor_start_plan.missing)
                return
            apply_armor_start(self.upgrade,self.armor_start_plan)
            if not self.armor_start_plan.armed:
                self.write('Armor başlangıç planı: '+self.armor_start_plan.status)
                return
            self.upgrade.armor_stamp_qword=0 # Explicit separate clock fixture, not a source-start write.
            self.upgrade_execution=UpgradeExecution(self.upgrade)
            self.write('Armor: kaynak başlangıç/NPC seçici/panel eşlemesi yerel gözlemlerden kuruldu; oyunda arama yapılmaz. '
                       'Panel seçeneğinde iki combo okuması sabit yerel profil örneğidir; kapalıyken ayrı girişlerdir. '
                       'İlk arama mesafesi7, pointer/ofset/konum, stamp0, mesajlar ve helper dönüşleri sentetik. Miktar1 ve selectorA0 kaynak sabitleri. '
                       'Çanta ID, vendor karşılaştırmaları, helper/temizleme dönüşleri ve dört saat sentetik. '
                       'Kayıtlar yalnız yerel kuyruğa alınır; oyun eylemi/ACK yoktur.')
        elif case in ('Sell Merchant', 'Buy Merchant'):
            kind = MerchantKind.BUY if case == 'Buy Merchant' else MerchantKind.SELL
            rows=(MerchantRow(values['item_id'], values['quantity'], values['price']),)
            if kind==MerchantKind.BUY and self.use_class_panel.get():
                if self.configuration_reader is None:raise ValueError('Alış pazarı panel kaynağı bağlanmadı')
                panel_values,panel_lists=self.configuration_reader()
                self.buy_merchant_compiled=compile_buy_merchant_panel(panel_values,route_text=self.panel_route_sample('BMerchant'))
                settings=buy_merchant_settings_from_panel(self.buy_merchant_compiled,rows=rows)
                self.write('BUY panel ayarları yerel denemeye alındı; otomatik start modu, alarm ve rota alanları '
                           'tek başına oyun eylemi değildir. '+('Rota adı kendi panelinden alındı.'
                           if self.buy_merchant_compiled.route_text is not None else 'Rota adı gözlemi eksik.'))
            elif kind==MerchantKind.SELL and self.use_class_panel.get():
                if self.configuration_reader is None:raise ValueError('Satış pazarı panel kaynağı bağlanmadı')
                panel_values,panel_lists=self.configuration_reader()
                self.sell_merchant_compiled=compile_sell_merchant_panel(panel_values,route_text=self.panel_route_sample('SMerchant'))
                settings=sell_merchant_settings_from_panel(self.sell_merchant_compiled,rows=rows)
                self.write('SELL panel sırası/zaman/politika ayarları alındı. Bu denemede satış satırı ayrı örnektir; '
                           'panelin satış listesini veya gerçek çantayı işlemez. Alarm ve rota işlemi yapılmaz.')
            else:
                settings=MerchantSettings(kind=kind,
                    buy_free_threshold=int(self.buy_merchant_threshold.get()) if kind==MerchantKind.BUY else 0,rows=rows)
            self.merchant = MerchantRunner(settings)
            self.sell_preparation_enabled=kind==MerchantKind.SELL and self.sell_preparation_fixture.get()
            self.sell_cost_enabled=self.sell_preparation_enabled and self.sell_cost_fixture.get()
            self.sell_wait_enabled=kind==MerchantKind.SELL and self.sell_wait_fixture.get()
            self.sell_failure_enabled=kind==MerchantKind.SELL and self.sell_failure_fixture.get()
            self.buy_failure_enabled=kind==MerchantKind.BUY and self.buy_failure_fixture.get()
            self.merchant.start()
            self.merchant_open_state=BuyOpenState();self.merchant_open_queue=QueueState();self.merchant_open_last=None
            self.merchant_open_frame=None;self.merchant_open_frame_last=None
            self.merchant_reply_enabled=kind==MerchantKind.BUY and self.buy_reply_fixture.get()
            self.merchant_reply_state=MerchantReplyState();self.merchant_reply_last=None
        elif case == 'Loot':
            self.loot_records = (LootRecord('deneme', 0, item_ids=(values['item_id'], 0, 0, 0, 0, 0, 0, 0)),)
            self.loot_bundle_ids = {'deneme':0x11223344} # Explicit synthetic source record+0.
        elif case == 'Flood':
            self.messages = MessageSequence()
            self.messages.start([MessageRow('Merchant', 'Birinci deneme mesajı', values['wait']),
                                 MessageRow('Merchant', 'İkinci deneme mesajı', values['wait'])])
        elif case == 'Maden':
            self.mining = MiningRunner(MiningRunnerConfig(crash_wait_enabled=True,
                crash_wait_minutes=values['wait']))
            self.mining_state = MiningExecutionState(route_active=True)
        elif case=='NPC Onarım':
            self.repair_fields={0x640:0,0x644:0,0x648:0,0x64c:0,0x604:1,0x60c:0x100000,0x555:1}
            self.repair_globals={0x553e44:0,0x561fb0:0,0x561f58:0}
        elif case=='NPC Enchant':
            self.enchant_fields={0x6c4:0,0x6c8:0,0x6d0:0,0x6d4:0,0x604:1,0x60c:0x100000}
        elif case=='NPC Satış':
            self.sale_state=NpcSaleState({0x654:13,0x658:0,0x660:0,0x664:0,0x604:1,0x60c:0x100000},
                                         {0x553e44:0,0x561f58:0})
            self.sale_plan_count=0
        elif case=='NPC Satın Alma':
            self.buy_state=NpcBuyState({0x690:0xffffffff,0x68c:1,0x694:0,0x698:0,0x69c:0,
                                        0x604:1,0x60c:0x100000})
            self.buy_plan_count=0
        self.initialized = True

    def protection_example(self):
        try:
            self.protection_sample.set(example_protection_sample(self.protection_trial.current_snapshot()))
        except (ValueError,OSError) as error:
            self.protection_trial.last=None
            self.write('Koruma sentetik örneği oluşturulamadı: '+str(error))

    def disconnect_example(self):
        try:self.disconnect_sample.set(example_disconnect_sample(self.disconnect_trial.current_snapshot()))
        except (ValueError,OSError) as error:
            self.disconnect_trial.last=None
            self.write('DC ayar önizlemesi hazırlanamadı: '+str(error))

    def genie_settings_example(self):
        try:self.genie_settings_sample.set(example_genie_settings_sample(self.genie_settings_trial.current_snapshot()))
        except ValueError as error:
            self.genie_settings_trial.last=None
            self.write('Genie ayar önizlemesi hazırlanamadı: '+str(error))

    def item_break_settings_example(self):
        try:self.item_break_settings_sample.set(example_item_break_settings_sample(self.item_break_settings_trial.current_snapshot()))
        except ValueError as error:
            self.item_break_settings_trial.last=None
            self.write('Item kırma ayar önizlemesi hazırlanamadı: '+str(error))

    def control_settings_example(self):
        try:self.control_settings_sample.set(example_control_settings_sample(self.control_settings_trial.current_snapshot()))
        except ValueError as error:
            self.control_settings_trial.last=None
            self.write('Kontrol ayar önizlemesi hazırlanamadı: '+str(error))

    def jail_selection_example(self):
        try:self.jail_selection_sample.set(example_selection_sample(self.jail_selection_trial.current_snapshot()))
        except (ValueError,OSError) as error:
            self.jail_selection_trial.last=None
            self.write('DC–Hapis örneği oluşturulamadı: '+str(error))

    def dc_example(self):
        try:self.dc_sample.set(example_dc_sample(self.dc_trial.current_snapshot()))
        except ValueError as error:
            self.dc_trial.last=None;self.write('DC örneği oluşturulamadı: '+str(error))

    def tp_example(self):
        try:
            if self.configuration_reader is None:raise ValueError('Panel bağlantısı gerekli')
            values,_=self.configuration_reader()
            self.tp_sample.set(example_tp_sample(tp_snapshot(values),bytes.fromhex(self.tp_packet.get())))
        except ValueError as error:
            self.tp_trial.last=None
            self.write('TP sentetik örneği oluşturulamadı: '+str(error))

    def transformation_example(self):
        try:
            if self.configuration_reader is None:raise ValueError('Panel bağlantısı gerekli')
            values,_=self.configuration_reader()
            self.transformation_sample.set(example_transformation_sample(transformation_snapshot(values)))
        except ValueError as error:
            self.transformation_trial.last=None
            self.write('Transformation sentetik örneği oluşturulamadı: '+str(error))

    def event_example(self):
        try:
            if self.configuration_reader is None:raise ValueError('Panel bağlantısı gerekli')
            values,_=self.configuration_reader()
            self.event_sample.set(example_event_sample(event_snapshot(values)))
        except ValueError as error:
            self.event_trial.last=None
            self.write('Etkinlik sentetik örneği oluşturulamadı: '+str(error))

    def allocation_example(self):
        try:
            if self.configuration_reader is None:raise ValueError('Panel bağlantısı gerekli')
            values,lists=self.configuration_reader()
            self.allocation_sample.set(example_allocation_sample(compile_allocation_panel(values,lists)))
        except ValueError as error:
            self.allocation_trial.last=None
            self.write('Stat/Skill sentetik örneği oluşturulamadı: '+str(error))

    def start_ms_achievement(self):
        if self.case.get()=='Achieve MS' and self.achievement_trial.frame.final is None and self.achievement_trial.frame.calls:
            self.tick(0)
            return
        queue=self.achievement_trial.frame.queue
        self.case.set('Achieve MS');self.reset()
        self.achievement_trial.reset(queue)
        self.achievement_sample.set('{}')
        self.tick(0)

    def tick(self, elapsed=1000):
        try:
            if self.case.get()=='Item Kırma Ayarları':
                self.now_ms+=elapsed;self.item_break_settings_trial.step(self.item_break_settings_sample.get())
                self.write('%d ms • Item kırma ayar önizlemesi • %s'%(self.now_ms,self.describe(describe_item_break_settings_trial(self.item_break_settings_trial))))
                return
            if self.case.get()=='Kontrol Ayarları':
                self.now_ms+=elapsed;self.control_settings_trial.step(self.control_settings_sample.get())
                self.write('%d ms • Kontrol ayar önizlemesi • %s'%(self.now_ms,self.describe(describe_control_settings_trial(self.control_settings_trial))))
                return
            if self.case.get()=='Genie Ayarları':
                self.now_ms+=elapsed;self.genie_settings_trial.step(self.genie_settings_sample.get())
                self.write('%d ms • Genie ayar önizlemesi • %s'%(self.now_ms,self.describe(describe_genie_settings_trial(self.genie_settings_trial))))
                return
            if self.case.get()=='DC / Relog Ayarları':
                self.now_ms+=elapsed;self.disconnect_trial.step(self.disconnect_sample.get())
                self.write('%d ms • DC ayar önizlemesi • %s'%(self.now_ms,self.describe(describe_disconnect_trial(self.disconnect_trial))))
                return
            if self.case.get()=='DC Koruma':
                self.now_ms+=elapsed;self.dc_trial.step(self.dc_sample.get())
                self.write('%d ms • Yerel DC koruma • %s'%(self.now_ms,self.describe(describe_dc_trial(self.dc_trial))))
                return
            if self.case.get()=='DC–Hapis Listesi':
                self.now_ms+=elapsed
                self.jail_selection_trial.step(self.jail_selection_sample.get())
                self.write('%d ms • Yerel DC–Hapis kaydı • %s'%(self.now_ms,self.describe(describe_selection_trial(self.jail_selection_trial))))
                return
            if self.case.get()=='Koruma Ayarları':
                self.now_ms+=elapsed
                self.protection_trial.step(self.protection_sample.get())
                self.write('%d ms • Yerel ortak Koruma ayarları • %s'%(self.now_ms,self.describe(describe_protection_trial(self.protection_trial))))
                return
            if self.case.get()=='TP Koruma':
                self.now_ms+=elapsed
                self.tp_trial.step(self.tp_packet.get(),self.tp_sample.get())
                self.write('%d ms • Yerel TP koruma denemesi • %s'%(self.now_ms,self.describe(describe_tp_trial(self.tp_trial))))
                return
            if self.case.get()=='Transformation':
                self.now_ms+=elapsed
                self.transformation_trial.step(self.transformation_sample.get())
                self.write('%d ms • Yerel Transformation denemesi • %s'%(self.now_ms,self.describe(describe_transformation_trial(self.transformation_trial))))
                return
            if self.case.get()=='Etkinlik Katılımı':
                self.now_ms+=elapsed
                self.event_trial.step(self.event_sample.get())
                self.write('%d ms • Yerel etkinlik denemesi • %s'%(self.now_ms,self.describe(describe_event_trial(self.event_trial))))
                return
            if self.case.get()=='Stat/Skill Ayarları':
                self.now_ms+=elapsed
                result=self.allocation_trial.step(self.allocation_sample.get())
                self.write('%d ms • Yerel stat/skill ayar ve çağrı modeli • %s'%(self.now_ms,self.describe(describe_allocation_panel(result,self.allocation_trial.consumer_last))))
                return
            if self.case.get()=='Achieve MS':
                self.now_ms+=elapsed
                result=self.achievement_trial.step(self.achievement_sample.get())
                self.write('%d ms • Yerel Achieve MS denemesi • %s'%(self.now_ms,self.describe(describe_achievement_trial(result))))
                return
            if self.case.get()=='Monster Stone':
                self.now_ms+=elapsed
                result=self.ms_trial.step(self.ms_sample.get())
                self.write('%d ms • Yerel Monster Stone ayar/etkinleştirme denemesi • %s'%(self.now_ms,self.describe(describe_ms_trial(result))))
                return
            if self.case.get()=='Chat Yetenek İsteği':
                self.now_ms+=elapsed
                result=self.chat_skills_trial.step(self.chat_skills_packet.get(),self.chat_skills_sample.get(),int(self.chat_skills_codepage.get()))
                request=getattr(result,'queued_request',None)
                self.write('%d ms • Yerel chat yetenek isteği; yetenek kullanılmadı • İstek: %s • %s'%(self.now_ms,request.key if request else 'yok',self.describe(result)))
                return
            if self.case.get()=='Chat Komutları':
                self.now_ms+=elapsed
                result=self.chat_commands_trial.step(self.chat_commands_packet.get(),self.chat_commands_sample.get(),int(self.chat_commands_codepage.get()),self.chat_commands_detailed.get())
                helpers=self.chat_commands_trial.helpers
                self.write('%d ms • Yerel chat komutu denemesi; eylem yürütülmedi • Çağrı planı sayısı: %d • Yerel kuyruk kaydı: %d • %s'%(self.now_ms,len(getattr(result,'actions',())),len(helpers.queue.records) if helpers is not None else 0,self.describe(result)))
                return
            if self.case.get()=='Chat/PM Party':
                self.now_ms+=elapsed
                result=self.chat_party_trial.step(self.chat_party_packet.get(),self.chat_party_sample.get(),int(self.chat_party_codepage.get()))
                frame=self.chat_party_trial.frame
                self.write('%d ms • Yerel chat/PM denemesi; gönderim yok • Yerel kayıt sayısı: %d • %s'%(self.now_ms,len(frame.queue.records) if frame is not None else 0,self.describe(result)))
                return
            if self.case.get()=='Party Daveti':
                self.now_ms+=elapsed
                result=self.party_trial.step(self.party_packet.get(),self.party_sample.get(),int(self.party_codepage.get()))
                self.write('%d ms • Yerel davet planı; yanıt gönderilmedi • %s'%(self.now_ms,self.describe(result)))
                return
            if self.case.get()=='Takip':
                self.now_ms+=elapsed
                result=self.follow_trial.step(self.follow_sample.get())
                self.write('%d ms • Yerel takip denemesi • %s'%(self.now_ms,self.describe(result)))
                return
            values = self.numbers()
            if not self.initialized:
                self.setup(values)
                if not self.initialized:return
            self.now_ms += elapsed
            case = self.case.get()
            if case=='NPC Satın Alma' and self.buy_state.fields.get(0x690)==2:
                result={'Aşama':2,'Durum':'Tamamlandı','Satın alma planı toplamı':self.buy_plan_count}
            elif case=='NPC Satın Alma':
                record=NpcBuyRecord(values['item_id'],values['quantity'],0,0,values['distance'],values['price'])
                matches={name:name=='Sundries' for name,code in BUY_VENDORS}
                caches={slot:SellCacheSlot((values['item_id']+1)&0xffffffff,1,1) if self.full.get()
                        else SellCacheSlot(0,0,0) for slot in range(14,42)}
                if values['threshold']>0:caches[14]=SellCacheSlot(values['item_id'],1,values['threshold'])
                packet_obs=NpcBuyPacketObservation(values['hp'],values['hp_max'],matches,caches,{0:values['mp']})
                self.buy_last=npc_buy_step(self.buy_state,NpcBuyObservation(self.now_ms&0xffffffff,1,
                    NpcBuyRouteRow(1 if self.ready.get() else 0,0x3e418,record),matches,packet_obs))
                self.buy_state=self.buy_last.state;self.buy_plan_count+=len(self.buy_last.queue_payloads)
                result={'Aşama':self.buy_last.returned_phase,'Durum':self.buy_last.status,
                        'Toplanan satır':len(self.buy_state.batch),'Satın alma planı toplamı':self.buy_plan_count,
                        'Eksik gözlem':self.buy_last.missing}
            elif case=='NPC Satış' and self.sale_state.fields.get(0x654)==43:
                result={'Aşama':43,'Durum':'Tamamlandı','Toplu satış planı toplamı':self.sale_plan_count}
            elif case=='NPC Satış':
                phase=self.sale_state.fields[0x654]
                choice=SellFilterObservation(0,False,-1,False,list_index_41a5cc=1,
                                             list_checked_5622e1=self.ready.get())
                caches={slot:SellCacheSlot(values['item_id'],values['hp'],values['quantity']) for slot in range(14,42)}
                record=NpcSellRecord(values['item_id'],(phase-14)&255,values['quantity']&0xffff)
                self.sale_last=npc_sale_step(self.sale_state,NpcSaleObservation(self.now_ms&0xffffffff,
                    inventory_pointer=0x200000,current_target=1,slot_present_4637d8=values['item_id']!=0,
                    selection=choice,record=record,vendor_matches={name:name=='Sundries' for name,code in VENDORS},
                    cache_slots=caches))
                self.sale_state=self.sale_last.state
                self.sale_plan_count+=len(self.sale_last.queue_payloads)
                result={'Aşama':self.sale_last.returned_phase,'Durum':self.sale_last.status,
                        'Toplanan eşya':len(self.sale_state.batch),'Toplu satış planı toplamı':self.sale_plan_count,
                        'Eksik gözlem':self.sale_last.missing}
            elif case=='NPC Onarım' and self.repair_fields.get(0x640)==42:
                result={'Aşama':42,'Durum':'Tamamlandı','Onarım planı sayısı':0}
            elif case=='NPC Enchant' and self.enchant_fields.get(0x6c4)==8:
                result={'Aşama':8,'Durum':'Tamamlandı','Enchant planı sayısı':0}
            elif case=='NPC Onarım':
                slot=RepairSlot(values['item_id'],values['hp'],values['hp_max'],(values['item_id'],))
                slots={index:slot for index in STARTUP_SLOTS+tuple(range(14,42))}
                inventory=RepairInventoryObservation(slots,True,0,(values['item_id'],))
                self.repair_globals[0x561fb0]=0 if self.ready.get() else 0xffffffff
                self.repair_last=repair_step(self.repair_fields,self.repair_globals,
                    RepairObservation(self.now_ms&0xffffffff,current_target=1,
                        item_id_4634a4=values['item_id'],durability_46358c=values['hp'],
                        maximum_4635e0=values['hp_max'],mode0_cache_match=True,
                        producer_item_id_4634a4=values['item_id'],candidate_inventory=inventory))
                self.repair_fields=dict(self.repair_last.fields);self.repair_globals=dict(self.repair_last.globals)
                result={'Aşama':self.repair_last.returned_phase,'Durum':self.repair_last.status,
                        'Onarım planı sayısı':len(self.repair_last.queue_payloads),'Eksik gözlem':self.repair_last.missing}
            elif case=='NPC Enchant':
                zone={'Moradon':21,'Luferson':1,'EMC':2,'Karus Eslant':11,'Human Eslant':12}[self.enchant_zone.get()]
                self.enchant_last=enchant_step(self.enchant_fields,EnchantObservation(self.now_ms&0xffffffff,
                    str(values['item_id']).encode('ascii'),values['item_id'],current_target=1 if self.ready.get() else 2,
                    raw_level_462670=values['hp'],raw_zone_id=zone))
                self.enchant_fields=dict(self.enchant_last.fields)
                result={'Aşama':self.enchant_last.returned_phase,'Durum':self.enchant_last.status,
                        'Enchant planı sayısı':len(self.enchant_last.queue_payloads),'Eksik gözlem':self.enchant_last.missing}
            elif case == 'Upgrade':
                scroll_lookup=None
                if self.upgrade.source_clock and self.upgrade_scroll_fixture.get() and not self.ready.get():
                    scroll_lookup=self.upgrade_scroll_observation()
                sample=UpgradeSnapshot(self.now_ms&0xffffffff if self.upgrade.source_clock else self.now_ms,
                    queue_action_ready=self.ready.get(), scroll_index=None if scroll_lookup is not None else 0,
                    source_helper_returned=True,source_stamp_tick_dword=(self.now_ms+2)&0xffffffff,
                    scroll_lookup=scroll_lookup)
                if self.upgrade.source_clock:
                    self.upgrade_execution_last=self.upgrade_execution.step(sample,
                        UpgradePacketObservation(scroll_item_dword=0x10203040,target_item_dword=values['item_id']),
                        QueueSample((self.now_ms+1)&0xffffffff,int(self.upgrade_queue_gate.get())))
                    bound=self.upgrade_execution_last
                    result={'Durum':bound.status,'İşlem':bound.operation.status,
                            'Yerel kuyruk kayıtları':len(bound.queue.records),'Eksik gözlem':bound.missing}
                    if bound.packet and bound.packet.payload is not None:
                        result['Yerel57bayt(hex)']=bound.packet.payload.hex()
                else:result=self.upgrade.tick(sample)
                if self.upgrade.scroll_lookup_plan is not None:
                    self.write('Son örnek çanta ad taraması: '+self.describe(self.upgrade.scroll_lookup_plan))
            elif case=='Armor Alımı':
                relative=int(self.upgrade_scroll_slot.get())
                if not -1<=relative<=27:raise ValueError('Örnek boş yuva -1..27 olmalı')
                scan=ArmorFreeSlotObservation({slot:0 if relative>=0 and slot==relative+14 else 1 for slot in range(14,42)})
                packet=ArmorPacketObservation(free_scan=scan,vendor_matches={n:n=='Armor' for n,c in ARMOR_VENDORS})
                sample=UpgradeSnapshot(self.now_ms&0xffffffff,armor_distance=values['distance'],armor_blocked=self.full.get(),
                    source_helper_returned=self.ready.get(),source_stamp_tick_dword=(self.now_ms+3)&0xffffffff)
                fields=self.upgrade.armor_source_fields
                self.upgrade_execution_last=self.upgrade_execution.step(sample,
                    armor_inputs=ArmorExecutionInputs(fields[0x4c],fields[0x58],fields[0x5c],packet,self.ready.get()),
                    armor_queue_samples={0:QueueSample((self.now_ms+1)&0xffffffff,int(self.upgrade_queue_gate.get())),
                                         1:QueueSample((self.now_ms+2)&0xffffffff,int(self.armor_second_gate.get()))})
                bound=self.upgrade_execution_last
                result={'Durum':bound.status,'Yerel deneme sayacı':self.upgrade.armor_attempts,
                        'Kuyruk kayıtları':len(bound.queue.records),'Eksik gözlem':bound.missing}
                if bound.packet and bound.packet.packets:
                    result['Yerel tamponlar(hex)']=[(p.hex(),delay) for p,delay in bound.packet.packets]
            elif case in ('Sell Merchant', 'Buy Merchant'):
                coin_alarm=None
                if case=='Sell Merchant' and self.sell_merchant_compiled is not None:
                    coins=None
                    if self.sell_merchant_compiled.fields[0xe0] and self.sell_coin_current.get().strip():
                        coins=int(self.sell_coin_current.get(),0)
                    coin_alarm=sell_coin_alarm_from_panel(self.sell_merchant_compiled,coins,self.sell_coin_return.get())
                    if not plan_sell_coin_alarm(coin_alarm).complete:
                        result=self.merchant.tick(MerchantSnapshot(self.now_ms,sell_coin_alarm_inputs=coin_alarm))
                        self.write('%d ms • %s' % (self.now_ms,self.describe({'Yerel SELL kararı':result,
                            'Coin alarm planı':self.merchant.last_sell_coin_alarm_plan,'Canlı işlem doğrulandı':False})))
                        return
                # These are explicit synthetic producer flags, never observed server flags.
                buy_inputs=None;inventory=None
                if case=='Buy Merchant' and self.buy_merchant_fixture.get():
                    free=0 if self.full.get() else int(self.buy_merchant_free.get())
                    if not 0<=free<=28:raise ValueError('Örnek boş yuva 0–28 olmalı')
                    inventory=MerchantInventoryObservation((0,)*free+(1,)*(28-free))
                    buy_inputs=BuySetupObservation(preparation_inputs=self.buy_preparation_sample(),
                        inventory_inputs=inventory,coins_dword=int(self.buy_merchant_coins.get()),
                        stable_rows=True)
                sell_setup=None
                if (case=='Sell Merchant' and self.sell_preparation_enabled and self.merchant.phase==2
                        and self.now_ms>=(self.merchant.settings.extra_wait_seconds+61)*1000):
                    preparation=self.merchant_preparation_sample(SELL_LIST_PATH)
                    # Pure preview keeps unreached cost fields lazy; it executes no native effects.
                    preview=replay_sell_preparation(SellPreparationState(),preparation)
                    def sample_number(variable):return int(variable.get(),0) if variable.get().strip() else None
                    cost=None;matches=None;coins=None;cost_inputs=None
                    if self.sell_cost_enabled and preview.complete:
                        def sequence(variable):
                            parsed=json.loads(variable.get())
                            if type(parsed) is not list:raise ValueError('Taze helper sonuçları JSON dizisi olmalı')
                            return tuple(parsed)
                        order=(self.merchant.settings.sell_all_inventory if self.merchant.settings.sell_inventory_order is None
                               else self.merchant.settings.sell_inventory_order)
                        cost_inputs=SellCostObservation(inventory_order_byte=int(order),stable_rows=True)
                        cost_preview=plan_sell_cost(preview.state.records,cost_inputs)
                        if any(c[0]=='004634a4' for c in cost_preview.calls):
                            cost_inputs=replace(cost_inputs,item_results=sequence(self.sell_cost_items))
                            cost_preview=plan_sell_cost(preview.state.records,cost_inputs)
                        if any(c[0]=='00463538' for c in cost_preview.calls):
                            cost_inputs=replace(cost_inputs,quantity_results=sequence(self.sell_cost_quantities))
                            cost_preview=plan_sell_cost(preview.state.records,cost_inputs)
                        if cost_preview.complete:coins=sample_number(self.sell_setup_coins)
                    elif not self.sell_cost_enabled:
                        cost=sample_number(self.sell_setup_cost) if preview.complete else None
                        matches=sample_number(self.sell_setup_matches) if cost is not None else None
                        coins=sample_number(self.sell_setup_coins) if cost is not None and matches is not None else None
                    sell_setup=SellSetupObservation(preparation_inputs=preparation,
                        cost_qword=cost,matched_count_dword=matches,coins_dword=coins,
                        over_limit_span_returned=self.ready.get(),cost_inputs=cost_inputs)
                sell_selection=None
                if case=='Sell Merchant' and self.sell_preparation_enabled and self.merchant.phase==3:
                    previous=self.merchant.last_sell_setup_plan
                    if previous is not None and previous.preparation_plan is not None:
                        sell_selection=SellSelectionObservation(rows=previous.preparation_plan.state.records,stable_rows=True,
                            inventory_slot_dword=self.merchant.inventory_slot,list_index_dword=self.merchant.entry_index)
                merchant_snapshot=MerchantSnapshot(self.now_ms, currently_open=False,
                    close_pending=False, setup_result=0 if case=='Sell Merchant' and not self.sell_preparation_enabled else None,
                    buy_setup_inputs=buy_inputs,buy_inventory_inputs=inventory,sale_session_ready=self.ready.get(),
                    item_pending=False, prepared_slot_count=1, opening_pending=not self.ready.get(),
                    established_ms=0, setup_started_ms=0, bank_route_allowed=False,sell_setup_inputs=sell_setup,
                    sell_selection_inputs=sell_selection,sell_coin_alarm_inputs=coin_alarm)
                if case=='Sell Merchant' and self.sell_failure_enabled:
                    failure_text=self.sell_failure_json.get()
                    merchant_snapshot=replace(merchant_snapshot,bank_route_allowed=None,
                        sell_failure_factory=lambda:self.sell_failure_observation(failure_text))
                if case=='Sell Merchant' and self.sell_wait_enabled and self.merchant.phase==3:
                    wait_input=parse_sell_prepare_wait(self.sell_wait_json.get())
                    merchant_snapshot=replace(merchant_snapshot,
                        sale_session_ready=None if wait_input.ready_byte is None else bool(wait_input.ready_byte),
                        item_pending=None if wait_input.item_pending_byte is None else bool(wait_input.item_pending_byte),
                        sell_prepare_wait_inputs=wait_input)
                if case=='Buy Merchant' and self.merchant_reply_enabled:
                    opening_clock=None
                    monitor_inputs=None
                    if self.merchant.phase==4 and self.merchant_open_frame_last is not None:
                        opening_clock=BuyOpenClockSample(self.now_ms&0xffffffff,
                            self.merchant_open_frame_last.state.pending_stamp_qword)
                    if self.merchant.phase==5:
                        monitor_inputs=BuyMonitorObservation(reopen_byte=int(self.merchant.settings.reopen),
                            minutes_dword=self.merchant.settings.reopen_minutes,
                            established_stamp_qword=self.merchant_reply_state.established_stamp_qword,
                            tick_dword=self.now_ms&0xffffffff,threshold_dword=self.merchant.settings.buy_free_threshold,
                            inventory_inputs=inventory,display_span_returned=self.ready.get())
                    merchant_snapshot=merchant_snapshot_from_reply(self.merchant_reply_state,self.now_ms,
                        currently_open=False,buy_setup_inputs=buy_inputs,
                        buy_inventory_inputs=None if monitor_inputs is not None else inventory,
                        prepared_slot_count=1,bank_route_allowed=False,buy_open_clock=opening_clock,
                        buy_monitor_inputs=monitor_inputs)
                if case=='Buy Merchant' and self.buy_failure_enabled:
                    buy_failure_text=self.buy_failure_json.get()
                    merchant_snapshot=replace(merchant_snapshot,bank_route_allowed=None,
                        buy_failure_factory=lambda:self.buy_failure_observation(buy_failure_text))
                before_phase=self.merchant.phase
                if case=='Buy Merchant' and before_phase==3:
                    if self.merchant_open_frame is None:
                        self.merchant_open_frame=BuyOpenFrame(BuyOpenCallerState(accumulated_qword=self.merchant_open_state.accumulated_qword),
                                                               self.merchant_open_queue)
                    prepared=self.merchant.last_buy_setup_plan
                    observation=None
                    if inventory is None or prepared is None or prepared.preparation_plan is None:
                        pass # The caller pending/clock prefix still precedes this helper-input gap.
                    else:
                        observation=BuyOpenObservation(initial_global_base=0x7000,inventory_inputs=inventory,
                            coins_dword=int(self.buy_merchant_coins.get()),records=prepared.preparation_plan.state.records,
                            stable_records=True,fresh_global_bases={i:0x7000 for i in range(12)},
                            zero_helper_returns={i:self.ready.get() for i in range(12)},
                            memset_returns={i:self.ready.get() for i in range(12)})
                    caller=self.merchant_open_frame.step(entry_tick=self.now_ms&0xffffffff,observation=observation,
                        samples={0:QueueSample((self.now_ms+1)&0xffffffff,1),1:QueueSample((self.now_ms+2)&0xffffffff,1)},
                        helper_returned=self.ready.get())
                    self.merchant_open_frame_last=caller;self.merchant_open_last=caller.execution
                    if caller.complete:
                        self.merchant_open_state=BuyOpenState(caller.state.accumulated_qword);self.merchant_open_queue=caller.queue
                        if self.merchant_reply_enabled:
                            self.merchant_reply_state=replace(self.merchant_reply_state,
                                opening_pending_byte=caller.state.pending_byte)
                        result=self.merchant.tick(merchant_snapshot)
                        self.merchant.phase_ms=caller.state.pending_stamp_qword
                    else:result=OperationDecision('needs_adapter',reason=caller.missing)
                else:result=self.merchant.tick(merchant_snapshot)
                if case=='Buy Merchant' and before_phase==2 and self.merchant.phase==3:
                    self.merchant_open_state=BuyOpenState() # own projection of source +98/+9c reset
                    self.merchant_open_frame=None;self.merchant_open_frame_last=None;self.merchant_open_last=None
                if case=='Sell Merchant' and self.sell_failure_enabled and result.status=='bank_route':
                    failure_plan=self.merchant.last_sell_failure_plan
                    if self.bank_route_consumer is not None:self.sell_bank_handoff_last=self.bank_route_consumer(failure_plan)
                if case=='Buy Merchant' and self.buy_failure_enabled and result.status=='bank_route':
                    failure_plan=self.merchant.last_buy_failure_plan
                    if self.buy_bank_route_consumer is not None:self.buy_bank_handoff_last=self.buy_bank_route_consumer(failure_plan)
                if case=='Sell Merchant' and self.merchant.last_sell_setup_plan is not None:
                    result={'Yerel SELL kararı':result,'Liste/hazırlık planı':self.merchant.last_sell_setup_plan,
                        'Maliyet/eşleşme helper sonucu': ('taze envanter örneklerinden hesaplandı' if self.sell_cost_enabled
                            else 'ayrı verilen örnektir, listeden hesaplanmadı'),
                        'Son seçim planı':self.merchant.last_sell_selection_plan,
                        'Başarısızlık / rota planı':self.merchant.last_sell_failure_plan,
                        'Yerel rota aktarımı':self.sell_bank_handoff_last,
                        'Canlı işlem doğrulandı':False}
                if case=='Sell Merchant' and self.sell_wait_enabled:
                    result={'Yerel SELL sonucu':result,'Son hazırlık bekleme planı':self.merchant.last_sell_prepare_wait_plan,
                        'Yerel oturum damgası':self.merchant.phase_ms,'Yerel ürün damgası':self.merchant.item_ms,
                        'Gözlemler': 'elle verilen örnek; canlı oyundan okunmadı','Canlı işlem doğrulandı':False}
                if case=='Sell Merchant' and coin_alarm is not None:
                    result={'Yerel SELL sonucu':result,'Coin alarm planı':self.merchant.last_sell_coin_alarm_plan,
                        'Alarm dönüşü elle verilen örnektir':True,'Canlı işlem doğrulandı':False}
                if case=='Buy Merchant' and self.merchant.last_buy_setup_plan is not None:
                    plan=self.merchant.last_buy_setup_plan
                    result={'Pazar kararı':result,'Hazırlık sonucu':plan.result_dword,'Eksik gözlem':plan.missing,
                            'BUY başarısızlık planı':self.merchant.last_buy_failure_plan,'Yerel banka rotası aktarımı':self.buy_bank_handoff_last,
                        'Hazırlanan satırlar':plan.preparation_plan.prospective_state.records if plan.preparation_plan else ()}
                    if self.merchant_open_last is not None:
                        opened=self.merchant_open_last
                        result.update({'Açma tamam':opened.complete,'Açma eksiği':opened.missing,
                            'Yerel kuyruk kaydı':len(self.merchant_open_queue.records),
                            'Bellek yazma planı sayısı (uygulanmadı)':len(opened.source.write_plans),
                            'Yerel açma tamponları':[(p.hex(),delay) for p,delay in opened.source.packets]})
                    if self.merchant_open_frame_last is not None:
                        prefix=self.merchant_open_frame_last.prospective_state
                        result.update({'Açma prefix pending BYTE':prefix.pending_byte,'Açma ilk saat':prefix.pending_stamp_qword})
                    if self.merchant_reply_enabled:
                        result.update({'Yerel yanıt pending BYTE':self.merchant_reply_state.opening_pending_byte,
                            'Yerel yanıt saati':self.merchant_reply_state.established_stamp_qword,
                            'Son verilen yanıt örneği':self.merchant_reply_last,
                            'Canlı işlem doğrulandı':False})
                    if self.merchant.last_buy_monitor_plan is not None:
                        result['Son yerel izleme planı']=self.merchant.last_buy_monitor_plan
            elif case == 'Loot Filtre':
                if self.use_class_panel.get():
                    panel_values,panel_lists=self.configuration_reader()
                    self.loot_compiled=compile_loot_panel(panel_values)
                    fields=self.loot_compiled.fields
                    cache_rows=compile_loot_name_cache(panel_lists)
                else:
                    fields={4:3,0x18:0,0x1c:7,0x21:0,0x20:0,0x11:1,0x14:values['price']}
                    cache_rows=(LootCacheRow(self.loot_name.get(),1),)
                meta=LootMetadataObservation(1 if self.ready.get() else 0,1,values['quantity'],values['threshold'],values['price'])
                self.loot_name_plan=None;self.loot_name_conversion=None;self.loot_fixture_used_default=None
                name='';guard=False
                if fields.get(4)==3 and not self.loot_list_state.classified and self.ready.get() and values['item_id']:
                    name,guard=self.build_loot_name_fixture(values)
                if self.loot_name_plan is not None and self.loot_name_plan.ansi_bytes is None:
                    result=self.loot_name_plan
                else:
                    names=(name,'','','','','','',name)
                    self.loot_cached_last=classify_loot_with_name_cache(
                        (values['item_id'],0,0,0,0,0,0,values['item_id']),fields,LootListObservation({0:meta,7:meta}),
                        names,cache_rows,record_state=self.loot_list_state,cache_state=self.loot_cache_state,
                        input_nonempty=(guard,False,False,False,False,False,False,guard))
                    self.loot_cache_state=self.loot_cached_last.cache_state
                    self.loot_classifier_last=self.loot_cached_last.classification
                    if self.loot_classifier_last.complete:self.loot_list_state=self.loot_classifier_last.state
                    result={'İsim bayt planı':self.loot_name_plan,'Yerel dönüşüm':self.loot_name_conversion,
                        'Deneme bufferı varsayılan karakter kullanımı':self.loot_fixture_used_default,'Cache/sınıflandırma':self.loot_cached_last}
            elif case == 'Loot':
                self.loot_name_plan=None;self.loot_name_conversion=None;self.loot_fixture_used_default=None
                cache_rows=compile_loot_name_cache(self.configuration_reader()[1]) if self.use_class_panel.get() else (LootCacheRow(self.loot_name.get(),1),)
                if self.loot_pending is None:
                    records=tuple(replace(row,item_phase=self.ready.get()) for row in self.loot_records)
                    snapshot=LootSnapshot(self.now_ms&0xffffffff,records,open_state_allowed=True)
                    if self.use_class_panel.get():
                        configuration=compile_loot_panel(self.configuration_reader()[0],previous_mode=self.loot_previous_mode)
                    else:configuration=LootPanelConfiguration('compiled',LootSettings(),{4:1})
                    if configuration.settings is not None:self.loot_previous_mode=configuration.settings.mode
                    original_cache=self.loot_cache_state
                else:configuration,snapshot,original_cache=self.loot_pending
                self.loot_pipeline_last=replay_loot_pipeline(configuration,snapshot,{},cache_rows,cache_state=original_cache)
                if self.loot_pipeline_last.status=='needs_loot_producer' and self.loot_source_fixture.get():
                    reference=self.loot_pipeline_last.lifecycle.classifier_reference
                    record=next(r for r in snapshot.records if r.reference==reference)
                    item=next((item for item in record.item_ids if item),0)
                    name,guard=self.build_loot_name_fixture(dict(values,item_id=item))
                    meta=LootMetadataObservation(1,1,values['quantity'],values['threshold'],values['price'])
                    producer=LootRecordProducer(LootListObservation({i:meta for i,item in enumerate(record.item_ids) if item}),
                        None if name is None else tuple(name if item else '' for item in record.item_ids),
                        tuple(guard if item else False for item in record.item_ids))
                    self.loot_pipeline_last=replay_loot_pipeline(configuration,snapshot,{reference:producer},cache_rows,cache_state=original_cache)
                if self.loot_pipeline_last.complete:
                    self.loot_pending=None;self.loot_records=self.loot_pipeline_last.lifecycle.records
                    self.loot_cache_state=self.loot_pipeline_last.cache_state
                else:
                    self.loot_pending=(configuration,snapshot,original_cache) if self.loot_pipeline_last.lifecycle.classifier_reference is not None else None
                self.loot_last=self.loot_pipeline_last.lifecycle
                self.loot_packet_last=plan_loot_intents(self.loot_last,self.loot_bundle_ids)
                result={'Loot akışı':self.loot_pipeline_last,
                    'Sentetik kutu kimlikleri':self.loot_bundle_ids,
                    'Yerel tampon planları':self.loot_packet_last}
            elif case == 'Kontrol':
                self.control_guard_last=None;self.control_guard_compiled=None
                self.control_chain_last=None;self.control_continuation_last=None
                self.control_frame_last=None
                if self.use_class_panel.get():
                    if self.configuration_reader is None:raise ValueError('Kontrol panel kaynağı gerekli')
                    self.control_guard_compiled=compile_control_guards(self.configuration_reader()[0])
                    sampled=self.control_guard_data.get()
                    observation=ControlGuardObservation(
                        values['item_id'] if sampled else None,values['price'] if sampled else None,
                        values['hp'] if sampled else None,
                        True if self.control_guard_stop_return.get() else None,
                        True if self.control_guard_town_return.get() else None)
                    self.control_guard_last=plan_control_guards(self.control_guard_compiled,observation)
                    if self.control_follow_enabled.get() or self.control_frame_enabled.get():
                        follow_config=None;follow_observation=None
                        if self.control_guard_last.complete and not self.control_guard_last.source_return_planned:
                            follow_config=compile_control_continuation(self.configuration_reader()[0])
                            follow_observation=self.control_follow_observation()
                        self.control_chain_last=replay_control_chain(self.control_guard_compiled,observation,follow_config,follow_observation)
                        self.control_continuation_last=self.control_chain_last.continuation
                        if self.control_frame_enabled.get():
                            help_config=alarm_config=help_observation=alarm_observation=None
                            follow=self.control_continuation_last
                            if (self.control_chain_last.complete and follow is not None
                                    and not follow.source_return_planned and not follow.termination_call_planned):
                                sample=parse_control_sample(self.control_frame_json.get())
                                if not self.control_frame_seeded:
                                    self.control_frame_state=sample.initial_state or ControlFrameState(PartyHelpState(),LootActivityState())
                                    self.control_frame_seeded=True
                                panel_values=self.configuration_reader()[0]
                                help_config=compile_party_help(panel_values,observed_ansi=sample.observed_ansi)
                                alarm_config=compile_control_alarms(panel_values)
                                help_observation=sample.party_help;alarm_observation=sample.alarms
                            self.control_frame_last=replay_control_frame(
                                ControlFrameConfiguration(self.control_guard_compiled,follow_config,help_config,alarm_config),
                                self.control_frame_state,ControlFrameObservation(observation,follow_observation,help_observation,alarm_observation))
                            if self.control_frame_last.complete:self.control_frame_state=self.control_frame_last.state
                    result={'Panel guard planı':self.control_frame_last or self.control_chain_last or self.control_guard_last,
                        'Kapsam':'Karar/operand planı;RTL ve native helper etkileri doğrulanmadı',
                        'Canlı oyun işlemi':False}
                else:
                    result = evaluate_guards(GuardConfig(coin_limit=values['threshold']),
                        GuardSnapshot(coins=values['price']))
            elif case == 'Item Kır':
                result = abyss_crash_decision(CrashSnapshot(self.full.get(), values['quantity'] > 0,
                    1, float(values['distance'])), values['wait'], self.last_crash_ms, self.now_ms)
                if any(intent.action.value == 'crash_abyss_gem' for intent in result):
                    self.last_crash_ms = self.now_ms
            elif case == 'Tedarik':
                if self.use_class_panel.get():
                    panel_values,panel_lists=self.configuration_reader()
                    self.supply_compiled=compile_supply_panel(panel_values)
                    self.supply_weight_last=plan_supply_weight(self.supply_compiled,
                        weight_percent_dword(values['hp'],values['hp_max']),branch_reached=self.ready.get())
                    self.supply_list_last=compile_supply_list(panel_lists)
                    # Explicit stable local inventory fixture: only source slot14
                    # holds the entered ID/quantity; other27 slots return0.
                    inventory=SupplyStockObservation(
                        {(i,s):values['item_id'] if s==14 else 0 for i,row in enumerate(self.supply_list_last.rows)
                            if row.enabled for s in range(14,42)},
                        {(i,14):values['quantity'] for i,row in enumerate(self.supply_list_last.rows) if row.enabled})
                    self.supply_stock_last=plan_supply_stock(self.supply_list_last,inventory)
                    result={'Panel alanları':self.supply_compiled,'Ağırlık dalı':self.supply_weight_last,
                        'Panel alış listesi':self.supply_list_last,
                        'Sentetik envanterde stok helper denemesi':self.supply_stock_last}
                else:
                    result = {'ağırlık_tedarik': weight_supply_due(True, values['hp'], values['hp_max'], values['threshold']),
                              'stok_tedarik': stock_supply_due('Arrow', values['quantity'])}
            elif case == 'Flood':
                result = self.messages.tick(self.now_ms, 4)
            elif case == 'Eylem Kuyruğu':
                gate = 1 if self.ready.get() else 0
                if not self.action_queue_initialized:
                    quest = plan_take_quest([QuestRecord('Deneme NPC', b'deneme')],
                        QuestSnapshot(0,0,1,0x100000,0,1,0,values['item_id']))
                    for plan in quest.queue_plans:
                        decision = enqueue(self.action_queue, plan.payload, len(plan.payload),
                                           plan.delay_ms, gate, self.now_ms & 0xffffffff)
                        if decision.state is None:raise ValueError(decision.missing or decision.status)
                        self.action_queue = decision.state
                    self.action_queue_initialized = True
                observed = {row.record_id: QueueSample(self.now_ms & 0xffffffff, gate, True)
                            for row in self.action_queue.records}
                self.action_queue_last = drain(self.action_queue, observed)
                if self.action_queue_last.state is not None:self.action_queue = self.action_queue_last.state
                self.action_queue_send_plans += sum(e.kind=='native_send_plan' for e in self.action_queue_last.events)
                self.action_queue_drops += sum(e.kind=='due_disconnected_drop' for e in self.action_queue_last.events)
                result = {'Durum':self.action_queue_last.status,'Kalan kayıt':len(self.action_queue.records),
                          'Yerel çağrı planları':self.action_queue_send_plans,
                          'Gönderilmeden silinen':self.action_queue_drops,
                          'Sunucu onayı':False,'Kaynak':'Sentetik bağlantı kapısı ve sentetik helper dönüşü'}
            elif case == 'Görev Alma':
                result = plan_take_quest([QuestRecord('Deneme NPC', b'deneme')],
                    QuestSnapshot(selected_index=0, record_index_from_row=0,
                                  npc_id_465960=1 if self.ready.get() else 0,
                                  npc_pointer_464a10=0x100000, distance=float(values['distance']),
                                  current_target_462630=0, record_data_20=0,
                                  quest_lookup_4d642c=values['item_id']))
            elif case == 'Hedef Seçimi':
                if self.configuration_reader is None:raise ValueError('Panel ayar kaynağı bağlanmadı')
                panel_values,panel_lists=self.configuration_reader()
                self.target_compiled=compile_target_configuration(panel_values,panel_lists,
                    raw_pool_selector=None if self.target_pool.get()=='Panel' else int(self.target_pool.get()),previous_mode=self.target_previous_mode)
                if self.target_compiled.mode is not None:self.target_previous_mode=self.target_compiled.mode
                if self.target_compiled.status=='helper_branch_mode':
                    identifier=values['item_id']
                    obs=TargetBranchObservation(1,0,(identifier,identifier,identifier),
                        0x100000 if self.ready.get() else 0,1 if self.ready.get() else 0,autoz_state=1)
                    if self.target_compiled.mode==4:
                        active=compile_bot_combat(panel_values)
                        obs=LeaderTargetObservation(1,0,2,2,0x110000,identifier,
                            0x100000 if self.ready.get() else 0,
                            0 if active.target_range>=values['distance'] else 1,values['hp_max'],values['hp'])
                    self.target_branch_last=plan_target_branch(self.target_compiled.mode,obs)
                    result=self.target_branch_last
                elif self.target_compiled.settings is None:result=self.target_compiled
                else:
                    if self.target_resolver is None:self.target_resolver=TargetResolver(self.target_compiled.settings)
                    else:self.target_resolver.settings=self.target_compiled.settings
                    distance=values['distance'];identifier=values['item_id']
                    a=ResolverCandidate('fixture-A',identifier,'Worm',distance,distance,
                        visibility=self.ready.get(),repeated_visibility=self.ready.get())
                    b=ResolverCandidate('fixture-B',identifier+1,'Ape',distance+2,distance+2,
                        visibility=self.ready.get(),repeated_visibility=self.ready.get())
                    self.target_last=self.target_resolver.tick(self.now_ms,CurrentTargetObservation(0),
                                                               ResolverSnapshot((a,),(b,),True))
                    result=self.target_last
            elif case == 'Sınıf Ailesi':
                job=self.family_job.get()
                if self.configuration_reader is None:raise ValueError('Panel ayar kaynağı bağlanmadı')
                panel_values,_=self.configuration_reader()
                config=self.panel_configuration(job) if self.use_class_panel.get() else None
                runtime=None if self.family_runtime.get()=='Panel adayı' else int(self.family_runtime.get())
                guard=None if self.family_normal_guard.get()=='Bilinmiyor' else int(self.family_normal_guard.get())
                active=compile_bot_combat(panel_values,mode_byte_override=runtime)
                self.family_active=active
                flags=config.flags if config else {}
                snapshot=AlternateSnapshot(self.now_ms,locked_561f7e=False,raw_byte_55402c=0,
                    raw_float_554030=-1,guard_fe384=False,guard_46fe90=False,attack_enabled_561f6c=True,
                    target_id_562040=1,target_ready_56204c=True,current_target_462630=1,target_mode_561f64=0,
                    target_raw_byte_554034=0,priest_pointer_a_nonzero=True,priest_pointer_b_nonzero=True,
                    rogue_raw_463fc4=0,warrior_flag_89=flags.get(0x89) if config else False,
                    warrior_stat_462e08=100,mp_4611e0=values['mp'],rogue_flag_0=flags.get(0) if config else False,
                    rogue_flag_1c=flags.get(0x1c) if config else False,configured_interval_ms=active.attack_interval_ms,
                    rogue_minor_interval_ms=config.parameters[8] if config and job=='rogue' else 100,
                    actor_state_554034=0,rogue_minor_actor_state_554034=0,rogue_attack_actor_state_554034=0,
                    warrior_flag_198=flags.get(0x198) if config else False,
                    priest_final_raw_byte_55402c=0,priest_final_raw_float_554030=-1,
                    target_max_hp_positive=True,target_hp_positive=True)
                # Explicit false reply fixture for these existing head models only.
                import ast
                from pathlib import Path
                addresses=set()
                for name in ('job_dispatcher.py','alternate_dispatcher.py'):
                    tree=ast.parse((Path(__file__).parent/name).read_text(encoding='utf-8'))
                    addresses.update(n.value for n in ast.walk(tree) if isinstance(n,ast.Constant)
                        and isinstance(n.value,str) and len(n.value)==8 and all(c in '0123456789abcdef' for c in n.value))
                replies={address:HelperReply(False,False) for address in addresses}
                self.family_last=self.family_runner.tick(job,panel_values,snapshot,runtime_byte=runtime,
                    blocked_74=not self.ready.get(),normal_guard_45dc44=guard,replies=replies)
                result={'Kaynak':'Yerel aile/baş modeli; sentetik gözlemler',
                        'Seçim':self.family_last.selection,'Baş sonucu':self.family_last.result}
            elif case == 'Warrior Provoke':
                if self.use_class_panel.get():
                    config=self.panel_configuration('warrior')
                    settings=warrior_provoke_settings(config);flags=config.flags
                else:
                    settings=WarriorProvokeSettings(True,values['wait'],values['quantity'],values['price'])
                    flags={row[0]:True for row in PROVOKE_ROWS}
                self.provoke_settings=settings
                replies={(flag,'00464490',skill):False for flag,skill,*_ in PROVOKE_ROWS}
                replies.update({(flag,'004655e8',skill):self.ready.get() for flag,skill,*_ in PROVOKE_ROWS})
                self.provoke_last=replay_warrior_provoke(ProvokeSnapshot(self.now_ms&0xffffffff,flags,
                    {'00462e34':100,'00462e08':100},values['mp'],settings.window_seconds,
                    settings.start_delay_seconds,settings.skill_delay_seconds,settings.enabled,0,replies),self.provoke_state)
                self.provoke_state=self.provoke_last.state;result=self.provoke_last
            elif case == 'Rogue Combo Zinciri':
                self.attack_lock_last=plan_callback_attack_unlock(self.attack_lock_state,
                    CallbackQueueGate(1 if self.ready.get() else 0,1,0,0,1),
                    LockCallbackObservation(0,0,0,0,{h:True for h in ('00458c70','004c79a0','0045a4dc')}),
                    self.now_ms&0xffffffff)
                if self.attack_lock_last.complete:self.attack_lock_state=self.attack_lock_last.state
                config=self.panel_configuration('rogue') if self.use_class_panel.get() else None
                active=self.bot_combat_settings() if config is not None else None
                self.combo_config=compile_combo_panel(self.configuration_reader()[0]) if config is not None else ComboPanelConfiguration(True,False,False)
                combo=self.combo_config
                flags=dict(config.flags) if config is not None else {r.flag_offset:True for r in BOW_ROWS}
                if config is None:flags.update({0x91:True,0x89:True})
                ranges=rogue_alternate_bow_ranges(config) if config is not None else RogueAlternateBowRanges(8,8,8)
                source=RogueSnapshot(self.now_ms&0xffffffff,float(values['distance']),active.attack_range if active else 8,
                    values['mp'],flags,{'00462ddc':100,'00462670':100})
                head=AlternateSnapshot(now_ms=self.now_ms,locked_561f7e=not self.ready.get() or bool(self.attack_lock_state.byte),
                    raw_byte_55402c=0,raw_float_554030=0,actor_state_554034=0,
                    rogue_flag_0=False,attack_enabled_561f6c=True,guard_fe384=False,guard_46fe90=False,
                    target_id_562040=values['item_id'],target_ready_56204c=True,
                    current_target_462630=values['item_id'],target_mode_561f64=1,target_raw_byte_554034=0,
                    rogue_raw_463fc4=1)
                clocks={k:self.now_ms&0xffffffff for k in ('start','wait1','stage3','wait4','after4','wait5','wait6','after6','noncombo6','wait7')}
                obs=ComboObservation(self.attack_lock_state.byte,0,0x40,combo.w_byte,combo.s_byte,combo.run_byte,
                    distance_vs_one_ah=1 if values['distance']<1 else 0x40 if values['distance']==1 else 0,
                    helper_464564=0,actor_state=0,
                    interval_ms=active.attack_interval_ms if active else 1000,clocks=clocks,
                    helper_completed={k:True for k in ('pattern','reset','first','second')})
                helpers={r.skill_number:0 for r in BOW_ROWS};helpers.update({0x22b:0,0x203:0,8:0})
                self.rogue_chain_last=replay_rogue_chain(head,obs,state=self.rogue_chain_state,
                    replies={h:HelperReply(False,False) for h in ('004da2d4','004da568','004da784')},
                    selector_snapshot=source,selector_ranges=ranges,
                    selector_observation=AlternateBowObservation(combo.w_byte,combo.s_byte,target_id=values['item_id'],send_return=1,
                        prefix_first=102,helper_returns=helpers))
                self.rogue_chain_state=self.rogue_chain_last.state
                if self.rogue_chain_last.combo is not None and self.rogue_chain_last.combo.complete:
                    self.attack_lock_state=apply_lock_write_plans(self.attack_lock_state,self.rogue_chain_last.combo.local_writes)
                result={'Kilit modeli':self.attack_lock_last,'Zincir':self.rogue_chain_last,'Yerel kilit':self.attack_lock_state}
            elif case.endswith(' Alternatif'):
                snapshot = AlternateSnapshot(now_ms=self.now_ms,
                    locked_561f7e=not self.ready.get(), raw_byte_55402c=0, raw_float_554030=0,
                    actor_state_554034=0, attack_enabled_561f6c=True,
                    guard_fe384=False, guard_46fe90=False, target_id_562040=1,
                    current_target_462630=1, target_ready_56204c=True,
                    target_mode_561f64=0, target_raw_byte_554034=0,
                    warrior_flag_198=False, rogue_flag_0=False, rogue_raw_463fc4=0,
                    rogue_minor_actor_state_554034=0, rogue_attack_actor_state_554034=0,
                    priest_final_raw_byte_55402c=0, priest_final_raw_float_554030=0,
                    target_max_hp_positive=True, target_hp_positive=True)
                replies = {h: HelperReply(False, False) for h in
                           ('00499b88', '00499620', '004994bc', '00471c38', '00472b90',
                            '0050269c', '004cf8b8', '004d0c18', '004cfc74', '004cee18',
                            '004d20b0', '004d0434', '004da25c', '004da2d4', '004da568',
                            '004da784', '004dd2e0')}
                result = dispatch_alternate(case.split()[0].lower(),
                                            snapshot, self.alternate_state, replies)
                self.alternate_state = result.state
            elif case == 'Warrior Saldırı':
                configured_range=self.bot_combat_settings().attack_range if self.use_class_panel.get() else 8
                result = select_warrior_skill(WarriorSkillSnapshot(self.now_ms,
                    float(values['distance']), configured_range, values['mp'], self.attack_flags('warrior', WARRIOR_ROWS),
                    {k: 100 for k in ('00462ddc', '00462e08', '00462e34', '00462e60', '00462670')},
                    self.warrior_attack_timers))
                if result.local_timer_update is not None:
                    offset, value = result.local_timer_update
                    self.warrior_attack_timers[offset] = value
            elif case == 'Mage Saldırı':
                configured_range=self.bot_combat_settings().attack_range if self.use_class_panel.get() else 8
                result = select_mage_attack(MageAttackSnapshot(self.now_ms,
                    float(values['distance']), configured_range, values['mp'], self.attack_flags('mage', MAGE_ATTACK_ROWS),
                    {k: 100 for k in ('00462ddc', '00462e08', '00462e34', '00462670')},
                    self.mage_attack_timers, locked_561f7e=not self.ready.get(),
                    raw_field_55403c_nonzero=False, raw_field_554020_nonzero=False))
                self.mage_attack_timers.update(result.local_timer_updates)
            elif case in ('Kurian Saldırı','Kurian Özel','Kurian Döngü'):
                rows=KURIAN_ATTACK_ROWS+KURIAN_SPECIAL_ROWS
                active=self.bot_combat_settings() if self.use_class_panel.get() else None
                helpers={'00464490:%x'%row.skill_number:False for row in rows}
                helpers.update({'004655e8:%x'%row.skill_number:True for row in rows})
                source=RogueSnapshot(self.now_ms&0xffffffff,float(values['distance']),active.attack_range if active else 8,
                    values['mp'],self.attack_flags('kurian',rows),
                    {'00462ddc':100,'00462e34':100,'00462670':100,'preparation.3c_dword':0},
                    locked_561f7e=not self.ready.get(),helper_bools=helpers)
                if case=='Kurian Döngü':
                    self.combo_config=compile_combo_panel(self.configuration_reader()[0]) if active is not None else ComboPanelConfiguration(False,False,False,True)
                    settings=self.combo_config
                    cycle=KurianCycleSnapshot(self.now_ms&0xffffffff,float(values['distance']),
                        active.attack_range if active else 8,not self.ready.get(),settings.r_attack,
                        settings.w_combo,settings.s_combo,target_462630=values['item_id'])
                    self.kurian_cycle_last=replay_kurian_cycle(cycle,source,self.kurian_cycle_state)
                    self.kurian_cycle_state=self.kurian_cycle_last.cycle.state
                    result=self.kurian_cycle_last
                else:
                    result=select_kurian_special(source) if case=='Kurian Özel' else select_kurian_attack(source)
                    self.kurian_attack_last=result
            elif case in ('Rogue Yakın', 'Rogue Yay', 'Rogue Özel', 'Rogue Çoklu', 'Rogue Alternatif Yay'):
                rows = MELEE_ROWS + BOW_ROWS + SPECIAL_ROWS
                config=self.panel_configuration('rogue') if self.use_class_panel.get() else None
                flags = dict(config.flags) if config is not None else dict(self.attack_flags('rogue', rows))
                if not self.use_class_panel.get():
                    flags.update({0x89: True, 0x91: True})
                active=self.bot_combat_settings() if config is not None else None
                snapshot = RogueSnapshot(self.now_ms, float(values['distance']), active.attack_range if active else 8,
                    values['mp'], flags,
                    {k: 100 for k in ('00462ddc', '00462e08', '00462670')},
                    self.rogue_attack_timers, locked_561f7e=not self.ready.get(),
                    alternate_561f88=active.legal_mode if active else False, timestamp_5620a4_5620a8=0,
                    helper_bools={'00463924:160ddbd8': True}, raw_skill_prefix_46256c=102)
                if case == 'Rogue Alternatif Yay':
                    ranges=rogue_alternate_bow_ranges(config) if config is not None else RogueAlternateBowRanges(8,8,8)
                    self.alternate_bow_ranges=ranges
                    self.combo_config=compile_combo_panel(self.configuration_reader()[0]) if config is not None else ComboPanelConfiguration(True,False,False)
                    helpers={r.skill_number:0 for r in BOW_ROWS};helpers.update({0x22b:0,0x203:0,8:0})
                    result=plan_alternate_bow(snapshot,ranges,AlternateBowObservation(self.combo_config.w_byte,
                        self.combo_config.s_byte,0,prefix_first=102,helper_returns=helpers))
                    self.alternate_bow_last=result
                elif case == 'Rogue Yakın':
                    result = select_rogue_melee(snapshot)
                elif case == 'Rogue Yay':
                    result = select_rogue_bow(snapshot)
                elif case == 'Rogue Özel':
                    result = select_rogue_special(snapshot)
                else:
                    ranges=rogue_volley_ranges(config) if config is not None else None
                    self.volley_ranges=ranges
                    result = plan_rogue_volley(snapshot, active.attack_interval_ms if active else 1000, range_10=ranges.triple if ranges else 8,
                                               range_14=ranges.quintuple if ranges else 8,
                                               client_variant_553e46=1, flag_553e44=False)
                    self.volley_last=result
                if case != 'Rogue Alternatif Yay':
                    self.rogue_attack_timers.update(result.local_timer_updates)
            elif case == 'Priest Saldırı':
                configured_range=self.bot_combat_settings().attack_range if self.use_class_panel.get() else 8
                result = select_priest_attack(PriestAttackSnapshot(self.now_ms,
                    float(values['distance']), configured_range, values['mp'],
                    self.attack_flags('priest', PRIEST_ATTACK_ROWS),
                    {k: 100 for k in ('00462ddc', '00462e08', '00462e34', '00462e60', '00462670')},
                    self.priest_attack_timers, locked_561f7e=not self.ready.get()))
                for offset, value in result.local_timer_updates:
                    self.priest_attack_timers[offset] = value
            elif case in ('Priest', 'Rogue Minor', 'Kurian', 'Mage TP'):
                panel_support = None
                if self.use_class_panel.get():
                    job={'Priest':'priest','Rogue Minor':'rogue','Kurian':'kurian','Mage TP':'mage'}[case]
                    panel_support=support_settings_from_config(self.panel_configuration(job))
                actor = Vitals(1, values['hp'], values['hp_max'], values['mp'])
                members = (PartyMember(Vitals(2, values['hp'], values['hp_max']), mage_eligible=self.ready.get()),) if case == 'Mage TP' else ()
                snapshot = SupportSnapshot(self.now_ms, actor, members=members,
                    party_count=2 if members else 1, party_complete=True,
                    global_blocked=False, route_guard_active=False, alternate_action_path=False,
                    self_heal_ready=self.ready.get(), minor_action_ready=self.ready.get(),
                    kurian_action_ready=self.ready.get(), tp_action_ready=self.ready.get(),
                    unnamed_stat=10 if case=='Mage TP' else 5,
                    last_self_heal_ms=self.last_self_ms, last_minor_ms=self.last_minor_ms)
                if case == 'Priest':
                    self.support_settings=panel_support or PriestSettings(self_enabled=True,
                        self_threshold=values['threshold'], self_skill_id=values['item_id'])
                    result = priest_heal(self.support_settings, snapshot)
                elif case == 'Rogue Minor':
                    self.support_settings=panel_support or MinorSettings(enabled=True, threshold=values['threshold'])
                    result = rogue_minor(self.support_settings, snapshot)
                elif case == 'Kurian':
                    self.support_settings=panel_support or KurianSettings(True, values['threshold'])
                    result = kurian_heal(self.support_settings, snapshot)
                else:
                    self.support_settings=panel_support or MageSettings(low_hp_tp=True, threshold=values['threshold'])
                    result = mage_tp(self.support_settings, snapshot)
                self.support_last=result
                if result.consumes_retry:
                    if case == 'Priest':
                        self.last_self_ms = self.now_ms
                    elif case == 'Rogue Minor':
                        self.last_minor_ms = self.now_ms
            else:
                if self.use_class_panel.get():
                    self.mining_compiled=compile_mining_panel(self.configuration_reader()[0],
                        previous_start_mode=self.mining_previous_start,previous_speed_mode=self.mining_previous_speed,
                        manual_route_ansi=self.panel_route_sample('Mine',ansi=True))
                    self.mining_previous_start=self.mining_compiled.fields.get(0x5ff8)
                    self.mining_previous_speed=self.mining_compiled.fields.get(0x6048)
                    configuration=self.mining_compiled
                else:configuration=MiningPanelConfiguration('local_fixture',
                    {0x6029:1,0x602c:values['wait'],0x6035:0,0x604c:0,0x6030:1,0x6034:0,
                     0x603c:1,0x6040:30,0x6047:0,0x603b:0,0x6038:0,0x6039:0,
                     0x6036:0,0x6028:0,0x6037:0,0x5ff8:1,0x6044:0,0x6045:0,0x6046:0})
                self.mining.config=mining_runner_configuration(configuration)
                self.mining_ore_settings=mining_ore_settings(configuration)
                outer=MiningSnapshot(blocked_561f7e=bool(self.mining_speed_values[0x561f7e]));ore=None
                if self.mining_fixture.get():
                    if not 0<=values['quantity']<=28:raise ValueError('Sentetik ore sayısı0–28 olmalı')
                    outer=MiningSnapshot(comparison_505118=self.ready.get(),helper_479988_result=True,
                        fallback_coordinate_selected=True,distance_outer=values['distance'],distance_inner=values['distance'],
                        helper_465960_target_id=values['item_id'],helper_477770_count=values['quantity'],
                        helper_464a10_result=True,distance_ore=values['distance'],job_568dbc_active=False,
                        storage_5690b8_active=False,storage_5690cc_value=48,
                        blocked_561f7e=bool(self.mining_speed_values[0x561f7e]))
                    ore=OreSlotSnapshot(self.ready.get(),self.mining_ws_zero.get(),self.mining_request_zero.get())
                # A fresh explicit execution snapshot owns the shared index.
                state=MiningPipelineState(self.mining_state,replace(self.mining_ore_state,item_index=self.mining_state.item_index))
                name_observation=None
                if self.mining_name_fixture.get():
                    kind=self.mining_name_kind.get()
                    names={'Ore':ORE_NAME,'Gold':GOLD_NAME,'Boş yuva':b'','Diğer':b'Changed item'}
                    if kind not in names:raise ValueError('Geçerli sentetik isim seçimi gerekli')
                    name=names[kind];size=max(16,len(name))
                    name_observation=SlotNameObservation(0x100,0x20,0x30,0x200,0x300,
                        0 if kind=='Boş yuva' else 0x400,0x500,0x600,123000,456,
                        ItemNameObservation(metadata_category=3,storage_dword=size,pointer_dword=0x700,
                            bad_read_result=0,captured=name.ljust(size,b'\0')))
                scheduler={}
                tick=self.now_ms&0xffffffff
                if self.mining_scheduler_fixture.get():
                    scheduler=dict(active_initial=1,dead=int(self.mining_dead.get()),death_qword=1,
                        respawn_wait_tick=tick,respawn_retry_tick=tick,
                        respawn_retry_qword=self.mining_scheduler_times[0x553df0],respawn_stamp_tick=tick,
                        merchant_after_speed=0,mining_after_merchant=int(self.mining_maintenance_active.get()),
                        route_after_mining=int(self.mining_post_route.get() if self.mining_maintenance_active.get() else self.mining_state.route_active),
                        active_after_route=1,mining_after_route=0,
                        **{'returned:004c8d48':True})
                speed=None
                if self.mining_speed_fixture.get():
                    family=self.mining_speed_family.get()
                    if family not in ('Rogue','Warrior','Diğer'):raise ValueError('Geçerli hız örnek sınıfı gerekli')
                    speed=dict(lock_561f7e=self.mining_speed_values[0x561f7e],dead_561f6f=int(self.mining_dead.get()),
                        ready_561f6e=1,blocked_561f70=0,merchant_568d81=0,route_5f54=int(self.mining_state.route_active),
                        actor_gate_initial=1,rogue_predicate_505d20=int(family=='Rogue'),warrior_predicate_505d20=int(family=='Warrior'),
                        class_1=101,class_2=101,class_3=101,stat_462670=100,stat_462e34=100,
                        gate_464490=0,buff_1=0,buff_2=0,buff_3=0,retry_tick=tick,
                        retry_qword=self.mining_speed_values[0x553de8],retry_stamp_tick=tick,
                        actor_462650=1,actor_gate_refresh=0,target_462630_first=0,target_gate_45dc44=0,
                        cast_result=int(self.mining_speed_success.get()),lock_stamp_tick=tick,
                        **{'returned:004655e8':True})
                if self.mining_maintenance_active.get():
                    state=MiningPipelineState(replace(state.execution,route_active=self.mining_post_route.get()),state.ore)
                frame_state=MiningFrameState(state,self.mining_request_queue)
                maintenance=None
                if self.mining_maintenance_fixture.get():
                    case_name=self.mining_maintenance_case.get()
                    if case_name not in ('Boş','Kazma','Hammer','Hammer yok','Dolu','Onarım EMC','Onarım Luferson','Onarım Moradon'):raise ValueError('Geçerli bakım örneği gerekli')
                    maintenance=dict(storage_5690b8=self.mining_maintenance_values[0x5690b8],
                        storage_helper_4fe384=0,inn_helper_46fe90=0,
                        mattock_first_equal=int(case_name=='Kazma'),mattock_second_equal=0,
                        change_item_4634a4=1,change_quantity_46358c=0,replacement_slot_477544=14,
                        hammer_item_4634a4=int(case_name in ('Hammer','Hammer yok')),hammer_quantity_46358c=0,
                        magic_hammer_present_463950=int(case_name!='Hammer yok'),hammer_gate_4631a8=0,
                        hammer_tick=tick,hammer_qword=self.mining_maintenance_values[0x553de0],
                        hammer_actor_462650=1,hammer_stamp_tick=tick,
                        full_463ac0=int(case_name=='Dolu'),vip_tick=tick,vip_qword=self.mining_maintenance_values[0x5690d0],
                        ore_count_477770=values['quantity']&0xffffffff,
                        repair_item_4634a4=int(case_name.startswith('Onarım')),repair_quantity_46358c=0,
                        repair_hammer_tick=tick,repair_hammer_qword=self.mining_maintenance_values[0x553de0],
                        repair_region_1_equal=int(case_name=='Onarım EMC'),repair_region_2_equal=int(case_name=='Onarım Luferson'),
                        repair_region_3_equal=int(case_name=='Onarım Moradon'),repair_distance_fpu_ah=0x40,
                        repair_use_constructor_defaults=1,tail_gate_4631a8=1,
                        **{'returned:'+a:True for a in ('004651bc','00465640','00464d10','00404260','0040ae0c',
                            '004ebca0','004eb9f4')})
                post_lock_text=self.mining_post_lock.get()
                if post_lock_text not in ('Bilinmiyor','0','1'):raise ValueError('Geçerli bakım sonrası kilit örneği gerekli')
                frame_observation=MiningFrameObservation(scheduler,MiningPipelineObservation(outer,ore),name_observation,
                    (QueueSample(tick,1),QueueSample(tick,1)),speed,maintenance,
                    None if post_lock_text=='Bilinmiyor' else int(post_lock_text),
                    self.mining_effect_observation(tick),self.mining_effect_observation(tick))
                self.mining_callback_last=None
                bound_control=self.mining_control_enabled.get() or self.mining_interlude_enabled.get()
                if self.mining_callback_fixture.get() or bound_control:
                    lock=AttackLockState(self.mining_speed_values[0x561f7e],
                        self.mining_speed_values[0x561f80],self.mining_speed_values[0x561f84])
                    gate=CallbackQueueGate(1,1,0,0,1)
                    completed={a:True for a in ('00458c70','004c79a0','0045a4dc','004ff918','00470a94')}
                    bound_inputs=None;control_state=None;interlude_observation=None;interlude_state=None
                    if bound_control:
                        # The earlier helpers are still synthetic normal returns.
                        # Control itself is supplied by the complete local model.
                        prefix=LockCallbackObservation(self.mining_maintenance_values[0x5690b8],0,0,1,completed)
                        bound_inputs=self.mining_control_inputs();control_state=self.mining_control_state
                        control_preview=replay_control_callback(ControlCallbackState(lock,control_state),gate,prefix,bound_inputs,tick)
                        if control_preview.status=='needs_timer_lock_observation':
                            bound_inputs=replace(bound_inputs,timer_lock=self.mining_lock_observation(self.mining_control_timer_lock))
                            control_preview=replay_control_callback(ControlCallbackState(lock,control_state),gate,prefix,bound_inputs,tick)
                        segment_return=post_lock=post_mode=None
                        if control_preview.complete and control_preview.unlock.timer_reached:
                            segment_ready=False
                            if self.mining_interlude_enabled.get():
                                sample=parse_interlude_sample(self.mining_interlude_json.get())
                                if not self.mining_interlude_seeded:
                                    self.mining_interlude_state=sample.initial_state or CallbackInterludeState()
                                    self.mining_interlude_seeded=True
                                interlude_state=self.mining_interlude_state;interlude_observation=sample.observation
                                segment_ready=replay_callback_interlude(interlude_state,interlude_observation).complete
                            else:
                                segment_return=True if self.mining_control_segment_return.get() else None
                                segment_ready=segment_return is True
                            if segment_ready:
                                post_lock=self.mining_lock_observation(self.mining_control_post_lock)
                                if post_lock is not None:
                                    mode_text=self.mining_control_post_mode.get().strip()
                                    post_mode=int(mode_text) if mode_text else None
                    else:
                        prefix=LockCallbackObservation(self.mining_maintenance_values[0x5690b8],0,0,1,
                            {**completed,'00458f98':True})
                        # Legacy explicit closed-world fixture: opaque segment
                        # is declared returned and preserves the timer result.
                        preview=plan_callback_attack_unlock(lock,gate,prefix,tick)
                        segment_return=True;post_lock=preview.state;post_mode=2
                    if post_lock is not None:
                        frame_observation=replace(frame_observation,pipeline=replace(frame_observation.pipeline,
                            outer=replace(frame_observation.pipeline.outer,blocked_561f7e=bool(post_lock.byte))))
                    self.mining_callback_last=replay_mining_callback(configuration,
                        MiningCallbackState(lock,frame_state,control_state,interlude_state),
                        MiningCallbackObservation(gate,prefix,tick,segment_return,post_lock,post_mode,frame_observation,bound_inputs,interlude_observation),self.now_ms)
                    self.mining_frame_last=self.mining_callback_last.frame
                else:self.mining_frame_last=replay_mining_frame(configuration,frame_state,frame_observation,self.now_ms)
                self.mining_pipeline_last=self.mining_frame_last.pipeline if self.mining_frame_last else None
                self.mining_last=self.mining_pipeline_last.outer if self.mining_pipeline_last else None
                self.mining_name_request_last=self.mining_frame_last.request if self.mining_frame_last else None
                self.mining_queue_last=self.mining_frame_last.queue if self.mining_frame_last else None
                self.mining_local_complete=(self.mining_callback_last or self.mining_frame_last).complete
                self.mining_repair_route_last=(self.mining_frame_last.maintenance.repair_route
                    if self.mining_frame_last and self.mining_frame_last.maintenance else None)
                if self.mining_local_complete:
                    accepted=self.mining_callback_last.state.frame if self.mining_callback_last else self.mining_frame_last.state
                    self.mining_state=accepted.pipeline.execution
                    self.mining_ore_state=accepted.pipeline.ore
                    self.mining_request_queue=accepted.queue
                    if self.mining_frame_last:
                        for address,low,high in self.mining_frame_last.scheduler.writes:
                            self.mining_scheduler_times[address]=low|(high<<32)
                        if self.mining_frame_last.speed is not None:
                            for address,value,width in self.mining_frame_last.speed.writes:
                                self.mining_speed_values[address]=value
                        if self.mining_frame_last.maintenance is not None:
                            for address,value,width in self.mining_frame_last.maintenance.writes:
                                self.mining_maintenance_values[address]=value
                            if frame_observation.post_maintenance_lock_byte is not None:
                                self.mining_speed_values[0x561f7e]=frame_observation.post_maintenance_lock_byte
                        effect=self.mining_frame_last.maintenance_effect
                        if effect is not None and effect.start is not None and effect.complete:
                            self.mining_maintenance_active.set(False) # source global561f6c=0, own fixture only
                    if self.mining_callback_last:
                        lock=self.mining_callback_last.state.lock
                        self.mining_speed_values.update({0x561f7e:lock.byte,0x561f80:lock.duration_ms,0x561f84:lock.started_ms})
                        if bound_control:self.mining_control_state=self.mining_callback_last.state.control
                        if self.mining_interlude_enabled.get():self.mining_interlude_state=self.mining_callback_last.state.interlude
                result={'Maden paneli':configuration,'Callback/maden planı':self.mining_callback_last or self.mining_frame_last,
                    'Bekleyen yerel tampon':len(self.mining_request_queue.records)}
            if case in ('Warrior Saldırı','Mage Saldırı','Priest Saldırı','Rogue Yakın','Rogue Yay','Rogue Özel','Rogue Çoklu','Rogue Alternatif Yay'):
                self.attack_last=result
            self.write('%d ms • %s' % (self.now_ms, self.describe(result)))
        except (ValueError, TypeError, OSError) as error:
            self.write('Deneme değeri geçersiz: ' + str(error))

    def party_example(self):
        self.party_packet.set('2f02ffff0500416c696365')
        self.party_sample.set(example_invitation_sample())

    def chat_party_example(self):
        self.chat_party_trial.reset()
        self.chat_party_packet.set(EXAMPLE_CHAT_HEX)
        self.chat_party_sample.set(example_chat_party_sample())

    def chat_skills_example(self):
        self.chat_skills_trial.reset()
        self.chat_skills_packet.set(EXAMPLE_SKILL_HEX)
        self.chat_skills_sample.set(example_chat_skills_sample(self.chat_skills_example_family.get()))

    def chat_commands_example(self):
        self.chat_commands_trial.reset()
        self.chat_commands_detailed.set(False)
        self.chat_commands_packet.set(EXAMPLE_COMMAND_HEX)
        self.chat_commands_sample.set(example_chat_commands_sample())

    def chat_commands_detailed_example(self):
        self.chat_commands_trial.reset()
        self.chat_commands_detailed.set(True)
        self.chat_commands_packet.set(EXAMPLE_COMMAND_HEX)
        self.chat_commands_sample.set(example_detailed_commands_sample())

    def describe(self, value):
        if value is None:
            return 'İşlem kararı yok.'
        if isinstance(value, Enum):
            return str(value.value)
        if is_dataclass(value):
            value = {part.name:getattr(value,part.name) for part in dataclass_fields(value)}
        if isinstance(value, Mapping):
            return ' • '.join('%s: %s' % (key, self.describe(part)) for key, part in value.items()
                              if part is not None and part != () and key not in ('records', 'source_address'))
        if isinstance(value, (list, tuple)):
            return '; '.join(self.describe(part) for part in value)
        return str(value)
