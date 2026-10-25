import tkinter as tk
from tkinter import ttk
from mining_engine import load_mining_routes


class MiningRoutesPage:
    def __init__(self, frame):
        self.routes = load_mining_routes()
        self.choice = tk.StringVar(value=next(iter(self.routes)))
        top = ttk.Frame(frame, padding=8)
        top.pack(fill='x')
        ttk.Label(top, text='Maden rotası:').pack(side='left')
        selector = ttk.Combobox(top, values=list(self.routes), textvariable=self.choice, state='readonly', width=25)
        selector.pack(side='left', padx=8)
        selector.bind('<<ComboboxSelected>>', lambda _: self.render())
        self.info = tk.StringVar()
        ttk.Label(top, textvariable=self.info).pack(side='left')
        split = ttk.Panedwindow(frame, orient='horizontal')
        split.pack(fill='both', expand=True)
        table_frame, graph_frame = ttk.Frame(split), ttk.Frame(split)
        split.add(table_frame, weight=1)
        split.add(graph_frame, weight=1)
        self.table = ttk.Treeview(table_frame, columns=('step', 'command', 'one', 'two', 'status'), show='headings')
        for name, caption, width in [('step', '#', 35), ('command', 'Komut', 90),
                                     ('one', 'X / NPC', 125), ('two', 'Y', 75), ('status', 'Kayıt', 85)]:
            self.table.heading(name, text=caption)
            self.table.column(name, width=width)
        scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        scroll.pack(side='right', fill='y')
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(fill='both', expand=True)
        self.graph = tk.Canvas(graph_frame, width=480, height=440, background='#fafafa', highlightthickness=0)
        self.graph.pack(fill='both', expand=True)
        ttk.Label(frame, text='Kayıtlı koordinatların görünümü. Oyun haritası veya canlı hareket değildir.',
                  padding=8).pack(anchor='w')
        self.render()

    def render(self):
        route = self.routes[self.choice.get()]
        records = route['records']
        missing = sum(not row['literal_recovered'] for row in records)
        self.info.set('%d adım • %s' % (len(records), 'Tam kayıt' if not missing else '%d kayıt çözümlenmedi' % missing))
        self.table.delete(*self.table.get_children())
        self.graph.delete('all')
        for row in records:
            self.table.insert('', 'end', values=(row['index'] + 1, row.get('command') or 'Bilinmiyor',
                row.get('parameter_1_text') or '', row.get('parameter_2_text') or '',
                'Kurtarıldı' if row['literal_recovered'] else 'Eksik'))
        points = [row for row in records if row.get('command') == 'Koordinat' and row['literal_recovered']]
        if not points:
            return
        min_x, max_x = min(r['x'] for r in points), max(r['x'] for r in points)
        min_y, max_y = min(r['y'] for r in points), max(r['y'] for r in points)
        width, height = 460, 420
        scale = min((width - 50) / max(1, max_x - min_x), (height - 50) / max(1, max_y - min_y))
        previous = None
        for row in records:
            if row.get('command') != 'Koordinat' or not row['literal_recovered']:
                previous = None
                continue
            x, y = 25 + (row['x'] - min_x) * scale, height - 25 - (row['y'] - min_y) * scale
            if previous:
                self.graph.create_line(*previous, x, y, fill='#6486ae')
            self.graph.create_oval(x-3, y-3, x+3, y+3, fill='#2460a2', outline='')
            self.graph.create_text(x + 6, y - 7, text=str(row['index'] + 1), anchor='w', font=('Tahoma', 7))
            previous = (x, y)
