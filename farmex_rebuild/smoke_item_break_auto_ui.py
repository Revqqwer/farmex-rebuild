"""Actual auto checkbox/timer, captured worker children and shared manual state."""
import copy
import time
from dataclasses import replace
from item_break_auto_runtime import AutoBreakInput,ENABLE_PATH
from item_break_cycle import ItemBreakCycleObservation,ItemBreakClockObservation
from item_break_inventory import ItemBreakInventoryObservation,InventorySpaceObservation
from item_break_settings import ITEM_BREAK_FIELDS
from item_break_manual_runtime import BUTTON_PATH,ManualBreakInput
from smoke_item_break_manual_ui import captures
from direct_chat_packets import QueueAttempt


def check_item_break_auto_ui(app):
    p=app.panel;root=p.canvas.winfo_toplevel()
    saved=dict(p.values);lists=copy.deepcopy(p.lists);form=p.form.get();queue=p.flood_session.queue
    phase=dict(case='action',fixed=False,action=False,post=False,clock=False,
        notice=False,guard=False,stop=False,npc_notice=False)
    def pump_until(predicate):
        deadline=time.monotonic()+4
        while not predicate():
            if time.monotonic()>deadline:raise AssertionError('Automatic-break timer did not reach expected state')
            root.update();time.sleep(.005)
    def provider(context):
        assert context.configuration[ENABLE_PATH] is True
        if phase['case']=='blocked':return AutoBreakInput(ItemBreakCycleObservation(True,0))
        if phase['case']=='guard':
            scan=InventorySpaceObservation(True,{i:True for i in range(14,42)},{i:0x100 for i in range(14,42)})
            guard=ItemBreakInventoryObservation(True,inventory_inputs=scan,inventory_returned=True,
                stop_returned=True,full_notice_returned=phase['notice'])
            return AutoBreakInput(ItemBreakCycleObservation(True,1,1,1,second_work_byte=0),guard=guard,
                guard_parent_returned=phase['guard'])
        manual=captures(case='npc_zero' if phase['case']=='npc_zero' else 'success').observation
        known=0x553d50 in context.scalar_state
        c=ItemBreakCycleObservation(True,1,1,0,second_work_byte=1,
            clock_inputs=ItemBreakClockObservation(True,0,True,1000,None if known else 0,
                None if known else 0,1,None,phase['post'],1010),clock_returned=phase['clock'],
            stop_returned=phase['stop'],npc_notice_span_returned=phase['npc_notice'])
        request=manual.request_inputs
        request=replace(request,attempts={0:QueueAttempt(1,11,phase['fixed']),1:QueueAttempt(1,12,True)})
        return AutoBreakInput(c,request,manual.npc_inputs,npc_parent_returned=True,
            action_parent_returned=phase['action'])
    def result():return p.auto_item_break_result
    try:
        values=dict(saved);values[ENABLE_PATH]=False
        values[dict(ITEM_BREAK_FIELDS)[0xec8]]='1'
        p.bind_document(values,copy.deepcopy(lists))
        p.form.set('frmMain');p.render();p.section.set('Item Kır');p.select_sections()
        p.widgets[ENABLE_PATH].invoke()
        pump_until(lambda:result() is not None)
        assert result().plan.needed=='entry_reached'
        assert p.flood_session.queue==queue
        frame=p.auto_item_break.frame;p.render()
        assert p.auto_item_break.frame is frame
        p.widgets[ENABLE_PATH].invoke()
        assert p.auto_item_break_after_id is None and not p.auto_item_break.enabled

        p.auto_item_break_provider=provider;p.widgets[ENABLE_PATH].invoke()
        pump_until(lambda:len(p.flood_session.queue.records)==len(queue.records)+2)
        assert not result().complete
        assert 0x553d50 not in p.item_break_scalar_state
        # The manual path can run while automatic helpers are pending. Its
        # fresh NPC store must not be overwritten by replaying the old prefix.
        manual=captures().observation
        npc=replace(manual.npc_inputs,values={**manual.npc_inputs.values,'npc_id_eax':9,'selected_npc_eax':9})
        p.manual_item_break_provider=lambda context:ManualBreakInput(replace(manual,npc_inputs=npc),True)
        p.widgets[BUTTON_PATH].invoke()
        assert len(p.flood_session.queue.records)==len(queue.records)+5
        assert p.item_break_scalar_state[0x569a28]==(4,9)
        phase['fixed']=True
        pump_until(lambda:result().plan.needed=='action_parent_returned')
        assert len(p.flood_session.queue.records)==len(queue.records)+6
        assert p.item_break_scalar_state[0x569a28]==(4,9)
        assert 0x553d50 not in p.item_break_scalar_state
        phase['action']=True
        pump_until(lambda:result().plan.caller.caller.caller.clock is not None and
            result().plan.caller.caller.caller.clock.needed=='second_tick_returned')
        assert 0x553d50 not in p.item_break_scalar_state
        phase['post']=True
        pump_until(lambda:result().plan.needed=='clock_returned')
        assert p.item_break_scalar_state[0x553d50]==(4,1010)
        before=p.flood_session.queue
        phase['clock']=True
        pump_until(lambda:result().status=='waiting')
        assert p.flood_session.queue==before
        p.widgets[ENABLE_PATH].invoke()
        assert p.item_break_scalar_state[0x553d50]==(4,1010)
        phase['case']='blocked';p.widgets[ENABLE_PATH].invoke()
        pump_until(lambda:result() is not None and result().status=='outer_gate_zero')
        assert p.flood_session.queue==before

        phase['case']='guard'
        pump_until(lambda:result().plan.caller.caller.inventory_guard is not None and
            result().plan.caller.caller.inventory_guard.needed=='full_notice_returned')
        assert p.flood_session.queue==before
        phase['notice']=True
        pump_until(lambda:result().plan.needed=='guard_parent_returned')
        assert p.auto_item_break.enabled and p.values[ENABLE_PATH] is True
        phase['guard']=True
        pump_until(lambda:result().status=='second_work_gate_zero')
        assert p.flood_session.queue==before and p.auto_item_break.enabled

        phase['case']='npc_zero'
        pump_until(lambda:result().plan.needed=='stop_returned')
        phase['stop']=True
        pump_until(lambda:result().plan.needed=='npc_notice_span_returned')
        phase['npc_notice']=True
        pump_until(lambda:result().status=='npc_zero_stop_notice_returned')
        assert p.flood_session.queue==before
        # Changing profile inside the provider invalidates the old result.
        def replace_profile(context):
            values=dict(p.values);values[ENABLE_PATH]=False
            p.bind_document(values,copy.deepcopy(p.lists))
            return AutoBreakInput(ItemBreakCycleObservation(True,0))
        generation=p.auto_item_break.generation
        p.auto_item_break_provider=replace_profile
        pump_until(lambda:not p.auto_item_break.enabled)
        assert p.auto_item_break_provider is None and p.auto_item_break_result is None
        assert p.auto_item_break_after_id is None and not p.item_break_scalar_state
        p.widgets[ENABLE_PATH].invoke();current=p.auto_item_break_after_id
        assert current is not None
        assert p.advance_auto_item_break(generation) is None
        assert p.auto_item_break_after_id==current
        p.widgets[ENABLE_PATH].invoke()
        assert p.auto_item_break_after_id is None
        assert p.flood_session.queue==before
        print('Item-break automatic UI passed: actual checkbox/after callbacks, missing captures, full NPC/request chain, independent action/post-clock/parent returns, shared manual queue/NPC state, committed cooldown, outer gate, full-inventory guard/fresh work byte, NPC stop/notice and profile/stale callback invalidation; no game IO')
    finally:
        p.flood_session.queue=queue
        app.values.clear();app.values.update(saved)
        app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.bind_document(app.values,app.lists)
