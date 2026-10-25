"""Real Take/Give buttons -> captured frame -> common owned queue."""
import copy,time
from dataclasses import replace
import quest_refresh
from quest_action_worker import TAKE_PATH,GIVE_PATH,QuestActionContext
from smoke_quest_details_ui import seed
from test_quest_action import capture
from test_quest_lookup import capture as lookup_capture
from test_quest_name_compare import capture as name_compare_capture,Sample as NameCompareSample
from test_quest_read_string import capture as read_string_capture


def check_quest_action_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();queue=p.flood_session.queue
    def main():
        p.form.set('frmMain');p.render();p.section.set('Gorevler');p.select_sections()
    def select():
        table=p.widgets[quest_refresh.LIST_PATH];table.selection_set(table.get_children()[0])
    def observation():
        o=capture();v=dict(o.values)
        record=p.source_quest_refresh_state.collection.records[1]
        v.update(npc_cpp_bytes=record.npc_bytes.split(b'\0',1)[0],
                 script_cpp_bytes=record.script_bytes.split(b'\0',1)[0],
                 distance_lower_reject=False,distance_upper_reject=False)
        return replace(o,values=v)
    def pump(predicate):
        end=time.monotonic()+5
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'Quest action timeout'
    try:
        main();assert p.widgets[TAKE_PATH].instate(['disabled'])
        p.set_source_quest_refresh_provider(lambda context:seed())
        p.widgets[quest_refresh.BUTTON_PATH].invoke()
        assert p.source_quest_refresh_result.complete
        calls=[]
        def provider(context):
            assert isinstance(context,QuestActionContext)
            calls.append(context);return observation()
        p.set_source_quest_action_provider(provider);select()
        before=len(p.flood_session.queue.records)
        p.widgets[TAKE_PATH].invoke()
        assert p.source_quest_refresh_result.complete
        assert p.source_quest_refresh_result.action.record_index==1
        assert len(p.flood_session.queue.records)==before+3 and calls[-1].method=='take'
        p.widgets[GIVE_PATH].invoke()
        assert p.source_quest_refresh_result.complete
        assert len(p.flood_session.queue.records)==before+5 and calls[-1].method=='give'
        assert not p.source_quest_refresh_result.delivery_verified
        # A committed first append is visible while its outer return is missing.
        ready=[False];o=observation();normal=dict(o.normal_returns);normal[('enqueue',0)]=False
        p.set_source_quest_action_provider(lambda context:o if ready[0] else replace(o,normal_returns=normal))
        p.widgets[TAKE_PATH].invoke()
        assert not p.source_quest_refresh_result.complete
        assert len(p.flood_session.queue.records)==before+6
        assert all(p.widgets[path].instate(['disabled']) for path in (TAKE_PATH,GIVE_PATH,quest_refresh.BUTTON_PATH))
        p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:p.source_quest_refresh_pending is None)
        assert len(p.flood_session.queue.records)==before+8
        main();select()
        # Provider replacement cancels the old frame without retracting prefix.
        p.set_source_quest_action_provider(lambda context:replace(o,normal_returns=normal))
        p.widgets[TAKE_PATH].invoke();worker=p.source_quest_refresh_pending[0]
        generation=p.source_quest_refresh_generation
        count=len(p.flood_session.queue.records)
        p.set_source_quest_action_provider(provider)
        assert worker.cancelled and p.source_quest_refresh_pending is None
        assert p.advance_source_quest_refresh(generation) is None
        assert len(p.flood_session.queue.records)==count
        # Negative selection preserves the common queue; Give's AL!=3 exit
        # completes its local branch without manufacturing queued requests.
        table=p.widgets[quest_refresh.LIST_PATH];table.selection_remove(*table.selection())
        p.widgets[TAKE_PATH].invoke()
        assert p.source_quest_refresh_result.status=='no_selection'
        assert len(p.flood_session.queue.records)==count
        select();v=dict(o.values);v['status_eax']=2
        p.set_source_quest_action_provider(lambda context:replace(o,values=v))
        p.widgets[GIVE_PATH].invoke()
        assert p.source_quest_refresh_result.status=='give_status_not3'
        assert len(p.flood_session.queue.records)==count
        # Editing rows inside the provider invalidates its returned observation.
        rows=copy.deepcopy(p.lists[quest_refresh.LIST_PATH])
        def edited(context):
            p.lists[quest_refresh.LIST_PATH][0]['caption']='999';return o
        p.set_source_quest_action_provider(edited);p.widgets[TAKE_PATH].invoke()
        assert p.source_quest_refresh_error=='view_conflict'
        assert len(p.flood_session.queue.records)==count
        p.set_source_quest_action_provider(provider)
        p.lists[quest_refresh.LIST_PATH]=rows;main();select()
        # An observation returned after profile replacement cannot be consumed.
        def stale(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));return o
        p.set_source_quest_action_provider(stale);p.widgets[GIVE_PATH].invoke()
        assert p.source_quest_action_provider is None and p.source_quest_refresh_pending is None
        assert p.source_quest_refresh_after_id is None
        assert len(p.flood_session.queue.records)==count
        # The actual buttons accept inner lookup observations through the same
        # provider. Argument cleanup must finish before common queue additions.
        main();p.set_source_quest_refresh_provider(lambda context:seed())
        p.widgets[quest_refresh.BUTTON_PATH].invoke();select()
        o=replace(observation(),lookup=lookup_capture([dict(record=0)]*5))
        normal=dict(o.lookup.normal_returns);del normal[(-1,'argument_cleanup')]
        ready=[False];contexts=[]
        def nested(context):
            contexts.append(context)
            return o if ready[0] else replace(o,lookup=replace(o.lookup,normal_returns=normal))
        p.set_source_quest_action_provider(nested);p.widgets[TAKE_PATH].invoke()
        assert not p.source_quest_refresh_result.complete
        assert p.source_quest_refresh_result.action.lookup_plan.eax is None
        assert len(p.flood_session.queue.records)==count
        # A timer retry exposes nested phase/index/ordinal in provider context.
        p.advance_source_quest_refresh()
        assert contexts[-1].needed[0]=='lookup'
        ready[0]=True;pump(lambda:p.source_quest_refresh_pending is None)
        assert len(p.flood_session.queue.records)==count+3
        assert p.flood_session.queue.records[count].payload==b'\x64\x07\xff\xff\0\0'
        p.widgets[GIVE_PATH].invoke()
        assert p.source_quest_refresh_result.complete
        assert len(p.flood_session.queue.records)==count+5
        assert p.flood_session.queue.records[count+3].payload==b'\x64\x07\xff\xff\0\0'
        # A non-null lookup row consumes nested ANSI comparison before filters.
        start=len(p.flood_session.queue.records);ready=[False]
        cmp=name_compare_capture(NameCompareSample(False,True),NameCompareSample(False))
        cmp_normal=dict(cmp.normal_returns);del cmp_normal['equal_return']
        inner=lookup_capture([{},dict(record=0),dict(record=0),dict(record=0),dict(record=0)])
        def name_provider(context):
            sample=cmp if ready[0] else replace(cmp,normal_returns=cmp_normal)
            return replace(observation(),lookup=replace(inner,name_compares={0:sample}))
        p.set_source_quest_action_provider(name_provider);p.widgets[TAKE_PATH].invoke()
        assert not p.source_quest_refresh_result.complete
        plan=p.source_quest_refresh_result.action.lookup_plan
        assert plan.name_compare_plans[0][1].eax is None and plan.mode_comparisons==()
        assert len(p.flood_session.queue.records)==start
        ready[0]=True;pump(lambda:p.source_quest_refresh_pending is None)
        plan=p.source_quest_refresh_result.action.lookup_plan
        assert plan.name_compare_plans[0][1].eax==1 and len(plan.mode_comparisons)==1
        assert len(p.flood_session.queue.records)==start+3
        p.widgets[GIVE_PATH].invoke()
        assert p.source_quest_refresh_result.complete and len(p.flood_session.queue.records)==start+5
        print('Quest ANSI comparison composition UI passed: actual Take/Give -> lookup -> separate LStrCmp flag calls -> outer equality return -> filters and common queue; gap/resume and no Unicode fallback, captured local observations only')
        start=len(p.flood_session.queue.records);ready=[False]
        raw=b'Low quest'+b'\0'*6
        read_sample=read_string_capture(raw,constructor=b'Low quest')
        read_normal=dict(read_sample.normal_returns);del read_normal['cleanup']
        compare=name_compare_capture(NameCompareSample(use_owned_bytes=True),NameCompareSample(use_owned_bytes=True))
        def read_provider(context):
            r=read_sample if ready[0] else replace(read_sample,normal_returns=read_normal)
            lower=replace(inner,name_reads={0:r},name_compares={0:compare},use_read_name_operands=True)
            return replace(observation(),lookup=lower)
        p.set_source_quest_action_provider(read_provider);p.widgets[TAKE_PATH].invoke()
        plan=p.source_quest_refresh_result.action.lookup_plan
        assert not p.source_quest_refresh_result.complete
        assert plan.name_read_plans[0][1].destination_ansi==b'Low quest'
        assert plan.owned_name_values==() and len(p.flood_session.queue.records)==start
        ready[0]=True;pump(lambda:p.source_quest_refresh_pending is None)
        plan=p.source_quest_refresh_result.action.lookup_plan
        assert plan.owned_name_values==((0,b'Low quest'),) and plan.name_compare_plans[0][1].eax==1
        assert len(p.flood_session.queue.records)==start+3
        p.widgets[GIVE_PATH].invoke()
        assert p.source_quest_refresh_result.complete and len(p.flood_session.queue.records)==start+5
        print('Quest read-string composition UI passed: actual Take/Give -> lookup -> guard/copy/constructor/assignment prefix -> pending cleanup -> separate outer return -> owned ANSI comparison -> shared queue; captured source spans, no process reads or game send')
        print('Quest lookup composition UI passed: actual Take/Give provider, five signed-range rows, inner cleanup gap before queue, nested context, resume, FFFF lowWORD and common queue; captured local spans only')
        print('Quest action UI passed: real Take/Give, sorted caption index, shared queue prefixes, hidden timer resume, competing gates, provider cancellation and stale profile rejection; captured local observations only')
    finally:
        p.reset_source_quest_refresh('test_restore');p.reset_source_quest('test_restore')
        p.flood_session.queue=queue
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists);p.form.set(form);p.section.set(section);p.render()


if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:
        app=Application(root);check_quest_action_ui(app)
    finally:
        if 'app' in globals():app.connection_page.close()
        root.destroy()
