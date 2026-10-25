"""Three own panel widgets ->settings ->prefix ->TP source plan, no game calls."""
import json,tempfile
from pathlib import Path
from teleport_protection import TP_INPUTS

def check_tp_protection_ui(app):
    e=app.engine_page;p=app.panel;old_values=dict(app.values);old_case=e.case.get();old_form=p.form.get()
    old_packet=e.tp_packet.get();old_sample=e.tp_sample.get();old_hp=e.inputs['hp'].get()
    enabled,stop,dc=TP_INPUTS
    try:
        for path,value in zip(TP_INPUTS,(False,False,True)):app.profiles.update(app.values,path,value)
        p.form.set('frmMain');p.render();p.widgets[enabled].invoke();p.widgets[stop].invoke()
        assert app.values[enabled] is True and app.values[stop] is True
        e.case.set('TP Koruma');e.reset();e.inputs['hp'].set('unrelated invalid HP')
        e.tp_packet.set('27 01 0a');e.tp_sample.set('{}');e.tick(1)
        assert e.tp_trial.last.settings.needed==('entry','0046c0e1') and e.tp_trial.last.dispatch is None
        e.tp_example();data=json.loads(e.tp_sample.get());data['normal_returns']['notice_block']=False
        e.tp_sample.set(json.dumps(data));e.tick(1)
        assert e.tp_trial.last.dispatch.child.needed==('normal','notice_block')
        assert e.tp_trial.last.dispatch.child.stores==()
        data['normal_returns']['notice_block']=True;e.tp_sample.set(json.dumps(data));e.tick(1)
        assert e.tp_trial.last.dispatch.complete
        assert 'tp_stop' in [c[2] for c in e.tp_trial.last.dispatch.child.calls]
        frame=e.tp_trial.dispatch;e.tick(1);assert e.tp_trial.dispatch is frame
        p.widgets[dc].invoke();e.tick(1);assert e.tp_trial.last is None
        e.tp_example();e.tick(1)
        assert e.tp_trial.last.dispatch.complete
        assert 'tp_disconnect' in [c[2] for c in e.tp_trial.last.dispatch.child.calls]
        e.tp_packet.set('10');e.tick(1);assert e.tp_trial.last is None
        e.tp_example();e.tick(1)
        assert e.tp_trial.last.dispatch.status=='earlier_branch_not_bound'
        assert e.tp_trial.last.dispatch.child is None
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'tp.json';app.profiles.save(path,app.values,app.lists)
            restored,_=app.profiles.load_document(path)
            assert all(restored[k]==app.values[k] for k in TP_INPUTS)
        e.tp_sample.set('{bad');e.tick(1);assert e.tp_trial.last is None
        assert 'Oyunda işlem doğrulandı: False' in e.output.get('1.0','end')
    finally:
        app.values.clear();app.values.update(old_values);e.tp_packet.set(old_packet);e.tp_sample.set(old_sample)
        e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
    print('TP protection UI passed: three actual controls ->bounded settings ->14 opcode prefix ->TP plan; notice gap/resume, stop/DC radio mapping, stale panel/packet rejection, same-frame continuation, earlier-branch stop and profile roundtrip; no game action')

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_tp_protection_ui(Application(root))
    finally:root.destroy()
