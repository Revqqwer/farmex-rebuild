"""Real own Tk command widgets and reached observations, no native actions."""
import json
from chat_commands import ROOT,SPECS
from chat_commands_trial import example_chat_commands_sample,example_detailed_commands_sample

def check_chat_commands_ui(app):
    e=app.engine_page;p=app.panel;old_values=dict(app.values)
    old_form=p.form.get();old_case=e.case.get();old_hp=e.inputs['hp'].get()
    old_hex=e.chat_commands_packet.get();old_sample=e.chat_commands_sample.get();old_cp=e.chat_commands_codepage.get()
    old_detailed=e.chat_commands_detailed.get()
    try:
        for _,check,text,*_ in SPECS:
            app.profiles.update(app.values,ROOT+check,False);app.profiles.update(app.values,ROOT+text,'go')
        p.form.set('frmMain');p.render()
        p.widgets[ROOT+'chkmtdc'].invoke()
        e.case.set('Chat Komutları');e.reset();e.inputs['hp'].set('unused bad HP')
        assert e.chat_commands_controls.winfo_manager()=='grid'
        e.chat_commands_codepage.set('1254');e.chat_commands_packet.set('10');e.chat_commands_sample.set('{}');e.tick(1)
        assert not e.chat_commands_trial.last.complete and e.chat_commands_trial.frame is None
        e.chat_commands_example();e.tick(1)
        assert e.chat_commands_trial.last.complete and [a.key for a in e.chat_commands_trial.last.actions]==['disconnect']
        p.widgets[ROOT+'chkmtbotbaslat'].invoke();e.tick(1)
        assert [a.key for a in e.chat_commands_trial.last.actions]==['disconnect','bot_start']
        assert 'Çağrı planı sayısı: 2' in e.output.get('1.0','end')
        frame=e.chat_commands_trial.frame;e.tick(1);assert e.chat_commands_trial.frame is frame
        p.variables[ROOT+'txtkmtbotbaslat'].set('GO');e.tick(1)
        assert [a.key for a in e.chat_commands_trial.last.actions]==['disconnect']
        p.variables[ROOT+'txtkmtbotbaslat'].set('go');e.chat_commands_example()
        raw=json.loads(example_chat_commands_sample());raw['helper_returns']['action:disconnect']=False
        raw['helper_returns']['compare:return_center']='unvisited'
        e.chat_commands_sample.set(json.dumps(raw));e.tick(1)
        assert not e.chat_commands_trial.last.complete and [a.key for a in e.chat_commands_trial.last.actions]==['disconnect']
        e.chat_commands_sample.set(example_chat_commands_sample());e.tick(1)
        assert e.chat_commands_trial.last.complete and len(e.chat_commands_trial.last.actions)==2
        e.chat_commands_sample.set('{bad');e.tick(1)
        assert e.chat_commands_trial.last is None and e.chat_commands_trial.frame is None
        p.widgets[ROOT+'chkmtdc'].invoke();p.widgets[ROOT+'chkmtbotbaslat'].invoke()
        e.chat_commands_sample.set(example_chat_commands_sample());e.tick(1)
        assert e.chat_commands_trial.last.complete and e.chat_commands_trial.last.actions==()
        assert not e.chat_commands_trial.last.native_execution_verified
        for _,check,text,*_ in SPECS:
            if not p.variables[ROOT+check].get():p.widgets[ROOT+check].invoke()
            p.variables[ROOT+text].set('go')
        e.chat_commands_detailed_example();e.tick(1)
        result=e.chat_commands_trial.last
        assert e.chat_commands_detailed.get() and result.complete and len(result.actions)==8
        assert all(a.helper_execution is not None and a.helper_execution.complete for a in result.actions)
        assert [r.payload for r in e.chat_commands_trial.helpers.queue.records]==[b'\0',b'\x12\x01']
        assert 'Yerel kuyruk kaydı: 2' in e.output.get('1.0','end')
        frame=e.chat_commands_trial.frame;e.tick(1);assert e.chat_commands_trial.frame is frame
        assert len(e.chat_commands_trial.helpers.queue.records)==2
        e.chat_commands_detailed_example();raw=json.loads(example_detailed_commands_sample())
        raw['helpers']['town']['helper_returns']['thread_helper']=False
        e.chat_commands_sample.set(json.dumps(raw));e.tick(1)
        assert not e.chat_commands_trial.last.complete and 'thread_helper' in e.chat_commands_trial.last.missing
        assert len(e.chat_commands_trial.helpers.queue.records)==2
        raw['helpers']['town']['buffer_address']='already consumed'
        raw['helpers']['town']['global_samples']='already consumed'
        raw['helpers']['town']['helper_returns']['thread_helper']=True
        e.chat_commands_sample.set(json.dumps(raw));e.tick(1)
        assert e.chat_commands_trial.last.complete
        assert not e.chat_commands_trial.last.actions[-1].helper_execution.thread_callback_verified
        e.chat_commands_sample.set('{bad');e.tick(1)
        assert e.chat_commands_trial.helpers is None and e.chat_commands_trial.frame is None
    finally:
        app.values.clear();app.values.update(old_values)
        e.chat_commands_packet.set(old_hex);e.chat_commands_sample.set(old_sample);e.chat_commands_codepage.set(old_cp)
        e.chat_commands_detailed.set(old_detailed)
        e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
    print('Chat command UI passed: real flag/text widgets, exact case, eight typed helper bindings, shared2record queue, detailed Town gap/prefix resume, cached invocation and stale-result clearing; no native actions')
