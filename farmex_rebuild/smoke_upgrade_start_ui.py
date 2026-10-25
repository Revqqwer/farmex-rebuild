"""Exercise actual Start/Stop buttons with explicit observations, no game IO."""
import copy
import time
from upgrade_editor import START_PATH,STOP_PATH,LIST_PATH
from upgrade_parameter_ui import WAIT_PATH,SCROLL_PATH
from smoke_upgrade_parameter_ui import capture as parameter_capture
from upgrade_start_frame import UpgradeStartFrameObservation
from upgrade_scroll import UpgradeScrollObservation,UpgradeScrollSample


def receipts(**changes):
    values=dict(gate_byte=1,start_ui_returned=True,stop_ui_returned=True,
        vector_end_returned=True,vector_begin_returned=True,vector_erase_returned=True,
        scroll_conversion_returned=True,
        scroll_lookup=UpgradeScrollObservation({14:UpgradeScrollSample(b'Scroll',b'Scroll')}),
        scroll_lookup_returned=True,scroll_cleanup_returned=True,
        caption_returns={0:True,2:True},caption_cleanup_returns={0:True,2:True},append_returns={0:True,2:True})
    values.update(changes)
    return UpgradeStartFrameObservation(**values)


def check_upgrade_start_ui(app):
    p=app.panel
    values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get()
    editor_provider=p.source_upgrade_provider;parameter_provider=p.source_upgrade_parameter_provider
    runner=p.source_upgrade_runner;parameters=p.source_upgrade_parameter_state
    cache=dict(p.source_upgrade_parameter_text_cache)
    def main():p.form.set('frmMain');p.render();p.section.set('Upgrade');p.select_sections()
    def pump(predicate):
        deadline=time.monotonic()+4
        while not predicate() and time.monotonic()<deadline:app.root.update();time.sleep(.01)
        assert predicate(),'start/stop UI timeout'
    try:
        p.reset_source_upgrade_editor('test_start')
        main();p.set_source_upgrade_editor_provider(None)
        assert p.widgets[START_PATH].instate(['disabled']) and p.widgets[STOP_PATH].instate(['disabled'])
        # No constructor fallback is accepted as observed cached source data.
        p.set_source_upgrade_editor_provider(lambda context:receipts())
        p.widgets[START_PATH].invoke()
        assert p.source_upgrade_result.needed==('cached_scroll_bytes',)
        assert p.source_upgrade_runner.state==0 and p.source_upgrade_pending
        p.set_source_upgrade_editor_provider(lambda context:receipts())
        assert not p.source_upgrade_pending and p.widgets[STOP_PATH].instate(['!disabled'])
        p.widgets[STOP_PATH].invoke()
        assert p.source_upgrade_result.status=='stopped'
        p.lists[LIST_PATH]=[dict(caption='14',subitems=['kept'],checked=True),
                                dict(caption='bad',subitems=[],checked=False),
                                dict(caption='$FFFFFFFF',subitems=[],checked=True)]
        p.render()
        p.set_source_upgrade_parameter_provider(lambda context:parameter_capture())
        p.widgets[SCROLL_PATH].set('Scroll');p.widgets[SCROLL_PATH].event_generate('<<ComboboxSelected>>')
        p.variables[WAIT_PATH].set('1500')
        assert p.source_upgrade_parameter_state.interval_dword==1500
        p.set_source_upgrade_editor_provider(lambda context:receipts())
        shared=p.source_upgrade_runner;shared.queue_stamp_qword=101;shared.armor_stamp_qword=202
        assert p.widgets[START_PATH].instate(['!disabled']) and p.widgets[STOP_PATH].instate(['disabled'])
        p.widgets[START_PATH].invoke()
        assert p.source_upgrade_result.status=='started'
        assert (shared.state,shared.queue,shared.source_scroll_index)==(1,(14,0xffffffff),0)
        assert p.widgets[START_PATH].instate(['disabled']) and p.widgets[STOP_PATH].instate(['!disabled'])
        p.render()
        assert p.widgets[STOP_PATH].instate(['!disabled'])
        p.widgets[STOP_PATH].invoke()
        assert p.source_upgrade_result.status=='stopped' and shared.state==0
        assert (shared.queue,shared.queue_stamp_qword,shared.armor_stamp_qword)==((14,0xffffffff),101,202)
        assert p.widgets[START_PATH].instate(['!disabled']) and p.widgets[STOP_PATH].instate(['disabled'])
        # Runtime gate0 does not flip the local buttons.
        p.set_source_upgrade_editor_provider(lambda context:receipts(gate_byte=0))
        p.widgets[START_PATH].invoke()
        assert p.source_upgrade_result.status=='gate_closed' and shared.state==0
        assert shared.queue==(14,0xffffffff) and p.widgets[START_PATH].instate(['!disabled'])
        # A helper gap preserves UI prefix; own FIFO defers Stop until Start completes.
        ready=[False]
        p.set_source_upgrade_editor_provider(lambda context:receipts(vector_erase_returned=ready[0]))
        p.widgets[START_PATH].invoke()
        assert shared.queue==(14,0xffffffff) and p.source_upgrade_pending
        p.widgets[STOP_PATH].invoke();assert len(p.source_upgrade_pending)==2
        p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:not p.source_upgrade_pending)
        assert p.source_upgrade_result.status=='stopped' and shared.state==0
        assert shared.queue==(14,0xffffffff)
        # Profile replacement invalidates frame and late provider return.
        main()
        def replaced(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists))
            return receipts()
        p.set_source_upgrade_editor_provider(replaced)
        generation=p.source_upgrade_generation;p.widgets[START_PATH].invoke()
        assert p.source_upgrade_runner is not shared
        assert p.source_upgrade_runner.state==0 and p.source_upgrade_runner.queue==()
        assert p.source_upgrade_provider is None and p.source_upgrade_result is None
        assert not p.source_upgrade_pending and p.source_upgrade_after_id is None
        assert p.advance_source_upgrade_editor(generation) is None
        print('Upgrade start/stop UI passed: actual buttons, cached parameters, shared runner, checked captions, preserved clocks/queue, gate0, runtime enable/rerender, helper gaps, hidden FIFO stop and stale profile rejection; no game IO')
    finally:
        p.reset_source_upgrade_editor('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists)
        p.source_upgrade_runner=runner;p.source_upgrade_parameter_state=parameters
        p.source_upgrade_parameter_text_cache=cache
        p.set_source_upgrade_editor_provider(editor_provider)
        p.set_source_upgrade_parameter_provider(parameter_provider)
        p.form.set(form);p.section.set(section);p.render()
