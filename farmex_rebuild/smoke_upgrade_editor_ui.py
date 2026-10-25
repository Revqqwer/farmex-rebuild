"""Actual two Upgrade buttons with captured gate/target/normal observations."""
import copy,time
from upgrade_editor import UpgradeEditorObservation,SELECT_PATH,ID_PATH,ANVIL_PATH,LIST_PATH
from target_id_frames import TargetIdObservation
from source_coin import GuardedDwordSample


def capture(value=42,*,gate=1,getter=True,formatted=True,cleaned=True):
    return UpgradeEditorObservation(gate,TargetIdObservation(0x100,
        GuardedDwordSample(0x100,1,0x1000),True,4,
        GuardedDwordSample(0x1004,1,value),True,getter),formatted,cleaned)


def check_upgrade_editor_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get();section=p.section.get()
    provider=p.source_upgrade_provider;result=p.source_upgrade_result;queue=p.flood_session.queue
    def main():p.form.set('frmMain');p.render();p.section.set('Upgrade');p.select_sections()
    def rows(count=2):
        p.lists[LIST_PATH]=[dict(caption='invalid caption',subitems=['kept'],checked=False) for _ in range(count)]
        p.render()
    def pump(predicate):
        end=time.monotonic()+3
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'own Upgrade editor UI timeout'
    try:
        main();rows();p.set_source_upgrade_editor_provider(None)
        assert p.widgets[SELECT_PATH].instate(['disabled']) and p.widgets[ID_PATH].instate(['disabled'])
        p.widgets[SELECT_PATH].invoke();assert not any(r['checked'] for r in p.lists[LIST_PATH])
        p.set_source_upgrade_editor_provider(lambda context:capture(gate=0))
        p.widgets[SELECT_PATH].invoke();assert p.source_upgrade_result.status=='gate_closed'
        assert not any(r['checked'] for r in p.lists[LIST_PATH])
        p.set_source_upgrade_editor_provider(lambda context:capture())
        p.widgets[SELECT_PATH].invoke();assert p.source_upgrade_result.complete
        assert all(r['checked'] for r in p.lists[LIST_PATH])
        assert all(r['caption']=='invalid caption' and r['subitems']==['kept'] for r in p.lists[LIST_PATH])
        p.widgets[SELECT_PATH].invoke();assert all(r['checked'] for r in p.lists[LIST_PATH])
        p.render();assert p.widgets[LIST_PATH].item('0','values')[0]=='☑ invalid caption'
        # ID AL has no561f55 gate and must preserve full DWORD/signed formatting.
        p.set_source_upgrade_editor_provider(lambda context:capture(0xffffffff,gate=0))
        p.widgets[ID_PATH].invoke();assert p.source_upgrade_result.complete
        assert p.values[ANVIL_PATH]=='-1' and p.variables[ANVIL_PATH].get()=='-1'
        p.set_source_upgrade_editor_provider(lambda context:capture(0,gate={}))
        p.widgets[ID_PATH].invoke();assert p.source_upgrade_result.status=='no_target' and p.values[ANVIL_PATH]=='-1'
        # Getter normal receipt freezes the earlier DWORD; format/cleanup separate.
        ready=[False];formatted=[False];cleaned=[False]
        def delayed(context):return capture(7 if not ready[0] else 8,getter=ready[0],formatted=formatted[0],cleaned=cleaned[0])
        p.set_source_upgrade_editor_provider(delayed);p.widgets[ID_PATH].invoke()
        assert p.source_upgrade_result.needed==('target',('getter_returned',))
        ready[0]=True;pump(lambda:p.source_upgrade_result.needed==('format_returned',))
        assert p.values[ANVIL_PATH]=='-1'
        formatted[0]=True;pump(lambda:p.source_upgrade_result.needed==('cleanup_returned',))
        assert p.values[ANVIL_PATH]=='7'
        p.variables[ANVIL_PATH].set('999');p.form.set('frmBlackList');p.render();cleaned[0]=True
        pump(lambda:not p.source_upgrade_pending);assert p.values[ANVIL_PATH]=='999'
        # Large own lists yield at the chunk boundary; profile invalidates suffix.
        main();rows(80);p.set_source_upgrade_editor_provider(lambda context:capture())
        p.widgets[SELECT_PATH].invoke();assert p.source_upgrade_pending
        checked=sum(row['checked'] for row in p.lists[LIST_PATH]);assert 0<checked<80
        old=p.source_upgrade_generation;new=copy.deepcopy(p.lists)
        new[LIST_PATH]=[dict(caption='new profile',subitems=[],checked=False)]
        p.bind_document(dict(p.values),new)
        assert p.source_upgrade_provider is None and not p.source_upgrade_pending and p.source_upgrade_after_id is None
        assert p.advance_source_upgrade_editor(old) is None and not p.lists[LIST_PATH][0]['checked']
        # Reentrant click waits in FIFO and uses its own target frame.
        main();rows();entered=[False]
        def reentrant(context):
            if not entered[0]:entered[0]=True;p.widgets[ID_PATH].invoke()
            return capture(42)
        p.set_source_upgrade_editor_provider(reentrant);p.widgets[SELECT_PATH].invoke()
        pump(lambda:not p.source_upgrade_pending)
        assert all(row['checked'] for row in p.lists[LIST_PATH]) and p.values[ANVIL_PATH]=='42'
        # A provider changing profile cannot commit its stale capture.
        def replaced(context):
            new_values=dict(p.values);new_values[ANVIL_PATH]='200'
            p.bind_document(new_values,copy.deepcopy(p.lists));return capture(17)
        p.set_source_upgrade_editor_provider(replaced);p.widgets[ID_PATH].invoke()
        assert p.values[ANVIL_PATH]=='200' and p.source_upgrade_result is None
        assert not p.source_upgrade_pending and p.source_upgrade_after_id is None
        assert p.flood_session.queue==queue
        print('Upgrade editor UI passed: two actual conditional buttons, raw gate select-only, checked rows without caption parsing/toggle, full target signed32 and unguarded ID AL, getter/format/cleanup gaps, hidden form, chunk/profile cancellation, FIFO/reentrant click and stale provider; no game IO')
    finally:
        p.reset_source_upgrade_editor('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.set_source_upgrade_editor_provider(provider);p.source_upgrade_result=result
