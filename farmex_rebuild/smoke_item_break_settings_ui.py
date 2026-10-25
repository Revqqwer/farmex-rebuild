"""Hidden own UI: three actual controls, partial stores, profiles and freshness."""
import json,tempfile
from pathlib import Path
from item_break_settings import ITEM_BREAK_FIELDS

def check_item_break_settings_ui(app):
    engine=app.engine_page;panel=app.panel;paths=dict(ITEM_BREAK_FIELDS)
    old_values=dict(app.values);old_case=engine.case.get();old_form=panel.form.get()
    old_sample=engine.item_break_settings_sample.get();old_hp=engine.inputs['hp'].get()
    try:
        for slot,path in ITEM_BREAK_FIELDS:app.profiles.update(app.values,path,'1' if slot==0xec8 else False)
        panel.form.set('frmMain');panel.render()
        panel.widgets[paths[0xec0]].invoke();panel.widgets[paths[0xa28]].invoke()
        assert app.values[paths[0xec0]] is True and app.values[paths[0xa28]] is True
        speed=panel.widgets[paths[0xec8]];speed.delete(0,'end');speed.insert(0,'-1')
        engine.case.set('Item Kırma Ayarları');engine.reset();engine.inputs['hp'].set('unrelated invalid HP')
        assert engine.item_break_settings_controls.grid_info() and not engine.control_settings_controls.grid_info()
        engine.item_break_settings_sample.set('{}');engine.tick(1)
        assert engine.item_break_settings_trial.last.needed==('settings',('entry','00470cd5'))
        engine.item_break_settings_example();data=json.loads(engine.item_break_settings_sample.get())
        data['normal_returns']['parser_outer_ec8']=False
        engine.item_break_settings_sample.set(json.dumps(data));engine.tick(1)
        assert len(engine.item_break_settings_trial.scalar_state)==1
        data['normal_returns']['parser_outer_ec8']=True;data['normal_returns']['toggle']=False
        engine.item_break_settings_sample.set(json.dumps(data));engine.tick(1)
        assert engine.item_break_settings_trial.last.needed=='toggle_returned'
        assert engine.item_break_settings_trial.scalar_state[0x569a24]==(4,0xffffffff)
        assert engine.item_break_settings_trial.scalar_state[0x569a2c]==(4,0)
        data['normal_returns']['toggle']=True;engine.item_break_settings_sample.set(json.dumps(data));engine.tick(1)
        assert engine.item_break_settings_trial.last.complete
        frame=engine.item_break_settings_trial.frame;state=dict(engine.item_break_settings_trial.scalar_state)
        engine.tick(1);assert engine.item_break_settings_trial.frame is frame and engine.item_break_settings_trial.scalar_state==state
        speed.delete(0,'end');speed.insert(0,'5');engine.tick(1)
        assert engine.item_break_settings_trial.last is None
        engine.item_break_settings_example();engine.tick(1)
        assert engine.item_break_settings_trial.last.complete
        data=json.loads(engine.item_break_settings_sample.get());engine.item_break_settings_trial.reset()
        data['values']={'fresh_enabled_byte':0};engine.item_break_settings_sample.set(json.dumps(data));engine.tick(1)
        assert engine.item_break_settings_trial.last is None
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'item_break.json';app.profiles.save(target,app.values,app.lists)
            values,_=app.profiles.load_document(target)
            assert all(values[path]==app.values[path] for _,path in ITEM_BREAK_FIELDS)
        engine.item_break_settings_sample.set('{bad');engine.tick(1)
        assert engine.item_break_settings_trial.last is None
    finally:
        app.values.clear();app.values.update(old_values)
        engine.item_break_settings_sample.set(old_sample);engine.inputs['hp'].set(old_hp);engine.case.set(old_case);engine.reset()
        panel.form.set(old_form);panel.render()
    print('Item-break settings UI passed:3 actual fields, signed-lowDWORD speed, source reset/toggle prefix, independent HP, stale/override rejection, idempotence and profiles; local only')

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_item_break_settings_ui(Application(root))
    finally:root.destroy()
