import json
import ntpath
from pathlib import Path
from dataclasses import replace
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from routes import RouteStep, RouteRunner, route_to_data, route_from_data
from profiles import atomic_json_write
from special_routes import SPECIAL_COMMANDS, SpecialRouteSnapshot
from source_route_ini import import_source_route
from name_codec import WindowsNameCodec
from supply_configuration import compile_supply_panel
from supply_routes import compile_supply_route_lists,SupplyRouteState,route_codec_fixture
from supply_route_start import plan_panel_route_choice,import_panel_route_choice
from global_route_choices import ROUTE_GLOBALS,compile_mining_route_inputs,plan_global_route_choice,compile_panel_route_name
from mining_configuration import compile_mining_npc_flags
from npc_route_engine import NpcRouteFrame,NpcRouteObservation
from npc_lookup import NpcCandidate
from repair_engine import RepairObservation
from repair_inventory import RepairInventoryObservation,RepairSlot,STARTUP_SLOTS
from npc_sell_engine import NpcSaleObservation
from npc_buy_engine import NpcBuyObservation,NpcBuyRouteRow
from repair_replies import replay_repair_reply
from merchant_bank_route import MerchantBankRoutePlan
from merchant_sell_failure import SellFailurePlan
from merchant_buy_failure import BuyFailurePlan
from route_catalog import read_local_route_catalog,ROUTE_COMBO_PATHS

ROUTE_KIND_LABELS={'Tedarik':'supply','Dönüş':'return','Maden':'Mine','Sell Merchant':'SMerchant',
    'Buy Merchant':'BMerchant','AntiCR':'AntiCR','Karşı ırk':'Enemy','Notice':'Notice','PM kontrol':'PMKONTROL','Relog':'Relog'}


class RoutePage:
    def __init__(self, frame, configuration_reader=None,combo_text_reader=None):
        self.configuration_reader=configuration_reader
        self.combo_text_reader=combo_text_reader
        self.supply_route_state=SupplyRouteState(0,0) # Owned demonstration counters, not observed game globals.
        self.mine_route_counter=0
        self.steps = []
        self.runner = RouteRunner()
        self.now_ms = 0
        self.npc_frame=None;self.npc_index=None;self.npc_profile_last=None
        self.npc_nested_active=False
        self.npc_reply_last=None;self.npc_repair_case_active='Boş'
        ttk.Label(frame, text='Koordinat, Bekle ve özel rota adımları • Yerel simülasyon', padding=10).pack(anchor='w')
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x')
        self.command = tk.StringVar(value='Koordinat')
        ttk.Combobox(toolbar, values=['Koordinat', 'Bekle', *SPECIAL_COMMANDS], textvariable=self.command,
                     state='readonly', width=18).pack(side='left')
        self.first, self.second = tk.StringVar(value='0'), tk.StringVar(value='0')
        ttk.Label(toolbar, text='X / saniye / parametre1:').pack(side='left', padx=5)
        ttk.Entry(toolbar, textvariable=self.first, width=12).pack(side='left')
        ttk.Label(toolbar, text='Y / parametre2:').pack(side='left', padx=5)
        ttk.Entry(toolbar, textvariable=self.second, width=12).pack(side='left')
        ttk.Button(toolbar, text='Ekle', command=self.add).pack(side='left', padx=5)
        self.list = ttk.Treeview(frame, columns=('command', 'p1', 'p2'), show='headings', height=10)
        for col, title in [('command', 'Komut'), ('p1', 'X / saniye / parametre1'), ('p2', 'Y / parametre2')]:
            self.list.heading(col, text=title)
        self.list.pack(fill='both', expand=True, padx=5, pady=10)
        edits = ttk.Frame(frame)
        edits.pack(fill='x')
        for label, callback in [('Seçileni sil', self.remove), ('Yukarı', lambda: self.reorder(-1)),
                                ('Aşağı', lambda: self.reorder(1)), ('Rota aç', self.load), ('Rota kaydet', self.save)]:
            ttk.Button(edits, text=label, command=callback).pack(side='left', padx=3)
        ttk.Button(edits,text='Farmex .R aç',command=self.load_source).pack(side='left',padx=3)
        ttk.Label(edits,text='Kaynak metin kod sayfası:').pack(side='left',padx=3)
        self.source_codepage=tk.StringVar(value='1254')
        ttk.Combobox(edits,textvariable=self.source_codepage,values=('1254','65001'),state='readonly',width=7).pack(side='left')
        panel_route=ttk.LabelFrame(frame,text='Panel rota türü • Yerel deneme',padding=5)
        panel_route.pack(fill='x',pady=5)
        self.supply_directory=tk.StringVar();self.supply_manual=tk.StringVar()
        self.supply_kind=tk.StringVar(value='Tedarik')
        self.use_panel_route_text=tk.BooleanVar(value=True)
        ttk.Label(panel_route,text='Rota klasörü:').grid(row=0,column=0)
        ttk.Entry(panel_route,textvariable=self.supply_directory,width=40).grid(row=0,column=1)
        ttk.Label(panel_route,text='Elle rota adı:').grid(row=0,column=2,padx=4)
        ttk.Entry(panel_route,textvariable=self.supply_manual,width=25).grid(row=0,column=3)
        ttk.Combobox(panel_route,textvariable=self.supply_kind,values=tuple(ROUTE_KIND_LABELS),state='readonly',width=15).grid(row=1,column=0,pady=4)
        ttk.Button(panel_route,text='Panelden rotayı yükle',command=self.load_panel_route).grid(row=1,column=1,sticky='w')
        ttk.Label(panel_route,text='Tedarik, dönüş ve maden farklı rota listelerini kullanır.').grid(row=1,column=2,columnspan=2,sticky='w')
        ttk.Checkbutton(panel_route,text='Panelde seçili rota dosyasını kullan',variable=self.use_panel_route_text).grid(row=3,column=0,columnspan=4,sticky='w')
        self.mine_check_directory=tk.StringVar()
        ttk.Label(panel_route,text='Maden liste kontrol klasörü:').grid(row=2,column=0,pady=3)
        ttk.Entry(panel_route,textvariable=self.mine_check_directory,width=40).grid(row=2,column=1)
        sim = ttk.Frame(frame, padding=10)
        sim.pack(fill='x')
        self.distance = tk.StringVar(value='10')
        self.blocked = tk.BooleanVar(value=False)
        ttk.Label(sim, text='Hedefe mesafe:').pack(side='left')
        ttk.Entry(sim, textvariable=self.distance, width=10).pack(side='left', padx=5)
        ttk.Checkbutton(sim, text='Hareket engelli', variable=self.blocked).pack(side='left')
        ttk.Button(sim, text='Simülasyonu başlat', command=self.start).pack(side='left', padx=5)
        ttk.Button(sim, text='Durdur', command=self.stop).pack(side='left')
        ttk.Button(sim, text='+100 ms adım', command=self.tick).pack(side='left', padx=5)
        ttk.Button(sim, text='+1000 ms adım', command=lambda: self.tick(1000)).pack(side='left')
        conditions = ttk.Frame(frame, padding=5)
        conditions.pack(fill='x')
        self.special_ready = tk.BooleanVar(value=True)
        self.npc_complete = tk.BooleanVar(value=False)
        ttk.Checkbutton(conditions, text='Özel adım kapısı açık (deneme)', variable=self.special_ready).pack(side='left')
        self.npc_complete_control=ttk.Checkbutton(conditions,text='NPC adımı tamamlandı (deneme)',variable=self.npc_complete)
        self.npc_complete_control.pack(side='left',padx=10)
        npc_controls=ttk.LabelFrame(frame,text='NPC iç akış / panel tercihi • Yerel deneme',padding=5)
        npc_controls.pack(fill='x')
        self.npc_profile_fixture=tk.BooleanVar(value=False)
        self.npc_runtime_mode=tk.StringVar(value='Bilinmiyor')
        self.npc_kind=tk.StringVar(value='Sundries')
        self.npc_helper_fixture=tk.BooleanVar(value=False);self.npc_worker_fixture=tk.BooleanVar(value=False)
        self.npc_entry=tk.StringVar(value='Aşama3')
        self.npc_lookup_fixture=tk.BooleanVar(value=False);self.npc_name_fixture=tk.BooleanVar(value=False)
        self.npc_nested_fixture=tk.BooleanVar(value=False)
        self.npc_repair_case=tk.StringVar(value='Boş')
        self.npc_reply_hex=tk.StringVar(value='')
        self.npc_reply_refresh=tk.BooleanVar(value=False)
        ttk.Checkbutton(npc_controls,text='Profil bağlı NPC modeli',variable=self.npc_profile_fixture,command=self.toggle_npc_profile).grid(row=0,column=0,sticky='w')
        ttk.Label(npc_controls,text='Bağımsız çalışma modu örneği').grid(row=0,column=1,padx=4)
        ttk.Combobox(npc_controls,textvariable=self.npc_runtime_mode,values=('Bilinmiyor','0','1','2','3'),state='readonly',width=12).grid(row=0,column=2)
        ttk.Combobox(npc_controls,textvariable=self.npc_kind,values=('Sundries','Armor','Weapon','Potion','DC Sundries','Inn Hostess','Royal National Enchanter'),state='readonly',width=25).grid(row=0,column=3,padx=4)
        ttk.Checkbutton(npc_controls,text='Örnek helper sonuçları',variable=self.npc_helper_fixture).grid(row=1,column=0,sticky='w')
        ttk.Checkbutton(npc_controls,text='Depo/banka worker tamamlanmış örneği',variable=self.npc_worker_fixture).grid(row=1,column=1,columnspan=3,sticky='w')
        ttk.Combobox(npc_controls,textvariable=self.npc_entry,values=('Aşama3','Aşama1'),state='readonly',width=12).grid(row=2,column=0,sticky='w')
        ttk.Checkbutton(npc_controls,text='Örnek NPC arama kaydı',variable=self.npc_lookup_fixture).grid(row=2,column=1,sticky='w')
        ttk.Checkbutton(npc_controls,text='Örnek ANSI isim kaydı',variable=self.npc_name_fixture).grid(row=2,column=2,columnspan=2,sticky='w')
        ttk.Checkbutton(npc_controls,text='Alt motor örnekleri',variable=self.npc_nested_fixture).grid(row=3,column=0,sticky='w')
        ttk.Combobox(npc_controls,textvariable=self.npc_repair_case,values=('Boş','Hasarlı ekipman1'),state='readonly',width=24).grid(row=3,column=1,sticky='w')
        ttk.Label(npc_controls,text='Başlangıç/alt motor seçimi yeniden başlatmada uygulanır. Hasarlı ekipman1: ID100,1/100 dayanıklılık;paket üreticisinde ayrı ID200 okuması. Satış boş ve satın alma satırı kapalıdır. Tüm örnekler sentetiktir;gerçek NPC/işlem/ACK değildir.',wraplength=1000).grid(row=4,column=0,columnspan=4,sticky='w')
        ttk.Label(npc_controls,text='Yerel yanıt hex:').grid(row=5,column=0,sticky='w')
        ttk.Entry(npc_controls,textvariable=self.npc_reply_hex,width=26).grid(row=5,column=1,sticky='w')
        ttk.Checkbutton(npc_controls,text='Örnek refresh helper normal döndü',variable=self.npc_reply_refresh).grid(row=5,column=2,sticky='w')
        ttk.Button(npc_controls,text='Yanıtı yerel frame’e uygula',command=self.apply_npc_reply).grid(row=5,column=3,sticky='w')
        ttk.Label(npc_controls,text='Yanıt girdisi önceki dispatch kapılarının geçildiği varsayımıdır. Durum1 helper dönüşü ister; diğer durumlar da beklemeyi çözebilir. Bu ağ yakalama veya gerçek onarım başarısı değildir.',wraplength=1000).grid(row=6,column=0,columnspan=4,sticky='w')
        ttk.Label(frame, text='Özel adımlar örnek HP100/100 ve bulunan NPC kullanır. Delos Gate için mesafe yer değiştirmedir. Change Camp parametre1: sayı veya Randomize.',
                  padding=5, wraplength=1000).pack(anchor='w')
        self.status = tk.StringVar(value='Durduruldu. Oyuna hareket gönderilmez.')
        ttk.Label(frame, textvariable=self.status, padding=10, wraplength=1000).pack(anchor='w')

    def refresh(self):
        self.list.delete(*self.list.get_children())
        for index, step in enumerate(self.steps):
            self.list.insert('', 'end', iid=str(index), values=(step.command,
                step.x if step.command == 'Koordinat' else step.seconds if step.command == 'Bekle' else step.parameter1,
                step.y if step.command == 'Koordinat' else '' if step.command == 'Bekle' else step.parameter2))

    def edited(self):
        self.runner.stop('Rota değişti')
        self.status.set('Rota değişti; simülasyon durduruldu.')
        self.refresh()

    def add(self):
        try:
            if self.command.get() == 'Koordinat':
                step = RouteStep('Koordinat', float(self.first.get()), float(self.second.get()))
            elif self.command.get() == 'Bekle':
                step = RouteStep('Bekle', seconds=int(self.first.get()))
            else:
                step = RouteStep(self.command.get(), parameter1=self.first.get(), parameter2=self.second.get())
            self.steps.append(step)
            self.edited()
        except ValueError as error:
            messagebox.showerror('Rota', str(error))

    def remove(self):
        selected = self.list.selection()
        if selected:
            self.steps.pop(int(selected[0]))
            self.edited()

    def reorder(self, delta):
        selected = self.list.selection()
        if selected:
            index = int(selected[0])
            dest = index + delta
            if 0 <= dest < len(self.steps):
                self.steps[index], self.steps[dest] = self.steps[dest], self.steps[index]
                self.edited()
                self.list.selection_set(str(dest))

    def save(self):
        try:
            data = route_to_data(self.steps)
            path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Rota', '*.json')])
            if path:
                atomic_json_write(path, data)
        except (ValueError, OSError) as error:
            messagebox.showerror('Rota', str(error))

    def load(self):
        path = filedialog.askopenfilename(filetypes=[('Rota', '*.json')])
        if path:
            try:
                with open(path, encoding='utf-8') as stream:
                    new_steps = route_from_data(json.load(stream))
                self.steps = new_steps
                self.edited()
            except (ValueError, OSError) as error:
                messagebox.showerror('Rota', str(error))

    def accept_bank_route(self,failure):
        """Own simulator handoff only after ready import and outer caller gate."""
        if (not isinstance(failure,(SellFailurePlan,BuyFailurePlan)) or not failure.complete
                or failure.status!='bank_route_span_returned' or failure.phase_dword!=0):
            raise ValueError('Tam dış pazar başarısızlık/rota çağrı planı gerekli')
        plan=failure.route_plan
        expected='SMerchant' if isinstance(failure,SellFailurePlan) else 'BMerchant'
        if (not isinstance(plan,MerchantBankRoutePlan) or plan.kind!=expected or plan.filename_global!=ROUTE_GLOBALS[expected]
                or not plan.complete or not plan.ready
                or plan.imported_start is None or not plan.imported_start.ready):
            raise ValueError('Tam yerel banka rotası import planı gerekli')
        self.steps=list(plan.imported_start.imported.steps);self.edited();self.start()
        self.status.set('Banka rotası yerel simülasyona aktarıldı; oyun eylemi yok')
        return dict(local_simulation_started=self.runner.active,steps=len(self.steps),kind=expected,live_compatibility_verified=False)

    def start(self):
        try:
            self.runner.start(self.steps)
            self.now_ms = 0
            self.npc_frame=None;self.npc_index=None;self.npc_profile_last=None
            self.status.set('Simülasyon başladı. +100 ms adım ile ilerlet.')
        except ValueError as error:
            self.status.set(str(error))

    def load_source(self):
        path=filedialog.askopenfilename(filetypes=[('Farmex kaynak rota','*.R'),('Tüm dosyalar','*.*')])
        if path:self.load_source_path(path)

    def load_source_path(self,path):
        try:
            result=import_source_route(path,WindowsNameCodec(int(self.source_codepage.get())))
            if result.complete and result.changed:
                self.steps=list(result.steps);self.edited()
                self.status.set('Kaynak INI rotası yüklendi: %d adım • Yerel simülasyon'%len(self.steps))
            else:self.status.set('Kaynak rota: '+result.status+(' • '+result.missing if result.missing else ''))
            return result
        except (ValueError,OSError) as error:
            self.status.set('Kaynak rota okunamadı: '+str(error))
            return None

    def choose_catalog_directory(self):
        directory=filedialog.askdirectory(title='Rota dosyalarının bulunduğu klasör',initialdir=self.supply_directory.get() or None)
        if directory:self.supply_directory.set(directory)

    def read_catalog(self):
        return read_local_route_catalog(self.supply_directory.get(),WindowsNameCodec(int(self.source_codepage.get())))

    def load_panel_route(self):
        try:
            if self.configuration_reader is None:raise ValueError('Kaynak panel bağlantısı gerekli')
            directory=self.supply_directory.get()
            if not ntpath.isabs(directory):raise ValueError('Mutlak rota klasörü gerekli')
            codec=WindowsNameCodec(int(self.source_codepage.get()))
            prefix=codec.encode(directory.rstrip('\\/')+'\\')[0]
            values,profile_lists=self.configuration_reader()
            kind=ROUTE_KIND_LABELS[self.supply_kind.get()]
            panel_texts=None
            if self.use_panel_route_text.get():
                if self.combo_text_reader is None:raise ValueError('Panel rota seçimi bağlantısı gerekli')
                panel_texts=self.combo_text_reader()
                text=panel_texts.get(ROUTE_COMBO_PATHS[kind])
                if type(text) is not str:raise ValueError('Seçilen rota için panel Text gözlemi gerekli')
            else:text=self.supply_manual.get()
            manual,used=codec.encode(text)
            if used or codec.decode(manual)!=text:raise ValueError('Rota adı seçilen kod sayfasında kayıpsız temsil edilemiyor')
            if kind in ('supply','return'):
                panel=compile_supply_panel(values,combo_texts=panel_texts)
                lists=compile_supply_route_lists(profile_lists,codec=codec)
                choice=plan_panel_route_choice(panel,lists,kind,self.supply_route_state,manual)
                if choice.cyclic is not None and choice.cyclic.selected_index is not None:
                    names=lists.supply if kind=='supply' else lists.returning
                    obs=route_codec_fixture(names[choice.cyclic.selected_index],prefix,codec)
                    obs=replace(obs,file_exists_byte=int(Path(obs.path_unicode).is_file()))
                    choice=plan_panel_route_choice(panel,lists,kind,self.supply_route_state,manual,obs)
            else:
                observed=compile_panel_route_name(kind,panel_texts,codec) if panel_texts is not None else {ROUTE_GLOBALS[kind]:manual}
                mine=compile_mining_route_inputs(values,profile_lists,codec) if kind=='Mine' else None
                kwargs={} if mine is None else dict(mine_change_byte=mine.change_byte,mine_names=mine.names,mine_counter=self.mine_route_counter)
                choice=plan_global_route_choice(kind,observed,self.supply_route_state,**kwargs)
                if kind=='Mine' and choice.cyclic is not None and choice.cyclic.selected_index is not None:
                    check_directory=self.mine_check_directory.get()
                    if not ntpath.isabs(check_directory):raise ValueError('Maden liste kontrolü için ayrı mutlak klasör gerekli')
                    check_prefix=codec.encode(check_directory.rstrip('\\/')+'\\')[0]
                    obs=route_codec_fixture(mine.names[choice.cyclic.selected_index],check_prefix,codec)
                    obs=replace(obs,file_exists_byte=int(Path(obs.path_unicode).is_file()))
                    choice=plan_global_route_choice(kind,observed,self.supply_route_state,observation=obs,**kwargs)
            if choice.complete:
                self.supply_route_state=choice.state
                if kind=='Mine':self.mine_route_counter=choice.mine_counter
            self.panel_route_choice=choice
            self.panel_route_last=import_panel_route_choice(choice,prefix,codec)
            result=self.panel_route_last
            if result.ready:
                self.steps=list(result.imported.steps);self.edited()
                self.status.set('Panel rota yüklendi • '+choice.status+' • Yerel simülasyon')
            elif result.stop_required:
                self.runner.stop('Kaynak rota hatası')
                self.status.set('Kaynak rota hatası • Yerel yürütücü durduruldu • '+result.status)
            else:self.status.set('Panel rota gözlemi eksik • '+result.status+' • '+result.missing)
            return result
        except (ValueError,OSError) as error:
            self.status.set('Panel rota okunamadı: '+str(error))
            return None

    def stop(self):
        self.runner.stop()
        self.npc_frame=None;self.npc_index=None;self.npc_profile_last=None
        self.status.set('Durduruldu; rota çalışma durumu temizlendi.')

    def toggle_npc_profile(self):
        enabled=self.npc_profile_fixture.get()
        if enabled:self.npc_complete.set(False)
        self.npc_complete_control.configure(state='disabled' if enabled else 'normal')
        self.npc_frame=None;self.npc_index=None;self.npc_profile_last=None

    def apply_npc_reply(self):
        try:
            if (not self.npc_profile_fixture.get() or self.npc_frame is None or not self.runner.active
                    or not self.runner.processing or self.npc_index!=self.runner.index):
                raise ValueError('Yanıt için etkin yerel NPC görevi gerekli')
            captured=bytes.fromhex(self.npc_reply_hex.get())
            result=replay_repair_reply(self.npc_frame,captured,
                refresh_returned=True if self.npc_reply_refresh.get() else None)
            self.npc_reply_last=result
            self.npc_frame=result.frame
            plan=result.plan
            self.status.set('Yerel yanıt: %s • durum:%s • yazım:%d • %s • canlı ACK doğrulanmadı'%
                (plan.status,plan.reply_status,len(plan.global_writes),plan.missing))
        except ValueError as error:
            self.status.set(str(error))

    def tick(self, elapsed=100):
        try:
            distance = float(self.distance.get())
            observation = SpecialRouteSnapshot(self.now_ms & 0xffffffff,
                actor_raw_byte_554020=0 if self.special_ready.get() else 1,
                hp_4611a0=100, max_hp_4611c0=100, npc_found_465960=True,
                npc_pointer_found_464a10=True, npc_distance=distance,
                npc_interaction_raw_byte=0 if self.special_ready.get() else 1,
                displacement=distance, npc_helper_return_4f11a0=None if self.npc_profile_fixture.get() else self.npc_complete.get())
            nested=None;profile=None;mode=None
            if (self.npc_profile_fixture.get() and self.runner.active and self.runner.processing
                    and self.runner.steps[self.runner.index].command=='NPC' and self.runner.special_state.started):
                if self.configuration_reader is None:raise ValueError('NPC profil bağlantısı gerekli')
                profile=compile_mining_npc_flags(self.configuration_reader()[0])
                mode_text=self.npc_runtime_mode.get()
                if mode_text not in ('Bilinmiyor','0','1','2','3'):raise ValueError('Geçerli gözlenen mod örneği gerekli')
                mode=None if mode_text=='Bilinmiyor' else int(mode_text)
                kind=self.npc_kind.get()
                kinds=('Sundries','Armor','Weapon','Potion','DC Sundries','Inn Hostess','Royal National Enchanter')
                if kind not in kinds:raise ValueError('Geçerli NPC karşılaştırma örneği gerekli')
                if self.npc_frame is None or self.npc_index!=self.runner.index:
                    self.npc_index=self.runner.index
                    entry=self.npc_entry.get()
                    if entry not in ('Aşama3','Aşama1'):raise ValueError('Geçerli NPC başlangıç aşaması gerekli')
                    phase=1 if entry=='Aşama1' else 3
                    self.npc_frame=NpcRouteFrame(phase,{0x604:0,0x63c:0,0x650:0,0x688:0,0x689:0,0x18:0,0x1c:0,0x556:0,0x6d8:0,0x6c0:0},
                        {0x553fec:12,0x553fe8:8,0x5690b8:0,0x5690cc:0,0x5690d8:0,0x5690e0:0},texts={} if phase==1 else {0x610:kind})
                    self.npc_nested_active=self.npc_nested_fixture.get()
                    self.npc_reply_last=None
                    if self.npc_nested_active:
                        self.npc_repair_case_active=self.npc_repair_case.get()
                        if self.npc_repair_case_active not in ('Boş','Hasarlı ekipman1'):raise ValueError('Geçerli onarım örneği gerekli')
                        self.npc_frame=replace(self.npc_frame,fields={**self.npc_frame.fields,
                            0x60c:0x100000,0x644:0,0x658:0,0x694:0,0x18:0x300000,0x1c:0x300024},
                            globals={**self.npc_frame.globals,0x553e44:1})
                frame=self.npc_frame
                if self.npc_worker_fixture.get():
                    frame=replace(frame,globals={**frame.globals,0x5690b8:0,0x5690cc:48,0x5690d8:1,0x5690e0:0})
                helpers=({'004edf34':42,'004eebf4':43,'004fe384':0,'0046fe90':0,'004f035c':8,'004efa84':1}
                    if self.npc_helper_fixture.get() else {})
                entry_observations={}
                if self.npc_nested_active:
                    # Typed child inputs replace whole-helper completion markers.
                    for address in ('004edf34','004eebf4','004efa84'):helpers.pop(address,None)
                    target=frame.fields[0x604]&0xffffffff
                    repair_slots={slot:RepairSlot(0) for slot in STARTUP_SLOTS}
                    damaged=self.npc_repair_case_active=='Hasarlı ekipman1'
                    if damaged:repair_slots[1]=RepairSlot(100,1,100)
                    damaged_current=damaged and frame.fields.get(0x640)==1
                    entry_observations.update(
                        repair_observation=RepairObservation(self.now_ms&0xffffffff,current_target=target,
                            item_id_4634a4=100 if damaged_current else 0,
                            durability_46358c=1 if damaged_current else None,
                            maximum_4635e0=100 if damaged_current else None,
                            producer_item_id_4634a4=200 if damaged_current else None,
                            candidate_inventory=RepairInventoryObservation(repair_slots,False)),
                        sale_observation=NpcSaleObservation(self.now_ms&0xffffffff,inventory_pointer=0x400000,
                            current_target=target,slot_present_4637d8=False),
                        buy_observation=NpcBuyObservation(self.now_ms&0xffffffff,current_target=target,row=NpcBuyRouteRow(0)))
                if self.npc_lookup_fixture.get():
                    # Own observed-row fixture; never enumerate game objects.
                    entry_observations.update(lookup_candidates=(NpcCandidate(8,17,kind.encode('cp1254')),),
                        lookup_traversal_complete=True,inn_in_moradon=False if kind=='Inn Hostess' else None)
                if self.npc_name_fixture.get():
                    name_bytes=kind.encode('cp1254')
                    helpers.update({'00464a10':0x100000,'0045dc44:raw_field_fec':len(name_bytes)})
                    # Inline copy is255 bytes; the long branch uses an explicit indirect pointer.
                    count=255 if len(name_bytes)<16 else len(name_bytes)
                    if len(name_bytes)>=16:helpers['0045dc44:raw_field_fe8']=0x200000
                    entry_observations.update(text_readable=True,copied_bytes=name_bytes+b'\0'*(count-len(name_bytes)),codec='cp1254')
                nested=NpcRouteObservation(frame,{name:name==kind for name in kinds},helpers,**entry_observations)
            decision = self.runner.tick(self.now_ms, distance, self.blocked.get(), observation,nested,
                npc_profile_configuration=profile,npc_runtime_mode=mode)
            detail=''
            if nested is not None:
                self.npc_profile_last=self.runner.npc_profile_result
                self.npc_frame=self.npc_profile_last.frame
                detail=' • NPC aşama:%d • kaynak veri:%s'%(self.npc_frame.phase,self.npc_profile_last.status)
            self.status.set('Zaman: %d ms • Komut: %d • %s' %
                            (self.now_ms, decision.index + 1,
                             '%s • yerel çağrı: %d • gönderim planı: %d • %s' %
                             (decision.kind, len(decision.calls), len(decision.queue_payloads), decision.reason))+detail)
            self.now_ms += elapsed
        except ValueError as error:
            self.status.set(str(error))
