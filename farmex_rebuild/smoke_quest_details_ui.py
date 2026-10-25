"""Real main-list mouse release -> details column headers and row prefixes."""
import copy,time
from dataclasses import replace
import quest_refresh,quest_details
from quest_metadata import METHODS
from smoke_quest_npc_filter_ui import seed_capture
from test_quest_refresh import TrackingNulls
from test_quest_record import string
from test_quest_details import capture as detail_capture
from test_quest_npc_filter import capture as filter_capture


def seed():
    o=seed_capture();prepared=dict(o.prepared.overrides);second=prepared[1]
    strings=dict(second.record.strings);strings['display']=string(b'Low quest',50)
    prepared[1]=replace(second,record=replace(second.record,strings=strings))
    return replace(o,prepared=TrackingNulls(prepared))


def check_quest_details_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();queue=p.flood_session.queue
    def main():p.form.set('frmMain');p.render();p.section.set('Gorevler');p.select_sections()
    def click(index):
        w=p.widgets[quest_details.MAIN_PATH]
        if index is None:w.selection_remove(*w.selection())
        else:w.selection_set(w.get_children()[index])
        w.event_generate('<ButtonRelease-1>',x=5,y=5)
    def pump(predicate):
        end=time.monotonic()+5
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'Quest details UI timeout'
    def headings():return p.source_quest_detail_headings()
    try:
        main();p.set_source_quest_refresh_provider(lambda context:seed())
        p.widgets[quest_refresh.BUTTON_PATH].invoke()
        assert p.source_quest_refresh_result.complete
        assert headings()==('','')
        old=copy.deepcopy(p.lists[quest_details.DETAILS_PATH]);click(0)
        assert p.lists[quest_details.DETAILS_PATH]==old and p.source_quest_details_state is None
        p.set_source_quest_details_provider(lambda context:detail_capture())
        collection=p.source_quest_refresh_state.collection
        before=(collection.records,collection.header,collection.revision)
        click(0)
        assert p.source_quest_refresh_result.complete and p.source_quest_refresh_result.record_index==1
        assert headings()==('Level : 5','Low quest')
        rows=p.lists[quest_details.DETAILS_PATH]
        assert [(r['caption'],r['subitems']) for r in rows]==[('NPC:',['Other']),('-',['Görev']),('',[]),('-',['Ödül'])]
        assert len(p.widgets[quest_details.DETAILS_PATH].get_children())==4
        click(1);assert headings()==('Level : 80','Quest A')
        # Filtering preserves source collection captions used by detail lookup.
        p.set_source_quest_filter_provider(lambda context:filter_capture(2))
        combo=p.widgets[quest_refresh.NPC_PATH];combo.current(2);combo.event_generate('<<ComboboxSelected>>')
        assert p.lists[quest_details.MAIN_PATH][0]['caption']=='1'
        click(0);assert headings()==('Level : 5','Low quest')
        old=(headings(),copy.deepcopy(p.lists[quest_details.DETAILS_PATH]))
        click(None)
        assert p.source_quest_refresh_result.status=='no_selection'
        assert (headings(),p.lists[quest_details.DETAILS_PATH])==old
        # Headers precede Clear, including a pause while old rows remain.
        p.lists[quest_details.DETAILS_PATH]=[dict(caption='sentinel',subitems=['old'],checked=False)]
        main();ready=[False];o=detail_capture();normal=dict(o.normal_returns);normal['display_cleanup']=False
        p.set_source_quest_details_provider(lambda context:o if ready[0] else replace(o,normal_returns=normal))
        p.set_source_quest_provider(lambda context:None);click(0)
        assert p.source_quest_refresh_result.needed==('display_cleanup',)
        assert headings()==('Level : 5','Low quest')
        assert p.lists[quest_details.DETAILS_PATH][0]['caption']=='sentinel'
        assert all(p.widgets[path].instate(['disabled']) for path in METHODS)
        assert p.widgets[quest_refresh.BUTTON_PATH].instate(['disabled'])
        ticket=p.source_quest_refresh_ticket
        p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:p.source_quest_refresh_pending is None)
        main();assert headings()==('Level : 5','Low quest')
        assert len(p.lists[quest_details.DETAILS_PATH])==4 and p.source_quest_refresh_ticket==ticket
        # Local conversion failure preserves the committed first heading and
        # retries the same frame, including across the shared timer adapter.
        ready[0]=False
        p.set_source_quest_details_provider(lambda context:o if ready[0] else replace(o,code_pages={'display':0}))
        click(0);assert p.source_quest_refresh_error is not None
        assert p.source_quest_refresh_pending is not None
        ready[0]=True;pump(lambda:p.source_quest_refresh_pending is None)
        assert p.source_quest_refresh_result.complete
        # Editing a live detail heading inside a provider cannot be overwritten
        # by its stale observation.
        def edited(context):
            p.widgets[quest_details.DETAILS_PATH].heading('1',text='external')
            return o
        p.set_source_quest_details_provider(edited);click(0)
        assert p.source_quest_refresh_error=='view_conflict' and headings()[1]=='external'
        p.set_source_quest_details_provider(lambda context:o)
        assert p.source_quest_refresh_pending is None and p.source_quest_refresh_after_id is None
        assert p.source_quest_refresh_state.collection is collection
        click(0);assert p.source_quest_refresh_result.complete
        def replaced(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));return o
        p.set_source_quest_details_provider(replaced);generation=p.source_quest_refresh_generation;click(0)
        assert p.source_quest_refresh_pending is None and p.source_quest_details_provider is None
        assert p.source_quest_refresh_after_id is None and p.source_quest_details_state is None
        assert p.advance_source_quest_refresh(generation) is None
        assert (collection.records,collection.header,collection.revision)==before
        assert p.flood_session.queue==queue
        print('Quest details UI passed: real mouse-release binding, sorted/filtered caption record index, column headings before Clear, four detail rows including blank, no-selection preservation, hidden resume, conversion retry, competing-action gates and stale heading/profile rejection; captured own data, no native/live certificate')
    finally:
        p.reset_source_quest_refresh('test_restore');p.reset_source_quest('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists);p.form.set(form);p.section.set(section);p.render()
