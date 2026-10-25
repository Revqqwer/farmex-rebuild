"""Real Upgrade refresh button with synthetic guarded/name/normal captures."""
import copy,time
from dataclasses import replace
from upgrade_refresh import UpgradeRefreshObservation,UpgradeRefreshSlot,GuardedCapture
from upgrade_editor import REFRESH_PATH,SELECT_PATH,LIST_PATH,UpgradeEditorObservation
from source_coin import GuardedDwordSample,GuardedByteSample
from item_name import ItemNameObservation
from npc_unicode import NpcUnicodeObservation


def dword(at,value):return GuardedCapture(GuardedDwordSample(at,1,value),True)


def capture(*,name=b'Item',kind=5,name_returned=True,concat_returned=True,inventory=0x4000,final=True):
    slots={i:UpgradeRefreshSlot(0x20,dword(0x4000+0x20+i*4,0)) for i in range(14,42)}
    for slot,data,grade in ((14,name,9),(41,b'\x81',2)):
        record=0x5000+slot*0x100;lookup=0x8000;metadata=0x9000
        slots[slot]=UpgradeRefreshSlot(0x20,dword(0x4000+0x20+slot*4,record),dword(record+0x60,lookup),
            dword(record+0x64,metadata),dword(lookup,1000),dword(metadata,3),True,
            ItemNameObservation(metadata_category=5,storage_dword=15,pointer_dword=0,bad_read_result=0,captured=data+b'\0'*(255-len(data))),
            name_returned,NpcUnicodeObservation(False,1254,None,True,True,True),True,True,True,
            dword(metadata,grade),GuardedCapture(GuardedByteSample(metadata+0x44,1,kind),True),True,concat_returned,True)
    return UpgradeRefreshObservation(1,True,0x100,dword(0x100,0x1000),8,dword(0x1008,inventory),slots,final)


def check_upgrade_refresh_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get();section=p.section.get()
    provider=p.source_upgrade_provider;result=p.source_upgrade_result;queue=p.flood_session.queue
    def main():p.form.set('frmMain');p.render();p.section.set('Upgrade');p.select_sections()
    def seed():p.lists[LIST_PATH]=[dict(caption='old',subitems=['old'],checked=True)];p.render()
    def pump(predicate):
        end=time.monotonic()+3
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'own Upgrade refresh UI timeout'
    try:
        main();seed();p.set_source_upgrade_editor_provider(None)
        assert p.widgets[REFRESH_PATH].instate(['disabled'])
        p.set_source_upgrade_editor_provider(lambda context:UpgradeRefreshObservation(gate_byte=0,root={}))
        p.widgets[REFRESH_PATH].invoke();assert p.source_upgrade_result.status=='gate_closed' and p.lists[LIST_PATH][0]['caption']=='old'
        p.set_source_upgrade_editor_provider(lambda context:UpgradeRefreshObservation(gate_byte=1))
        p.widgets[REFRESH_PATH].invoke();assert p.lists[LIST_PATH]==[]
        assert p.source_upgrade_result.needed==('entry','initial_text_returned')
        # Full captured inventory -> actual list; relative caption and fresh grade.
        p.set_source_upgrade_editor_provider(lambda context:capture() if context.method=='refresh' else UpgradeEditorObservation(gate_byte=1))
        p.widgets[REFRESH_PATH].invoke();pump(lambda:not p.source_upgrade_pending)
        assert p.lists[LIST_PATH]==[dict(caption='0',subitems=['Item (+9)'],checked=False),dict(caption='27',subitems=['\x81 (+2)'],checked=False)]
        p.render();assert p.widgets[LIST_PATH].item('0','values')[0]=='☐ 0'
        p.widgets[SELECT_PATH].invoke();assert all(row['checked'] for row in p.lists[LIST_PATH])
        # Null inventory still clears; final string cleanup remains independent.
        ready=[False]
        p.set_source_upgrade_editor_provider(lambda context:capture(inventory=0,final=ready[0]))
        p.widgets[REFRESH_PATH].invoke();assert p.lists[LIST_PATH]==[]
        assert p.source_upgrade_result.needed==('entry','final_cleanup_returned')
        p.form.set('frmBlackList');p.render();ready[0]=True;pump(lambda:not p.source_upgrade_pending)
        assert p.source_upgrade_result.complete and p.lists[LIST_PATH]==[]
        # Name/Unicode must finish before a later type filter could reject.
        main();ready[0]=False
        p.set_source_upgrade_editor_provider(lambda context:capture(kind=1,name_returned=ready[0]))
        p.widgets[REFRESH_PATH].invoke();active=p.source_upgrade_pending[0][1]
        assert p.source_upgrade_result.needed==(14,'name_returned')
        assert (14,'variant_fresh') not in active.reads and (14,'kind') not in active.reads
        ready[0]=True;pump(lambda:not p.source_upgrade_pending);assert p.lists[LIST_PATH]==[]
        # Pending concat preserves caption and freezes completed name/grade.
        ready[0]=False
        p.set_source_upgrade_editor_provider(lambda context:capture(name=b'Changed' if ready[0] else b'Item',concat_returned=ready[0]))
        p.widgets[REFRESH_PATH].invoke()
        assert p.lists[LIST_PATH]==[dict(caption='0',subitems=[],checked=False)]
        p.form.set('frmBlackList');p.render();ready[0]=True;pump(lambda:not p.source_upgrade_pending)
        assert p.lists[LIST_PATH][0]['subitems']==['Item (+9)']
        # An invalidated token is never replaced by a row with the same index.
        main();ready[0]=False;p.set_source_upgrade_editor_provider(lambda context:capture(concat_returned=ready[0]))
        p.widgets[REFRESH_PATH].invoke()
        p.lists[LIST_PATH]=[dict(caption='replacement',subitems=['x'],checked=False)];p.render()
        ready[0]=True;pump(lambda:not p.source_upgrade_pending)
        assert not p.source_upgrade_result.complete and p.lists[LIST_PATH][0]['caption']=='replacement'
        # Reentrant select-all waits until refresh completed its FIFO work.
        entered=[False]
        def reentrant(context):
            if context.method=='refresh':
                if not entered[0]:entered[0]=True;p.widgets[SELECT_PATH].invoke()
                return capture()
            return UpgradeEditorObservation(gate_byte=1)
        p.set_source_upgrade_editor_provider(reentrant);p.widgets[REFRESH_PATH].invoke();pump(lambda:not p.source_upgrade_pending)
        assert len(p.lists[LIST_PATH])==2 and all(row['checked'] for row in p.lists[LIST_PATH])
        def replaced(context):
            new=copy.deepcopy(p.lists);new[LIST_PATH]=[dict(caption='new profile',subitems=[],checked=False)]
            p.bind_document(dict(p.values),new);return capture()
        p.set_source_upgrade_editor_provider(replaced);old=p.source_upgrade_generation;p.widgets[REFRESH_PATH].invoke()
        assert p.source_upgrade_provider is None and p.source_upgrade_result is None and not p.source_upgrade_pending
        assert p.advance_source_upgrade_editor(old) is None and p.source_upgrade_after_id is None
        assert p.lists[LIST_PATH][0]['caption']=='new profile' and p.flood_session.queue==queue
        print('Upgrade refresh UI passed: actual conditional button, clear before root, null inventory/final cleanup, full28-slot scan, supplied-pointer name/explicit Unicode, fresh grade/type filter, relative captions, select-all handoff, delayed concat/hidden form, deleted token, FIFO/reentrant/profile; no game IO')
    finally:
        p.reset_source_upgrade_editor('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.set_source_upgrade_editor_provider(provider);p.source_upgrade_result=result
