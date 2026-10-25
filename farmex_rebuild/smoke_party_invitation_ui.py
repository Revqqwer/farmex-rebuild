"""Own invitation UI integration; no game client or network action."""
import copy,json
from party_invitation import ROOT,PARTY_LIST
from party_invitation_trial import example_invitation_sample

def check_party_invitation_ui(app):
    e=app.engine_page;p=app.panel;old_values=dict(app.values);old_lists=copy.deepcopy(app.lists)
    old_form=p.form.get();old_case=e.case.get();old_hex=e.party_packet.get();old_sample=e.party_sample.get()
    old_cp=e.party_codepage.get();old_hp=e.inputs['hp'].get()
    try:
        for path,value in ((ROOT+'chotoparty',False),(ROOT+'rdAllPartyAccept',True),(ROOT+'chpartyred',True),(ROOT+'chDisablePtBug',False)):
            app.profiles.update(app.values,path,value)
        app.lists[PARTY_LIST]=[{'caption':'Alice','subitems':[],'checked':False}]
        p.form.set('frmMain');p.render();p.widgets[ROOT+'chotoparty'].invoke();p.widgets[ROOT+'rdListPartyAccept'].invoke()
        e.case.set('Party Daveti');e.reset();e.inputs['hp'].set('unrelated bad HP');e.party_codepage.set('1254')
        e.party_packet.set('2f02');e.party_sample.set('{}');e.tick(1)
        assert not e.party_trial.last.complete and e.party_trial.last.action is None
        e.party_example();e.tick(1)
        assert e.party_trial.last.complete and e.party_trial.last.action=='accept'
        assert e.party_trial.last.handler_return_dword==1
        p.widgets[ROOT+'chDisablePtBug'].invoke();e.tick(1)
        assert e.party_trial.last.action=='accept' and e.party_trial.last.handler_return_dword==0
        e.party_packet.set('2f02ffff0300426f62');e.tick(1)
        assert e.party_trial.last.action=='reject'
        p.widgets[ROOT+'rdAllPartyAccept'].invoke();e.tick(1)
        assert e.party_trial.last.action=='accept' and not e.party_trial.last.matched
        r=json.loads(example_invitation_sample());r['helper_returns']['name_filter']=False
        e.party_sample.set(json.dumps(r));e.tick(1)
        assert not e.party_trial.last.complete and e.party_trial.last.action is None
        e.party_sample.set('{bad');e.tick(1);assert e.party_trial.last is None
        p.widgets[ROOT+'chotoparty'].invoke();e.party_sample.set(example_invitation_sample());e.tick(1)
        assert e.party_trial.last.status=='auto_accept_disabled'
        assert not e.party_trial.last.native_execution_verified
    finally:
        app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
        e.party_packet.set(old_hex);e.party_sample.set(old_sample);e.party_codepage.set(old_cp)
        e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
    print('Party invitation UI passed: real enable/all/list/bug widgets, unchecked list row, accept/reject decisions, independent filter gate and stale-result clearing; no network actions')
