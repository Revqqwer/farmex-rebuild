"""Hidden own DC checkboxes -> four-layer fixture, never live operations."""
import json,tempfile
from pathlib import Path
from dc_panel_trial import DC_PANEL_INPUTS
import test_dc_panel_trial as fixture

def check_dc_panel_ui(app):
    e=app.engine_page;p=app.panel;old_values=dict(app.values)
    old_case=e.case.get();old_form=p.form.get();old_sample=e.dc_sample.get();old_hp=e.inputs['hp'].get()
    try:
        for key in DC_PANEL_INPUTS:app.profiles.update(app.values,key,False)
        p.form.set('frmMain');p.render()
        p.widgets[DC_PANEL_INPUTS[0]].invoke();p.widgets[DC_PANEL_INPUTS[1]].invoke()
        assert tuple(app.values[k] for k in DC_PANEL_INPUTS)==(True,True)
        e.case.set('DC Koruma');e.reset();e.inputs['hp'].set('unrelated invalid HP')
        e.dc_sample.set('{}');e.tick(1)
        assert e.dc_trial.last.needed==('parent',('entry','00459981'))
        e.dc_example();d=json.loads(e.dc_sample.get());d['parent']['normal_returns']['post_tick']=False
        e.dc_sample.set(json.dumps(d));e.tick(1)
        assert e.dc_trial.last.needed==('parent',('normal','post_tick'))
        assert e.dc_trial.last.action.consumer.kind=='list'
        assert e.dc_trial.shadow_stores=={}
        d['parent']['normal_returns']['post_tick']=True;e.dc_sample.set(json.dumps(d));e.tick(1)
        assert e.dc_trial.last.complete and e.dc_trial.shadow_stores[0x553ce4]==(4,300010)
        frame=e.dc_trial.frame;e.tick(1);assert e.dc_trial.frame is frame
        p.widgets[DC_PANEL_INPUTS[1]].invoke();e.tick(1)
        assert e.dc_trial.last is None and e.dc_trial.prefix.write_intents==()
        e.dc_example();e.tick(1);assert e.dc_trial.last.action.consumer.kind=='scan'
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'dc.json';app.profiles.save(target,app.values,app.lists)
            values,_=app.profiles.load_document(target)
            assert all(values[k]==app.values[k] for k in DC_PANEL_INPUTS)
        p.widgets[DC_PANEL_INPUTS[1]].invoke();e.reset()
        helper=fixture.DCPanelTrialTests();helper.setUp();d=helper.source_sample()
        d['transfers']['row0.send']['normal_returns']['stub.wait']=False
        e.dc_sample.set(json.dumps(d));e.tick(1)
        assert len(e.dc_trial.last.write_intents)==2 and e.dc_trial.shadow_stores=={}
        d['transfers']['row0.send']['normal_returns']['stub.wait']=True
        e.dc_sample.set(json.dumps(d));e.tick(1);assert e.dc_trial.last.complete
        e.reset();d=helper.source_sample();d['transfers']['row0.send']['values']['copied_root_dword']='invalid'
        e.dc_sample.set(json.dumps(d));e.tick(1)
        assert e.dc_trial.last is None and len(e.dc_trial.prefix.write_intents)==1
        p.widgets[DC_PANEL_INPUTS[0]].invoke();e.dc_example();d=json.loads(e.dc_sample.get());d['consumer']='unreached invalid'
        e.dc_sample.set(json.dumps(d));e.tick(1)
        assert e.dc_trial.last.complete and e.dc_trial.last.action is None
    finally:
        app.values.clear();app.values.update(old_values)
        e.inputs['hp'].set(old_hp);e.dc_sample.set(old_sample);e.case.set(old_case);e.reset()
        p.form.set(old_form);p.render()
    print('DC panel UI passed: actual two checkbox widgets, list/scan/disabled routing, four-layer wait/resume, late invalid capture prefix, stale snapshot rejection and profile roundtrip; inert remote records only')

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_dc_panel_ui(Application(root))
    finally:root.destroy()
