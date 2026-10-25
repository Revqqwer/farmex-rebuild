"""Native configuration panel reconstructed from the recorded form hierarchy."""
import copy
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from dataclasses import replace
from name_list_controls import LIST_PATHS,TEXT_PATHS,BUTTON_ACTIONS,edit_name_list
from name_cfg_codec import NameCfgDocument,NameCfgCodecResult,read_name_cfg,write_name_cfg,local_codepage
from route_catalog import ROUTE_COMBO_PATHS
import flood_editor
from flood_compilation import compile_flood_rows
from name_codec import WindowsNameCodec
from flood_runtime import OwnedFloodSession,TOGGLE_PATH,windows_tick_count
from flood_selected import OwnedSelectedMessageFrame,BUTTON_PATH as FLOOD_SELECTED_BUTTON
from merchant_results_session import (OwnedMerchantResults, FILTER_PATHS as MERCHANT_FILTER_PATHS,
    KIND_PATH as MERCHANT_KIND, CATEGORY_PATH as MERCHANT_CATEGORY,
    SEARCH_PATH as MERCHANT_SEARCH, TABLE_PATH as MERCHANT_TABLE,MerchantTableUpdate)
from merchant_search_field import plan_search_focus,GRAY_TEXT
from merchant_text_normalization import WindowsMerchantText
from merchant_cell_runtime import OwnedMerchantCells
import merchant_scan_runtime as scan_runtime
from merchant_scan_loop import OwnedMerchantScanLoop,ScanLoopInput,OWN_TIMER_PERIOD_MS
from merchant_txt_export import export_displayed_txt,BUTTON_PATH as MERCHANT_EXPORT_BUTTON
from merchant_quick_table import prepare_quick_table
import item_break_manual_runtime as manual_break_runtime
import item_break_auto_runtime as auto_break_runtime
from item_break_settings import ITEM_BREAK_FIELDS
import route_panel_runtime as route_panel_runtime
import route_save_runtime
import route_load_runtime
import route_command_runtime
import route_coordinate_click as coordinate_click
import manual_coordinate_runtime as manual_coordinate_runtime
from manual_coordinate import BUTTON_PATH as MANUAL_COORDINATE_BUTTON
import route_npc_click as npc_click
from route_npc_source import NpcSourceFrame
from route_gate_runtime import OwnedGateRecording,OWN_TIMER_PERIOD_MS as GATE_RECORD_TIMER_MS
import upgrade_editor
from upgrade_refresh import UpgradeRefreshFrame
from upgrade_parameter_frame import UpgradeParameterFrame,UpgradeParameterState
from upgrade_start_frame import UpgradeStartFrame
from operation_engine import UpgradeRunner
from upgrade_worker import OwnedUpgradeWorker,UpgradeWorkerContext
from armor_start_frame import ArmorStartFrame
from armor_start import COMBO_PATH as ARMOR_COMBO_PATH
import upgrade_parameter_ui as parameter_ui
from source_route_save import write_source_route_rows
import quest_metadata
import quest_refresh
import quest_details
import quest_action
import quest_action_worker
from quest_collection import QuestCollection
from quest_row import QuestRow,QuestRowSink
from quest_list_emit import QuestNpcSink

SOURCE_ROUTE_LIST='frmMain/RotaPanel/lstRota'
SOURCE_ROUTE_CLEAR='frmMain/RotaPanel/Button122'
SOURCE_ROUTE_DELETE='frmMain/RotaPanel/Button48'


class ConfigurationPanel:
    def __init__(self, frame, catalog, profiles, values, lists):
        self.catalog, self.profiles = catalog, profiles
        self.values, self.lists = values, lists
        self.forms = [n for n in catalog if '/' not in n['path']]
        self.widgets, self.variables, self.radio_variables = {}, {}, {}
        self.button_handlers={}
        self.source_quest_refresh_provider=None;self.source_quest_refresh_pending=None
        self.source_quest_refresh_state=None;self.source_quest_refresh_result=None
        self.source_quest_refresh_generation=0;self.source_quest_refresh_ticket=0
        self.source_quest_refresh_after_id=None;self.source_quest_refresh_stepping=False
        self.source_quest_npc_items=None;self.source_quest_refresh_projection=None
        self.source_quest_refresh_error=None
        self.source_quest_filter_provider=None;self.source_quest_refresh_operation=None
        self.source_quest_details_provider=None;self.source_quest_details_state=None
        self.source_quest_details_projection=None;self.source_quest_details_painted_headings=None
        self.source_quest_action_provider=None
        for path,method in quest_action_worker.METHODS.items():
            self.button_handlers[path]=lambda m=method:self.start_source_quest_action(m)
        self.button_handlers[quest_refresh.BUTTON_PATH]=self.start_source_quest_refresh
        self.source_quest_provider=None;self.source_quest_pending=[];self.source_quest_result=None
        self.source_quest_generation=0;self.source_quest_invocation=0
        self.source_quest_after_id=None;self.source_quest_stepping=False
        for path,method in quest_metadata.METHODS.items():
            self.button_handlers[path]=lambda m=method:self.start_source_quest(m)
        self.route_panel=route_panel_runtime.OwnedRoutePanel()
        self.route_panel_update=None
        for node in catalog:
            if node['properties'].get('OnClick')=='Button21Click':
                self.button_handlers[node['path']]=self.open_source_route_panel
        self.button_handlers[route_panel_runtime.CLOSE_PATH]=self.close_source_route_panel
        self.button_handlers[SOURCE_ROUTE_CLEAR]=lambda:self.edit_source_route_rows('clear')
        self.button_handlers[SOURCE_ROUTE_DELETE]=lambda:self.edit_source_route_rows('delete_selected')
        self.route_list_edit_result=None
        self.button_handlers[route_save_runtime.BUTTON_PATH]=self.save_source_route
        self.route_save_context_reader=None
        self.route_save_writer=write_source_route_rows
        self.route_save_result=None
        self.route_load_result=None
        self.route_load_reader_factory=route_load_runtime.WindowsRouteReader
        self.route_command_result=None
        self.source_coordinate_provider=None;self.source_coordinate_pending=[]
        self.source_coordinate_result=None;self.source_coordinate_generation=0;self.source_coordinate_invocation=0
        self.source_coordinate_after_id=None;self.source_coordinate_stepping=False
        self.button_handlers[coordinate_click.BUTTON_PATH]=self.start_source_coordinate
        self.manual_coordinate=manual_coordinate_runtime.OwnedManualCoordinate(lambda:self.values)
        self.manual_coordinate_provider=None;self.manual_coordinate_after_id=None
        self.button_handlers[MANUAL_COORDINATE_BUTTON]=self.start_manual_coordinate
        self.source_npc_provider=None;self.source_npc_pending=[]
        self.source_npc_result=None;self.source_npc_generation=0;self.source_npc_invocation=0
        self.source_npc_after_id=None;self.source_npc_stepping=False
        self.source_npc_dialog=self.ask_source_npc_dialog
        self.source_npc_notice=lambda:messagebox.showwarning('NPC Secilmedi !',
            'Rotaya eklemek için oyun içinde NPC seçmelisiniz.',parent=self.canvas)
        self.button_handlers[npc_click.BUTTON_PATH]=self.start_source_npc
        self.source_gates=OwnedGateRecording(lambda:self.source_route_sink(self.values,self.lists),
            lambda:self.values[route_panel_runtime.GATES_PATH])
        self.source_gate_after_id=None
        self.source_upgrade_provider=None;self.source_upgrade_pending=[]
        self.source_upgrade_result=None;self.source_upgrade_generation=0;self.source_upgrade_invocation=0
        self.source_upgrade_after_id=None;self.source_upgrade_stepping=False
        self.source_upgrade_parameter_provider=None;self.source_upgrade_parameter_pending=[]
        self.source_upgrade_parameter_result=None;self.source_upgrade_parameter_invocation=0
        self.source_upgrade_parameter_after_id=None;self.source_upgrade_parameter_stepping=False
        self.source_upgrade_parameter_state=UpgradeParameterState();self.source_upgrade_parameter_text_cache={}
        self.source_upgrade_runner=UpgradeRunner(source_clock=True)
        self.source_upgrade_runner.source_start_ui=(True,False)
        self.source_upgrade_worker=None;self.source_upgrade_worker_provider=None;self.source_upgrade_worker_result=None
        self.source_upgrade_worker_after_id=None;self.source_upgrade_worker_stepping=False;self.source_upgrade_worker_generation=0
        for path,method in upgrade_editor.METHODS.items():
            self.button_handlers[path]=lambda m=method:self.start_source_upgrade_editor(m)
        for path,method in {**route_command_runtime.BUTTON_METHODS,**route_command_runtime.ADVANCED_BUTTON_METHODS}.items():
            self.button_handlers[path]=lambda m=method:self.add_source_route_command(m)
        self.item_break_scalar_state={}
        self.manual_item_break=manual_break_runtime.OwnedManualItemBreak(self.item_break_scalar_state)
        self.manual_item_break_provider=None
        self.manual_item_break_result=None
        self.manual_item_break_after_id=None
        self.manual_item_break_stepping=False
        self.button_handlers[manual_break_runtime.BUTTON_PATH]=self.start_manual_item_break
        self.auto_item_break=auto_break_runtime.OwnedAutoItemBreak(self.item_break_scalar_state)
        self.auto_item_break_provider=None
        self.auto_item_break_result=None
        self.auto_item_break_after_id=None
        self.auto_item_break_stepping=False
        self.merchant_scan=scan_runtime.OwnedMerchantScan()
        self.merchant_scan_update=None
        self.merchant_scan_loop=OwnedMerchantScanLoop()
        self.merchant_scan_provider=None
        self.merchant_scan_after_id=None
        self.merchant_scan_loop_result=None
        self.button_handlers[scan_runtime.START_PATH]=self.start_merchant_scan
        self.button_handlers[scan_runtime.STOP_PATH]=self.stop_merchant_scan
        self.button_handlers[scan_runtime.QUICK_PATH]=self.quick_scan_merchants
        self.merchant_quick_provider=None
        self.merchant_quick_result=None
        self.button_handlers[MERCHANT_EXPORT_BUTTON]=self.export_merchant_txt
        self.merchant_export_context_provider=None
        self.merchant_export_result=None
        self.configure_merchant_scan()
        self.merchant_results=OwnedMerchantResults()
        self.merchant_search_observer=None
        self.merchant_text_factory=WindowsMerchantText
        self.merchant_codepage_reader=local_codepage
        self.merchant_text_policy=None
        self.merchant_result_update=None
        self.merchant_search_color=GRAY_TEXT
        self.flood_edit_result=None
        self.flood_compilation=None
        self.flood_codepage_reader=local_codepage
        self.flood_codec_factory=WindowsNameCodec
        self.flood_session=OwnedFloodSession()
        self.merchant_cells=OwnedMerchantCells(self.flood_session.queue)
        self.merchant_cell_result=None
        self.flood_clock=windows_tick_count
        self.flood_after_id=None
        self.flood_runtime_result=None
        self.flood_selected_result=None
        self.button_handlers[TOGGLE_PATH]=self.toggle_flood_loop
        self.button_handlers[FLOOD_SELECTED_BUTTON]=self.write_selected_flood
        for path,action in flood_editor.BUTTON_ACTIONS.items():
            self.button_handlers[path]=lambda a=action:self.edit_flood_control(a)
        self.route_catalog_reader=None
        self.route_catalog_last=None
        self.route_directory_chooser=None
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', pady=4)
        ttk.Label(toolbar, text='Form:').pack(side='left')
        self.form = tk.StringVar(value='frmMain')
        select = ttk.Combobox(toolbar, textvariable=self.form,
                             values=[n['path'] for n in self.forms], state='readonly', width=23)
        select.pack(side='left', padx=5)
        select.bind('<<ComboboxSelected>>', lambda _: self.render())
        self.job = tk.StringVar(value='Mage')
        ttk.Label(toolbar, text='Sınıf ayarları:').pack(side='left', padx=5)
        job = ttk.Combobox(toolbar, textvariable=self.job,
                          values=['Mage', 'Rogue', 'Priest', 'Warrior', 'Kurian'], state='readonly', width=10)
        job.pack(side='left')
        job.bind('<<ComboboxSelected>>', lambda _: self.render())
        self.show_inactive = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text='Gizli alanları göster', variable=self.show_inactive,
                        command=self.render).pack(side='left', padx=10)
        self.list_help=tk.StringVar(value='Listeler: çift tıkla → düzenle')
        ttk.Label(toolbar,textvariable=self.list_help).pack(side='left')
        ttk.Button(toolbar,text='Rota klasörü',command=self.choose_route_directory).pack(side='left',padx=4)
        self.name_list_result=None
        self.name_cfg_documents={}
        self.name_cfg_result=None
        self.name_cfg_bar=ttk.Frame(frame)
        self.name_cfg_kind=tk.StringVar(value='Beyaz liste')
        self.name_cfg_codepage=tk.StringVar(value=str(local_codepage()))
        ttk.Label(self.name_cfg_bar,text='İsim CFG:').pack(side='left')
        ttk.Combobox(self.name_cfg_bar,textvariable=self.name_cfg_kind,values=('Beyaz liste','Kara liste'),state='readonly',width=13).pack(side='left',padx=4)
        ttk.Label(self.name_cfg_bar,text='BOM yoksa kod sayfası:').pack(side='left')
        ttk.Combobox(self.name_cfg_bar,textvariable=self.name_cfg_codepage,values=('1254','1252','65001','1200','1201'),width=8).pack(side='left',padx=4)
        ttk.Button(self.name_cfg_bar,text='CFG aç',command=self.choose_name_cfg_import).pack(side='left',padx=3)
        ttk.Button(self.name_cfg_bar,text='CFG kaydet',command=self.choose_name_cfg_export).pack(side='left',padx=3)
        self.toolbar=toolbar
        navigation = ttk.Frame(frame)
        navigation.pack(fill='x', pady=3)
        self.section, self.inner_section = tk.StringVar(value='Genel'), tk.StringVar()
        ttk.Label(navigation, text='Bölüm:').pack(side='left')
        self.section_select = ttk.Combobox(navigation, textvariable=self.section, state='readonly', width=24)
        self.section_select.pack(side='left', padx=5)
        self.section_select.bind('<<ComboboxSelected>>', lambda _: self.select_sections())
        ttk.Label(navigation, text='Sınıf alt bölümü:').pack(side='left')
        self.inner_select = ttk.Combobox(navigation, textvariable=self.inner_section, state='readonly', width=24)
        self.inner_select.pack(side='left', padx=5)
        self.inner_select.bind('<<ComboboxSelected>>', lambda _: self.select_sections())
        self.canvas = tk.Canvas(frame, background='#f0f0f0', highlightthickness=0)
        self.canvas.bind('<Destroy>',self.destroy_panel_timers)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(fill='both', expand=True)
        self.surface = None
        self.render()
        self.compile_current_flood()

    def bind_document(self, values, lists):
        self.reset_source_quest_refresh('profile_change')
        self.reset_source_quest('profile_change')
        self.reset_source_coordinates('profile_change')
        self.reset_manual_coordinate()
        self.reset_source_npcs('profile_change')
        self.reset_source_gates('profile_change')
        self.reset_source_upgrade_editor('profile_change')
        self.route_list_edit_result=None
        self.route_save_result=None
        self.route_load_result=None
        self.route_command_result=None
        self.cancel_auto_item_break_timer()
        self.auto_item_break.reset();self.auto_item_break_provider=None
        self.auto_item_break_result=None
        self.cancel_manual_item_break_timer()
        self.manual_item_break.reset()
        self.manual_item_break_provider=None
        self.manual_item_break_result=None
        self.cancel_merchant_scan_timer()
        self.merchant_scan_loop.stop('profile_change')
        self.merchant_scan_provider=None
        self.merchant_scan_loop_result=None
        self.values, self.lists = values, lists
        self.merchant_scan=scan_runtime.OwnedMerchantScan()
        self.merchant_scan_update=None
        self.merchant_results=OwnedMerchantResults()
        self.merchant_export_result=None
        self.merchant_export_context_provider=None
        self.configure_merchant_scan()
        self.merchant_quick_provider=None
        self.merchant_quick_result=None
        self.merchant_result_update=None
        self.merchant_search_color=GRAY_TEXT
        self.merchant_text_policy=None
        self.merchant_cells=OwnedMerchantCells(self.flood_session.queue)
        self.merchant_cell_result=None
        self.flood_edit_result=None
        self.flood_selected_result=None
        self.flood_compilation=None
        self.name_cfg_documents={}
        self.render()
        self.compile_current_flood()

    def source_route_sink(self,values,lists):
        def current():
            if self.values is not values or self.lists is not lists:
                raise ValueError('Rota yükleme sırasında profil değişti')
        panel=self
        class Sink:
            def locate(self,token):
                current()
                for index,row in enumerate(panel.lists[SOURCE_ROUTE_LIST]):
                    if row is token:return index,row
                raise ValueError('Rota satırı silindi veya değiştirildi')
            def validate(self,token):self.locate(token)
            def table(self):
                table=panel.widgets.get(SOURCE_ROUTE_LIST)
                return table if table is not None and table.winfo_exists() else None
            def clear(self):
                current();table=self.table()
                if table is not None:table.delete(*table.get_children())
                panel.lists[SOURCE_ROUTE_LIST]=[]
            def add_row(self):
                current();index=len(panel.lists[SOURCE_ROUTE_LIST])
                table=self.table()
                if table is not None:table.insert('','end',iid=str(index),values=('',))
                row=dict(caption='',subitems=[],checked=False);panel.lists[SOURCE_ROUTE_LIST].append(row)
                return row
            def set_caption(self,token,text):
                index,row=self.locate(token);table=self.table()
                if table is not None:table.item(str(index),values=[text]+row['subitems'])
                row['caption']=text
            def add_subitem(self,token,text):
                index,row=self.locate(token);items=row['subitems']+[text];table=self.table()
                if table is not None:table.item(str(index),values=[row['caption']]+items)
                row['subitems']=items
        return Sink()

    def add_source_route_command(self,method):
        values=self.values;lists=self.lists
        def read_wait():
            if self.values is not values or self.lists is not lists:raise ValueError('Rota ekleme sırasında profil değişti')
            return self.values[route_command_runtime.WAIT_PATH]
        def read_value(path):
            if self.values is not values or self.lists is not lists:raise ValueError('Rota ekleme sırasında profil değişti')
            return self.values[path]
        sink=self.source_route_sink(values,lists)
        if method in route_command_runtime.ADVANCED_CAPTIONS:
            result=route_command_runtime.append_source_route_advanced(method,sink,read_value)
        else:result=route_command_runtime.append_source_route_command(method,sink,read_wait)
        if self.values is not values or self.lists is not lists:return result
        self.route_command_result=result
        if result.complete:self.list_help.set('Rotaya komut eklendi: '+{**route_command_runtime.CAPTIONS,**route_command_runtime.ADVANCED_CAPTIONS}[method])
        else:self.list_help.set('Rota komutu kısmen eklendi: '+str(result.error))
        return result

    def load_source_route(self,index):
        path=route_load_runtime.EDITOR_PATH
        self.set_value(path,index)
        values=self.values;lists=self.lists
        def current():
            if self.values is not values or self.lists is not lists:raise ValueError('Rota yükleme sırasında profil değişti')
        try:
            selected=self.widgets[path].get()
            if self.route_save_context_reader is None:raise ValueError('Rota klasörü bağlantısı gerekli')
            context=self.route_save_context_reader();current()
            result=route_load_runtime.load_source_route_choice(selected,context,self.source_route_sink(values,lists),reader_factory=self.route_load_reader_factory)
        except (ValueError,OSError) as error:
            result=route_load_runtime.RouteLoadResult('load_incomplete',False,error=str(error))
        if self.values is not values or self.lists is not lists:return result
        self.route_load_result=result
        if result.status=='rows_loaded':self.list_help.set('Rota yüklendi: %d satır'%result.completed_rows)
        elif result.status in ('file_missing_preserve','nonpositive_count_preserve'):
            self.list_help.set('Dosya veya pozitif kayıt sayısı bulunamadı; mevcut rota korunuyor.')
        elif result.status=='directory_required':self.list_help.set('Rota klasörü düğmesinden mevcut bir klasör seçin.')
        else:self.list_help.set('Rota yükleme tamamlanamadı: '+str(result.error or result.status))
        return result

    def save_source_route(self):
        values=self.values;lists=self.lists
        def current():
            if self.values is not values or self.lists is not lists:
                raise ValueError('Rota kaydı sırasında profil değişti')
        def read_name():
            current();return self.values[route_save_runtime.NAME_PATH]
        def read_count():
            current();return len(self.lists[route_save_runtime.LIST_PATH])
        def context():
            current()
            if self.route_save_context_reader is None:raise ValueError('Rota klasörü bağlantısı gerekli')
            result=self.route_save_context_reader();current();return result
        def read_row(index):
            current();row=self.lists[route_save_runtime.LIST_PATH][index]
            if len(row['subitems'])<2:raise ValueError('Rota satırında iki ek sütun gerekli')
            return (row['caption'],row['subitems'][0],row['subitems'][1])
        result=route_save_runtime.save_source_route_panel(read_name,read_count,context,read_row,self.route_save_writer)
        if self.values is not values or self.lists is not lists:return result
        self.route_save_result=result
        if result.status=='name_required':self.list_help.set('Rotayı kaydetmek için bir isim giriniz.')
        elif result.status=='empty_rows_preserve':self.list_help.set('Rota listesi boş; dosya korunuyor.')
        elif result.status in ('directory_required','directory_missing'):
            self.list_help.set('Rota klasörü düğmesinden mevcut bir klasör seçin.')
        elif result.status=='write_calls_completed' and result.write.writes_succeeded:
            self.list_help.set('Rota kaydedildi: '+result.path)
        elif result.status=='write_calls_completed':
            self.list_help.set('Rota yazma çağrıları tamamlandı; dosyaya yazma başarısı doğrulanamadı.')
        else:self.list_help.set('Rota kaydı tamamlanamadı: '+str(result.error or result.status))
        return result

    def edit_source_route_rows(self,action):
        """Own table/profile projection of source Clear/DeleteSelected calls."""
        if action not in ('clear','delete_selected'):raise ValueError('Known route list action required')
        table=self.widgets.get(SOURCE_ROUTE_LIST)
        if table is None:
            self.route_list_edit_result=dict(status='needs_table',changed=False)
            return
        rows=self.lists[SOURCE_ROUTE_LIST]
        children=table.get_children()
        if len(children)!=len(rows):raise ValueError('Route table and profile rows differ')
        selected={table.index(iid) for iid in table.selection()}
        removed=set(range(len(rows))) if action=='clear' else selected
        if not removed:
            self.route_list_edit_result=dict(status='unchanged',action=action,changed=False,removed=0)
            return
        candidate=[row for i,row in enumerate(rows) if i not in removed]
        self.profiles.validate_lists({SOURCE_ROUTE_LIST:candidate})
        table.delete(*children)
        for index,row in enumerate(candidate):
            table.insert('', 'end',iid=str(index),values=[row['caption']]+row['subitems'])
        self.lists[SOURCE_ROUTE_LIST]=candidate
        self.route_list_edit_result=dict(status='edited',action=action,changed=True,removed=len(removed),
            native_execution_verified=False,live_compatibility_verified=False)
        self.list_help.set('Rota listesi güncellendi; %d satır kaldırıldı.'%len(removed))

    def bind_button(self,path,callback):
        node=next((n for n in self.catalog if n['path']==path),None)
        if node is None or node['class'] not in ('TButton','TBitBtn') or not callable(callback):
            raise ValueError('Known source button and callable adapter required')
        self.button_handlers[path]=callback
        widget=self.widgets.get(path)
        if widget is not None:
            widget.configure(command=callback)
            if node['properties'].get('Enabled') is not False and not node['disabled_by']:widget.state(['!disabled'])

    def edit_flood_control(self,action):
        """Working own list UI; original VCL helper effects are not presumed."""
        self.flood_edit_result=None
        try:
            path=flood_editor.LIST_PATH
            rows=flood_editor.read_rows(self.lists[path]);selected=None
            widget=self.widgets.get(path)
            if action=='selected' and widget is not None:
                selection=widget.selection()
                if selection:selected=int(selection[0])
            result=flood_editor.edit_flood(action,rows,
                channels=tuple(self.profiles.combo_items(flood_editor.CHANNEL_PATH)),
                channel_index=self.values[flood_editor.CHANNEL_PATH],
                message=self.values[flood_editor.MESSAGE_PATH],
                delay_text=self.values[flood_editor.DELAY_PATH],selected_index=selected)
            if result.changed:
                candidate=flood_editor.write_rows(result.rows)
                self.profiles.validate_lists({path:candidate})
                self.lists[path]=candidate
                if widget is not None:
                    for child in widget.get_children():widget.delete(child)
                    for index,row in enumerate(candidate):
                        widget.insert('','end',iid=str(index),values=[row['caption']]+row['subitems'])
                    if result.selected_index is not None:
                        iid=str(result.selected_index);widget.selection_set(iid);widget.focus(iid);widget.see(iid)
            self.flood_edit_result=result
            compiled=None
            if result.changed or action in ('selected','clear'):
                compiled=self.compile_current_flood()
            self.list_help.set({'added':'Mesaj eklendi','removed':'Seçilen mesaj silindi','cleared':'Mesaj listesi temizlendi',
                'already_empty':'Mesaj listesi zaten boş','no_selection':'Silinecek mesajı seçin',
                'delay_rejected':'Bekleme süresi en az 5 saniye olmalı'}[result.status])
            if compiled is not None and not compiled.complete:
                self.list_help.set(self.list_help.get()+' • Mesaj kayıtları hazırlanamadı: '+compiled.error)
            return result
        except (ValueError,KeyError) as error:
            self.list_help.set(str(error));return None

    def compile_current_flood(self):
        self.flood_compilation=None
        try:
            rows=flood_editor.read_rows(self.lists[flood_editor.LIST_PATH])
            code_page=self.flood_codepage_reader()
            self.flood_compilation=compile_flood_rows(rows,code_page,codec_factory=self.flood_codec_factory)
            return self.flood_compilation
        except (ValueError,OSError,KeyError) as error:
            self.list_help.set('Mesaj kayıtları hazırlanamadı: '+str(error))
            return None

    def current_flood_compilation(self):
        """Never expose an old result as the current UI/codepage compilation."""
        try:
            plan=self.flood_compilation
            if plan is None or plan.snapshot!=flood_editor.read_rows(self.lists[flood_editor.LIST_PATH]) or plan.code_page!=self.flood_codepage_reader():return None
            return plan
        except (ValueError,OSError,KeyError):return None

    def cancel_flood_timer(self):
        if self.flood_after_id is not None:
            try:self.canvas.after_cancel(self.flood_after_id)
            except tk.TclError:pass
            self.flood_after_id=None

    def write_selected_flood(self):
        self.flood_selected_result=None
        def selected():
            widget=self.widgets.get(flood_editor.LIST_PATH)
            choices=() if widget is None else widget.selection()
            return int(choices[0])&0xffffffff if choices else 0xffffffff
        def rows():
            compiled=self.current_flood_compilation()
            if compiled is None or not compiled.complete:raise ValueError('Güncel mesaj kayıtları gerekli')
            return compiled.rows
        frame=OwnedSelectedMessageFrame(self.flood_session.queue)
        plan=frame.advance(selected,rows,self.flood_clock,lambda:1)
        self.flood_session.queue=plan.queue;self.flood_selected_result=plan
        labels={'no_selection':'Önce bir mesaj satırı seçin',
                'locally_enqueued':'Seçilen mesaj yerel kuyruğa eklendi • Oyuna gönderim bağlı değil',
                'not_enqueued':'Seçilen mesaj yerel kuyruğa alınmadı',
                'unknown_channel':'Seçilen mesajın kanalı eşleşmedi',
                'unresolved_source_index':'Seçim ve mesaj kayıtları uyuşmuyor; listeyi yenileyin',
                'unresolved_source_stack_alias':'Bu mesaj uzunluğu için paket davranışı henüz doğrulanmadı'}
        self.list_help.set(labels.get(plan.status,'Seçilen mesaj hazırlanamadı; mesaj kayıtlarını kontrol edin'))
        return plan

    def schedule_flood_timer(self):
        self.cancel_flood_timer()
        if self.flood_session.state.enabled:
            self.flood_after_id=self.canvas.after(100,self.advance_flood_loop)

    def toggle_flood_loop(self):
        self.cancel_flood_timer();self.flood_runtime_result=None
        widget=self.widgets.get(TOGGLE_PATH)
        caption=widget.cget('text') if widget is not None else self.flood_session.state.caption
        state=self.flood_session.toggle(caption)
        if widget is not None:widget.configure(text=state.caption)
        self.list_help.set('Yerel Flood döngüsü başladı • Oyuna gönderim bağlı değil' if state.enabled else 'Yerel Flood döngüsü durdu • Kuyruk korundu')
        self.schedule_flood_timer()
        return state

    def advance_flood_loop(self):
        self.cancel_flood_timer();self.flood_runtime_result=None
        if not self.flood_session.state.enabled:return None
        compiled=self.current_flood_compilation()
        if compiled is None or not compiled.complete:
            self.list_help.set('Yerel Flood bekliyor: güncel mesaj kayıtları hazırlanmalı')
        else:
            # This is an explicitly owned preview admission gate, never a
            # fabricated observation of the game's connection state.
            self.flood_runtime_result=self.flood_session.advance(compiled.rows,self.flood_clock,lambda:1)
            plan=self.flood_runtime_result
            if plan.complete:self.list_help.set('Yerel Flood: %d kuyruk kaydı • Oyuna gönderim bağlı değil'%len(plan.queue.records))
            else:self.list_help.set('Yerel Flood ilerleyemedi: '+plan.status)
        self.schedule_flood_timer()
        return self.flood_runtime_result

    def set_value(self, path, value):
        try:
            self.profiles.update(self.values, path, value)
            if path in parameter_ui.PARAMETER_PATHS.values():
                if path==parameter_ui.SCROLL_PATH:
                    parameter_ui.remember_scroll_text(self.values,self.widgets,self.source_upgrade_parameter_text_cache)
                self.start_source_upgrade_parameters(path)
            if path in scan_runtime.SETTING_PATHS:self.configure_merchant_scan()
            if path==auto_break_runtime.ENABLE_PATH:self.configure_auto_item_break()
            if path in MERCHANT_FILTER_PATHS:self.refresh_merchant_results()
            prefix='frmMain/MainTab/SheetBot/GroupBox5/'
            pool=(prefix+'chOnlyMobSelect',prefix+'chOnlyPlayerSelect')
            if path in pool:
                for sibling in pool:
                    if sibling in self.variables:self.variables[sibling].set(self.values[sibling])
            for group in self.profiles.radio_groups.values():
                if path in group:
                    parent = path.rsplit('/', 1)[0]
                    selected = next((k for k in group if self.values[k]), '')
                    if parent in self.radio_variables:
                        self.radio_variables[parent].set(selected)
                    break
        except ValueError as error:
            messagebox.showerror('Ayar', str(error))

    def choose_route_directory(self):
        if self.route_directory_chooser is not None:self.route_directory_chooser()

    def _write_source_route_panel(self,field,value):
        widget=self.widgets.get(route_panel_runtime.PANEL_PATH)
        if widget is None:raise ValueError('Rota paneli ana formda olmalı')
        try:
            if field=='visible':
                if value:
                    g=self.route_panel.geometry
                    widget.place(x=g['left'],y=g['top'],height=g['height'],width=g['width'])
                else:widget.place_forget()
            elif widget.place_info():
                widget.place_configure(**{{'left':'x','top':'y','height':'height','width':'width'}[field]:value})
            # Hidden geometry is retained in the owned controller, so setters
            # do not accidentally show a forgotten Tk widget before Visible.
        except tk.TclError as error:raise OSError(str(error)) from error

    def apply_source_route_panel(self):
        widget=self.widgets.get(route_panel_runtime.PANEL_PATH)
        if widget is None:return
        g=self.route_panel.geometry
        if widget.place_info() and g:
            widget.place_configure(**{{'left':'x','top':'y','height':'height','width':'width'}[k]:v for k,v in g.items()})
        if self.route_panel.visible is not None:self._write_source_route_panel('visible',self.route_panel.visible)

    def open_source_route_panel(self):
        def read(field):
            tabs=self.widgets.get(route_panel_runtime.TABS_PATH)
            if tabs is None:raise ValueError('Rota paneli ana formda açılmalı')
            return int(tabs.place_info()[{'left':'x','top':'y','height':'height'}[field]])
        self.route_panel_update=self.route_panel.open(read,self._write_source_route_panel)
        if self.route_panel_update.complete:
            self.list_help.set('Rota paneli açıldı • Komut/dosya işlemlerinin bağlantısı ayrı izleniyor')
        else:self.list_help.set('Rota paneli açılamadı: '+str(self.route_panel_update.error))
        return self.route_panel_update

    def close_source_route_panel(self):
        def uncheck():
            path=route_panel_runtime.GATES_PATH
            self.profiles.update(self.values,path,False)
            if path in self.variables:self.variables[path].set(False)
        self.route_panel_update=self.route_panel.close(uncheck,self._write_source_route_panel)
        if self.route_panel_update.complete:self.list_help.set('Rota paneli kapatıldı')
        else:self.list_help.set('Rota paneli kapatılamadı: '+str(self.route_panel_update.error))
        return self.route_panel_update

    def configure_merchant_scan(self):
        return self.merchant_scan.configure(self.values[MERCHANT_KIND],
            *(bool(self.values[p]) for p in scan_runtime.SETTING_PATHS))

    def merchant_scan_button(self,index,enabled):
        path=(scan_runtime.START_PATH,scan_runtime.STOP_PATH,scan_runtime.QUICK_PATH)[index]
        widget=self.widgets.get(path)
        # Keep source enable intent separate from availability of a handler.
        if widget is not None:widget.state(['!disabled' if enabled and path in self.button_handlers else 'disabled'])

    def merchant_scan_status(self,text):
        widget=self.widgets.get(scan_runtime.STATUS_PATH)
        if widget is not None:widget.configure(text=text)

    def start_merchant_scan(self):
        self.cancel_merchant_scan_timer()
        def rows():
            return tuple((row['subitems'][0] if row['subitems'] else '',
                          row['subitems'][1] if len(row['subitems'])>1 else '')
                         for row in self.lists[scan_runtime.ROUTE_LIST])
        def mode(index):
            self.values[MERCHANT_KIND]=index
            widget=self.widgets.get(MERCHANT_KIND)
            if widget is not None:widget.current(index)
            self.refresh_merchant_results()
        self.merchant_scan_update=self.merchant_scan.start(
            bool(self.values[scan_runtime.SELL_PATH]),bool(self.values[scan_runtime.BUY_PATH]),rows,
            lambda:self.accept_merchant_records(()),self.merchant_scan_button,mode,self.merchant_scan_status)
        p=self.merchant_scan_update
        self.merchant_scan_loop.restart(self.merchant_scan.state)
        self.merchant_scan_loop_result=None
        self.schedule_merchant_scan_timer()
        if p.complete:self.list_help.set('Yerel tarama hazır • Oyun verisi bağlantısı bekleniyor')
        else:self.list_help.set('Rota satırı %d: %s koordinatı geçersiz'%(p.failed_row+1,p.failed_coordinate.upper()))
        return p

    def stop_merchant_scan(self):
        self.cancel_merchant_scan_timer()
        self.merchant_scan_loop.stop()
        self.merchant_scan_update=self.merchant_scan.stop(self.merchant_scan_button,self.merchant_scan_status)
        self.list_help.set('Yerel tarama durdu • Sonuçlar korundu')
        return self.merchant_scan_update

    def cancel_merchant_scan_timer(self):
        if self.merchant_scan_after_id is not None:
            try:self.canvas.after_cancel(self.merchant_scan_after_id)
            except tk.TclError:pass
            self.merchant_scan_after_id=None

    def cancel_manual_coordinate_timer(self):
        if self.manual_coordinate_after_id is not None:
            try:self.canvas.after_cancel(self.manual_coordinate_after_id)
            except tk.TclError:pass
            self.manual_coordinate_after_id=None

    def manual_coordinate_availability(self):
        widget=self.widgets.get(MANUAL_COORDINATE_BUTTON)
        node=next(n for n in self.catalog if n['path']==MANUAL_COORDINATE_BUTTON)
        enabled=(callable(self.manual_coordinate_provider) and not self.manual_coordinate.pending
                 and node['properties'].get('Enabled') is not False and not node['disabled_by'])
        if widget is not None and widget.winfo_exists():widget.state(['!disabled'] if enabled else ['disabled'])

    def reset_manual_coordinate(self):
        self.cancel_manual_coordinate_timer();self.manual_coordinate.reset()
        self.manual_coordinate_provider=None;self.manual_coordinate_availability()

    def set_manual_coordinate_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Coordinate provider must be callable or None')
        self.reset_manual_coordinate();self.manual_coordinate_provider=provider
        self.manual_coordinate_availability()

    def start_manual_coordinate(self):
        if not callable(self.manual_coordinate_provider):
            self.list_help.set('Koordinat dönüşüm bağlantısı gerekli.');return None
        if self.manual_coordinate.pending or self.manual_coordinate.busy:return self.manual_coordinate.result
        self.manual_coordinate.start();self.manual_coordinate_availability()
        return self.advance_manual_coordinate()

    def advance_manual_coordinate(self,generation=None):
        runtime=self.manual_coordinate
        if generation is not None and generation!=runtime.generation:return None
        if runtime.busy:return None
        self.cancel_manual_coordinate_timer()
        if not runtime.pending or not callable(self.manual_coordinate_provider):return runtime.result
        current_generation=runtime.generation
        result=runtime.tick(self.manual_coordinate_provider)
        if current_generation!=runtime.generation:
            # A replacement provider may have started a new generation from
            # inside the callback; ensure its pending continuation is retained.
            if runtime.pending and self.manual_coordinate_after_id is None:
                next_generation=runtime.generation
                self.manual_coordinate_after_id=self.canvas.after(manual_coordinate_runtime.OWN_TIMER_PERIOD_MS,
                    lambda:self.advance_manual_coordinate(next_generation))
            return None
        self.manual_coordinate_availability()
        if result is not None and result.complete:
            self.list_help.set('Koordinat çağrı akışı doğrulandı; oyun hareketi yürütülmedi.')
        elif runtime.error:self.list_help.set('Koordinat gözlemi reddedildi: '+runtime.error)
        else:self.list_help.set('Koordinat çağrı sonucu bekleniyor; oyun hareketi yürütülmedi.')
        if runtime.pending:
            self.manual_coordinate_after_id=self.canvas.after(manual_coordinate_runtime.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_manual_coordinate(current_generation))
        return result

    def cancel_source_coordinate_timer(self):
        if self.source_coordinate_after_id is not None:
            try:self.canvas.after_cancel(self.source_coordinate_after_id)
            except tk.TclError:pass
            self.source_coordinate_after_id=None

    def source_coordinate_availability(self):
        widget=self.widgets.get(coordinate_click.BUTTON_PATH)
        node=next(n for n in self.catalog if n['path']==coordinate_click.BUTTON_PATH)
        enabled=callable(self.source_coordinate_provider) and node['properties'].get('Enabled') is not False and not node['disabled_by']
        if widget is not None:
            try:widget.state(['!disabled' if enabled else 'disabled'])
            except tk.TclError:pass

    def reset_source_coordinates(self,reason):
        self.cancel_source_coordinate_timer();self.source_coordinate_generation+=1
        for _,frame,_ in self.source_coordinate_pending:frame.cancel(reason)
        self.source_coordinate_pending.clear();self.source_coordinate_provider=None;self.source_coordinate_result=None
        self.source_coordinate_availability()

    def set_source_coordinate_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Coordinate provider must be callable or None')
        self.reset_source_coordinates('provider_change');self.source_coordinate_provider=provider
        self.source_coordinate_availability()

    def schedule_source_coordinate_timer(self):
        self.cancel_source_coordinate_timer()
        if self.source_coordinate_pending:
            generation=self.source_coordinate_generation
            self.source_coordinate_after_id=self.canvas.after(coordinate_click.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_source_coordinate(generation))

    def start_source_coordinate(self):
        if not callable(self.source_coordinate_provider):
            self.list_help.set('Konum bağlantısı gerekli.');return None
        self.source_coordinate_invocation+=1
        frame=coordinate_click.CoordinateClickFrame(self.source_route_sink(self.values,self.lists))
        self.source_coordinate_pending.append((self.source_coordinate_invocation,frame,self.source_coordinate_provider))
        if not self.source_coordinate_stepping:self.advance_source_coordinate()
        return frame.result

    def advance_source_coordinate(self,generation=None):
        if generation is not None and generation!=self.source_coordinate_generation:return None
        if self.source_coordinate_stepping:return None
        self.cancel_source_coordinate_timer()
        if not self.source_coordinate_pending:return None
        current_generation=self.source_coordinate_generation;self.source_coordinate_stepping=True
        ticket,frame,provider=self.source_coordinate_pending[0]
        try:
            result=frame.advance()
            if not result.done:
                axis=result.coordinates.axes[-1] if result.coordinates and result.coordinates.axes else None
                context=coordinate_click.CoordinateCaptureContext(ticket,current_generation,
                    None if axis is None else axis.axis,None if axis is None else axis.needed)
                try:capture=provider(context)
                except (ValueError,OSError) as error:capture=None;result=frame.hold(str(error))
                if current_generation!=self.source_coordinate_generation or not self.source_coordinate_pending or self.source_coordinate_pending[0][1] is not frame:return None
                if capture is not None:result=frame.advance(capture)
            if current_generation!=self.source_coordinate_generation:return None
            self.source_coordinate_result=result
            if result.done:
                self.source_coordinate_pending.pop(0)
                self.list_help.set('Konum satırı eklendi.' if result.complete else 'Konum satırı tamamlanamadı; mevcut kısmı korundu.')
            else:self.list_help.set('Konum bilgisi bekleniyor.')
            return result
        finally:
            self.source_coordinate_stepping=False;self.schedule_source_coordinate_timer()

    def ask_source_npc_dialog(self):
        return simpledialog.askstring('İşlem Kodunu Giriniz',
            'Atak: 0, AC: 1, BUFF: 2, SW: 3, Hepsi: 4',initialvalue='',parent=self.canvas)

    def cancel_source_npc_timer(self):
        if self.source_npc_after_id is not None:
            try:self.canvas.after_cancel(self.source_npc_after_id)
            except tk.TclError:pass
            self.source_npc_after_id=None

    def source_npc_availability(self):
        widget=self.widgets.get(npc_click.BUTTON_PATH)
        node=next(n for n in self.catalog if n['path']==npc_click.BUTTON_PATH)
        enabled=callable(self.source_npc_provider) and node['properties'].get('Enabled') is not False and not node['disabled_by']
        if widget is not None:
            try:widget.state(['!disabled' if enabled else 'disabled'])
            except tk.TclError:pass

    def reset_source_npcs(self,reason):
        self.cancel_source_npc_timer();self.source_npc_generation+=1
        for _,frame,_ in self.source_npc_pending:frame.cancel(reason)
        self.source_npc_pending.clear();self.source_npc_provider=None;self.source_npc_result=None
        self.source_npc_availability()

    def set_source_npc_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('NPC provider must be callable or None')
        self.reset_source_npcs('provider_change');self.source_npc_provider=provider
        self.source_npc_availability()

    def schedule_source_npc_timer(self):
        self.cancel_source_npc_timer()
        if self.source_npc_pending:
            generation=self.source_npc_generation
            self.source_npc_after_id=self.canvas.after(npc_click.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_source_npc(generation))

    def start_source_npc(self):
        if not callable(self.source_npc_provider):
            self.list_help.set('NPC bağlantısı gerekli.');return None
        self.source_npc_invocation+=1
        frame=NpcSourceFrame(self.source_route_sink(self.values,self.lists))
        self.source_npc_pending.append((self.source_npc_invocation,frame,self.source_npc_provider))
        if not self.source_npc_stepping:self.advance_source_npc()
        return frame.result

    def advance_source_npc(self,generation=None):
        if generation is not None and generation!=self.source_npc_generation:return None
        if self.source_npc_stepping:return None
        self.cancel_source_npc_timer()
        if not self.source_npc_pending:return None
        current_generation=self.source_npc_generation;self.source_npc_stepping=True
        ticket,frame,provider=self.source_npc_pending[0]
        def current():
            return current_generation==self.source_npc_generation and bool(self.source_npc_pending) and self.source_npc_pending[0][1] is frame
        try:
            result=frame.advance()
            if not result.done and not str(result.needed).startswith('dialog_text'):
                context=npc_click.NpcCaptureContext(ticket,current_generation,frame.phase,result.needed)
                try:capture=provider(context)
                except (ValueError,OSError) as error:capture=None;result=frame.hold(error)
                if not current():return None
                if capture is not None:
                    # Dialog values come from our UI, never from the data provider.
                    if isinstance(capture,npc_click.NpcClickInput):capture=replace(capture,dialog_text=None)
                    result=frame.advance(capture)
            if not result.done and str(result.needed).startswith('dialog_text'):
                try:answer=self.source_npc_dialog()
                except (ValueError,OSError,tk.TclError) as error:
                    result=frame.hold(error)
                else:
                    if not current():return None
                    result=frame.advance(npc_click.NpcClickInput(
                        dialog_text=npc_click.NpcValueCapture('' if answer is None else answer,True)))
            if current_generation!=self.source_npc_generation:return None
            self.source_npc_result=result
            if result.done:
                self.source_npc_pending.pop(0)
                messages={'row_completed':'NPC rota satırı eklendi.','no_selection':'NPC seçilmedi.',
                    'lookup_empty':'Seçili hedef bilgisi bulunamadı.','name_unmatched':'Bu NPC için rota işlemi bulunamadı.',
                    'dialog_rejected':'İşlem kodu kabul edilmedi.'}
                self.list_help.set(messages.get(result.status,'NPC satırı tamamlanamadı; mevcut kısmı korundu.'))
                if result.status=='no_selection':self.source_npc_notice()
            else:self.list_help.set('NPC bilgisi bekleniyor.')
            return result
        finally:
            self.source_npc_stepping=False;self.schedule_source_npc_timer()

    def cancel_source_gate_timer(self):
        if self.source_gate_after_id is not None:
            try:self.canvas.after_cancel(self.source_gate_after_id)
            except tk.TclError:pass
            self.source_gate_after_id=None

    def reset_source_gates(self,reason):
        self.cancel_source_gate_timer();self.source_gates.reset(reason)

    def set_source_gate_provider(self,provider):
        self.cancel_source_gate_timer();self.source_gates.set_provider(provider)

    def submit_source_gate_packet(self,packet):
        result=self.source_gates.dispatch(packet)
        self.schedule_source_gate_timer()
        return result

    def schedule_source_gate_timer(self):
        self.cancel_source_gate_timer()
        if self.source_gates.pending:
            generation=self.source_gates.generation
            self.source_gate_after_id=self.canvas.after(GATE_RECORD_TIMER_MS,
                lambda:self.advance_source_gates(generation))

    def advance_source_gates(self,generation=None):
        if generation is not None and generation!=self.source_gates.generation:return None
        self.cancel_source_gate_timer()
        try:return self.source_gates.advance(generation)
        finally:self.schedule_source_gate_timer()

    def source_upgrade_editor_sink(self):
        panel=self;values=self.values;lists=self.lists
        def current():
            if panel.values is not values or panel.lists is not lists:raise ValueError('Upgrade profile changed')
        class Sink:
            def locate(self,token):
                current()
                for index,row in enumerate(lists[upgrade_editor.LIST_PATH]):
                    if row is token:return index,row
                raise ValueError('Upgrade row deleted or replaced')
            def validate(self,token):self.locate(token)
            def table(self):
                table=panel.widgets.get(upgrade_editor.LIST_PATH)
                return table if table is not None and table.winfo_exists() else None
            def clear(self):
                current();table=self.table()
                if table is not None:table.delete(*table.get_children())
                lists[upgrade_editor.LIST_PATH]=[]
            def add_row(self):
                current();index=len(lists[upgrade_editor.LIST_PATH]);table=self.table()
                if table is not None:table.insert('','end',iid=str(index),values=('☐ ',))
                row=dict(caption='',subitems=[],checked=False);lists[upgrade_editor.LIST_PATH].append(row)
                return row
            def set_caption(self,token,text):
                index,row=self.locate(token);table=self.table()
                if table is not None:table.item(str(index),values=[('☑ ' if row['checked'] else '☐ ')+text]+row['subitems'])
                row['caption']=text
            def add_subitem(self,token,text):
                index,row=self.locate(token);items=row['subitems']+[text];table=self.table()
                if table is not None:table.item(str(index),values=[('☑ ' if row['checked'] else '☐ ')+row['caption']]+items)
                row['subitems']=items
            def count(self):current();return len(lists[upgrade_editor.LIST_PATH])
            def checked(self,index):current();return lists[upgrade_editor.LIST_PATH][index]['checked']
            def caption(self,index):current();return lists[upgrade_editor.LIST_PATH][index]['caption']
            def armor_combo(self):
                current();widget=panel.widgets.get(ARMOR_COMBO_PATH)
                return widget.current() if widget is not None and widget.winfo_exists() else values[ARMOR_COMBO_PATH]
            def set_enabled(self,name,value):
                current();runner=panel.source_upgrade_runner
                start,stop=runner.source_start_ui
                runner.source_start_ui=(value,stop) if name=='start' else (start,value)
                panel.source_upgrade_availability()
            def set_checked(self,index,value):
                current();row=lists[upgrade_editor.LIST_PATH][index];row['checked']=value
                table=panel.widgets.get(upgrade_editor.LIST_PATH)
                if table is not None and table.winfo_exists():
                    table.item(str(index),values=[('☑ ' if value else '☐ ')+row['caption']]+row['subitems'])
            def set_anvil_text(self,text):
                current();path=upgrade_editor.ANVIL_PATH
                before=panel.source_upgrade_parameter_invocation;self.parameter_generation=panel.source_upgrade_generation
                if path in panel.variables:panel.variables[path].set(text)
                else:panel.set_value(path,text)
                self.parameter_jobs=[frame for ticket,_,frame,_ in panel.source_upgrade_parameter_pending if ticket>before]
                current()
                if values[path]!=text:raise ValueError('Own Anvil text setter did not retain text')
            def anvil_text_ready(self):
                current()
                if getattr(self,'parameter_generation',panel.source_upgrade_generation)!=panel.source_upgrade_generation:
                    raise ValueError('Upgrade parameter callback context changed')
                jobs=getattr(self,'parameter_jobs',())
                if any(frame.result.done and not frame.result.complete for frame in jobs):
                    raise ValueError('Nested Upgrade parameter callback did not complete')
                return all(frame.result.done for frame in jobs)
        return Sink()

    def cancel_source_upgrade_timer(self):
        if self.source_upgrade_after_id is not None:
            try:self.canvas.after_cancel(self.source_upgrade_after_id)
            except tk.TclError:pass
            self.source_upgrade_after_id=None

    def source_upgrade_availability(self):
        for path in upgrade_editor.METHODS:
            node=next(n for n in self.catalog if n['path']==path)
            own_enabled=node['properties'].get('Enabled') is not False
            disabled_by=node['disabled_by']
            if path in (upgrade_editor.START_PATH,upgrade_editor.STOP_PATH):
                own_enabled=self.source_upgrade_runner.source_start_ui[0 if path==upgrade_editor.START_PATH else 1]
                disabled_by=[ancestor for ancestor in disabled_by if ancestor!=path]
            enabled=callable(self.source_upgrade_provider) and own_enabled and not disabled_by
            widget=self.widgets.get(path)
            if widget is not None and widget.winfo_exists():widget.state(['!disabled'] if enabled else ['disabled'])

    def reset_source_upgrade_editor(self,reason):
        self.cancel_source_upgrade_timer();self.source_upgrade_generation+=1
        for _,frame,_ in self.source_upgrade_pending:frame.cancel(reason)
        self.source_upgrade_pending.clear();self.source_upgrade_provider=None;self.source_upgrade_result=None
        self.cancel_source_upgrade_parameter_timer()
        for _,_,frame,_ in self.source_upgrade_parameter_pending:frame.cancel(reason)
        self.source_upgrade_parameter_pending.clear();self.source_upgrade_parameter_provider=None;self.source_upgrade_parameter_result=None
        if reason!='provider_change':
            self.cancel_source_upgrade_worker_timer();self.source_upgrade_worker_generation+=1
            self.source_upgrade_worker=None;self.source_upgrade_worker_provider=None;self.source_upgrade_worker_result=None
            self.source_upgrade_parameter_state=UpgradeParameterState();self.source_upgrade_parameter_text_cache={}
            self.source_upgrade_runner=UpgradeRunner(source_clock=True)
            self.source_upgrade_runner.source_start_ui=(True,False)
        self.source_upgrade_availability()

    def set_source_upgrade_editor_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable Upgrade editor provider required')
        parameter_provider=self.source_upgrade_parameter_provider
        self.reset_source_upgrade_editor('provider_change');self.source_upgrade_provider=provider
        self.source_upgrade_parameter_provider=parameter_provider
        self.source_upgrade_availability()

    def schedule_source_upgrade_timer(self):
        self.cancel_source_upgrade_timer()
        if self.source_upgrade_pending:
            generation=self.source_upgrade_generation
            self.source_upgrade_after_id=self.canvas.after(upgrade_editor.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_source_upgrade_editor(generation))

    def start_source_upgrade_editor(self,method):
        if not callable(self.source_upgrade_provider):
            self.list_help.set('Upgrade veri bağlantısı gerekli.');return None
        sink=self.source_upgrade_editor_sink()
        if method in ('start','stop','armor'):
            if self.source_upgrade_worker is not None and self.source_upgrade_worker.pending:
                self.list_help.set('Upgrade işlemi sürüyor; tamamlanmasını bekleyin.');return None
            try:
                frame=ArmorStartFrame(self.source_upgrade_runner,sink.armor_combo) if method=='armor' else UpgradeStartFrame(method,self.source_upgrade_runner,self.source_upgrade_parameter_state,sink)
            except ValueError:self.list_help.set('Upgrade işlemi sürüyor; tamamlanmasını bekleyin.');return None
        else:frame=UpgradeRefreshFrame(sink) if method=='refresh' else upgrade_editor.UpgradeEditorFrame(method,sink)
        self.source_upgrade_invocation+=1
        self.source_upgrade_pending.append((self.source_upgrade_invocation,frame,self.source_upgrade_provider))
        if not self.source_upgrade_stepping:self.advance_source_upgrade_editor()
        return frame.result

    def advance_source_upgrade_editor(self,generation=None):
        if generation is not None and generation!=self.source_upgrade_generation:return None
        if self.source_upgrade_stepping:return None
        self.cancel_source_upgrade_timer()
        if not self.source_upgrade_pending:return None
        active_generation=self.source_upgrade_generation;self.source_upgrade_stepping=True
        ticket,frame,provider=self.source_upgrade_pending[0]
        def current():
            return active_generation==self.source_upgrade_generation and bool(self.source_upgrade_pending) and self.source_upgrade_pending[0][1] is frame
        try:
            result=frame.advance()
            if not result.done and result.status!='continuation' and result.needed!=('nested_parameters',):
                context=upgrade_editor.UpgradeEditorContext(ticket,active_generation,frame.method,frame.phase,result.needed)
                try:capture=provider(context)
                except (ValueError,OSError) as error:capture=None;result=frame.hold(error)
                if not current():return None
                if capture is not None:
                    try:result=frame.advance(capture)
                    except (ValueError,OSError) as error:result=frame.hold(error)
            if not current():return None
            self.source_upgrade_result=result
            if result.done:self.source_upgrade_pending.pop(0)
            self.list_help.set({'refreshed':'Upgrade listesi yenilendi.','selected_all':'Upgrade satırları seçildi.','target_id_set':'Anvil ID güncellendi.',
                'started':'Upgrade kuyruğu hazır.','stopped':'Upgrade durduruldu.',
                'armor_armed':'Armor başlangıç ayarları hazır.','npc_missing':'Armor satıcısı bulunamadı.',
                'too_far':'Armor satıcısı uzakta.','item_missing':'Armor seçimi gerekli.','bag_full':'Envanter dolu.',
                'npc_pointer_zero':'Armor satıcısının bilgisi alınamadı.',
                'no_target':'Seçili hedef yok; Anvil ID korunuyor.','gate_closed':'Upgrade durum kapısı kapalı.'}.get(
                    result.status,'Upgrade bilgisi bekleniyor.' if not result.done else 'Upgrade işlemi tamamlanamadı.'))
            return result
        finally:
            self.source_upgrade_stepping=False;self.schedule_source_upgrade_timer();self.schedule_source_upgrade_worker_timer()

    def cancel_source_upgrade_worker_timer(self):
        if self.source_upgrade_worker_after_id is not None:
            try:self.canvas.after_cancel(self.source_upgrade_worker_after_id)
            except tk.TclError:pass
            self.source_upgrade_worker_after_id=None

    def set_source_upgrade_worker_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable captured Upgrade worker provider required')
        self.cancel_source_upgrade_worker_timer();self.source_upgrade_worker_generation+=1
        self.source_upgrade_worker_provider=provider
        self.schedule_source_upgrade_worker_timer()

    def schedule_source_upgrade_worker_timer(self):
        self.cancel_source_upgrade_worker_timer()
        pending=self.source_upgrade_worker is not None and self.source_upgrade_worker.pending
        if callable(self.source_upgrade_worker_provider) and (self.source_upgrade_runner.state in (1,2) or pending):
            generation=self.source_upgrade_worker_generation
            self.source_upgrade_worker_after_id=self.canvas.after(upgrade_editor.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_source_upgrade_worker(generation))

    def advance_source_upgrade_worker(self,generation=None):
        if generation is not None and generation!=self.source_upgrade_worker_generation:return None
        if self.source_upgrade_worker_stepping or not callable(self.source_upgrade_worker_provider):return None
        self.cancel_source_upgrade_worker_timer()
        if self.source_upgrade_pending or self.source_upgrade_parameter_pending:
            self.schedule_source_upgrade_worker_timer();return None
        if self.source_upgrade_worker is None:
            values=self.values;lists=self.lists;bound_runner=self.source_upgrade_runner
            def current_document():
                if self.values is not values or self.lists is not lists or self.source_upgrade_runner is not bound_runner:
                    raise ValueError('Upgrade document changed')
            def reader():current_document();return self.flood_session.queue
            def writer(queue):current_document();self.flood_session.queue=queue
            self.source_upgrade_worker=OwnedUpgradeWorker(self.source_upgrade_runner,self.source_upgrade_parameter_state,
                self.source_upgrade_editor_sink(),reader,writer)
        worker=self.source_upgrade_worker;provider=self.source_upgrade_worker_provider
        active_generation=self.source_upgrade_worker_generation;self.source_upgrade_worker_stepping=True
        def current():
            return active_generation==self.source_upgrade_worker_generation and self.source_upgrade_worker is worker and self.source_upgrade_worker_provider is provider
        try:
            context=UpgradeWorkerContext(active_generation,self.source_upgrade_runner.state,worker.result.status,worker.result.needed)
            try:capture=provider(context)
            except (OSError,ValueError) as error:
                capture=None
                if current():self.source_upgrade_worker_result=worker.hold(error)
            if not current():return None
            if capture is not None:
                try:result=worker.step(capture)
                except (OSError,ValueError) as error:
                    if current():self.source_upgrade_worker_result=worker.hold(error)
                    return self.source_upgrade_worker_result
                if not current():return None
                self.source_upgrade_worker_result=result
                self.source_upgrade_availability()
            return self.source_upgrade_worker_result
        finally:
            self.source_upgrade_worker_stepping=False;self.schedule_source_upgrade_worker_timer()

    def cancel_source_upgrade_parameter_timer(self):
        if self.source_upgrade_parameter_after_id is not None:
            try:self.canvas.after_cancel(self.source_upgrade_parameter_after_id)
            except tk.TclError:pass
            self.source_upgrade_parameter_after_id=None

    def set_source_upgrade_parameter_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable parameter provider required')
        editor_provider=self.source_upgrade_provider
        self.reset_source_upgrade_editor('provider_change');self.source_upgrade_provider=editor_provider
        self.source_upgrade_parameter_provider=provider;self.source_upgrade_availability()

    def schedule_source_upgrade_parameter_timer(self):
        self.cancel_source_upgrade_parameter_timer()
        if self.source_upgrade_parameter_pending:
            generation=self.source_upgrade_generation
            self.source_upgrade_parameter_after_id=self.canvas.after(upgrade_editor.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_source_upgrade_parameters(generation))

    def start_source_upgrade_parameters(self,path):
        if not callable(self.source_upgrade_parameter_provider):return None
        values=self.values;lists=self.lists;cache=self.source_upgrade_parameter_text_cache
        def read(field):
            if self.values is not values or self.lists is not lists:raise ValueError('Upgrade parameter profile changed')
            try:return parameter_ui.read_parameter_text(field,values,self.catalog,self.widgets,cache,self.variables)
            except tk.TclError as error:raise OSError(str(error)) from error
        frame=UpgradeParameterFrame(self.source_upgrade_parameter_state,read)
        self.source_upgrade_parameter_invocation+=1
        self.source_upgrade_parameter_pending.append((self.source_upgrade_parameter_invocation,path,frame,self.source_upgrade_parameter_provider))
        if not self.source_upgrade_parameter_stepping:self.advance_source_upgrade_parameters()
        return frame.result

    def advance_source_upgrade_parameters(self,generation=None):
        if generation is not None and generation!=self.source_upgrade_generation:return None
        if self.source_upgrade_parameter_stepping:return None
        self.cancel_source_upgrade_parameter_timer()
        if not self.source_upgrade_parameter_pending:return None
        active_generation=self.source_upgrade_generation;self.source_upgrade_parameter_stepping=True
        ticket,path,frame,provider=self.source_upgrade_parameter_pending[0]
        def current():
            return active_generation==self.source_upgrade_generation and bool(self.source_upgrade_parameter_pending) and self.source_upgrade_parameter_pending[0][2] is frame
        try:
            try:result=frame.advance()
            except (ValueError,OSError) as error:result=frame.hold(error)
            if not result.done:
                context=parameter_ui.UpgradeParameterContext(ticket,active_generation,path,frame.phase,result.needed)
                try:capture=provider(context)
                except (ValueError,OSError) as error:capture=None;result=frame.hold(error)
                if not current():return None
                if capture is not None:
                    try:result=frame.advance(capture)
                    except (ValueError,OSError) as error:result=frame.hold(error)
            if not current():return None
            self.source_upgrade_parameter_result=result
            if result.done:self.source_upgrade_parameter_pending.pop(0)
            self.list_help.set('Upgrade parametreleri güncellendi.' if result.complete else 'Upgrade parametre bilgisi bekleniyor.')
            return result
        finally:self.source_upgrade_parameter_stepping=False;self.schedule_source_upgrade_parameter_timer()

    def destroy_panel_timers(self,event):
        if event.widget is not self.canvas:return
        self.cancel_flood_timer();self.cancel_merchant_scan_timer()
        self.merchant_scan_loop.stop('panel_destroyed')
        self.cancel_manual_item_break_timer();self.manual_item_break.reset()
        self.cancel_auto_item_break_timer();self.auto_item_break.reset()
        self.reset_source_coordinates('panel_destroyed')
        self.reset_manual_coordinate()
        self.reset_source_npcs('panel_destroyed')
        self.reset_source_gates('panel_destroyed')
        self.reset_source_upgrade_editor('panel_destroyed')
        self.reset_source_quest('panel_destroyed')
        self.reset_source_quest_refresh('panel_destroyed')

    def cancel_source_quest_refresh_timer(self):
        if self.source_quest_refresh_after_id is not None:
            try:self.canvas.after_cancel(self.source_quest_refresh_after_id)
            except tk.TclError:pass
            self.source_quest_refresh_after_id=None

    def reset_source_quest_refresh(self,reason):
        if self.source_quest_refresh_pending is not None and self.source_quest_refresh_operation=='action':
            self.source_quest_refresh_pending[0].cancel()
        self.source_quest_action_provider=None
        self.cancel_source_quest_refresh_timer();self.source_quest_refresh_generation+=1
        self.source_quest_refresh_pending=None;self.source_quest_refresh_provider=None
        self.source_quest_refresh_state=None;self.source_quest_refresh_result=None
        self.source_quest_npc_items=None;self.source_quest_refresh_projection=None
        self.source_quest_refresh_error=None
        self.source_quest_filter_provider=None;self.source_quest_refresh_operation=None
        self.source_quest_details_provider=None;self.source_quest_details_state=None
        self.source_quest_details_projection=None;self.source_quest_details_painted_headings=None
        self.source_quest_availability()

    def set_source_quest_refresh_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable captured refresh provider required')
        self.reset_source_quest_refresh('provider_change');self.source_quest_refresh_provider=provider
        self.source_quest_availability()

    def set_source_quest_filter_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable captured NPC-filter provider required')
        if self.source_quest_refresh_pending is not None and self.source_quest_refresh_operation=='npc_filter':
            self.cancel_source_quest_refresh_timer();self.source_quest_refresh_generation+=1
            self.source_quest_refresh_pending=None;self.source_quest_refresh_result=None
            self.source_quest_refresh_error=None
        self.source_quest_filter_provider=provider;self.source_quest_availability()

    def select_source_quest_npc(self,index):
        if self.source_quest_refresh_pending is not None or self.source_quest_pending:
            self.list_help.set('Görev işlemi sürüyor.');self.restore_source_quest_npcs();return None
        state=self.source_quest_refresh_state
        if state is not None:state.npc_selected=index
        if state is None or not callable(self.source_quest_filter_provider):
            self.list_help.set('NPC filtresi için veri bağlantısı gerekli.');return None
        from quest_npc_filter import QuestNpcFilterFrame
        rows=tuple(QuestRow(r['caption'],tuple(r['subitems'])) for r in self.lists[quest_refresh.LIST_PATH])
        state.rows=QuestRowSink(rows);state.npc_selected=index
        frame=QuestNpcFilterFrame(state.collection,state.rows,index,state.npcs.items,equality_mode='owned_bytes',sort_mode='owned')
        self.source_quest_refresh_ticket+=1;self.source_quest_refresh_operation='npc_filter'
        self.source_quest_refresh_pending=(frame,self.source_quest_filter_provider)
        self.source_quest_refresh_projection=(copy.deepcopy(self.lists[quest_refresh.LIST_PATH]),state.npc_selected)
        self.source_quest_refresh_error=None;self.source_quest_availability()
        self.advance_source_quest_refresh()
        return self.source_quest_refresh_result

    def set_source_quest_details_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable captured details provider required')
        if self.source_quest_refresh_pending is not None and self.source_quest_refresh_operation=='details':
            self.cancel_source_quest_refresh_timer();self.source_quest_refresh_generation+=1
            self.source_quest_refresh_pending=None;self.source_quest_refresh_result=None
            self.source_quest_refresh_error=None
        self.source_quest_details_provider=provider;self.source_quest_availability()

    def source_quest_detail_headings(self):
        widget=self.widgets.get(quest_details.DETAILS_PATH)
        if widget is not None and widget.winfo_exists():
            return tuple(widget.heading(c,'text') for c in widget['columns'])
        if self.source_quest_details_painted_headings is not None:return self.source_quest_details_painted_headings
        node=next(n for n in self.catalog if n['path']==quest_details.DETAILS_PATH)
        return tuple(c.get('Caption','') for c in node['properties']['Columns'])

    def restore_source_quest_detail_headings(self):
        state=self.source_quest_details_state;widget=self.widgets.get(quest_details.DETAILS_PATH)
        if state is not None and widget is not None and widget.winfo_exists():
            for column,text in zip(widget['columns'],state.headings):widget.heading(column,text=text)

    def paint_source_quest_details(self):
        state=self.source_quest_details_state
        if state is None:return
        rows=[dict(caption=r.caption,subitems=list(r.subitems),checked=False) for r in state.rows]
        if self.lists[quest_details.DETAILS_PATH]!=rows:
            self.lists[quest_details.DETAILS_PATH]=rows
            widget=self.widgets.get(quest_details.DETAILS_PATH)
            if widget is not None and widget.winfo_exists():
                widget.delete(*widget.get_children())
                for i,row in enumerate(rows):widget.insert('','end',iid=str(i),values=(row['caption'],*row['subitems']))
        self.source_quest_details_painted_headings=state.headings;self.restore_source_quest_detail_headings()
        self.source_quest_details_projection=(copy.deepcopy(rows),state.headings)

    def paint_source_quest_operation(self):
        if self.source_quest_refresh_operation=='action':return
        if self.source_quest_refresh_operation=='details':self.paint_source_quest_details()
        else:self.paint_source_quest_refresh()

    def set_source_quest_action_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable captured action provider required')
        if self.source_quest_refresh_pending is not None and self.source_quest_refresh_operation=='action':
            self.source_quest_refresh_pending[0].cancel()
            self.cancel_source_quest_refresh_timer();self.source_quest_refresh_generation+=1
            self.source_quest_refresh_pending=None;self.source_quest_refresh_result=None
            self.source_quest_refresh_error=None
        self.source_quest_action_provider=provider;self.source_quest_availability()

    def start_source_quest_action(self,method):
        if method not in ('take','give'):raise ValueError('Selected take or give required')
        if self.source_quest_refresh_pending is not None or self.source_quest_pending:
            self.list_help.set('Görev işlemi sürüyor.');return None
        state=self.source_quest_refresh_state;table=self.widgets.get(quest_details.MAIN_PATH)
        if state is None or not callable(self.source_quest_action_provider):
            self.list_help.set('Görev Al/Ver için veri bağlantısı gerekli.');return None
        if table is None or not table.winfo_exists():return None
        selected=table.selection();index=table.get_children().index(selected[0]) if selected else -1
        rows=tuple(QuestRow(r['caption'],tuple(r['subitems'])) for r in self.lists[quest_details.MAIN_PATH])
        frame=quest_action.QuestActionFrame(method,state.collection,rows,index,use_owned_scalar_model=True)
        session=self.flood_session
        def write(queue):session.queue=queue
        worker=quest_action_worker.QuestActionWorker(frame,lambda:session.queue,write)
        self.source_quest_refresh_ticket+=1;self.source_quest_refresh_operation='action'
        self.source_quest_refresh_pending=(worker,self.source_quest_action_provider)
        self.source_quest_refresh_projection=(copy.deepcopy(self.lists[quest_details.MAIN_PATH]),state.npc_selected)
        self.source_quest_refresh_error=None;self.source_quest_availability()
        self.advance_source_quest_refresh()
        return self.source_quest_refresh_result

    def start_source_quest_details(self,event=None):
        if self.source_quest_refresh_pending is not None or self.source_quest_pending:
            self.list_help.set('Görev işlemi sürüyor.');return None
        state=self.source_quest_refresh_state;table=self.widgets.get(quest_details.MAIN_PATH)
        if state is None or not callable(self.source_quest_details_provider):
            self.list_help.set('Görev ayrıntıları için veri bağlantısı gerekli.');return None
        if table is None or not table.winfo_exists():return None
        selected=table.selection();index=table.get_children().index(selected[0]) if selected else -1
        headings=self.source_quest_detail_headings()
        rows=tuple(QuestRow(r['caption'],tuple(r['subitems'])) for r in self.lists[quest_details.DETAILS_PATH])
        main_rows=tuple(QuestRow(r['caption'],tuple(r['subitems'])) for r in self.lists[quest_details.MAIN_PATH])
        details=quest_details.QuestDetailsState(headings,rows)
        frame=quest_details.QuestDetailsFrame(state.collection,details,main_rows,index,use_owned_scalar_model=True)
        self.source_quest_details_state=details;self.source_quest_details_painted_headings=headings
        self.source_quest_details_projection=(copy.deepcopy(self.lists[quest_details.DETAILS_PATH]),headings)
        self.source_quest_refresh_ticket+=1;self.source_quest_refresh_operation='details'
        self.source_quest_refresh_pending=(frame,self.source_quest_details_provider)
        self.source_quest_refresh_projection=(copy.deepcopy(self.lists[quest_details.MAIN_PATH]),state.npc_selected)
        self.source_quest_refresh_error=None;self.source_quest_availability()
        self.advance_source_quest_refresh()
        return self.source_quest_refresh_result

    def restore_source_quest_npcs(self):
        widget=self.widgets.get(quest_refresh.NPC_PATH)
        if self.source_quest_npc_items is not None and widget is not None and widget.winfo_exists():
            widget.configure(values=self.source_quest_npc_items)
            index=self.source_quest_refresh_state.npc_selected if self.source_quest_refresh_state is not None else self.values[quest_refresh.NPC_PATH]
            if 0<=index<len(self.source_quest_npc_items):widget.current(index)
            else:widget.set('')

    def paint_source_quest_refresh(self):
        state=self.source_quest_refresh_state
        if state is None:return
        rows=[dict(caption=r.caption,subitems=list(r.subitems),checked=False) for r in state.rows.rows]
        if self.lists[quest_refresh.LIST_PATH]!=rows:
            self.lists[quest_refresh.LIST_PATH]=rows
            table=self.widgets.get(quest_refresh.LIST_PATH)
            if table is not None and table.winfo_exists():
                table.delete(*table.get_children())
                for i,row in enumerate(rows):table.insert('','end',iid=str(i),values=(row['caption'],*row['subitems']))
        self.source_quest_npc_items=state.npcs.items
        self.restore_source_quest_npcs()
        self.source_quest_refresh_projection=(copy.deepcopy(rows),state.npc_selected)

    def start_source_quest_refresh(self):
        if not callable(self.source_quest_refresh_provider):
            self.list_help.set('Görev listesi için veri bağlantısı gerekli.');return None
        if self.source_quest_refresh_pending is not None or self.source_quest_pending:
            self.list_help.set('Görev işlemi sürüyor.');return None
        previous=self.source_quest_refresh_state
        collection=previous.collection if previous is not None else QuestCollection()
        rows=tuple(QuestRow(r['caption'],tuple(r['subitems'])) for r in self.lists[quest_refresh.LIST_PATH])
        choices=self.source_quest_npc_items
        if choices is None:choices=tuple(self.profiles.combo_items(quest_refresh.NPC_PATH))
        selected=previous.npc_selected if previous is not None else self.values[quest_refresh.NPC_PATH]
        state=quest_refresh.QuestRefreshState(collection,QuestRowSink(rows),QuestNpcSink(choices),selected)
        frame=quest_refresh.QuestRefreshFrame(state,sort_mode='owned')
        self.source_quest_refresh_state=state;self.source_quest_refresh_ticket+=1
        self.source_quest_refresh_operation='refresh'
        self.source_quest_refresh_pending=(frame,self.source_quest_refresh_provider)
        self.source_quest_refresh_projection=(copy.deepcopy(self.lists[quest_refresh.LIST_PATH]),state.npc_selected)
        self.source_quest_refresh_error=None;self.source_quest_availability()
        self.advance_source_quest_refresh()
        return self.source_quest_refresh_result

    def advance_source_quest_refresh(self,generation=None):
        if generation is not None and generation!=self.source_quest_refresh_generation:return None
        if self.source_quest_refresh_stepping or self.source_quest_refresh_pending is None:return None
        self.cancel_source_quest_refresh_timer()
        active=self.source_quest_refresh_generation;frame,provider=self.source_quest_refresh_pending
        values=self.values;lists=self.lists;state=self.source_quest_refresh_state;self.source_quest_refresh_stepping=True
        operation=self.source_quest_refresh_operation;details=self.source_quest_details_state
        def current():
            return active==self.source_quest_refresh_generation and self.source_quest_refresh_pending is not None and self.source_quest_refresh_pending[0] is frame and self.values is values and self.lists is lists and self.source_quest_refresh_state is state and (operation!='details' or self.source_quest_details_state is details)
        def view_current():
            main=(self.lists[quest_refresh.LIST_PATH],state.npc_selected)==self.source_quest_refresh_projection
            return main and (operation!='details' or (self.lists[quest_details.DETAILS_PATH],self.source_quest_detail_headings())==self.source_quest_details_projection)
        try:
            if not view_current():
                self.source_quest_refresh_error='view_conflict'
                self.list_help.set('Görev listesi değişti; yenileme bekletiliyor.');return None
            try:
                result=frame.advance()
                if not result.complete and not (operation=='action' and result.status in ('needs_queue_publish','queue_conflict')):
                    if operation=='action':
                        child=frame.frame
                        context=quest_action_worker.QuestActionContext(self.source_quest_refresh_ticket,active,child.method,child.phase,child.selected,child.cache.get('record_index'),result.needed)
                    else:context=(quest_details.QuestDetailsContext(self.source_quest_refresh_ticket,active,frame.phase,frame.selected,frame.cache.get('record_index'),result.needed)
                             if operation=='details' else quest_refresh.QuestRefreshContext(self.source_quest_refresh_ticket,active,frame.phase,frame.index,result.needed))
                    observation=provider(context)
                    if not current():return None
                    if not view_current():
                        self.source_quest_refresh_error='view_conflict'
                        self.list_help.set('Görev listesi değişti; yenileme bekletiliyor.');return None
                    if observation is not None:result=frame.advance(observation)
                if not current():return None
                self.source_quest_refresh_result=result;self.source_quest_refresh_error=None
                self.paint_source_quest_operation()
                if result.complete:self.source_quest_refresh_pending=None
                self.list_help.set(('Görev seçilmedi.' if result.status=='no_selection' else 'Görev Al/Ver yerel akışı tamamlandı; oyun sonucu doğrulanmadı.' if operation=='action' else 'Görev ayrıntıları güncellendi (yerel veriler).' if operation=='details' else 'Görev listesi güncellendi (yerel veriler).') if result.complete else 'Görev bilgisi için veri bekleniyor.')
                return result
            except (ValueError,OSError) as error:
                if current() and view_current():
                    self.source_quest_refresh_error=str(error);self.paint_source_quest_operation()
                    self.list_help.set('Görev listesi güncellenemedi; mevcut kısmı korundu.')
                return None
        finally:
            self.source_quest_refresh_stepping=False;self.source_quest_availability()
            if current():
                self.source_quest_refresh_after_id=self.canvas.after(100,lambda:self.advance_source_quest_refresh(active))

    def source_quest_sink(self):
        panel=self;values=self.values;lists=self.lists
        def current():
            if panel.values is not values or panel.lists is not lists:raise ValueError('Quest profile changed')
        class Sink:
            def count(self):current();return len(lists[quest_metadata.LIST_PATH])
            def caption(self,index):
                current();rows=lists[quest_metadata.LIST_PATH]
                if not 0<=index<len(rows):raise ValueError('Quest row no longer available')
                return rows[index]['caption']
            def selected_index(self):
                current();table=panel.widgets.get(quest_metadata.LIST_PATH)
                if table is None or not table.winfo_exists():raise ValueError('Current Quest selection unavailable')
                selected=table.selection()
                return table.get_children().index(selected[0]) if selected else -1
        return Sink()

    def source_quest_availability(self):
        refreshing=self.source_quest_refresh_pending is not None
        for path in quest_action_worker.METHODS:
            widget=self.widgets.get(path)
            if widget is not None and widget.winfo_exists():
                node=next(n for n in self.catalog if n['path']==path)
                enabled=callable(self.source_quest_action_provider) and self.source_quest_refresh_state is not None and not refreshing and not self.source_quest_pending and node['properties'].get('Enabled') is not False and not node['disabled_by']
                widget.state(['!disabled'] if enabled else ['disabled'])
        combo=self.widgets.get(quest_refresh.NPC_PATH)
        if combo is not None and combo.winfo_exists():
            node=next(n for n in self.catalog if n['path']==quest_refresh.NPC_PATH)
            enabled=not refreshing and not self.source_quest_pending and node['properties'].get('Enabled') is not False and not node['disabled_by']
            combo.configure(state='readonly' if enabled else 'disabled')
        widget=self.widgets.get(quest_refresh.BUTTON_PATH)
        if widget is not None and widget.winfo_exists():
            node=next(n for n in self.catalog if n['path']==quest_refresh.BUTTON_PATH)
            enabled=callable(self.source_quest_refresh_provider) and not refreshing and not self.source_quest_pending and node['properties'].get('Enabled') is not False and not node['disabled_by']
            widget.state(['!disabled'] if enabled else ['disabled'])
        for path in quest_metadata.METHODS:
            node=next(n for n in self.catalog if n['path']==path)
            enabled=callable(self.source_quest_provider) and not refreshing and node['properties'].get('Enabled') is not False and not node['disabled_by']
            widget=self.widgets.get(path)
            if widget is not None and widget.winfo_exists():widget.state(['!disabled'] if enabled else ['disabled'])

    def cancel_source_quest_timer(self):
        if self.source_quest_after_id is not None:
            try:self.canvas.after_cancel(self.source_quest_after_id)
            except tk.TclError:pass
            self.source_quest_after_id=None

    def reset_source_quest(self,reason):
        self.cancel_source_quest_timer();self.source_quest_generation+=1
        for _,frame,_ in self.source_quest_pending:frame.cancel(reason)
        self.source_quest_pending.clear();self.source_quest_provider=None;self.source_quest_result=None
        self.source_quest_availability()

    def set_source_quest_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable captured Quest provider required')
        self.reset_source_quest('provider_change');self.source_quest_provider=provider;self.source_quest_availability()

    def schedule_source_quest_timer(self):
        self.cancel_source_quest_timer()
        if self.source_quest_pending:
            generation=self.source_quest_generation
            self.source_quest_after_id=self.canvas.after(100,lambda:self.advance_source_quest(generation))

    def start_source_quest(self,method):
        if self.source_quest_refresh_pending is not None:
            self.list_help.set('Görev listesi yenileniyor.');return None
        if not callable(self.source_quest_provider):
            self.list_help.set('Görev bilgisi bağlantısı gerekli.');return None
        frame=quest_metadata.QuestMetadataFrame(method,self.source_quest_sink());self.source_quest_invocation+=1
        self.source_quest_pending.append((self.source_quest_invocation,frame,self.source_quest_provider))
        if not self.source_quest_stepping:self.advance_source_quest()
        return frame.result

    def advance_source_quest(self,generation=None):
        if generation is not None and generation!=self.source_quest_generation:return None
        if self.source_quest_stepping:return None
        self.cancel_source_quest_timer()
        if not self.source_quest_pending:return None
        active=self.source_quest_generation;ticket,frame,provider=self.source_quest_pending[0]
        self.source_quest_stepping=True
        def current():
            return active==self.source_quest_generation and bool(self.source_quest_pending) and self.source_quest_pending[0][1] is frame
        try:
            try:result=frame.advance()
            except (ValueError,OSError) as error:result=frame.hold(error)
            if not result.done and result.status!='continuation':
                context=quest_metadata.QuestMetadataContext(ticket,active,frame.method,frame.phase,frame.index,result.needed)
                try:capture=provider(context)
                except (ValueError,OSError) as error:capture=None;result=frame.hold(error)
                if not current():return None
                if capture is not None:
                    try:result=frame.advance(capture)
                    except (ValueError,OSError) as error:result=frame.hold(error)
            if not current():return None
            self.source_quest_result=result
            if result.done:self.source_quest_pending.pop(0)
            self.list_help.set('Görev bilgisi okundu.' if result.complete and result.status!='no_selection' else
                'Görev seçilmedi.' if result.status=='no_selection' else 'Görev bilgisi bekleniyor.' if not result.done else 'Görev bilgisi okunamadı.')
            return result
        finally:self.source_quest_stepping=False;self.schedule_source_quest_timer();self.source_quest_availability()

    def cancel_auto_item_break_timer(self):
        if self.auto_item_break_after_id is not None:
            try:self.canvas.after_cancel(self.auto_item_break_after_id)
            except tk.TclError:pass
            self.auto_item_break_after_id=None

    def configure_auto_item_break(self):
        self.cancel_auto_item_break_timer()
        self.auto_item_break.configure(self.values[auto_break_runtime.ENABLE_PATH])
        self.auto_item_break_result=None
        self.schedule_auto_item_break_timer()

    def schedule_auto_item_break_timer(self):
        self.cancel_auto_item_break_timer()
        if self.auto_item_break.enabled:
            generation=self.auto_item_break.generation
            self.auto_item_break_after_id=self.canvas.after(auto_break_runtime.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_auto_item_break(generation))

    def advance_auto_item_break(self,generation=None):
        runtime=self.auto_item_break
        if generation is not None and generation!=runtime.generation:return None
        if self.auto_item_break_stepping:return None
        self.cancel_auto_item_break_timer()
        if not runtime.enabled:return None
        current_generation=runtime.generation;self.auto_item_break_stepping=True
        try:
            config={path:self.values[path] for _,path in ITEM_BREAK_FIELDS}
            context=runtime.context(self.flood_session.queue,config)
            inputs=self.auto_item_break_provider(context) if self.auto_item_break_provider else auto_break_runtime.AutoBreakInput()
            if current_generation!=runtime.generation or not runtime.enabled:return None
            result=runtime.advance(self.flood_session.queue,inputs)
            self.auto_item_break_result=result;self.flood_session.queue=result.queue
            labels={'outer_gate_zero':'Bot çalışma koşulu bekleniyor','settings_disabled':'Kaynak çalışma bayrağı kapalı',
                'second_work_gate_zero':'İkinci çalışma bayrağı kapalı','waiting':'Item kırma süresi bekleniyor',
                'nonzero_mode_skips_clock':'Bu mod otomatik istek üretmedi',
                'action_returned_clock_updated':'Otomatik item kırma adımı ve zaman damgası işlendi',
                'conflicting_clock_observation':'Saat gözlemi önceki yerel zaman damgasıyla uyuşmuyor',
                'npc_zero_stop_notice_returned':'NPC bulunamayan durdurma/uyarı yolu işlendi'}
            self.list_help.set(labels.get(result.status,'Otomatik item kırma: işlem verisi veya yardımcı dönüşü bekleniyor')+
                ' • Yerel gözlem; oyuna gönderim bağlı değil')
            return result
        except (OSError,ValueError) as error:
            if current_generation==runtime.generation:self.list_help.set('Otomatik item kırma verisi alınamadı: '+str(error))
            return None
        finally:
            self.auto_item_break_stepping=False
            if current_generation==runtime.generation:self.schedule_auto_item_break_timer()

    def cancel_manual_item_break_timer(self):
        if self.manual_item_break_after_id is not None:
            try:self.canvas.after_cancel(self.manual_item_break_after_id)
            except tk.TclError:pass
            self.manual_item_break_after_id=None

    def schedule_manual_item_break_timer(self):
        self.cancel_manual_item_break_timer()
        if self.manual_item_break.pending:
            generation=self.manual_item_break.generation
            self.manual_item_break_after_id=self.canvas.after(manual_break_runtime.OWN_TIMER_PERIOD_MS,
                lambda:self.advance_manual_item_break(generation))

    def start_manual_item_break(self):
        self.manual_item_break.click();self.manual_item_break_result=None
        result=self.advance_manual_item_break()
        self.schedule_manual_item_break_timer()
        return result

    def advance_manual_item_break(self,generation=None):
        runtime=self.manual_item_break
        if generation is not None and generation!=runtime.generation:return None
        if self.manual_item_break_stepping:return None
        self.cancel_manual_item_break_timer()
        if not runtime.pending:return None
        current_generation=runtime.generation;self.manual_item_break_stepping=True
        try:
            context=runtime.context(self.flood_session.queue)
            captures=(self.manual_item_break_provider(context) if self.manual_item_break_provider
                else manual_break_runtime.ManualBreakInput())
            if current_generation!=runtime.generation or not runtime.pending:return None
            result=runtime.advance(self.flood_session.queue,captures)
            self.manual_item_break_result=result;self.flood_session.queue=result.queue
            if result.complete:
                labels={'npc_zero_notice_returned':'NPC yakınında olunmalı',
                    'gem_zero_notice_returned':'Abyss Gem bulunamadı',
                    'nonzero_mode_skips_manual_action':'Bu mod manuel işlem üretmedi',
                    'request_child_returned':'Manuel item kırma adımı tamamlandı'}
                text=labels.get(result.status,'Manuel item kırma adımı tamamlandı')
            else:text='Manuel item kırma: işlem verisi veya yardımcı dönüşü bekleniyor'
            self.list_help.set(text+' • Yerel gözlem; oyuna gönderim bağlı değil')
            return result
        except (OSError,ValueError) as error:
            if current_generation==runtime.generation:self.list_help.set('Manuel item kırma verisi alınamadı: '+str(error))
            return None
        finally:
            self.manual_item_break_stepping=False
            if current_generation==runtime.generation:self.schedule_manual_item_break_timer()

    def schedule_merchant_scan_timer(self):
        self.cancel_merchant_scan_timer()
        if self.merchant_scan_loop.state.active:
            generation=self.merchant_scan_loop.generation
            self.merchant_scan_after_id=self.canvas.after(OWN_TIMER_PERIOD_MS,
                lambda:self.advance_merchant_scan_loop(generation))

    def advance_merchant_scan_loop(self,generation=None):
        loop=self.merchant_scan_loop
        if generation is not None and generation!=loop.generation:return None
        self.cancel_merchant_scan_timer()
        if not loop.state.active:return None
        current_generation=loop.generation
        try:
            context=loop.context(self.merchant_scan.state,self.flood_session.queue)
            captures=self.merchant_scan_provider(context) if self.merchant_scan_provider else ScanLoopInput()
            # Providers can stop, restart, or replace the profile reentrantly.
            if current_generation!=loop.generation or not loop.state.active:return None
            result=loop.advance(self.merchant_scan.state,self.flood_session.queue,captures,clock=self.flood_clock)
            self.merchant_scan_loop_result=result
            self.merchant_scan.state=result.control
            self.flood_session.queue=result.queue
            if result.added_records:
                self.accept_merchant_records(self.merchant_results.records+result.added_records)
            if result.status=='completed':
                self.merchant_scan_update=self.merchant_scan.stop(self.merchant_scan_button,self.merchant_scan_status,completed=True)
                self.list_help.set('Yerel tarama tamamlandı • Oyunda doğrulama yapılmadı')
            elif not result.active:
                self.merchant_scan_update=self.merchant_scan.stop(self.merchant_scan_button,self.merchant_scan_status)
                self.list_help.set('Tarama akışı tamamlanamadı: '+result.status)
            else:
                labels={'busy':'Tarama yanıtı bekleniyor','waiting':'Sonraki tarama adımı bekleniyor',
                    'needs_child_observation':'Tarama verisi bekleniyor','needs_parent_return':'Tarama adımının dönüşü bekleniyor',
                    'local_step':'Yerel tarama adımı işlendi','reply_scan_consumed':'Tarama yanıtı işlendi',
                    'reply_needs_metadata':'Yanıtın karakter ve eşya bilgileri bekleniyor',
                    'reply_needs_parser_return':'Yanıt okuma adımının dönüşü bekleniyor',
                    'reply_needs_finish_setup':'Yanıt sonlandırma hazırlığı bekleniyor',
                    'reply_needs_finish_enqueue':'Yanıt sonlandırma kuyruğu bekleniyor',
                    'reply_needs_finish_return':'Yanıt sonlandırma dönüşü bekleniyor',
                    'reply_truncated':'Eksik tarama yanıtı alındı','reply_truncated_scan_data':'Eksik tarama verisi alındı',
                    'reply_outside_active_scan_scope':'Yanıt tarama kapsamı dışında','own_clock_error':'Tarama saati okunamadı'}
                self.list_help.set(labels.get(result.status,'Tarama için ek gözlem bekleniyor')+' • Oyunda doğrulama yapılmadı')
            return result
        except (OSError,ValueError) as error:
            if current_generation==loop.generation:
                self.list_help.set('Tarama verisi alınamadı: '+str(error))
            return None
        finally:
            if current_generation==loop.generation:self.schedule_merchant_scan_timer()

    def receive_merchant_scan_reply(self,payload):
        """Accept explicit immutable captured bytes; this installs no hook."""
        ticket=self.merchant_scan_loop.enqueue_reply(payload)
        if ticket is not None:self.schedule_merchant_scan_timer()
        return ticket

    def quick_scan_merchants(self):
        self.merchant_quick_result=None
        self.merchant_results.replace_records(())
        self.merchant_result_update=None
        table=self.widgets.get(MERCHANT_TABLE)
        if table is not None:table.delete(*table.get_children())
        try:
            snapshot=self.merchant_quick_provider() if self.merchant_quick_provider else None
            self.merchant_quick_result=prepare_quick_table(snapshot)
        except (OSError,ValueError) as error:
            self.list_help.set('Tek tarama verisi alınamadı: '+str(error));return None
        result=self.merchant_quick_result
        if not result.complete:
            self.list_help.set('Tek tarama bekliyor: veri bağlantısı gerekli' if result.status=='needs_quick_scan_provider'
                else 'Tek tarama verisi tamamlanamadı')
            return result
        update=self.accept_merchant_records(result.display_records)
        if update.complete:self.list_help.set('Yerel tek tarama: %d görünür kayıt'%len(update.rows))
        return result

    def accept_merchant_records(self, records):
        """Accept explicit decoded records, never poll a game or replay packets."""
        self.merchant_results.replace_records(records)
        return self.refresh_merchant_results()

    def export_merchant_txt(self):
        self.merchant_export_result=None
        update=self.merchant_result_update;table=self.widgets.get(MERCHANT_TABLE)
        if update is None or not update.complete or table is None:
            self.list_help.set('TXT: önce sonuç listesi tamamlanmalı');return None
        actual=tuple(tuple(table.item(i,'values')) for i in table.get_children())
        expected=tuple((r.caption,)+r.subitems for r in update.rows)
        if actual!=expected:
            self.list_help.set('TXT: sonuç listesi yenilenmeli');return None
        # Read current header controls, including the placeholder if present.
        query=self.values[MERCHANT_SEARCH]
        category=self.profiles.combo_text(self.values,MERCHANT_CATEGORY)
        kind=self.profiles.combo_text(self.values,MERCHANT_KIND)
        try:
            context=self.merchant_export_context_provider() if self.merchant_export_context_provider else None
            self.merchant_export_result=export_displayed_txt(context,kind,category,query,update.rows)
        except (OSError,ValueError) as error:
            self.list_help.set('TXT hazırlanamadı: '+str(error));return None
        result=self.merchant_export_result
        if result.complete:self.list_help.set('TXT kaydedildi: '+result.path)
        elif result.status=='needs_export_context':self.list_help.set('TXT: kimlik, zaman ve kodlama bağlamı bekleniyor')
        else:self.list_help.set('TXT kaydı tamamlanamadı: '+(result.error or result.close_error or result.status))
        return result

    def refresh_merchant_results(self):
        query=self.values[MERCHANT_SEARCH]
        # Explicit captured query observations override our own local policy.
        # The own host ACP is not an observation of the game's RTL global.
        normalized=None
        policy=None
        if query and self.merchant_search_color==0 and self.merchant_search_observer is not None:
            normalized=self.merchant_search_observer(query)
        if query and self.merchant_search_color==0 and (self.merchant_search_observer is None or normalized is not None):
            if self.merchant_text_factory is not None:
                try:
                    policy=self.merchant_text_factory(self.merchant_codepage_reader())
                except (OSError,ValueError) as error:
                    self.merchant_text_policy=None
                    self.merchant_result_update=MerchantTableUpdate(False,'local_text_policy:'+str(error),None)
                    self.merchant_results.last=self.merchant_result_update
                    self.paint_merchant_results()
                    return self.merchant_result_update
        self.merchant_text_policy=policy
        self.merchant_result_update=self.merchant_results.rebuild(
            self.profiles.combo_text(self.values,MERCHANT_KIND),
            self.profiles.combo_text(self.values,MERCHANT_CATEGORY),query,
            search_color=self.merchant_search_color,normalized_search=normalized,text_policy=policy)
        self.paint_merchant_results()

        return self.merchant_result_update

    def focus_merchant_search(self, phase):
        plan=plan_search_focus(self.values[MERCHANT_SEARCH],self.merchant_search_color,phase)
        if plan.changed:
            variable=self.variables.get(MERCHANT_SEARCH)
            if variable is not None:variable.set(plan.text)
            else:self.set_value(MERCHANT_SEARCH,plan.text)
            # SetText/OnChange sees the previous color; SetColor is later.
            self.merchant_search_color=plan.color
            self.paint_merchant_search_color()
            if plan.rebuild_requested:self.refresh_merchant_results()
        return plan

    def paint_merchant_search_color(self):
        widget=self.widgets.get(MERCHANT_SEARCH)
        if widget is not None:
            style='MerchantSearch%x.TEntry'%id(self)
            ttk.Style(widget).configure(style,foreground='black' if self.merchant_search_color==0 else 'SystemGrayText')
            widget.configure(style=style)

    def sort_merchant_column(self, column):
        try:self.merchant_result_update=self.merchant_results.sort_column(column)
        except ValueError as error:
            self.list_help.set('Merchant: '+str(error));return None
        self.paint_merchant_results()
        return self.merchant_result_update

    def paint_merchant_results(self):
        update=self.merchant_result_update
        widget=self.widgets.get(MERCHANT_TABLE)
        if update is None:return
        if widget is not None:
            widget.delete(*widget.get_children())
            for index,row in enumerate(update.rows):
                widget.insert('', 'end', iid=str(index), values=(row.caption,)+row.subitems)
            self.list_help.set(('Yerel Merchant: %d kayıt'%len(update.rows)) if update.complete
                else 'Merchant eksik aşama: '+update.status)

    def merchant_cell_release(self,event):
        widget=self.widgets.get(MERCHANT_TABLE)
        update=self.merchant_result_update
        if widget is None:return
        if widget.identify_region(event.x,event.y)!='cell':return
        column=widget.identify_column(event.x)
        if column not in ('#5','#6'):return
        self.merchant_cell_result=None
        if update is None or not update.complete:return
        selected=widget.selection()
        if not selected or widget.identify_row(event.y)!=selected[0]:return
        try:
            index=int(selected[0]);row=update.rows[index]
            if tuple(widget.item(selected[0],'values'))!=(row.caption,)+row.subitems:
                self.list_help.set('Merchant: tablo yenilenmeli');return
        except (ValueError,IndexError):return
        if column=='#6':
            self.cancel_merchant_scan_timer()
            self.merchant_scan_loop.stop('move_to_seller')
            self.merchant_scan_update=self.merchant_scan.interrupt_for_movement(self.merchant_scan_button)
        self.merchant_cells.queue=self.flood_session.queue
        self.merchant_cell_result=self.merchant_cells.activate(row,int(column[1:])-1,
            codec_factory=self.flood_codec_factory,codepage_reader=self.merchant_codepage_reader,
            clock=self.flood_clock)
        self.flood_session.queue=self.merchant_cell_result.queue
        result=self.merchant_cell_result
        if not result.complete:self.list_help.set('Merchant eksik aşama: '+result.status)
        elif result.action=='private_chat':
            self.list_help.set('Yerel PM kuyruğu: %d kayıt • Gönderim bağlantısı bekliyor'%len(result.queue.records))
        elif result.action=='move_to_seller':
            self.list_help.set('Yerel GİT hedefi: %s, %s • Hareket bağlantısı bekliyor'%(row.subitems[5],row.subitems[6]))

    def combo_texts(self):
        return {path:self.profiles.combo_text(self.values,path) for path in ROUTE_COMBO_PATHS.values()}

    def refresh_route_combo(self,path):
        self.route_catalog_last=None
        try:
            if self.route_catalog_reader is None:raise ValueError('Rota klasörü bağlantısı gerekli')
            catalog=self.route_catalog_reader()
            self.route_catalog_last=catalog
            if not catalog.complete:raise ValueError('Rota klasörü tam okunamadı: '+catalog.missing)
            self.profiles.install_route_choices(self.values,path,catalog.rows)
            widget=self.widgets.get(path)
            if widget is not None:widget.configure(values=catalog.rows);widget.set('')
            if catalog.failed_operation=='scandir_open':self.list_help.set('Rota klasörü açılamadı; liste temizlendi')
            elif catalog.failed_operation=='scandir_next':self.list_help.set('Tarama kesildi; yalnız okunan rota adları gösteriliyor')
            else:self.list_help.set('Rota listesi yenilendi; bir dosya seçin')
            return catalog
        except (ValueError,OSError) as error:
            self.list_help.set('Rota listesi okunamadı: '+str(error))
            return None

    def apply_boolean_updates(self, updates):
        self.profiles.apply_boolean_updates(self.values,updates)
        for path,value in updates.items():
            if path in self.variables:self.variables[path].set(value)
        prefix='frmMain/MainTab/SheetBot/GroupBox5/'
        pool=(prefix+'chOnlyMobSelect',prefix+'chOnlyPlayerSelect')
        if any(path in updates for path in pool):
            for path in pool:
                if path in self.variables:self.variables[path].set(self.values[path])
        for group in self.profiles.radio_groups.values():
            if any(path in updates for path in group):
                parent=group[0].rsplit('/',1)[0]
                if parent in self.radio_variables:
                    self.radio_variables[parent].set(next((p for p in group if self.values[p]),''))

    def render(self):
        if self.surface is not None:
            self.surface.destroy()
        self.canvas.delete('all')
        self.widgets, self.variables, self.radio_variables = {}, {}, {}
        source = next(n for n in self.forms if n['path'] == self.form.get())
        if self.form.get()=='frmBlackList':self.name_cfg_bar.pack(fill='x',after=self.toolbar)
        else:self.name_cfg_bar.pack_forget()
        self.list_help.set('İsim listeleri: çift tıkla → seçileni sil' if self.form.get()=='frmBlackList' else 'Listeler: çift tıkla → düzenle')
        props = source['properties']
        width, height = props.get('ClientWidth', 874), props.get('ClientHeight', 471)
        self.surface = ttk.Frame(self.canvas, width=width, height=height)
        self.canvas.create_window(0, 0, window=self.surface, anchor='nw')
        self.canvas.configure(scrollregion=(0, 0, max(width, 900), max(height, 500)))
        self.widgets[source['path']] = self.surface
        for node in self.catalog:
            path = node['path']
            if not path.startswith(source['path'] + '/'):
                continue
            parent_path = path.rsplit('/', 1)[0]
            parent = self.widgets[parent_path]
            p, cls = node['properties'], node['class']
            caption = p.get('Caption', '')
            if path==TOGGLE_PATH:caption=self.flood_session.state.caption
            if cls == 'TTabSheet':
                widget = ttk.Frame(parent)
                parent.add(widget, text=caption or path.rsplit('/', 1)[-1])
            elif cls == 'TPageControl':
                widget = ttk.Notebook(parent)
            elif cls == 'TGroupBox':
                widget = ttk.LabelFrame(parent, text=caption)
            elif cls == 'TPanel':
                widget = ttk.Frame(parent)
            elif cls == 'TLabel':
                widget = ttk.Label(parent, text=caption, font=('Tahoma', 8), anchor='w')
            elif cls == 'TCheckBox':
                variable = tk.BooleanVar(value=self.values[path])
                self.variables[path] = variable
                widget = ttk.Checkbutton(parent, text=caption, variable=variable,
                    command=lambda k=path, v=variable: self.set_value(k, v.get()))
            elif cls == 'TRadioButton':
                group = self.profiles.radio_groups[parent_path]
                if parent_path not in self.radio_variables:
                    selected = next((k for k in group if self.values[k]), '')
                    self.radio_variables[parent_path] = tk.StringVar(value=selected)
                widget = ttk.Radiobutton(parent, text=caption, variable=self.radio_variables[parent_path],
                    value=path, command=lambda k=path: self.set_value(k, True))
            elif cls == 'TEdit':
                variable = tk.StringVar(value=self.values[path])
                self.variables[path] = variable
                widget = ttk.Entry(parent, textvariable=variable)
                variable.trace_add('write', lambda *_, k=path, v=variable: self.set_value(k, v.get()))
                if path==MERCHANT_SEARCH:
                    widget.bind('<FocusIn>',lambda _:self.focus_merchant_search('enter'))
                    widget.bind('<FocusOut>',lambda _:self.focus_merchant_search('exit'))
                if p.get('ReadOnly', False):
                    widget.configure(state='readonly')
            elif cls == 'TComboBox':
                choices = self.profiles.combo_items(path)
                widget = ttk.Combobox(parent, values=choices, state='readonly')
                if path in ROUTE_COMBO_PATHS.values() or path==route_load_runtime.EDITOR_PATH:
                    widget.configure(postcommand=lambda k=path:self.refresh_route_combo(k))
                if 0 <= self.values[path] < len(choices):
                    widget.current(self.values[path])
                elif path==parameter_ui.SCROLL_PATH:
                    parameter_ui.restore_scroll_text(widget,self.values,self.source_upgrade_parameter_text_cache)
                if path==route_load_runtime.EDITOR_PATH:
                    widget.bind('<<ComboboxSelected>>',lambda _,w=widget:self.load_source_route(w.current()))
                elif path==quest_refresh.NPC_PATH:
                    widget.bind('<<ComboboxSelected>>',lambda _,w=widget:self.select_source_quest_npc(w.current()))
                else:widget.bind('<<ComboboxSelected>>', lambda _, k=path, w=widget: self.set_value(k, w.current()))
            elif cls == 'TScrollBar':
                variable = tk.DoubleVar(value=self.values[path])
                self.variables[path] = variable
                widget = ttk.Scale(parent, from_=p.get('Min', 0), to=p.get('Max', 100), variable=variable,
                    command=lambda v, k=path: self.set_value(k, int(float(v))))
            elif cls == 'TListView':
                columns = p.get('Columns', [])
                names = [str(index) for index in range(max(1, len(columns)))]
                widget = ttk.Treeview(parent, columns=names, show='headings', selectmode='browse')
                for index, name in enumerate(names):
                    col = columns[index] if index < len(columns) else {}
                    widget.heading(name, text=col.get('Caption', '' if path==quest_details.DETAILS_PATH else 'Ad'))
                    if path==MERCHANT_TABLE:
                        widget.heading(name,command=lambda c=index:self.sort_merchant_column(c))
                    widget.column(name, width=col.get('Width', 90), minwidth=20)
                    if path==MERCHANT_TABLE:
                        widget.column(name,width=col.get('Width',col.get('MinWidth',50)),
                            minwidth=col.get('MinWidth',0),stretch=False)
                for index, row in enumerate(() if path==MERCHANT_TABLE else self.lists[path]):
                    title = ('☑ ' if row['checked'] else '☐ ') if p.get('Checkboxes') else ''
                    widget.insert('', 'end', iid=str(index), values=[title + row['caption']] + row['subitems'])
                if path!=MERCHANT_TABLE:
                    widget.bind('<Double-1>', lambda _, k=path: self.edit_list(k))
                else:widget.bind('<ButtonRelease-1>',self.merchant_cell_release,add='+')
                if path==quest_details.MAIN_PATH:widget.bind('<ButtonRelease-1>',self.start_source_quest_details,add='+')
            elif cls == 'TListBox':
                widget = tk.Listbox(parent, font=('Tahoma', 8))
                for row in self.lists[path]:
                    widget.insert('end', row['caption'])
                if path in LIST_PATHS.values():
                    widget.configure(exportselection=False)
                    kind=next(k for k,v in LIST_PATHS.items() if v==path)
                    widget.bind('<Double-1>',lambda _,k=kind:self.edit_name_control(k,'remove'))
                else:widget.bind('<Double-1>', lambda _, k=path: self.edit_list(k))
            elif cls in ('TButton', 'TBitBtn'):
                if path in self.button_handlers:
                    widget=ttk.Button(parent,text=caption,command=self.button_handlers[path])
                elif path in BUTTON_ACTIONS:
                    kind,action=BUTTON_ACTIONS[path]
                    widget=ttk.Button(parent,text=caption,command=lambda k=kind,a=action:self.edit_name_control(k,a))
                else:
                    # Game-dependent source buttons still require an adapter.
                    widget = ttk.Button(parent, text=caption, state='disabled')
            elif cls == 'TRichEdit':
                widget = tk.Text(parent, font=('Tahoma', 8), wrap='word')
                widget.insert('1.0', self.values.get(path, ''))
                widget.configure(state='disabled')
            elif cls == 'TProgressBar':
                widget = ttk.Progressbar(parent, maximum=p.get('Max', 100), value=p.get('Position', 0))
            elif cls == 'TImage':
                widget = ttk.Label(parent, text='Görsel', anchor='center', relief='groove')
            elif cls == 'TUpDown':
                widget = ttk.Spinbox(parent, from_=p.get('Min', 0), to=p.get('Max', 100), width=2, state='disabled')
            elif cls == 'TStatusBar':
                widget = ttk.Label(parent, text=p.get('SimpleText', ''), relief='sunken')
            else:
                widget = ttk.Frame(parent)
            self.widgets[path] = widget
            if cls != 'TTabSheet':
                x, y, w, h = p.get('Left', 0), p.get('Top', 0), p.get('Width', 100), p.get('Height', 20)
                if '/SheetJob/pnl' in path and path.count('/') == 3:
                    x, y, w, h = 3, 3, 590, 430
                widget.place(x=x, y=y, width=max(1, w), height=max(1, h))
                if (p.get('Enabled') is False or node['disabled_by']) and hasattr(widget, 'state'):
                    widget.state(['disabled'])
                visible = p.get('Visible', True)
                class_group = path.rsplit('/', 1)[-1]
                job_groups = {'pnlMage': 'Mage', 'pnlRogue': 'Rogue', 'pnlPri': 'Priest',
                              'pnlWarrior': 'Warrior', 'pnlKurian': 'Kurian'}
                if class_group in job_groups:
                    visible = job_groups[class_group] == self.job.get()
                if not visible and not self.show_inactive.get():
                    widget.place_forget()
        self.configure_navigation()
        self.paint_merchant_search_color()
        self.paint_merchant_results()
        for index,enabled in enumerate(self.merchant_scan.state.button_enabled):
            self.merchant_scan_button(index,bool(enabled))
        if self.merchant_scan.state.status_text is not None:
            self.merchant_scan_status(self.merchant_scan.state.status_text)
        if self.auto_item_break.enabled!=self.values[auto_break_runtime.ENABLE_PATH]:
            self.configure_auto_item_break()
        self.apply_source_route_panel()
        self.source_coordinate_availability()
        self.source_npc_availability()
        self.manual_coordinate_availability()
        self.source_upgrade_availability()

        self.source_quest_availability()
        self.restore_source_quest_npcs()
        self.restore_source_quest_detail_headings()

    def edit_name_control(self,kind,action):
        path=LIST_PATHS[kind];rows=self.lists[path]
        widget=self.widgets.get(path);selected=None
        if action=='remove' and widget is not None:
            indices=widget.curselection()
            if indices:selected=int(indices[0])
        text=self.values[TEXT_PATHS[kind]] if action=='add' else None
        result=edit_name_list(kind,action,tuple(r['caption'] for r in rows),text=text,selected_index=selected)
        self.name_list_result=result
        if result.changed:
            if action=='add':rows.append(dict(caption=text,subitems=[],checked=False))
            elif action=='remove':rows.pop(result.index)
            else:rows.clear()
            if widget is not None:
                widget.delete(0,'end')
                for row in rows:widget.insert('end',row['caption'])
        self.list_help.set(result.reason)
        return 'break'

    def _name_cfg_kind(self):
        choices={'Beyaz liste':'white','Kara liste':'black'}
        if self.name_cfg_kind.get() not in choices:raise ValueError('Liste seçimi geçersiz')
        return choices[self.name_cfg_kind.get()]

    def import_name_cfg_path(self,path):
        kind=self._name_cfg_kind()
        target=LIST_PATHS[kind]
        # Source004603fc clears the selected UI list before opening the file.
        self.lists[target]=[]
        widget=self.widgets.get(target)
        if widget is not None:widget.delete(0,'end')
        try:result=read_name_cfg(path,int(self.name_cfg_codepage.get()))
        except (OSError,ValueError) as e:result=NameCfgCodecResult(False,'file_import_error',missing=str(e))
        self.name_cfg_result=result
        if result.complete:
            doc=result.document
            self.lists[target]=[dict(caption=text,subitems=[],checked=False) for text in doc.rows]
            self.name_cfg_documents[kind]=doc
            widget=self.widgets.get(target)
            if widget is not None:
                widget.delete(0,'end')
                for text in doc.rows:widget.insert('end',text)
            self.list_help.set('CFG açıldı: %d isim'%len(doc.rows))
        else:self.list_help.set('Liste temizlendi; '+self._name_cfg_error(result.status))
        return result

    def export_name_cfg_path(self,path):
        kind=self._name_cfg_kind();rows=tuple(r['caption'] for r in self.lists[LIST_PATHS[kind]])
        try:
            previous=self.name_cfg_documents.get(kind)
            doc=replace(previous,rows=rows) if previous is not None else NameCfgDocument(rows,int(self.name_cfg_codepage.get()))
            result=write_name_cfg(path,doc)
        except (OSError,ValueError) as e:result=NameCfgCodecResult(False,'file_export_error',missing=str(e))
        self.name_cfg_result=result
        self.list_help.set('CFG kaydedildi' if result.complete else self._name_cfg_error(result.status))
        return result

    @staticmethod
    def _name_cfg_error(status):
        return {'file_unreadable':'CFG dosyası okunamadı','local_file_budget':'CFG dosyası boyut sınırını aşıyor',
                'unresolved_codec_conversion':'Metin seçilen kod sayfasında kayıpsız dönüştürülemedi',
                'needs_custom_delimiter_observation':'Bu satır ayıracı henüz desteklenmiyor',
                'unresolved_negative_native_length':'Bu boş liste ve satır sonu ayarı henüz desteklenmiyor',
                'file_import_error':'CFG yolu veya kod sayfası geçersiz','file_export_error':'CFG yazılamadı; yolu ve izinleri kontrol edin'}.get(status,'CFG işlemi tamamlanamadı')

    def choose_name_cfg_import(self):
        path=filedialog.askopenfilename(parent=self.surface.winfo_toplevel(),title='İsim CFG aç',filetypes=[('CFG dosyası','*.cfg'),('Tüm dosyalar','*.*')])
        if path:self.import_name_cfg_path(path)

    def choose_name_cfg_export(self):
        kind=self._name_cfg_kind();name='AntiCRWhiteList.cfg' if kind=='white' else 'AntiCRBlackList.cfg'
        path=filedialog.asksaveasfilename(parent=self.surface.winfo_toplevel(),title='İsim CFG kaydet',initialfile=name,defaultextension='.cfg',filetypes=[('CFG dosyası','*.cfg')])
        if path:self.export_name_cfg_path(path)

    def configure_navigation(self):
        self.main_tabs = [n for n in self.catalog if n['class'] == 'TTabSheet' and
                          n['path'].startswith('frmMain/MainTab/') and n['path'].count('/') == 2]
        class_path = {'Mage': 'pnlMage', 'Rogue': 'pnlRogue', 'Priest': 'pnlPri',
                      'Warrior': 'pnlWarrior', 'Kurian': 'pnlKurian'}[self.job.get()]
        prefix = 'frmMain/MainTab/SheetJob/' + class_path + '/'
        self.inner_tabs = [n for n in self.catalog if n['class'] == 'TTabSheet' and n['path'].startswith(prefix)]
        for variable, selector, tabs in [(self.section, self.section_select, self.main_tabs),
                                          (self.inner_section, self.inner_select, self.inner_tabs)]:
            labels = [n['properties'].get('Caption', '') for n in tabs] if self.form.get() == 'frmMain' else []
            selector.configure(values=labels, state='readonly' if labels else 'disabled')
            if variable.get() not in labels:
                variable.set(labels[0] if labels else '')
        self.select_sections()

    def select_sections(self):
        for variable, tabs in [(self.section, self.main_tabs), (self.inner_section, self.inner_tabs)]:
            for node in tabs:
                path = node['path']
                if node['properties'].get('Caption', '') == variable.get() and path in self.widgets:
                    self.widgets[path.rsplit('/', 1)[0]].select(self.widgets[path])
                    break

    def edit_list(self, path):
        editor = tk.Toplevel(self.surface.winfo_toplevel())
        editor.title('Liste düzenle')
        editor.geometry('720x570')
        working = copy.deepcopy(self.lists[path])
        table = ttk.Treeview(editor, columns=('caption', 'subitems', 'checked'), show='headings')
        for name, label in [('caption', 'Ad'), ('subitems', 'Ek sütunlar'), ('checked', 'Seçili')]:
            table.heading(name, text=label)
        table.pack(fill='both', expand=True)
        def redraw():
            table.delete(*table.get_children())
            for index, row in enumerate(working):
                table.insert('', 'end', iid=str(index), values=(row['caption'], ' | '.join(row['subitems']), row['checked']))
        row_frame = ttk.Frame(editor, padding=5)
        row_frame.pack(fill='x')
        caption = tk.StringVar()
        checked = tk.BooleanVar()
        node = next(n for n in self.catalog if n['path'] == path)
        columns = node['properties'].get('Columns', [])
        sub_count = max([len(columns) - 1, 0] + [len(row['subitems']) for row in working])
        subitems = [tk.StringVar() for _ in range(sub_count)]
        ttk.Label(row_frame, text='Ad').grid(row=0, column=0)
        ttk.Entry(row_frame, textvariable=caption, width=32).grid(row=0, column=1)
        for index, variable in enumerate(subitems):
            label = columns[index + 1].get('Caption', '') if index + 1 < len(columns) else ''
            ttk.Label(row_frame, text=label or 'Alan %d' % (index + 1)).grid(row=index + 1, column=0)
            ttk.Entry(row_frame, textvariable=variable, width=40).grid(row=index + 1, column=1)
        ttk.Checkbutton(row_frame, text='Seçili', variable=checked).grid(row=sub_count + 1, column=1, sticky='w')
        def selected(_=None):
            choice = table.selection()
            if choice:
                row = working[int(choice[0])]
                caption.set(row['caption'])
                for index, variable in enumerate(subitems):
                    variable.set(row['subitems'][index] if index < len(row['subitems']) else '')
                checked.set(row['checked'])
        table.bind('<<TreeviewSelect>>', selected)
        def write(replace=False):
            try:
                row = {'caption': caption.get(), 'subitems': [v.get() for v in subitems], 'checked': checked.get()}
                candidate = copy.deepcopy(working)
                if replace and table.selection():
                    candidate[int(table.selection()[0])] = row
                elif replace:
                    return
                else:
                    candidate.append(row)
                self.profiles.validate_lists({path: candidate})
                working[:] = candidate
                redraw()
            except ValueError as error:
                messagebox.showerror('Liste', str(error), parent=editor)
        def delete():
            if table.selection():
                working.pop(int(table.selection()[0]))
                redraw()
        def apply():
            self.lists[path] = copy.deepcopy(working)
            if path==flood_editor.LIST_PATH:self.compile_current_flood()
            editor.destroy()
            self.render()
        buttons = ttk.Frame(editor, padding=5)
        buttons.pack(fill='x')
        for label, callback in [('Ekle', write), ('Satırı değiştir', lambda: write(True)),
                                ('Seçileni sil', delete), ('Uygula', apply), ('İptal', editor.destroy)]:
            ttk.Button(buttons, text=label, command=callback).pack(side='left', padx=3)
        redraw()
