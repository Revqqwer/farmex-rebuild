"""Three actual field events and nested ID AL OnChange; synthetic receipts."""
import copy,time
from upgrade_parameter_frame import UpgradeParameterObservation
from upgrade_parameter_ui import SCROLL_PATH,ANVIL_PATH,WAIT_PATH
from upgrade_editor import ID_PATH
from smoke_upgrade_editor_ui import capture as editor_capture


def capture(**changes):
    fields=dict(gate_byte=1,text_init_returns={k:True for k in ('scroll','anvil','wait')},
        text_get_returns={k:True for k in ('scroll','anvil','wait')},effective_codepage=1254,
        scroll_conversion_returned=True,scroll_assignment_returned=True,
        scroll_ansi_cleanup_returned=True,scroll_unicode_cleanup_returned=True,
        scalar_returns={'anvil':True,'wait':True},number_cleanup_returns={'anvil':True,'wait':True})
    fields.update(changes);return UpgradeParameterObservation(**fields)


def check_upgrade_parameter_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get();section=p.section.get()
    editor_provider=p.source_upgrade_provider;parameter_provider=p.source_upgrade_parameter_provider
    editor_result=p.source_upgrade_result;parameter_result=p.source_upgrade_parameter_result
    state=p.source_upgrade_parameter_state;cache=dict(p.source_upgrade_parameter_text_cache);queue=p.flood_session.queue
    def main():p.form.set('frmMain');p.render();p.section.set('Upgrade');p.select_sections()
    def pump(predicate):
        end=time.monotonic()+3
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'own parameter UI timeout'
    def idle():return not p.source_upgrade_parameter_pending and not p.source_upgrade_pending
    try:
        main();p.set_source_upgrade_parameter_provider(None)
        p.variables[WAIT_PATH].set('2001')
        assert p.source_upgrade_parameter_state.interval_dword is None and not p.source_upgrade_parameter_pending
        contexts=[]
        p.set_source_upgrade_parameter_provider(lambda context:contexts.append(context) or capture())
        p.widgets[SCROLL_PATH].current(3);p.widgets[SCROLL_PATH].event_generate('<<ComboboxSelected>>')
        assert p.source_upgrade_parameter_result.complete
        assert p.source_upgrade_parameter_state.scroll_bytes==b'Blessed Upgrade Scroll'
        p.variables[ANVIL_PATH].set('4294967297')
        assert p.source_upgrade_parameter_state.anvil_dword==1
        p.variables[WAIT_PATH].set('$100000005')
        assert p.source_upgrade_parameter_state.interval_dword==5
        assert {c.trigger_path for c in contexts}=={SCROLL_PATH,ANVIL_PATH,WAIT_PATH}
        # Guard0 preserves cached object while our visible edit still changes.
        p.set_source_upgrade_parameter_provider(lambda context:capture(gate_byte=0))
        p.variables[WAIT_PATH].set('3000')
        assert p.values[WAIT_PATH]=='3000' and p.source_upgrade_parameter_state.interval_dword==5
        assert p.source_upgrade_parameter_result.status=='gate_closed'
        # Reached Anvil text freezes, later wait text stays fresh; events FIFO.
        ready=[False]
        p.set_source_upgrade_parameter_provider(lambda context:capture(text_get_returns={'scroll':True,'anvil':ready[0],'wait':True}))
        p.variables[ANVIL_PATH].set('2')
        assert p.source_upgrade_parameter_result.needed==('text_get_returns','anvil')
        p.variables[ANVIL_PATH].set('99');p.variables[WAIT_PATH].set('6000')
        assert len(p.source_upgrade_parameter_pending)==3
        p.form.set('frmBlackList');p.render();ready[0]=True
        p.advance_source_upgrade_parameters()
        assert p.source_upgrade_parameter_state.anvil_dword==2 and p.source_upgrade_parameter_state.interval_dword==6000
        pump(idle);assert p.source_upgrade_parameter_state.anvil_dword==99
        # Invalid text requires returned scalar bits; no implicit fallback.
        main();ready[0]=False
        p.set_source_upgrade_parameter_provider(lambda context:capture(scalar_qwords={'anvil':0} if ready[0] else {}))
        p.variables[ANVIL_PATH].set('invalid')
        assert p.source_upgrade_parameter_result.needed==('scalar_qwords','anvil')
        assert p.source_upgrade_parameter_state.anvil_dword==99
        ready[0]=True;pump(idle);assert p.source_upgrade_parameter_state.anvil_dword==0
        # Actual ID AL text setter waits for its nested parameter callback.
        ready[0]=False
        p.set_source_upgrade_parameter_provider(lambda context:capture(scalar_returns={'anvil':ready[0],'wait':True}))
        p.set_source_upgrade_editor_provider(lambda context:editor_capture(12,gate=0))
        p.widgets[ID_PATH].invoke()
        assert p.values[ANVIL_PATH]=='12' and p.source_upgrade_parameter_state.anvil_dword==0
        assert p.source_upgrade_result.needed==('nested_parameters',)
        parent=p.source_upgrade_pending[0][1]
        assert 'cleanup_returned' not in parent.cache
        ready[0]=True;pump(idle)
        assert p.source_upgrade_parameter_state.anvil_dword==12 and p.source_upgrade_result.complete
        p.set_source_upgrade_parameter_provider(lambda context:capture(gate_byte=0))
        p.set_source_upgrade_editor_provider(lambda context:editor_capture(13))
        p.widgets[ID_PATH].invoke();assert p.values[ANVIL_PATH]=='13'
        assert p.source_upgrade_parameter_state.anvil_dword==12 and p.source_upgrade_result.complete
        # An observed ItemIndex-1 Text survives own hide/rerender; no invented Text.
        p.set_source_upgrade_parameter_provider(lambda context:capture())
        p.widgets[SCROLL_PATH].set('Özel Scroll');p.widgets[SCROLL_PATH].event_generate('<<ComboboxSelected>>')
        assert p.values[SCROLL_PATH]==-1 and p.source_upgrade_parameter_state.scroll_bytes==b'\xd6zel Scroll'
        p.form.set('frmBlackList');p.render();main()
        assert p.widgets[SCROLL_PATH].get()=='Özel Scroll'
        # New document cannot inherit the old observed combo Text or frames.
        def replaced(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));return capture()
        p.set_source_upgrade_parameter_provider(replaced);old=p.source_upgrade_generation
        p.variables[WAIT_PATH].set('7000')
        assert p.source_upgrade_parameter_state.scroll_bytes is None and p.source_upgrade_parameter_text_cache=={}
        assert p.source_upgrade_parameter_provider is None and p.source_upgrade_parameter_result is None
        assert not p.source_upgrade_parameter_pending and p.source_upgrade_parameter_after_id is None
        assert p.advance_source_upgrade_parameters(old) is None and p.flood_session.queue==queue
        print('Upgrade parameter UI passed: three actual combo/edit events, unknown/zero gate distinction, cached ANSI and lowDWORD prefix, fresh later fields/FIFO, invalid scalar observation, nested ID AL waits before cleanup, observed minus-one Text/hidden form and profile generation; no game IO')
    finally:
        p.reset_source_upgrade_editor('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.set_source_upgrade_editor_provider(editor_provider);p.set_source_upgrade_parameter_provider(parameter_provider)
        p.source_upgrade_result=editor_result;p.source_upgrade_parameter_result=parameter_result
        p.source_upgrade_parameter_state=state;p.source_upgrade_parameter_text_cache=cache
