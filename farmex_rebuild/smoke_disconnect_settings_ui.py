"""Own hidden UI: DC settings, route Text, retained prefix and profile roundtrip."""
import copy,json,tempfile
from pathlib import Path
from disconnect_settings import DC_SETTING_FIELDS
from name_codec import WindowsNameCodec


def check_disconnect_settings_ui(app):
    e=app.engine_page;p=app.panel;paths=dict(DC_SETTING_FIELDS)
    old_values=dict(app.values);old_choices=copy.deepcopy(app.profiles.route_choices);old_bounds=dict(app.profiles.bounds)
    old_case=e.case.get();old_form=p.form.get();old_sample=e.disconnect_sample.get();old_hp=e.inputs['hp'].get()
    old_cp=app.route_page.source_codepage.get()
    try:
        app.route_page.source_codepage.set('1254')
        app.profiles.install_route_choices(app.values,paths[0x84c],('Rota Seciniz !','DC Örnek.R'))
        app.profiles.update(app.values,paths[0x84c],1)
        app.profiles.update(app.values,paths[0x828],False)
        app.profiles.update(app.values,paths[0x83c],2)
        p.form.set('frmMain');p.render();p.widgets[paths[0x828]].invoke()
        assert app.values[paths[0x828]] is True
        entry=p.widgets[paths[0x834]];entry.delete(0,'end');entry.insert(0,'25')
        assert app.values[paths[0x834]]=='25'
        e.case.set('DC / Relog Ayarları');e.reset();e.inputs['hp'].set('unrelated invalid HP')
        e.disconnect_sample.set('{}');e.tick(1)
        assert e.disconnect_trial.last.needed==('entry','00457d02') and e.disconnect_trial.scalar_state=={}
        e.disconnect_example();data=json.loads(e.disconnect_sample.get())
        data['normal_returns']['text_cleanup_834']=False
        e.disconnect_sample.set(json.dumps(data));e.tick(1)
        assert e.disconnect_trial.last.needed==('normal','text_cleanup_834')
        assert e.disconnect_trial.scalar_state[0x56221e]==(1,1)
        assert e.disconnect_trial.scalar_state[0x562228]==(4,25)
        assert e.disconnect_trial.string_state=={}
        data['normal_returns']['text_cleanup_834']=True;e.disconnect_sample.set(json.dumps(data));e.tick(1)
        assert e.disconnect_trial.last.complete
        assert e.disconnect_trial.scalar_state[0x562224]==(4,2)
        assert e.disconnect_trial.scalar_state[0x56222e]==(1,1)
        assert e.disconnect_trial.string_state[0x562230]==WindowsNameCodec(1254).encode('DC Örnek.R')[0]
        frame=e.disconnect_trial.frame;state=dict(e.disconnect_trial.scalar_state);e.tick(1)
        assert e.disconnect_trial.frame is frame and e.disconnect_trial.scalar_state==state
        # Same index, changed Text invalidates the prior snapshot.
        app.profiles.install_route_choices(app.values,paths[0x84c],('Rota Seciniz !','Başka.R'))
        app.profiles.update(app.values,paths[0x84c],1);p.render()
        e.tick(1);assert e.disconnect_trial.last is None
        e.disconnect_example();e.tick(1);assert e.disconnect_trial.last.complete
        assert e.disconnect_trial.string_state[0x562230]==WindowsNameCodec(1254).encode('Başka.R')[0]
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'disconnect.json';app.profiles.save(target,app.values,app.lists)
            restored,_=app.profiles.load_document(target)
            assert all(restored[path]==app.values[path] for _,path in DC_SETTING_FIELDS)
        p.widgets[paths[0x828]].invoke();assert app.values[paths[0x828]] is False
        e.disconnect_example();data=json.loads(e.disconnect_sample.get());data['ansi_hex']['84c']='xx'
        e.disconnect_sample.set(json.dumps(data));e.tick(1)
        assert e.disconnect_trial.last is None and e.disconnect_trial.scalar_state[0x56221e]==(1,0)
        e.disconnect_sample.set('{bad');e.tick(1);assert e.disconnect_trial.last is None
    finally:
        app.profiles.route_choices.clear();app.profiles.route_choices.update(old_choices);app.profiles.bounds=old_bounds
        app.values.clear();app.values.update(old_values);app.route_page.source_codepage.set(old_cp)
        e.disconnect_sample.set(old_sample);e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset()
        p.form.set(old_form);p.render()
    print('DC settings UI passed:14 actual fields, widget/route Text, raw combo/number, constant manual flag, prefix resume, stale snapshot rejection, idempotence and profile roundtrip; local only')


if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_disconnect_settings_ui(Application(root))
    finally:root.destroy()
