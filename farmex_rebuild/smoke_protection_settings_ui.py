"""Fifty own settings controls, dynamic route Text and persistent shadow state."""
import copy,json,tempfile
from pathlib import Path
from protection_panel_trial import PROTECTION_FIELDS
from name_codec import WindowsNameCodec

def check_protection_settings_ui(app):
    e=app.engine_page;p=app.panel;paths=dict(PROTECTION_FIELDS)
    old_values=dict(app.values);old_choices=copy.deepcopy(app.profiles.route_choices);old_bounds=dict(app.profiles.bounds)
    old_case=e.case.get();old_form=p.form.get();old_sample=e.protection_sample.get();old_hp=e.inputs['hp'].get()
    old_cp=app.route_page.source_codepage.get()
    try:
        app.route_page.source_codepage.set('1254')
        app.profiles.install_route_choices(app.values,paths[0x760],('Rota Seciniz !','Örnek.R'))
        app.profiles.update(app.values,paths[0x760],1)
        app.profiles.update(app.values,paths[0x748],False)
        app.profiles.update(app.values,paths[0x770],True)
        p.form.set('frmMain');p.render();p.widgets[paths[0x748]].invoke()
        assert app.values[paths[0x748]] is True
        e.case.set('Koruma Ayarları');e.reset();e.inputs['hp'].set('unrelated invalid HP')
        e.protection_sample.set('{}');e.tick(1)
        assert e.protection_trial.last.needed==('entry','0046b928')
        assert e.protection_trial.scalar_state=={}
        e.protection_example();data=json.loads(e.protection_sample.get())
        data['normal_returns']['text_cleanup_74c']=False
        e.protection_sample.set(json.dumps(data));e.tick(1)
        assert e.protection_trial.last.needed==('normal','text_cleanup_74c')
        assert e.protection_trial.scalar_state[0x569100]==(1,1)
        assert e.protection_trial.scalar_state[0x569104][1]==int(app.values[paths[0x74c]])
        assert 0x56911c not in e.protection_trial.string_state
        data['normal_returns']['text_cleanup_74c']=True;e.protection_sample.set(json.dumps(data));e.tick(1)
        assert e.protection_trial.last.complete
        assert e.protection_trial.string_state[0x56911c]==WindowsNameCodec(1254).encode('Örnek.R')[0]
        assert e.protection_trial.frame.observation.texts['760']=='Örnek.R'
        assert e.protection_trial.scalar_state[0x569108]==(4,2)
        frame=e.protection_trial.frame;old_state=dict(e.protection_trial.scalar_state);e.tick(1)
        assert e.protection_trial.frame is frame and e.protection_trial.scalar_state==old_state
        for slot in (0x758,0x75c,0x76c,0x770):app.profiles.update(app.values,paths[slot],False)
        p.render();e.tick(1);assert e.protection_trial.last is None
        e.protection_example();e.tick(1)
        assert e.protection_trial.last.complete and 0x10 in e.protection_trial.last.unchanged_enum_offsets
        assert e.protection_trial.scalar_state[0x569108]==(4,2)
        app.profiles.update(app.values,paths[0x760],0);p.render();e.tick(1)
        assert e.protection_trial.last is None
        e.protection_example();e.tick(1);assert e.protection_trial.last.complete
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'protection.json';app.profiles.save(path,app.values,app.lists)
            restored,_=app.profiles.load_document(path)
            assert all(restored[key]==app.values[key] for slot,key in PROTECTION_FIELDS)
        p.widgets[paths[0x748]].invoke();assert app.values[paths[0x748]] is False
        e.protection_example();data=json.loads(e.protection_sample.get());data['ansi_hex']['760']='xx'
        e.protection_sample.set(json.dumps(data));e.tick(1)
        assert e.protection_trial.last is None and e.protection_trial.scalar_state[0x569100]==(1,0)
        e.protection_sample.set('{bad');e.tick(1);assert e.protection_trial.last is None
        assert 'Oyunda ayar uygulaması doğrulandı: False' in e.output.get('1.0','end')
    finally:
        app.profiles.route_choices.clear();app.profiles.route_choices.update(old_choices);app.profiles.bounds=old_bounds
        app.values.clear();app.values.update(old_values);app.route_page.source_codepage.set(old_cp)
        e.protection_sample.set(old_sample);e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset()
        p.form.set(old_form);p.render()
    print('Common protection UI passed:50 source members, actual widget/route Text, four numeric/string captures, cleanup/error prefix shadow, no-match enum retention, stale snapshot rejection, same-frame idempotence and profile roundtrip; local Windows conversion only, no native game action')

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_protection_settings_ui(Application(root))
    finally:root.destroy()
