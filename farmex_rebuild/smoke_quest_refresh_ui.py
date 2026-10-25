"""Actual Refresh button with explicit captured fixtures; hidden own UI only."""
import copy,time
from dataclasses import replace
import quest_refresh
from quest_record import QuestPreparedObservation
from quest_collection import QuestVectorHeader as Header
from test_quest_candidate import capture as candidate_capture
from test_quest_record import capture as record_capture
from test_quest_collection import capture as append_capture
from test_quest_list_emit import capture as emission_capture
from test_quest_refresh import capture as refresh_capture,TrackingNulls
from quest_metadata import METHODS


def full_capture():
    first=record_capture();second=record_capture();v=dict(second.values);v['fresh_minimum']=5
    prepared=TrackingNulls({0:QuestPreparedObservation(candidate_capture(),first),
                           1:QuestPreparedObservation(candidate_capture(),replace(second,values=v))})
    o=refresh_capture(prepared=prepared,appends={0:append_capture(),1:append_capture(
        size_header=Header(0x1000,0x101c),inplace_end_dword=0x1038,post_header=Header(0x1000,0x1038,0x1038))},
        emission=replace(emission_capture(2),npc_contains={0:False,1:True}))
    normal=dict(o.normal_returns);normal.update({('candidate_cleanup',i):True for i in (0,1)})
    return replace(o,normal_returns=normal)


def check_quest_refresh_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();queue=p.flood_session.queue
    def main():p.form.set('frmMain');p.render();p.section.set('Gorevler');p.select_sections()
    def pump(predicate):
        end=time.monotonic()+5
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'Quest Refresh UI timeout'
    try:
        main();p.set_source_quest_refresh_provider(None)
        assert p.widgets[quest_refresh.BUTTON_PATH].instate(['disabled'])
        p.set_source_quest_refresh_provider(lambda context:full_capture())
        p.widgets[quest_refresh.BUTTON_PATH].invoke()
        assert p.source_quest_refresh_result.complete
        assert [r['caption'] for r in p.lists[quest_refresh.LIST_PATH]]==['1','0']
        table=p.widgets[quest_refresh.LIST_PATH]
        assert [table.item(i,'values')[1] for i in table.get_children()]==['5','80']
        assert tuple(p.widgets[quest_refresh.NPC_PATH]['values'])==('HEPSI','NPC')
        assert p.source_quest_refresh_state.npc_selected==0 and p.source_quest_refresh_after_id is None
        assert p.values[quest_refresh.NPC_PATH]==values[quest_refresh.NPC_PATH]
        p.profiles.validate({'version':1,'values':p.values})
        assert p.flood_session.queue==queue
        # Partial row/append data is painted and survives hide/render/timer.
        ready=[False];o=full_capture();normal=dict(o.normal_returns);normal['tail_display']=False
        def paused(context):return o if ready[0] else replace(o,normal_returns=normal)
        p.set_source_quest_refresh_provider(paused)
        p.set_source_quest_provider(lambda context:None)
        p.widgets[quest_refresh.BUTTON_PATH].invoke()
        assert p.source_quest_refresh_result.needed==('tail_display',)
        assert p.source_quest_refresh_pending is not None
        assert all(p.widgets[path].instate(['disabled']) for path in METHODS)
        before=copy.deepcopy(p.lists[quest_refresh.LIST_PATH]);revision=p.source_quest_refresh_state.rows.revision
        p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:p.source_quest_refresh_pending is None)
        assert p.lists[quest_refresh.LIST_PATH]==before
        assert p.source_quest_refresh_state.rows.revision==revision
        main();assert tuple(p.widgets[quest_refresh.NPC_PATH]['values'])==('HEPSI','NPC')
        # Source observations cannot overwrite a provider's same-profile edit.
        def edited(context):
            p.lists[quest_refresh.LIST_PATH]=[dict(caption='external',subitems=[],checked=False)]
            return full_capture()
        p.set_source_quest_refresh_provider(edited);p.widgets[quest_refresh.BUTTON_PATH].invoke()
        assert p.source_quest_refresh_error=='view_conflict'
        assert p.lists[quest_refresh.LIST_PATH][0]['caption']=='external'
        p.cancel_source_quest_refresh_timer()
        # Profile replacement invalidates the callback result and timer ticket.
        def changed(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));return full_capture()
        p.set_source_quest_refresh_provider(changed);generation=p.source_quest_refresh_generation
        p.widgets[quest_refresh.BUTTON_PATH].invoke()
        assert p.source_quest_refresh_pending is None and p.source_quest_refresh_provider is None
        assert p.source_quest_refresh_after_id is None and p.source_quest_refresh_result is None
        assert p.advance_source_quest_refresh(generation) is None
        assert p.flood_session.queue==queue
        print('Quest Refresh UI passed: actual button, two accepted candidates among30001, numeric level order, collection captions, NPC options/selection, pending tail and hidden-form resume, no duplicate mutation, metadata exclusion, stale view/profile protection; captured own data only, no native/live verification')
    finally:
        p.reset_source_quest_refresh('test_restore');p.reset_source_quest('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists)
        p.form.set(form);p.section.set(section);p.render()
