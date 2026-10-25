"""Own actual NPC button/dialog/timers; synthetic source captures only."""
import copy,time
from dataclasses import replace
import route_npc_click as npc
from route_npc_source import NpcSourceInput
from target_id_frames import TargetIdObservation
from route_npc_name import RouteNpcNameObservation
from source_coin import GuardedDwordSample
from npc_actor_lookup import NpcLookupObservation,LookupContextSample
from npc_unicode import NpcUnicodeObservation
from route_panel_runtime import OPEN_PATH
from panel_ui import SOURCE_ROUTE_LIST,SOURCE_ROUTE_CLEAR


def capture(name=b'Potion',third=3001,**changes):
    c=lambda value:npc.NpcValueCapture(value,True)
    fields=dict(target_gate=c(10),target_lookup=c(11),actor=c(0x1000),
                name_bytes=c(name),target_classify=c(third))
    fields.update(changes);return npc.NpcClickInput(**fields)


def lower_capture(name=b'DC Sundries',third=3001,copy_returned=True):
    def target(slot,root,value):
        return TargetIdObservation(slot,GuardedDwordSample(slot,1,root),True,4,
            GuardedDwordSample(root+4,1,value),True,True)
    name_capture=RouteNpcNameObservation(8,GuardedDwordSample(0x1008,1,5),True,
        True,True,True,True,4,None,None,True,True,name+b'\0'*(255-len(name)),
        copy_returned,True,True,True)
    return NpcSourceInput(target(0x100,0x1000,77),target(0x200,0x2000,88),
        NpcLookupObservation(0x8000,LookupContextSample(0x8000,0x9000),0x700000,
            0xfeed,True,0x1000,True,True),name_capture,target(0x300,0x3000,third))


def check_source_route_npc_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get();section=p.section.get()
    geometry=dict(p.route_panel.geometry);visible=p.route_panel.visible;last=p.route_panel.last;update=p.route_panel_update
    provider=p.source_npc_provider;result=p.source_npc_result;dialog=p.source_npc_dialog;notice=p.source_npc_notice
    queue=p.flood_session.queue
    def pump(predicate):
        end=time.monotonic()+3
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'own NPC UI timeout'
    def main():
        p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections();p.widgets[OPEN_PATH].invoke()
    def empty():p.widgets[SOURCE_ROUTE_CLEAR].invoke();assert not p.lists[SOURCE_ROUTE_LIST]
    try:
        main();empty();p.set_source_npc_provider(None)
        assert p.widgets[npc.BUTTON_PATH].instate(['disabled'])
        p.widgets[npc.BUTTON_PATH].invoke();assert not p.lists[SOURCE_ROUTE_LIST]
        ready=[False];seen=[]
        def provider_wait(context):
            seen.append(context)
            return capture() if ready[0] else None
        p.set_source_npc_provider(provider_wait);p.widgets[npc.BUTTON_PATH].invoke()
        assert not p.source_npc_result.done and not p.lists[SOURCE_ROUTE_LIST]
        p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:not p.source_npc_pending)
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='NPC',subitems=['Potion','-'],checked=False)]
        main();assert tuple(p.widgets[SOURCE_ROUTE_LIST].item('0','values'))==('NPC','Potion','-')
        # Real Tk InputBox equivalent, completed through its actual Entry/OK.
        empty();p.source_npc_dialog=p.ask_source_npc_dialog;completed=[]
        p.set_source_npc_provider(lambda context:capture(b'Royal National Potion',dialog_text=npc.NpcValueCapture('4',True)))
        def descendants(widget):
            nodes=[]
            for child in widget.winfo_children():nodes.append(child);nodes.extend(descendants(child))
            return nodes
        dialog_deadline=time.monotonic()+3
        def fill_dialog():
            widgets=descendants(app.root)
            entries=[w for w in widgets if w.winfo_class()=='Entry']
            buttons=[w for w in widgets if w.winfo_class()=='Button' and w.cget('text')=='OK']
            if not entries or not buttons:
                if time.monotonic()<dialog_deadline:app.root.after(10,fill_dialog)
                else:
                    for widget in widgets:
                        if widget.winfo_class()=='Toplevel':widget.destroy()
                return
            entries[-1].delete(0,'end');entries[-1].insert(0,'3');completed.append(True);buttons[-1].invoke()
        app.root.after(30,fill_dialog);p.widgets[npc.BUTTON_PATH].invoke()
        assert completed and not p.source_npc_pending
        # Provider's4 is ignored: our real dialog's3 is the committed value.
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='NPC',subitems=['Royal National Enchanter','3'],checked=False)]
        for answer in (None,'01',' 1','5'):
            empty();p.source_npc_dialog=lambda a=answer:a
            p.widgets[npc.BUTTON_PATH].invoke()
            assert p.source_npc_result.status=='dialog_rejected' and not p.lists[SOURCE_ROUTE_LIST]
        # First zero warns; lookup-zero and unmatched-name do not warn.
        notices=[];p.source_npc_notice=lambda:notices.append(True)
        for sample,status in [(capture(target_gate=npc.NpcValueCapture(0,True)),'no_selection'),
                              (capture(actor=npc.NpcValueCapture(0,True)),'lookup_empty'),
                              (capture(b'unknown'),'name_unmatched')]:
            p.set_source_npc_provider(lambda context,s=sample:s);p.widgets[npc.BUTTON_PATH].invoke()
            assert p.source_npc_result.status==status and not p.lists[SOURCE_ROUTE_LIST]
        assert len(notices)==1
        # Late trade text holds one row, even with rerender and deletion.
        p.set_source_npc_provider(lambda context:capture(third=0));p.widgets[npc.BUTTON_PATH].invoke()
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='User Trade',subitems=[],checked=False)]
        empty();p.lists[SOURCE_ROUTE_LIST]=[dict(caption='replacement',subitems=['a','b'],checked=False)];p.render()
        pump(lambda:not p.source_npc_pending)
        assert not p.source_npc_result.complete and p.lists[SOURCE_ROUTE_LIST][0]['caption']=='replacement'
        # Reentrant click uses a separate FIFO invocation, with no game queue.
        empty();trigger=[False]
        def reentrant(context):
            if not trigger[0]:trigger[0]=True;p.widgets[npc.BUTTON_PATH].invoke()
            return capture(third=0,trade_text=npc.NpcValueCapture(str(context.invocation),True))
        p.set_source_npc_provider(reentrant);p.widgets[npc.BUTTON_PATH].invoke();pump(lambda:not p.source_npc_pending)
        assert len(p.lists[SOURCE_ROUTE_LIST])==2
        assert int(p.lists[SOURCE_ROUTE_LIST][1]['subitems'][0])==int(p.lists[SOURCE_ROUTE_LIST][0]['subitems'][0])+1
        # Actual button now also consumes lower root/guard/byte observations.
        empty();ready_lower=[False];lower_contexts=[]
        def lower_provider(context):
            lower_contexts.append(context)
            return lower_capture(copy_returned=ready_lower[0])
        p.set_source_npc_provider(lower_provider);p.widgets[npc.BUTTON_PATH].invoke()
        active=p.source_npc_pending[0][1]
        assert active.lookup.final.call.eax_dword==0 and active.lookup.final.call.ecx_dword==0x9000
        assert active.lookup.final.call.edx_dword==0xfeed and active.lookup.final.call.pushes==(1,88)
        assert active.name.observation.copied_bytes.startswith(b'DC Sundries')
        assert active.targets['target_classify'].observation.root_address_dword is None
        assert p.source_npc_result.needed==('name_bytes','copy_returned') and not p.lists[SOURCE_ROUTE_LIST]
        p.form.set('frmBlackList');p.render();ready_lower[0]=True
        pump(lambda:not p.source_npc_pending)
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='NPC',subitems=['DC Sundries','-'],checked=False)]
        assert any(context.needed==('name_bytes','copy_returned') for context in lower_contexts)
        main();empty();p.source_npc_dialog=lambda:'2'
        p.set_source_npc_provider(lambda context:lower_capture(b'Royal National'))
        p.widgets[npc.BUTTON_PATH].invoke()
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='NPC',subitems=['Royal National Enchanter','2'],checked=False)]
        # Lower Unicode producer stays after row/caption and before subitems.
        empty();unicode_ready=[False]
        def unicode_provider(context):
            return replace(lower_capture(b'\x81',third=0),trade_text=NpcUnicodeObservation(
                False,1254,None,unicode_ready[0],True,True))
        p.set_source_npc_provider(unicode_provider);p.widgets[npc.BUTTON_PATH].invoke()
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='User Trade',subitems=[],checked=False)]
        assert p.source_npc_result.needed==('trade_text',('rtl_returned',))
        active=p.source_npc_pending[0][1]
        assert active.unicode.ansi_bytes==b'\x81' and active.unicode.text=='\x81'
        p.form.set('frmBlackList');p.render();unicode_ready[0]=True
        pump(lambda:not p.source_npc_pending)
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='User Trade',subitems=['\x81','-'],checked=False)]
        main()
        # Nested modal loop/profile change cannot commit its stale answer.
        empty();p.set_source_npc_provider(lambda context:capture(b'Royal National'))
        old=p.source_npc_generation
        def changed_dialog():
            new=copy.deepcopy(p.lists);new[SOURCE_ROUTE_LIST]=[dict(caption='new profile',subitems=['x','y'],checked=False)]
            p.bind_document(dict(p.values),new);return '2'
        p.source_npc_dialog=changed_dialog;p.widgets[npc.BUTTON_PATH].invoke()
        assert p.source_npc_result is None and p.source_npc_provider is None and not p.source_npc_pending
        assert p.widgets[npc.BUTTON_PATH].instate(['disabled']) and p.lists[SOURCE_ROUTE_LIST][0]['caption']=='new profile'
        before=copy.deepcopy(p.lists);assert p.advance_source_npc(old) is None and p.lists==before
        assert p.source_npc_after_id is None and p.flood_session.queue==queue
        print('Source NPC-click UI passed: actual conditional button, real Tk dialog Entry/OK, provider cannot override dialog, rejection/cancel, distinct zero outcomes, delayed capture/hidden form, deleted row, FIFO/reentrant click and profile/modal generation; lower root/guard/name-byte producer and dialog bridge; captured indirect lookup context EAX0/ECX/EDX/pushes; late Unicode child flags0/explicit CP/independent return preserves row prefix; synthetic captures only, no game IO')
    finally:
        p.reset_source_npcs('test_restore');p.source_npc_dialog=dialog;p.source_npc_notice=notice
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last;p.route_panel_update=update
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.set_source_npc_provider(provider);p.source_npc_result=result
