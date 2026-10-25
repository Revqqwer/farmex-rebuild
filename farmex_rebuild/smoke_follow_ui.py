"""Real own widgets feed follow trial; no original process or game actions."""
import json
from follow_engine import ROOT
from follow_trial import example_follow_sample

def check_follow_ui(app):
    e=app.engine_page;p=app.panel;old_values=dict(app.values);old_case=e.case.get()
    old_form=p.form.get();old_sample=e.follow_sample.get();old_hp=e.inputs['hp'].get()
    try:
        app.profiles.update(app.values,ROOT+'chFollow',False)
        app.profiles.update(app.values,ROOT+'rdFollowPartyLeader',True)
        p.form.set('frmMain');p.render()
        p.widgets[ROOT+'chFollow'].invoke();p.variables[ROOT+'txtFollowNick'].set('Alice')
        e.case.set('Takip');e.reset();e.inputs['hp'].set('unrelated bad HP')
        e.follow_sample.set('{}');e.tick(1)
        assert not e.follow_trial.last.complete and e.follow_trial.last.movement is None
        e.follow_sample.set(example_follow_sample());e.tick(1)
        assert e.follow_trial.configuration.mode_dword==1
        assert e.follow_trial.last.movement==(0x41200000,0x41a00000)
        p.widgets[ROOT+'rdFollowManuelNick'].invoke();e.tick(1)
        assert app.values[ROOT+'rdFollowPartyLeader'] is False
        assert e.follow_trial.last.movement==(0x41200000,0x41c00000)
        assert e.follow_trial.state.cached_id_dword==7
        r=json.loads(example_follow_sample());r['helper_returns']['name_lookup']=False
        e.follow_sample.set(json.dumps(r));e.tick(1)
        assert e.follow_trial.last.complete # Same name uses cached ID.
        p.variables[ROOT+'txtFollowNick'].set('Bob');e.tick(1)
        assert not e.follow_trial.last.complete
        assert e.follow_trial.state.previous_name=='Bob' and e.follow_trial.state.cached_id_dword==0
        r['helper_returns']['name_lookup']=True;r['name_id_dword']=8
        e.follow_sample.set(json.dumps(r));e.tick(1)
        assert e.follow_trial.last.complete and e.follow_trial.state.cached_id_dword==8
        e.follow_sample.set('{bad');e.tick(1)
        assert e.follow_trial.last is None and e.follow_trial.state.cached_id_dword==8
        p.widgets[ROOT+'chFollow'].invoke()
        e.follow_sample.set(json.dumps(dict(entry_reached=True,helper_returns='unused bad')));e.tick(1)
        assert e.follow_trial.last.status=='disabled' and e.follow_trial.last.movement is None
        assert not e.follow_trial.last.native_execution_verified
    finally:
        app.values.clear();app.values.update(old_values)
        e.follow_sample.set(old_sample);e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset()
        p.form.set(old_form);p.render()
    print('Follow UI passed: real panel leader/manual/name/enable widgets, default gaps, cached ID and fresh-name invalidation, separate Y, stale-result clearing; no game movement')
