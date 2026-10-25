"""Actual Button5 and Tk polling over explicit source captures; no game IO."""
import copy
import time
from dataclasses import replace
from action_queue import enqueue
from direct_chat_packets import QueueAttempt
from event_packets import EventPacketObservation
from item_break_manual import ItemBreakManualObservation
from item_break_npc import ItemBreakNpcObservation
from item_break_requests import ItemBreakRequestObservation,FIRST_TEMPLATE,SECOND_TEMPLATE
from item_break_manual_runtime import BUTTON_PATH,ManualBreakInput
from item_break_settings import ITEM_BREAK_FIELDS


def captures(*,case='success',target_returned=True,handler_returned=True):
    npc=ItemBreakNpcObservation(True,dict(mode_dword=0,npc_id_eax=0 if case=='npc_zero' else 5,
        npc_object_eax=0x2000,first_offset=0x20,second_offset=0x24,
        first_coordinate_float_bits=0,second_coordinate_float_bits=0,distance_float_bits=0,
        zero_compare_ax=0x4000,ten_compare_ax=0x100,selected_npc_eax=5),
        dict.fromkeys(('empty_name_setup','moira_assignment','lookup_argument_setup','npc_lookup',
            'npc_object','first_coordinate','second_coordinate','distance','selected_npc',
            'success_cleanup','failure_cleanup'),True))
    target=EventPacketObservation(normal_returns=dict.fromkeys(('frame_setup','template_copy','target_copy','return'),True),
        attempt=QueueAttempt(1,10,target_returned))
    request=ItemBreakRequestObservation(True,{'first_selected_eax':5,'second_selected_eax':7},
        dict.fromkeys(('first_selected','second_selected','target_parent'),True),target,
        {0:QueueAttempt(1,11,True),1:QueueAttempt(1,12,True)})
    manual=ItemBreakManualObservation(True,
        {'fresh_mode_dword':1 if case=='other_mode' else 0,'gem_lookup_eax':0 if case=='gem_zero' else 1},
        dict.fromkeys(('npc_parent','gem_text_created','gem_lookup','gem_text_cleanup','gem_notice','npc_notice','request_parent'),True),
        npc,request)
    return ManualBreakInput(manual,handler_returned)


def check_item_break_manual_ui(app):
    p=app.panel;root=p.canvas.winfo_toplevel()
    values=dict(p.values);lists=copy.deepcopy(p.lists);form=p.form.get()
    queue=p.flood_session.queue
    phase={'target':False,'handler':False,'case':'success'}
    def pump_until(predicate):
        deadline=time.monotonic()+4
        while not predicate():
            if time.monotonic()>deadline:raise AssertionError('Manual-break timer did not reach expected state')
            root.update();time.sleep(.005)
    def provider(context):
        return captures(case=phase['case'],target_returned=phase['target'],handler_returned=phase['handler'])
    try:
        p.form.set('frmMain');p.render();p.section.set('Item Kır');p.select_sections()
        assert p.widgets[BUTTON_PATH].instate(['!disabled'])
        auto=dict(ITEM_BREAK_FIELDS)[0xec0]
        if p.values[auto]:p.widgets[auto].invoke()
        assert p.values[auto] is False
        # No provider must not fabricate helper entry, a nearby NPC or a gem.
        p.widgets[BUTTON_PATH].invoke()
        assert p.manual_item_break.pending and p.manual_item_break_after_id is not None
        assert not p.manual_item_break_result.complete
        assert p.flood_session.queue==queue
        frame=p.manual_item_break.frame;p.render()
        assert p.manual_item_break.frame is frame
        p.bind_document(dict(p.values),copy.deepcopy(p.lists))
        assert not p.manual_item_break.pending and p.manual_item_break_after_id is None

        p.manual_item_break_provider=provider
        p.widgets[BUTTON_PATH].invoke()
        assert len(p.flood_session.queue.records)==len(queue.records)+1
        assert p.flood_session.queue.records[-1].payload==bytes.fromhex('200107000000ffffffff')
        assert not p.manual_item_break_result.complete
        p.flood_session.queue=enqueue(p.flood_session.queue,b'other feature',13,0,1,13).state
        phase['target']=True
        pump_until(lambda:p.manual_item_break_result.plan.needed=='handler_returned')
        records=p.flood_session.queue.records
        assert [r.payload for r in records[-3:]]==[b'other feature',FIRST_TEMPLATE,SECOND_TEMPLATE]
        assert [r.delay_dword for r in records[-2:]]==[200,250]
        assert p.manual_item_break_result.scalar_state[0x569a28]==(4,5)
        before=p.flood_session.queue
        p.advance_manual_item_break();p.advance_manual_item_break()
        assert p.flood_session.queue==before
        phase['handler']=True
        pump_until(lambda:not p.manual_item_break.pending)
        assert p.manual_item_break_result.complete
        assert p.manual_item_break_after_id is None
        assert p.flood_session.queue==before
        assert p.values[auto] is False
        assert not p.manual_item_break_result.delivery_verified

        # Every actual click starts a fresh source frame; notices/nonzero mode
        # skip the request without consulting auto-enable or cooldown fields.
        for case,status in (('npc_zero','npc_zero_notice_returned'),
                            ('gem_zero','gem_zero_notice_returned'),
                            ('other_mode','nonzero_mode_skips_manual_action')):
            phase['case']=case;before=p.flood_session.queue
            p.widgets[BUTTON_PATH].invoke()
            assert p.manual_item_break_result.complete
            assert p.manual_item_break_result.status==status
            assert p.flood_session.queue==before

        # Reentrant click queues a second invocation instead of recursing.
        reentered=[]
        def reentrant_click(context):
            if not reentered:
                reentered.append(context.ticket);p.start_manual_item_break()
            return captures()
        p.manual_item_break_provider=reentrant_click
        before=len(p.flood_session.queue.records)
        p.widgets[BUTTON_PATH].invoke()
        pump_until(lambda:not p.manual_item_break.pending)
        assert len(p.flood_session.queue.records)==before+6

        # Profile replacement inside the provider rejects its old result.
        def replace_profile(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists))
            return captures()
        p.manual_item_break_provider=replace_profile
        before=p.flood_session.queue;generation=p.manual_item_break.generation
        p.widgets[BUTTON_PATH].invoke()
        assert p.manual_item_break_provider is None
        assert p.manual_item_break_result is None and p.flood_session.queue==before
        assert p.manual_item_break_after_id is None
        p.widgets[BUTTON_PATH].invoke()
        current=p.manual_item_break_after_id
        assert current is not None
        assert p.advance_manual_item_break(generation) is None
        assert p.manual_item_break_after_id==current
        p.bind_document(dict(p.values),copy.deepcopy(p.lists))
        assert not p.manual_item_break.pending and p.manual_item_break_after_id is None
        print('Item-break manual UI passed: actual Button5, no implicit provider, rerender, auto-disabled manual action, partial target enqueue, shared writer,200/250ms requests, independent handler return, NPC/gem/mode exits, reentrant FIFO and profile/stale callback invalidation; no game IO')
    finally:
        p.flood_session.queue=queue
        app.values.clear();app.values.update(values)
        app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.bind_document(app.values,app.lists)
