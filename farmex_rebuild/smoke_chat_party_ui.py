"""Exercise actual own Tk chat invite controls, no foreground/game operations."""
import copy
import json
from chat_party_invite import CHAT_PARTY_INPUTS, PARTY_LIST
from chat_party_trial import EXAMPLE_CHAT_HEX, example_chat_party_sample

def check_chat_party_ui(app):
    e=app.engine_page;p=app.panel
    old_values=dict(app.values);old_lists=copy.deepcopy(app.lists)
    old_form=p.form.get();old_case=e.case.get();old_hp=e.inputs['hp'].get()
    old_hex=e.chat_party_packet.get();old_sample=e.chat_party_sample.get();old_cp=e.chat_party_codepage.get()
    enabled,command,restricted=CHAT_PARTY_INPUTS
    try:
        for path,value in zip(CHAT_PARTY_INPUTS,(False,'add',True)):
            app.profiles.update(app.values,path,value)
        app.lists[PARTY_LIST]=[{'caption':'Alice','subitems':[],'checked':False}]
        p.form.set('frmMain');p.render()
        p.widgets[enabled].invoke()
        e.case.set('Chat/PM Party');e.reset();e.inputs['hp'].set('unused bad HP')
        e.chat_party_codepage.set('1254');e.chat_party_packet.set('10');e.chat_party_sample.set('{}');e.tick(1)
        assert not e.chat_party_trial.last.complete and e.chat_party_trial.frame is None
        e.chat_party_example();e.tick(1)
        assert e.chat_party_trial.last.complete and e.chat_party_trial.last.action=='invite'
        assert 'Yerel kayıt sayısı: 2' in e.output.get('1.0','end')
        frame=e.chat_party_trial.frame
        assert [r.payload for r in frame.queue.records]==[b'\x2f\x03\x05\x00Alice',b'\x2f\x01\x05\x00Alice']
        e.tick(1);assert e.chat_party_trial.frame is frame and len(frame.queue.records)==2
        p.variables[command].set('ADD');e.tick(1)
        assert app.values[command]=='ADD' and e.chat_party_trial.last.status=='command_mismatch'
        assert e.chat_party_trial.frame.queue.records==()
        p.variables[command].set('add')
        # Change to equal-length unlisted sender; actual panel restriction controls it.
        e.chat_party_packet.set(EXAMPLE_CHAT_HEX.replace('416c696365','4361726f6c'));e.tick(1)
        assert e.chat_party_trial.last.status=='unlisted' and e.chat_party_trial.frame.queue.records==()
        p.widgets[restricted].invoke();e.tick(1)
        assert e.chat_party_trial.last.action=='invite' and len(e.chat_party_trial.frame.queue.records)==2
        # A new invocation holds first record while second helper observation is absent.
        e.chat_party_example()
        raw=json.loads(example_chat_party_sample());del raw['queue_samples']['2']
        e.chat_party_sample.set(json.dumps(raw));e.tick(1)
        assert not e.chat_party_trial.last.complete and len(e.chat_party_trial.frame.queue.records)==1
        e.chat_party_sample.set(example_chat_party_sample());e.tick(1)
        assert e.chat_party_trial.last.complete and len(e.chat_party_trial.frame.queue.records)==2
        # New invalid input clears cached successful frame and local queue display.
        e.chat_party_sample.set('{bad');e.tick(1)
        assert e.chat_party_trial.last is None and e.chat_party_trial.frame is None
        p.widgets[enabled].invoke();e.chat_party_sample.set('{"helper_returns":"unvisited"}');e.tick(1)
        assert e.chat_party_trial.last.status=='disabled' and e.chat_party_trial.frame.queue.records==()
        assert not e.chat_party_trial.last.native_execution_verified
    finally:
        app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
        e.chat_party_packet.set(old_hex);e.chat_party_sample.set(old_sample);e.chat_party_codepage.set(old_cp)
        e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
    print('Chat/PM UI passed: real enable/command/list controls, unchecked caption, exact case, unlisted/all mode, partial two-record resume, no duplicate tick and stale-frame clearing; no native actions')
