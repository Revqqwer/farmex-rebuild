"""Working offline reconstruction workbench; does not connect to the game."""
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from profiles import Profiles
from potion_engine import PotionSettings, PotionSnapshot, potion_decision, HP_FALLBACK, MP_FALLBACK
from potion_packets import enqueue_potion_intent
from action_queue import QueueState
from configuration import compile_potions
from route_ui import RoutePage
from panel_ui import ConfigurationPanel
from connection_ui import ConnectionPage
from mining_ui import MiningRoutesPage
from simulation_ui import EnginePage
from merchant_bank_route import merchant_bank_route_inputs_from_panel
from name_codec import WindowsNameCodec
from route_save_runtime import RouteSaveContext
from ms_achievement import BUTTON_PATH as MS_ACHIEVEMENT_BUTTON

BASE = Path(__file__).parent


class Application:
    def __init__(self, root):
        self.root = root
        self.catalog = json.loads((BASE / 'ui_model.json').read_text(encoding='utf-8'))
        self.nodes = {n['path']: n for n in self.catalog}
        self.profiles = Profiles(self.catalog)
        self.values = dict(self.profiles.defaults)
        self.lists = self.profiles.validate_lists({})
        root.title('Farmex yeniden yapım — inceleme ve simülasyon')
        root.geometry('1120x740')
        self.status = tk.StringVar(value='Yeni sürüm • Ayarlar yerel profil için düzenlenir • Canlı eylemler henüz etkin değil')
        ttk.Label(root, textvariable=self.status,
                  padding=10).pack(fill='x')
        bar = ttk.Frame(root, padding=5)
        bar.pack(fill='x')
        ttk.Button(bar, text='Profil aç', command=self.load).pack(side='left')
        ttk.Button(bar, text='Profil kaydet', command=self.save).pack(side='left', padx=5)
        self.search = tk.StringVar()
        ttk.Label(bar, text='Kontrol ara:').pack(side='left', padx=10)
        ttk.Entry(bar, textvariable=self.search, width=40).pack(side='left')
        self.search.trace_add('write', lambda *_: self.populate())
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        panel_frame = ttk.Frame(notebook)
        notebook.add(panel_frame, text='Ayar paneli')
        self.panel = ConfigurationPanel(panel_frame, self.catalog, self.profiles, self.values, self.lists)
        page = ttk.Frame(notebook)
        notebook.add(page, text='Tüm formlar ve kontroller')
        split = ttk.Panedwindow(page, orient='horizontal')
        split.pack(fill='both', expand=True)
        left, self.detail = ttk.Frame(split), ttk.Frame(split, padding=15)
        split.add(left, weight=3)
        split.add(self.detail, weight=2)
        self.tree = ttk.Treeview(left, columns=('class',), selectmode='browse')
        self.tree.heading('#0', text='Form / kontrol')
        self.tree.heading('class', text='Tür')
        self.tree.column('#0', width=370)
        self.tree.column('class', width=110)
        scroll = ttk.Scrollbar(left, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.select)
        sim = ttk.Frame(notebook, padding=15)
        notebook.add(sim, text='HP / MP simülasyonu')
        self.build_simulator(sim)
        route_frame = ttk.Frame(notebook, padding=10)
        notebook.add(route_frame, text='Rota editörü / simülasyonu')
        self.route_page = RoutePage(route_frame,configuration_reader=lambda:(self.values,self.lists),combo_text_reader=self.panel.combo_texts)
        self.route_page.supply_directory.trace_add('write',lambda *_:setattr(self.profiles,'route_directory',self.route_page.supply_directory.get()))
        self.route_page.source_codepage.trace_add('write',lambda *_:setattr(self.profiles,'route_codepage',int(self.route_page.source_codepage.get())))
        self.panel.route_catalog_reader=self.route_page.read_catalog
        self.panel.route_directory_chooser=self.route_page.choose_catalog_directory
        self.panel.route_save_context_reader=lambda:RouteSaveContext(self.route_page.supply_directory.get(),
            WindowsNameCodec(int(self.route_page.source_codepage.get())))
        mining = ttk.Frame(notebook, padding=10)
        notebook.add(mining, text='Maden rotaları')
        self.mining_page = MiningRoutesPage(mining)
        engines = ttk.Frame(notebook, padding=8)
        notebook.add(engines, text='Davranış denemeleri')
        self.engine_page = EnginePage(engines, configuration_reader=lambda: (self.values, self.lists),
                                     configuration_writer=self.panel.apply_boolean_updates,
                                     route_configuration_reader=lambda:(self.panel.combo_texts(),int(self.route_page.source_codepage.get())),
                                     bank_route_reader=lambda:merchant_bank_route_inputs_from_panel(self.panel.combo_texts(),
                                         self.route_page.supply_directory.get() or None,WindowsNameCodec(int(self.route_page.source_codepage.get()))),
                                     bank_route_consumer=self.route_page.accept_bank_route,
                                     buy_bank_route_reader=lambda:merchant_bank_route_inputs_from_panel(self.panel.combo_texts(),
                                         self.route_page.supply_directory.get() or None,WindowsNameCodec(int(self.route_page.source_codepage.get())),kind='BMerchant'),
                                     buy_bank_route_consumer=self.route_page.accept_bank_route)
        connection = ttk.Frame(notebook, padding=15)
        notebook.add(connection, text='Oyun oturumu')
        self.connection_page = ConnectionPage(connection, self.status)
        root.protocol('WM_DELETE_WINDOW', self.close)
        def start_ms_achievement():
            notebook.select(engines)
            self.engine_page.start_ms_achievement()
        self.panel.bind_button(MS_ACHIEVEMENT_BUTTON,start_ms_achievement)
        self.populate()

    def close(self):
        self.connection_page.close()
        self.root.destroy()

    def populate(self):
        query = self.search.get().casefold().strip()
        keep = set()
        for node in self.catalog:
            path = node['path']
            if not query or query in (path + ' ' + str(node['properties'].get('Caption', ''))).casefold():
                keep.add(path)
                parent = path
                while '/' in parent:
                    parent = parent.rsplit('/', 1)[0]
                    keep.add(parent)
        self.tree.delete(*self.tree.get_children())
        for node in self.catalog:
            path = node['path']
            if path in keep:
                parent = path.rsplit('/', 1)[0] if '/' in path else ''
                caption = node['properties'].get('Caption', '')
                self.tree.insert(parent, 'end', iid=path,
                    text=(caption + ' — ' if caption else '') + path.rsplit('/', 1)[-1],
                    values=(node['class'],), open=bool(query))

    def select(self, *_):
        selected = self.tree.selection()
        if not selected:
            return
        for widget in self.detail.winfo_children():
            widget.destroy()
        path = selected[0]
        node = self.nodes[path]
        ttk.Label(self.detail, text=path, wraplength=400).pack(anchor='w')
        props = node['properties']
        ttk.Label(self.detail, text=props.get('Caption', node['class']),
                  wraplength=400, padding=(0, 10)).pack(anchor='w')
        if path in self.values:
            value = self.values[path]
            if type(value) is bool:
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(self.detail, text='Etkin', variable=var,
                    command=lambda: self.profiles.update(self.values, path, var.get())).pack(anchor='w')
            else:
                var = tk.StringVar(value=str(value))
                choices = self.profiles.combo_items(path) if node['class']=='TComboBox' else props.get('Items.Strings', [])
                if node['class'] == 'TComboBox' and choices:
                    editor = ttk.Combobox(self.detail, values=choices, state='readonly')
                    if 0 <= value < len(choices):
                        editor.current(value)
                    editor.bind('<<ComboboxSelected>>', lambda _: self.profiles.update(self.values, path, editor.current()))
                else:
                    editor = ttk.Entry(self.detail, textvariable=var)
                    def commit():
                        try:
                            self.profiles.update(self.values, path, int(var.get()) if type(value) is int else var.get())
                        except ValueError as error:
                            messagebox.showerror('Ayar', str(error))
                    ttk.Button(self.detail, text='Değeri uygula', command=commit).pack(anchor='w', pady=5)
                editor.pack(fill='x')
        elif node['class'] in ('TButton', 'TBitBtn'):
            ttk.Label(self.detail, text='Bu oyun eylemi henüz bağlı değil.').pack(anchor='w')
        rows = props.get('DecodedListItems', props.get('Items.Strings', []))
        text = tk.Text(self.detail, wrap='word', height=25)
        text.pack(fill='both', expand=True, pady=10)
        display = {'tasarımda_gizli': node['hidden_by'], 'tasarımda_devre_dışı': node['disabled_by'],
                   'liste_satırları': rows, 'kaynak_özellikleri': props}
        text.insert('1.0', json.dumps(display, ensure_ascii=False, indent=2))
        text.configure(state='disabled')

    def load(self):
        path = filedialog.askopenfilename(filetypes=[('Profil', '*.json')])
        if path:
            try:
                self.values, self.lists = self.profiles.load_document(path)
                self.panel.bind_document(self.values, self.lists)
                self.route_page.supply_directory.set(self.profiles.route_directory)
                self.route_page.source_codepage.set(str(self.profiles.route_codepage))
                self.select()
            except (ValueError, OSError) as error:
                messagebox.showerror('Profil', str(error))

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Profil', '*.json')])
        if path:
            try:
                self.profiles.save(path, self.values, self.lists)
            except (ValueError, OSError) as error:
                messagebox.showerror('Profil', str(error))

    def build_simulator(self, frame):
        ttk.Label(frame, text='MP önce değerlendirilir. Eşik karşılanırsa seçili iksir, ardından yedek aranır.\n'
                  'Bu ekran karar üretir; oyunda iksir kullanmaz.', wraplength=850).grid(row=0, columnspan=2, sticky='w', pady=10)
        defaults = [('HP', 30), ('Maksimum HP', 100), ('MP', 20), ('Maksimum MP', 100),
                    ('HP eşiği (%)', 50), ('MP eşiği (%)', 50)]
        self.sim_vars = []
        for row, (label, value) in enumerate(defaults, 1):
            var = tk.StringVar(value=str(value))
            self.sim_vars.append(var)
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', pady=5)
            ttk.Entry(frame, textvariable=var).grid(row=row, column=1)
        self.sim_result = tk.StringVar()
        self.sim_inventory = tk.StringVar(value='%d,%d' % (HP_FALLBACK[0].inventory_id, MP_FALLBACK[0].inventory_id))
        ttk.Label(frame, text='Deneme envanteri (eşya ID, virgülle ayır)').grid(row=7, column=0, sticky='w', pady=5)
        ttk.Entry(frame, textvariable=self.sim_inventory, width=40).grid(row=7, column=1)
        self.use_panel_potions = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text='Paneldeki HP/MP seçimlerini ve eşiklerini kullan',
                        variable=self.use_panel_potions).grid(row=8, columnspan=2, sticky='w')
        self.sim_actor = tk.StringVar(value='1')
        self.sim_connection = tk.BooleanVar(value=True)
        ttk.Label(frame, text='Deneme karakter ID').grid(row=9,column=0,sticky='w')
        ttk.Entry(frame,textvariable=self.sim_actor).grid(row=9,column=1)
        ttk.Checkbutton(frame,text='Deneme bağlantı kapısı açık',variable=self.sim_connection
                        ).grid(row=10,columnspan=2,sticky='w')
        ttk.Button(frame, text='Kararı hesapla', command=self.simulate).grid(row=11, column=0, pady=10)
        ttk.Label(frame, textvariable=self.sim_result, wraplength=800).grid(row=12, columnspan=2, sticky='w')

    def simulate(self):
        try:
            hp, hm, mp, mm, ht, mt = [int(v.get()) for v in self.sim_vars]
            settings = compile_potions(self.values) if self.use_panel_potions.get() else PotionSettings(
                hp_enabled=True, hp_threshold=ht, mp_enabled=True, mp_threshold=mt)
            ids = tuple(int(value.strip()) for value in self.sim_inventory.get().split(',') if value.strip())
            snapshot = PotionSnapshot(hp, hm, mp, mm, available_inventory_ids=ids,
                availability_complete=True, action_path='direct', state_3a=True, state_3b=False, state_3c=False)
            result = potion_decision(settings, snapshot)
            self.sim_queue = QueueState()
            self.sim_queue_results = []
            for intent in result.intents:
                queued = enqueue_potion_intent(self.sim_queue,intent,int(self.sim_actor.get()),
                           1 if self.sim_connection.get() else 0,0)
                self.sim_queue_results.append(queued)
                if queued.state is not None:self.sim_queue=queued.state
            choices = ', '.join(i.kind.upper() + ' (eşya ' + str(i.inventory_id) + ')' for i in result.intents)
            self.sim_result.set((choices + ' yerel deneme kararı' if choices else 'İksir kararı yok')
                                + ' • Yerel tekrar değeri: ' + str(result.retry_ms) + ' ms'
                                + ' • Kuyruk örneği: %d kayıt / %d bayt' % (len(self.sim_queue.records),sum(len(r.payload) for r in self.sim_queue.records))
                                + ' • Oyuna gönderilmedi')
        except ValueError as error:
            self.sim_result.set('Geçersiz değer: ' + str(error))


if __name__ == '__main__':
    root = tk.Tk()
    Application(root)
    root.mainloop()
