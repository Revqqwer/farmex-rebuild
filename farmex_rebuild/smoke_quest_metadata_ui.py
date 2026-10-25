"""Three real Quest metadata buttons; read traces only, no invented packet."""
import copy,time
from quest_metadata import (METHODS,LIST_PATH,QuestMetadataObservation,QuestMetadataDatabase,QuestMetadataRecord)


def capture(**changes):
    ready={i:True for i in range(-1,100)}
    values=dict(selection_returned=True,setup_returns=ready,caption_returns=ready,
        conversion_returns=ready,cleanup_returns=ready,read_returns=ready,epilogue_returns=ready,
        database=QuestMetadataDatabase(0x1000,(QuestMetadataRecord(111,0x2000,444),QuestMetadataRecord(222,0x3000,555))))
    values.update(changes);return QuestMetadataObservation(**values)


def check_quest_metadata_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();provider=p.source_quest_provider
    result=p.source_quest_result;queue=p.flood_session.queue
    paths={method:path for path,method in METHODS.items()}
    def main():p.form.set('frmMain');p.render();p.section.set('Gorevler');p.select_sections()
    def rows():
        p.lists[LIST_PATH]=[dict(caption='1',subitems=['5','Quest B'],checked=False),
                           dict(caption='0',subitems=['4','Quest A'],checked=False)]
        p.render()
    def pump(predicate):
        end=time.monotonic()+4
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'Quest metadata UI timeout'
    try:
        main();rows();p.set_source_quest_provider(None)
        assert all(p.widgets[path].instate(['disabled']) for path in METHODS)
        p.set_source_quest_provider(lambda context:capture())
        p.widgets[LIST_PATH].selection_set('0');p.widgets[paths['cancel']].invoke()
        assert p.source_quest_result.complete and p.source_quest_result.processed_rows==1
        assert p.source_quest_result.reads[-1][1:4]==(1,0x301c,555)
        p.widgets[paths['take_all']].invoke()
        assert p.source_quest_result.complete and p.source_quest_result.processed_rows==2
        assert [r[4] for r in p.source_quest_result.reads]==['direct_entry0','direct_entry0']
        p.widgets[paths['cancel_all']].invoke()
        assert p.source_quest_result.complete and len(p.source_quest_result.reads)==4
        assert p.flood_session.queue==queue
        p.widgets[LIST_PATH].selection_remove(*p.widgets[LIST_PATH].selection())
        p.widgets[paths['cancel']].invoke()
        assert p.source_quest_result.status=='no_selection' and p.source_quest_result.reads==()
        # A child normal-return gap keeps its read prefix; later count is fresh.
        ready=[False]
        p.set_source_quest_provider(lambda context:capture(epilogue_returns={0:ready[0]}))
        p.widgets[paths['take_all']].invoke()
        assert p.source_quest_result.needed==('epilogue_returns',0)
        assert len(p.source_quest_result.reads)==1
        p.lists[LIST_PATH].pop();p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:not p.source_quest_pending)
        assert p.source_quest_result.complete and p.source_quest_result.processed_rows==1
        main();rows()
        # A provider changing profile cannot apply its stale database observation.
        def replaced(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));return capture()
        p.set_source_quest_provider(replaced);generation=p.source_quest_generation
        p.widgets[paths['take_all']].invoke()
        assert p.source_quest_provider is None and p.source_quest_result is None
        assert not p.source_quest_pending and p.source_quest_after_id is None
        assert p.advance_source_quest(generation) is None and p.flood_session.queue==queue
        print('Quest metadata UI passed: three actual buttons, selected caption record index distinct from row, separate entry0/guarded1c read traces, fresh bulk count/hidden form, no-selection and stale profile cancellation; no quest packet or take/cancel ACK invented')
    finally:
        p.reset_source_quest('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists);p.set_source_quest_provider(provider);p.source_quest_result=result
        p.form.set(form);p.section.set(section);p.render()
