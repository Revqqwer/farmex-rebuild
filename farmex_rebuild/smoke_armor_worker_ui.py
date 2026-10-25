"""Actual Armor startup -> captured timer -> shared pair -> ordered limit stop."""
import copy,time
from action_queue import enqueue,QueueSample
from armor_start import COMBO_PATH,ITEM_IDS
from armor_start_frame import BUTTON_PATH
from smoke_armor_start_ui import capture as start_capture
from armor_worker import ArmorWorkerObservation
from upgrade_worker import UpgradeWorkerInput
from upgrade_armor import ArmorPacketObservation,VENDORS
from operation_engine import UpgradeSnapshot


def check_armor_worker_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();queue=p.flood_session.queue
    runner=p.source_upgrade_runner;parameters=p.source_upgrade_parameter_state
    cache=dict(p.source_upgrade_parameter_text_cache)
    ep=p.source_upgrade_provider;pp=p.source_upgrade_parameter_provider
    wp=p.source_upgrade_worker_provider;worker=p.source_upgrade_worker;wr=p.source_upgrade_worker_result
    def pump(predicate):
        end=time.monotonic()+4
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'Armor captured worker UI timeout'
    def capture(now=200,initial=0,**changes):
        fields=dict(distance_ftol_dword=9,bag_flag_byte=0,preparation_returned=True,
            packet=ArmorPacketObservation(3,vendor_matches={n:n=='Armor' for n,c in VENDORS}),
            queue_samples={0:QueueSample(now+1,1),1:QueueSample(now+2,1)},caller_cleanup_returned=True)
        fields.update(changes)
        return UpgradeWorkerInput(UpgradeSnapshot(now,source_helper_returned=True,source_stamp_tick_dword=now+3),
                                  initial_stamp_qword=initial,armor=ArmorWorkerObservation(**fields))
    try:
        p.reset_source_upgrade_editor('test_armor_worker');p.form.set('frmMain');p.render()
        p.section.set('Upgrade');p.select_sections()
        p.widgets[COMBO_PATH].current(6);p.widgets[COMBO_PATH].event_generate('<<ComboboxSelected>>')
        p.set_source_upgrade_editor_provider(lambda context:start_capture())
        p.widgets[BUTTON_PATH].invoke();shared=p.source_upgrade_runner
        assert shared.state==2 and shared.armor_stamp_qword is None and shared.armor_attempts==0
        flags=shared.source_start_ui
        assert p.source_upgrade_worker_after_id is None
        p.flood_session.queue=enqueue(queue,b'prefix',6,0,1,90).state;prefix=p.flood_session.queue
        p.set_source_upgrade_worker_provider(lambda context:capture(initial=None,packet=object()))
        pump(lambda:p.source_upgrade_worker_result is not None and p.source_upgrade_worker_result.needed==('initial_armor_stamp_qword',))
        assert p.flood_session.queue==prefix and shared.armor_attempts==0
        p.set_source_upgrade_worker_provider(lambda context:capture(queue_samples={0:QueueSample(201,1)}))
        pump(lambda:p.source_upgrade_worker_result.status=='needs_queue_observation')
        assert p.flood_session.queue==prefix and shared.armor_attempts==0
        p.widgets[BUTTON_PATH].invoke();assert not p.source_upgrade_pending
        p.set_source_upgrade_worker_provider(lambda context:capture(queue_samples={0:object(),1:QueueSample(202,1)}))
        pump(lambda:p.source_upgrade_worker_result.status=='local_armor_frame_complete')
        p.set_source_upgrade_worker_provider(None)
        records=p.flood_session.queue.records
        assert records[:-2]==prefix.records
        assert [(len(r.payload),r.created_tick,r.delay_dword) for r in records[-2:]]==[(20,201,0),(2,202,100)]
        assert int.from_bytes(records[-2].payload[11:15],'little')==ITEM_IDS[6] and records[-2].payload[19]==6
        assert (shared.armor_attempts,shared.armor_stamp_qword)==(1,203)
        # Explicit local fixture seed exercises the43 boundary without43 timer waits.
        shared.armor_attempts=42;shared.armor_source_fields[0x60]=42
        p.set_source_upgrade_worker_provider(lambda context:capture(403))
        pump(lambda:p.source_upgrade_worker_result.needed==('message_returned',))
        assert (shared.state,shared.armor_attempts,len(p.flood_session.queue.records))==(2,43,len(prefix.records)+4)
        p.set_source_upgrade_worker_provider(lambda context:capture(message_returned=True))
        pump(lambda:p.source_upgrade_worker_result.needed==('message_cleanup0_returned',))
        assert shared.state==2
        p.set_source_upgrade_worker_provider(lambda context:capture(message_cleanup0_returned=True))
        pump(lambda:p.source_upgrade_worker_result.needed==('message_cleanup1_returned',))
        assert shared.state==0 and p.source_upgrade_worker_after_id is not None
        assert shared.source_start_ui==flags
        p.set_source_upgrade_worker_provider(lambda context:capture(message_cleanup1_returned=True))
        pump(lambda:p.source_upgrade_worker_result.status=='stopped')
        assert p.source_upgrade_worker_after_id is None and shared.reason=='armor_attempt_limit'
        before=p.flood_session.queue
        p.widgets[BUTTON_PATH].invoke();assert shared.state==2
        def replaced(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));return capture(606)
        p.set_source_upgrade_worker_provider(replaced);generation=p.source_upgrade_worker_generation
        p.advance_source_upgrade_worker()
        assert p.source_upgrade_worker is None and p.source_upgrade_worker_provider is None
        assert p.source_upgrade_worker_after_id is None and p.flood_session.queue==before
        assert p.advance_source_upgrade_worker(generation) is None
        print('Armor worker UI passed: actual startup/cached fields -> explicit raw mode2 timer, unknown stamp hold, shared20/2-byte pair with independent clocks, no duplicate partial enqueue, counter43 notice/cleanup0/mode0/cleanup1 ordering, unchanged UI flags and stale profile rejection; no game IO')
    finally:
        p.reset_source_upgrade_editor('test_restore');p.flood_session.queue=queue
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists);p.source_upgrade_runner=runner;p.source_upgrade_parameter_state=parameters
        p.source_upgrade_parameter_text_cache=cache;p.source_upgrade_worker=worker;p.source_upgrade_worker_result=wr
        p.set_source_upgrade_editor_provider(ep);p.set_source_upgrade_parameter_provider(pp)
        p.set_source_upgrade_worker_provider(wp)
        p.form.set(form);p.section.set(section);p.render()
