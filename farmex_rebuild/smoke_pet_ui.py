"""Real owned Pet controls -> settings prefix -> worker plans; no game access."""
import json,tempfile
from pathlib import Path
from unittest.mock import patch
from pet_settings import PET_SETTING_FIELDS

def check_pet_ui(app):
    e=app.engine_page;p=app.panel;paths=dict(PET_SETTING_FIELDS)
    old_document=app.values;old_values=dict(app.values);old_lists=app.lists
    old_case=e.case.get();old_form=p.form.get();old_hp=e.inputs['hp'].get()
    old_settings=e.pet_settings_sample.get();old_runtime=e.pet_runtime_sample.get()
    try:
        for slot,path in PET_SETTING_FIELDS:
            app.profiles.update(app.values,path,'10' if slot==0xf1c else slot==0xf20)
        p.form.set('frmMain');p.render()
        p.widgets[paths[0xf14]].invoke();p.variables[paths[0xf1c]].set('20')
        assert app.values[paths[0xf14]] is True and app.values[paths[0xf1c]]=='20'
        e.case.set('Pet');e.reset();e.inputs['hp'].set('unrelated invalid HP')
        assert e.pet_controls.winfo_manager()=='grid'
        e.pet_settings_sample.set('{}');e.pet_runtime_sample.set('{}');e.tick(1)
        assert e.pet_trial.settings.last.needed==('entry','0040a3ac') and e.pet_trial.frame is None
        e.pet_example();settings=json.loads(e.pet_settings_sample.get())
        settings['normal_returns']['text_cleanup_f1c']=False
        e.pet_settings_sample.set(json.dumps(settings));e.tick(1)
        assert len(e.pet_trial.settings.scalar_state)==4 and e.pet_trial.frame is None
        settings['normal_returns']['text_cleanup_f1c']=True
        e.pet_settings_sample.set(json.dumps(settings));e.tick(1)
        assert e.pet_trial.last.status=='feed_returned'
        assert e.pet_trial.settings.scalar_state[0x5620e8]==(4,20)
        assert e.pet_trial.scalar_state[0x553c58]==(4,10002)
        frame=e.pet_trial.frame;before=dict(e.pet_trial.scalar_state);e.tick(1)
        assert e.pet_trial.frame is frame and e.pet_trial.scalar_state==before
        # Every real radio drives the common priority projection.
        for slot,expected in ((0xf28,1),(0xf24,2),(0xf20,3)):
            p.widgets[paths[slot]].invoke();e.tick(1)
            assert e.pet_trial.last is None # old panel digest is stale
            e.pet_example();e.tick(1)
            assert e.pet_trial.settings.scalar_state[0x5620e0]==(4,expected)
        p.widgets[paths[0xf18]].invoke();assert app.values[paths[0xf18]] is True
        e.pet_example();runtime=json.loads(e.pet_runtime_sample.get())
        runtime['values']['pet_mode_eax']=0;runtime['normal_returns']['set_mode']=False
        e.pet_runtime_sample.set(json.dumps(runtime));e.tick(1)
        assert e.pet_trial.last.needed==('normal_returns','set_mode')
        runtime['normal_returns']['set_mode']=True
        e.pet_runtime_sample.set(json.dumps(runtime));e.tick(1)
        assert e.pet_trial.last.status=='mode_returned'
        assert ('set_mode','004c7fe4',(0x561ef8,3)) in e.pet_trial.last.calls
        e.pet_example();runtime=json.loads(e.pet_runtime_sample.get())
        runtime['values']['pet_exists_eax']=0;runtime['normal_returns']['summon']=False
        e.pet_runtime_sample.set(json.dumps(runtime));e.tick(1)
        assert e.pet_trial.last.needed==('normal_returns','summon')
        assert len(e.pet_trial.last.stores)==3
        runtime['normal_returns']['summon']=True;e.pet_runtime_sample.set(json.dumps(runtime));e.tick(1)
        assert e.pet_trial.last.status=='summon_returned'
        # The actual app profile-load path replaces the document even at identical values.
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'pet.json';app.profiles.save(target,app.values,app.lists)
            with patch('app.filedialog.askopenfilename',return_value=str(target)):
                app.load()
            assert app.values is not old_document
            assert all(app.values[path]==old_document[path] for _,path in PET_SETTING_FIELDS)
            e.tick(1);assert e.pet_trial.frame is None and e.pet_trial.scalar_state=={}
            e.pet_example();e.tick(1);assert e.pet_trial.last.complete
        e.pet_runtime_sample.set('{bad');e.tick(1);assert e.pet_trial.last is None
        e.case.set('Upgrade');e.reset();assert e.pet_controls.winfo_manager()==''
    finally:
        app.values=old_document;app.values.clear();app.values.update(old_values);app.lists=old_lists
        p.bind_document(app.values,app.lists)
        e.pet_settings_sample.set(old_settings);e.pet_runtime_sample.set(old_runtime)
        e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
    print('Pet UI passed: six actual controls -> settings prefix/cleanup -> captured summon/mode/feed plans, retained timers and same-document tickets, stale/profile invalidation; no native or game action')

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_pet_ui(Application(root))
    finally:root.destroy()
