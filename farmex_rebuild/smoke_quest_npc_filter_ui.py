"""Actual NPC ComboboxSelected binding against captured owned Quest records."""
import copy,time
from dataclasses import replace
import quest_refresh
import panel_ui
from quest_metadata import METHODS
from smoke_quest_refresh_ui import full_capture
from test_quest_record import string
from test_quest_refresh import TrackingNulls
from test_quest_npc_filter import capture as filter_capture


def seed_capture():
    o=full_capture();prepared=dict(o.prepared.overrides)
    second=prepared[1];strings=dict(second.record.strings);strings['npc']=string(b'Other')
    prepared[1]=replace(second,record=replace(second.record,strings=strings))
    return replace(o,prepared=TrackingNulls(prepared),emission=replace(o.emission,npc_contains={0:False,1:False}))


def check_quest_npc_filter_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();queue=p.flood_session.queue
    showerror=panel_ui.messagebox.showerror
    def unexpected_dialog(*args,**kwargs):raise AssertionError('Unexpected modal dialog: '+str(args))
    def main():p.form.set('frmMain');p.render();p.section.set('Gorevler');p.select_sections()
    def choose(index):
        w=p.widgets[quest_refresh.NPC_PATH];w.current(index);w.event_generate('<<ComboboxSelected>>')
    def pump(predicate):
        end=time.monotonic()+5
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'Quest NPC filter UI timeout'
    try:
        panel_ui.messagebox.showerror=unexpected_dialog
        main();p.set_source_quest_refresh_provider(lambda context:seed_capture())
        p.widgets[quest_refresh.BUTTON_PATH].invoke()
        assert p.source_quest_refresh_result.complete
        assert tuple(p.widgets[quest_refresh.NPC_PATH]['values'])==('HEPSI','NPC','Other')
        collection=p.source_quest_refresh_state.collection
        before=(collection.records,collection.header,collection.revision)
        p.set_source_quest_filter_provider(lambda context:filter_capture(2))
        choose(1)
        assert p.source_quest_refresh_result.complete and p.source_quest_refresh_operation=='npc_filter'
        assert [r['caption'] for r in p.lists[quest_refresh.LIST_PATH]]==['0']
        choose(2);assert [r['caption'] for r in p.lists[quest_refresh.LIST_PATH]]==['1']
        choose(0);assert [r['caption'] for r in p.lists[quest_refresh.LIST_PATH]]==['1','0']
        assert (collection.records,collection.header,collection.revision)==before
        assert p.values[quest_refresh.NPC_PATH]==values[quest_refresh.NPC_PATH]
        p.profiles.validate({'version':1,'values':p.values})
        assert p.flood_session.queue==queue
        # A final cleanup gap retains the filtered row, disables competing
        # actions, and continues while its form is hidden.
        ready=[False];o=filter_capture(2);normal=dict(o.normal_returns);normal['selected_ansi_cleanup']=False
        p.set_source_quest_filter_provider(lambda context:o if ready[0] else replace(o,normal_returns=normal))
        p.set_source_quest_provider(lambda context:None);choose(1)
        assert p.source_quest_refresh_result.needed==('selected_ansi_cleanup',)
        assert p.widgets[quest_refresh.NPC_PATH].instate(['disabled'])
        assert p.widgets[quest_refresh.BUTTON_PATH].instate(['disabled'])
        assert all(p.widgets[path].instate(['disabled']) for path in METHODS)
        revision=p.source_quest_refresh_state.rows.revision
        p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:p.source_quest_refresh_pending is None)
        assert p.source_quest_refresh_state.rows.revision==revision
        main();assert p.widgets[quest_refresh.NPC_PATH].current()==1
        assert [r['caption'] for r in p.lists[quest_refresh.LIST_PATH]]==['0']
        # Clear is visible before an unresolved ANSI conversion, never a
        # fallback to all rows or an empty completed result.
        ready[0]=False
        p.set_source_quest_filter_provider(lambda context:o if ready[0] else replace(o,code_page=None))
        choose(2)
        assert not p.source_quest_refresh_result.complete
        assert p.source_quest_refresh_result.needed==('code_page_or_selected_ansi',)
        assert p.lists[quest_refresh.LIST_PATH]==[] and len(collection.records)==2
        ready[0]=True;pump(lambda:p.source_quest_refresh_pending is None)
        assert [r['caption'] for r in p.lists[quest_refresh.LIST_PATH]]==['1']
        # Replacing the filter provider cancels only that pending continuation,
        # preserving data needed for a later selection.
        p.set_source_quest_filter_provider(lambda context:None);choose(1)
        generation=p.source_quest_refresh_generation
        p.set_source_quest_filter_provider(lambda context:o)
        assert p.source_quest_refresh_pending is None and p.source_quest_refresh_after_id is None
        assert p.advance_source_quest_refresh(generation) is None
        assert p.source_quest_refresh_state.collection is collection
        choose(1);assert p.source_quest_refresh_result.complete
        def changed(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));return o
        p.set_source_quest_filter_provider(changed);choose(0)
        assert p.source_quest_refresh_pending is None and p.source_quest_filter_provider is None
        assert p.source_quest_refresh_after_id is None and p.source_quest_refresh_state is None
        assert p.flood_session.queue==queue
        print('Quest NPC filter UI passed: actual ComboboxSelected, NPC/Other/HEPSI choices, preserved record collection/index captions, numeric sort, clear-before-conversion gap, hidden tail resume, mutual exclusion, filter-provider cancellation and stale profile rejection; owned byte equality and captured data, no native/live certificate')
    finally:
        panel_ui.messagebox.showerror=showerror
        p.reset_source_quest_refresh('test_restore');p.reset_source_quest('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists);p.form.set(form);p.section.set(section);p.render()
