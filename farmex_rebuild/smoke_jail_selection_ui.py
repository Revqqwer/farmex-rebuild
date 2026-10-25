"""Hidden own panel checked-list, capture gaps and profile roundtrip."""
import copy,json,tempfile
from pathlib import Path
from jail_selection_trial import JAIL_LIST_PATH
from name_codec import WindowsNameCodec

def check_jail_selection_ui(app):
    e=app.engine_page;p=app.panel;old_lists=copy.deepcopy(app.lists)
    old_case=e.case.get();old_form=p.form.get();old_sample=e.jail_selection_sample.get()
    old_cp=app.route_page.source_codepage.get();old_hp=e.inputs['hp'].get()
    try:
        app.lists[JAIL_LIST_PATH]=[dict(caption='Örnek',subitems=['Karakter'],checked=True),
          dict(caption='Skipped',subitems=[],checked=False),dict(caption='Third',subitems=[],checked=True)]
        p.form.set('frmDCWindow');p.render()
        table=p.widgets[JAIL_LIST_PATH]
        assert table.item('0','values')[0]=='☑ Örnek'
        assert table.item('1','values')[0]=='☐ Skipped'
        app.route_page.source_codepage.set('1254')
        e.case.set('DC–Hapis Listesi');e.reset();e.inputs['hp'].set('unrelated invalid HP')
        e.jail_selection_sample.set('{}');e.tick(1)
        assert e.jail_selection_trial.last.needed==('entry','0046ce04')
        e.jail_selection_example();d=json.loads(e.jail_selection_sample.get())
        d['normal_returns']['row0.unicode_cleanup']=False
        e.jail_selection_sample.set(json.dumps(d));e.tick(1)
        assert e.jail_selection_trial.last.needed==('normal','row0.unicode_cleanup')
        assert e.jail_selection_trial.saved_rows==()
        d['normal_returns']['row0.unicode_cleanup']=True;e.jail_selection_sample.set(json.dumps(d));e.tick(1)
        assert e.jail_selection_trial.last.complete
        assert e.jail_selection_trial.saved_rows==(WindowsNameCodec(1254).encode('Örnek')[0],b'Third')
        frame=e.jail_selection_trial.frame;e.tick(1);assert e.jail_selection_trial.frame is frame
        app.lists[JAIL_LIST_PATH][1]['checked']=True;p.render();e.tick(1)
        assert e.jail_selection_trial.last is None
        e.jail_selection_example();e.tick(1);assert len(e.jail_selection_trial.saved_rows)==3
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'jail.json';app.profiles.save(target,app.values,app.lists)
            _,lists=app.profiles.load_document(target)
            assert lists[JAIL_LIST_PATH]==app.lists[JAIL_LIST_PATH]
        app.lists[JAIL_LIST_PATH][1]['checked']=False;p.render();e.reset()
        e.jail_selection_example();d=json.loads(e.jail_selection_sample.get());d['ansi_hex']['row2.title']='xx'
        e.jail_selection_sample.set(json.dumps(d));e.tick(1)
        assert e.jail_selection_trial.last is None
        assert e.jail_selection_trial.saved_rows==(WindowsNameCodec(1254).encode('Örnek')[0],)
        e.jail_selection_sample.set('{bad');e.tick(1);assert e.jail_selection_trial.last is None
    finally:
        app.lists.clear();app.lists.update(old_lists)
        app.route_page.source_codepage.set(old_cp);e.inputs['hp'].set(old_hp)
        e.jail_selection_sample.set(old_sample);e.case.set(old_case);e.reset()
        p.form.set(old_form);p.render()
    print('Jail selection UI passed: actual checked captions/order, local Windows conversion, cleanup gap, prefix on late invalid capture, stale snapshot rejection, profile roundtrip; no native/game action')

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_jail_selection_ui(Application(root))
    finally:root.destroy()
