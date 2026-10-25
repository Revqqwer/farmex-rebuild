"""Actual Armor button: two fresh combo reads, shared runner/prefix, no game IO."""
import copy,time
from armor_start import ArmorStartObservation,COMBO_PATH,ITEM_IDS
from armor_start_frame import ArmorStartFrameObservation,BUTTON_PATH


def capture(**changes):
    fields=dict(filter_ready_returned=True,npc_id_dword=9,npc_pointer_dword=0x7000,
        x_offset_dword=4,y_offset_dword=8,x_ftol_dword=30,y_ftol_dword=100,
        distance_ftol_dword=9,bag_flag_byte=0,
        message_returns={reason:True for reason in ('npc_missing','too_far','item_missing','bag_full')})
    fields.update(changes)
    return ArmorStartFrameObservation(1,ArmorStartObservation(**fields),{'first':True,'second':True},True,
        {(reason,index):True for reason in ('npc_missing','too_far','item_missing','bag_full') for index in (0,1)})


def check_armor_start_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();queue=p.flood_session.queue
    runner=p.source_upgrade_runner;parameters=p.source_upgrade_parameter_state
    cache=dict(p.source_upgrade_parameter_text_cache);ep=p.source_upgrade_provider;pp=p.source_upgrade_parameter_provider
    def main():p.form.set('frmMain');p.render();p.section.set('Upgrade');p.select_sections()
    def select(index):
        p.widgets[COMBO_PATH].current(index);p.widgets[COMBO_PATH].event_generate('<<ComboboxSelected>>')
    def pump(predicate):
        end=time.monotonic()+3
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'Armor start UI timeout'
    try:
        p.reset_source_upgrade_editor('test_armor');main()
        assert p.widgets[BUTTON_PATH].instate(['disabled'])
        p.set_source_upgrade_editor_provider(lambda context:ArmorStartFrameObservation(gate_byte=0))
        select(6);p.widgets[BUTTON_PATH].invoke()
        shared=p.source_upgrade_runner
        assert p.source_upgrade_result.status=='gate_closed' and not hasattr(shared,'armor_source_fields')
        ready=[False]
        def delayed(context):
            o=capture()
            return ArmorStartFrameObservation(1,o.source,o.combo_returns,ready[0],o.message_cleanup_returns)
        p.set_source_upgrade_editor_provider(delayed)
        shared.queue=(11,);shared.queue_stamp_qword=77;shared.armor_stamp_qword=99;shared.armor_attempts=8
        buttons=shared.source_start_ui
        p.widgets[BUTTON_PATH].invoke()
        assert p.source_upgrade_result.needed==('item_mapping_returned',)
        select(18);p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:not p.source_upgrade_pending)
        assert p.source_upgrade_result.status=='armor_armed'
        assert (shared.armor_source_fields[0x58],shared.armor_source_fields[0x5c])==(ITEM_IDS[6],18)
        assert (shared.state,shared.armor_attempts,shared.queue,shared.queue_stamp_qword,shared.armor_stamp_qword)==(2,0,(11,),77,99)
        assert shared.source_start_ui==buttons and p.source_upgrade_worker_after_id is None
        main();select(5)
        p.set_source_upgrade_editor_provider(lambda context:capture(bag_flag_byte=None))
        p.widgets[BUTTON_PATH].invoke()
        assert p.source_upgrade_result.status=='item_missing' and shared.state==2
        # Missing NPC message waits for both independent cleanup calls.
        p.set_source_upgrade_editor_provider(lambda context:ArmorStartFrameObservation(1,
            ArmorStartObservation(filter_ready_returned=True,npc_id_dword=0,message_returns={'npc_missing':True})))
        p.widgets[BUTTON_PATH].invoke()
        assert p.source_upgrade_result.needed==('message_cleanup','npc_missing',0)
        old=p.source_upgrade_pending[0][1];generation=p.source_upgrade_generation
        p.bind_document(dict(p.values),copy.deepcopy(p.lists))
        assert old.result.status=='cancelled' and p.source_upgrade_runner is not shared
        assert p.source_upgrade_provider is None and not p.source_upgrade_pending and p.source_upgrade_after_id is None
        assert p.advance_source_upgrade_editor(generation) is None and p.flood_session.queue==queue
        print('Armor start UI passed: actual conditional button/raw gate, shared runner source-field prefix, two fresh combo reads across mapping gap/hidden form, blank item early exit, separate message cleanup receipts, queue/clocks/button preservation and profile cancellation; mode2 worker still unbound, no game IO')
    finally:
        p.reset_source_upgrade_editor('test_restore')
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists);p.source_upgrade_runner=runner;p.source_upgrade_parameter_state=parameters
        p.source_upgrade_parameter_text_cache=cache
        p.set_source_upgrade_editor_provider(ep);p.set_source_upgrade_parameter_provider(pp)
        p.form.set(form);p.section.set(section);p.render()
