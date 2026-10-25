"""Own hidden UI Genie flag binding, prefix/stale behavior and persistence."""
import json,tempfile
from pathlib import Path
from genie_settings import GENIE_SETTING_FIELDS


def check_genie_settings_ui(app):
    e=app.engine_page;p=app.panel;paths=dict(GENIE_SETTING_FIELDS)
    old_values=dict(app.values);old_case=e.case.get();old_form=p.form.get()
    old_sample=e.genie_settings_sample.get();old_hp=e.inputs['hp'].get()
    try:
        for _,path in GENIE_SETTING_FIELDS:app.profiles.update(app.values,path,False)
        p.form.set('frmMain');p.render();p.widgets[paths[0xbd0]].invoke()
        assert app.values[paths[0xbd0]] is True
        p.widgets[paths[0xbd4]].invoke();assert app.values[paths[0xbd4]] is True
        e.case.set('Genie Ayarları');e.reset();e.inputs['hp'].set('unrelated invalid HP')
        e.genie_settings_sample.set('{}');e.tick(1)
        assert e.genie_settings_trial.last.needed==('entry','004580ac')
        assert e.genie_settings_trial.scalar_state=={}
        e.genie_settings_example();data=json.loads(e.genie_settings_sample.get());data['normal_returns']['checked_bd4']=False
        e.genie_settings_sample.set(json.dumps(data));e.tick(1)
        assert e.genie_settings_trial.last.needed==('normal','checked_bd4')
        assert e.genie_settings_trial.scalar_state[0x56224c]==(1,1)
        assert len(e.genie_settings_trial.scalar_state)==2
        data['normal_returns']['checked_bd4']=True;e.genie_settings_sample.set(json.dumps(data));e.tick(1)
        assert e.genie_settings_trial.last.complete
        assert e.genie_settings_trial.scalar_state[0x56224e]==(1,1)
        frame=e.genie_settings_trial.frame;before=dict(e.genie_settings_trial.scalar_state);e.tick(1)
        assert e.genie_settings_trial.frame is frame and e.genie_settings_trial.scalar_state==before
        p.widgets[paths[0xbe8]].invoke();e.tick(1)
        assert e.genie_settings_trial.last is None
        e.genie_settings_example();e.tick(1);assert e.genie_settings_trial.last.complete
        assert e.genie_settings_trial.scalar_state[0x562250]==(1,1)
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'genie.json';app.profiles.save(target,app.values,app.lists)
            restored,_=app.profiles.load_document(target)
            assert all(restored[path]==app.values[path] for _,path in GENIE_SETTING_FIELDS)
        e.genie_settings_sample.set('{bad');e.tick(1);assert e.genie_settings_trial.last is None
    finally:
        app.values.clear();app.values.update(old_values)
        e.genie_settings_sample.set(old_sample);e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset()
        p.form.set(old_form);p.render()
    print('Genie settings UI passed:5 actual checkbox fields, source-order shadow, prefix wait/resume, stale capture rejection, idempotence and profile roundtrip; no coupon sync or worker action')


if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_genie_settings_ui(Application(root))
    finally:root.destroy()
