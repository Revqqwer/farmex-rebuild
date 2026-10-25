"""Own model chain from real profile schema through phase2 handoff and one slot."""
import json,unittest
from dataclasses import replace
from pathlib import Path
from profiles import Profiles
from merchant_configuration import compile_sell_merchant_panel,sell_merchant_settings_from_panel
from merchant_sell_preparation import SellPreparationRow,SellPreparationObservation
from merchant_sell_cost import SellCostObservation
from merchant_sell_setup import SellSetupObservation
from merchant_sell_session import SellSessionState,SellSessionObservation,SellSessionFrame
from merchant_sell_selection import SellSelectionObservation,plan_sell_selection
from merchant_sell_tail import SellSlotState,SellSlotObservation,SellSlotFrame
from merchant_reply import MerchantReplyState,MerchantReplyObservation,plan_merchant_reply,merchant_snapshot_from_reply
from merchant_reply import sell_setup_delay_from_reply
from operation_engine import MerchantRunner
from action_queue import QueueState,QueueSample
from merchant_sell_open import SellOpeningState,SellOpeningObservation,SellOpeningFrame
from test_merchant_sell_open import own_open_operands
from merchant_sell_open_wait import SellOpenWaitState,SellOpenWaitObservation,SellOpenWaitFrame
from merchant_sell_monitor import SellMonitorObservation
from merchant_sell_prepare_wait import SellPrepareWaitObservation
from merchant_sell_setup_delay import SellSetupDelayObservation
from merchant_sell_close import SellCloseState,SellCloseFrame,SellCloseObservation
from merchant_sell_close_wait import SellCloseWaitObservation
from test_merchant_sell_close import own_close_samples
from source_coin import SourceCoinObservation,GuardedDwordSample
from merchant_callback import MerchantCallbackObservation,tick_merchant_callback

def run_sell_model_flow():
    catalog=json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8'))
    profile=Profiles(catalog);compiled=compile_sell_merchant_panel(profile.defaults)
    runner=MerchantRunner(sell_merchant_settings_from_panel(compiled));runner.start()
    reply=MerchantReplyState()
    def snapshot(now,**fields):return merchant_snapshot_from_reply(reply,now,**fields)
    def drive(value):
        # Explicit own eligible-gate fixture for each invocation; no live global sample.
        d=tick_merchant_callback(runner,MerchantCallbackObservation(1,0,0,None,1,1,(1,)),value)
        assert d.status=='callback_modeled' and d.callback.selected_kind=='sell'
        return d.operation
    close_frame=SellCloseFrame(SellCloseState(),QueueState())
    close_prefix=close_frame.step(own_close_samples())
    assert drive(snapshot(1,currently_open=True,sell_close_execution=close_prefix)).status=='needs_adapter'
    closed=close_frame.step(SellCloseObservation(close_tick_dword=0,queue_sample=QueueSample(0,1),enqueue_returned=True))
    assert drive(snapshot(1,currently_open=True,sell_close_execution=closed)).status=='close_attempt'
    reply=replace(reply,close_pending_byte=closed.state.pending_byte)
    assert drive(snapshot(1,sell_close_wait_inputs=SellCloseWaitObservation(
        reply.close_pending_byte,closed.state.close_stamp_qword,1))).status=='waiting'
    close_reply=plan_merchant_reply(reply,bytes.fromhex('680201000000'),
        MerchantReplyObservation(scan_active_byte=0,local_actor_dword=1,tick_dword=1))
    assert close_reply.complete and close_reply.state.setup_stamp_qword==1
    reply=close_reply.state
    drive(snapshot(2,sell_close_wait_inputs=SellCloseWaitObservation(reply.close_pending_byte)))
    assert runner.phase==2
    # These text/ANSI/normal-return values are explicit own fixtures, not game observations.
    row=SellPreparationRow(item_text='77',quantity_text='2',price_text='50',price_ansi=b'50',
        item_cleanup_returned=True,quantity_cleanup_returned=True,ansi_returned=True,
        price_ansi_cleanup_returned=True,price_unicode_cleanup_returned=True)
    preparation=SellPreparationObservation(clear_returned=True,counts=(1,1),rows={0:row},sizes={0:0},
        capacities={0:12},append_returns={0:True},local_decimal=True)
    setup=SellSetupObservation(preparation_inputs=preparation,
        cost_inputs=SellCostObservation(0,True,(77,),(2,)),coin_inputs=SourceCoinObservation(
            ((0x553e7c,0x1000),(0x553ff0,0x20)),(GuardedDwordSample(0x1000,1,0x2000),GuardedDwordSample(0x2020,1,1000))))
    delay=sell_setup_delay_from_reply(reply,runner.settings.extra_wait_seconds,91001,ready_span_returns=(True,))
    assert delay.started_stamp_qword==1
    p=drive(snapshot(91000,sell_setup_inputs=setup,sell_setup_delay_inputs=delay))
    assert p.status=='needs_adapter' and runner.last_sell_setup_plan is None
    delay=replace(delay,ready_span_returns=(True,True))
    p=drive(snapshot(91000,sell_setup_inputs=setup,sell_setup_delay_inputs=delay))
    assert p.status=='setup_gate_armed' and runner.phase==2
    prepared=runner.last_sell_setup_plan.preparation_plan.state.records
    assert runner.last_sell_setup_plan.cost_plan.cost_qword==100
    assert runner.last_sell_setup_plan.coin_plan.complete and runner.last_sell_setup_plan.coin_plan.coins_dword==1000
    old_slot=SellSlotState(used_bytes=runner.last_sell_setup_plan.cost_plan.prospective_used_bytes,
        accumulated_qword=999,net_qword=888,prepared_slots_dword=7)
    session=SellSessionFrame(SellSessionState(ready_byte=1,list_index_dword=5,inventory_slot_dword=30,slot=old_slot),closed.queue)
    waiting=session.step()
    assert drive(snapshot(91001,sell_setup_inputs=setup,sell_session_execution=waiting,
        sell_setup_delay_inputs=replace(delay,tick_dword=91002))).status=='needs_adapter'
    started=session.step(SellSessionObservation(91002,QueueSample(91003,1),True))
    result=drive(snapshot(91002,sell_setup_inputs=setup,sell_session_execution=started,
        sell_setup_delay_inputs=replace(delay,tick_dword=91002)))
    assert runner.phase==3 and result.status=='prepare_attempt'
    assert started.state.slot.accumulated_qword==0 and started.state.slot.used_bytes==(0,)*28
    queue=started.queue;slot=started.state.slot
    reply=replace(reply,session_ready_byte=started.state.ready_byte,item_pending_byte=slot.item_pending_byte)
    assert reply.session_ready_byte==0 and len(queue.records)==2
    assert drive(snapshot(91003,sell_prepare_wait_inputs=SellPrepareWaitObservation(
        ready_byte=0,session_stamp_qword=started.state.session_stamp_qword,tick_dword=91003))).status=='waiting'
    # Explicit supplied dispatcher bytes, never authenticated server acknowledgement.
    ready_reply=plan_merchant_reply(reply,bytes.fromhex('680101'),MerchantReplyObservation(scan_active_byte=0))
    assert ready_reply.complete and not ready_reply.independently_verified;reply=ready_reply.state
    selection_inputs=SellSelectionObservation(rows=prepared,stable_rows=True,item_results=(77,),
        used_bytes=slot.used_bytes,quantity_results=(2,),inventory_slot_dword=runner.inventory_slot,
        list_index_dword=runner.entry_index)
    selected=plan_sell_selection(False,selection_inputs)
    tail=SellSlotFrame(selected,slot,queue)
    partial=tail.step(SellSlotObservation(item_tick_dword=91004,disk_crt_replay=True))
    assert not partial.complete and 'control WORD' in partial.missing
    result=drive(snapshot(91004,prepared_slot_count=0,sell_selection_inputs=selection_inputs,sell_slot_execution=partial))
    assert result.status=='needs_adapter' and runner.entry_index==0
    finished=tail.step(SellSlotObservation(x87_control_word=0x37f,x87_clean_context=True,copy_returns=(True,)*5,
        queue_sample=QueueSample(91005,1),enqueue_returned=True))
    assert finished.complete and finished.state.net_qword==97
    result=drive(snapshot(91005,prepared_slot_count=0,sell_selection_inputs=selection_inputs,sell_slot_execution=finished))
    assert result.status=='slot_attempt' and runner.entry_index==1
    queue=finished.queue;slot=finished.state;reply=replace(reply,item_pending_byte=slot.item_pending_byte)
    assert len(queue.records)==3 and reply.item_pending_byte==1
    assert drive(snapshot(91006,sell_prepare_wait_inputs=SellPrepareWaitObservation(
        ready_byte=1,item_pending_byte=1,item_stamp_qword=slot.item_stamp_qword,tick_dword=91006))).status=='waiting'
    clear_reply=plan_merchant_reply(reply,bytes.fromhex('6803'),MerchantReplyObservation(scan_active_byte=0))
    assert clear_reply.complete;reply=clear_reply.state
    after=SellSelectionObservation(rows=prepared,stable_rows=True,list_index_dword=1,
        inventory_slot_dword=runner.inventory_slot)
    drive(snapshot(91007,prepared_slot_count=1,sell_selection_inputs=after,
        sell_prepare_wait_inputs=SellPrepareWaitObservation(ready_byte=1,item_pending_byte=0)))
    assert runner.phase==4 and len(queue.records)==3
    assert queue.records[0].payload==bytes.fromhex('6802')
    assert queue.records[1].payload==bytes.fromhex('6801')
    assert queue.records[2].payload==bytes.fromhex('68034d0000000200320000000000')
    opening=SellOpeningFrame(SellOpeningState(prepared_slots_dword=slot.prepared_slots_dword))
    partial=opening.step(SellOpeningObservation(opening_tick_dword=91008))
    assert drive(snapshot(91008,prepared_slot_count=1,sell_opening_execution=partial)).status=='needs_adapter'
    partial=opening.step(SellOpeningObservation(native_inputs=own_open_operands(),helper_returned=False))
    assert partial.native_plan.complete and not partial.complete
    assert drive(snapshot(91009,prepared_slot_count=1,sell_opening_execution=partial)).status=='needs_adapter'
    opened=opening.step(SellOpeningObservation(helper_returned=True))
    drive(snapshot(91010,prepared_slot_count=1,sell_opening_execution=opened))
    assert runner.phase==5 and runner.phase_ms==91008 and len(queue.records)==3
    reply=replace(reply,opening_pending_byte=opened.state.pending_byte)
    assert drive(snapshot(91011,prepared_slot_count=1)).status=='waiting'
    opened_reply=plan_merchant_reply(reply,bytes.fromhex('68070000000001000000'),
        MerchantReplyObservation(scan_active_byte=0,local_actor_dword=1,tick_dword=91012))
    assert opened_reply.complete and opened_reply.state.opening_pending_byte==0
    assert opened_reply.state.established_stamp_qword==91012
    reply=opened_reply.state
    waiting=SellOpenWaitFrame(SellOpenWaitState(pending_byte=reply.opening_pending_byte,
        pending_stamp_qword=opened.state.pending_stamp_qword,setup_gate_byte=int(runner.setup_seen),status_byte_90=1))
    partial=waiting.step(SellOpenWaitObservation(clear_span_returns=(True,True)))
    assert drive(snapshot(91012,prepared_slot_count=1,sell_open_wait_execution=partial)).status=='needs_adapter'
    assert runner.phase==5
    completed=waiting.step(SellOpenWaitObservation(clear_span_returns=(True,)*4,
        accumulated_qword=slot.accumulated_qword,net_qword=slot.net_qword))
    drive(snapshot(91013,prepared_slot_count=1,sell_open_wait_execution=completed))
    assert runner.phase==6 and not runner.setup_seen and len(queue.records)==3
    assert completed.display_plans==((3,100),(5,97))
    # Fresh source-clock inputs; the old outer monotonic clock does not drive this gate.
    monitor=SellMonitorObservation(reopen_byte=1,minutes_dword=1,
        established_stamp_qword=reply.established_stamp_qword,tick_dword=reply.established_stamp_qword+999)
    assert drive(snapshot(92011,sell_monitor_inputs=monitor)).status=='needs_adapter'
    assert runner.phase==6 and runner.last_sell_monitor_plan.display_seconds_signed==60
    observed=replace(monitor,display_span_returned=True)
    assert drive(snapshot(92012,sell_monitor_inputs=observed)).status=='monitoring'
    due=replace(monitor,tick_dword=reply.established_stamp_qword+60000)
    assert drive(snapshot(151012,sell_monitor_inputs=due)).status=='restart_due'
    assert runner.phase==0 and runner.restarting and len(queue.records)==3
    # UI-span receipts are own fixtures, not executed VCL or authenticated server replies.
    return dict(verification_status='passed',scope='Own typed model flow through supplied UI-span returns and phase6 source-clock restart decision; native/UI execution unverified',
        prepared_records=1,derived_cost_qword=100,derived_net_qword=97,local_queue_records=3,
        payloads=[q.payload.hex() for q in queue.records],ready_and_item_pending_require_supplied_replies=True,
        clock_and_enqueue_gaps_hold_caller=True,ftol_source=finished.ftol_source,
        opening_native_target_plan=hex(opened.native_plan.native_call.target_dword),
        supplied_open_reply_clears_pending=True,native_call_executed=False,
        native_ui_spans_executed=False,phase6_reached_with_explicit_span_samples=True,
        phase6_countdown_requires_span_return=True,phase6_timer_restarts_at_60000=True,
        phase3_session_and_item_wait_use_raw_source_clock=True,
        phase2_setup_requires_two_explicit_ui_span_returns=True,
        phase2_start_stamp_from_supplied_matching_close_reply=True,
        phase0_pending_from_bound_close_frame=True,phase1_wait_uses_raw_source_clock=True,
        setup_coins_from_explicit_guarded_reader_samples=True,
        outer_callback_gate_supplied_per_invocation=True,
        source_opening_executed=False,original_crt_dll_executed=False,live_compatibility_verified=False)

class SellModelFlowTests(unittest.TestCase):
    def test_complete_local_chain(self):self.assertEqual(run_sell_model_flow()['verification_status'],'passed')

if __name__=='__main__':unittest.main()
