"""Actual Start -> captured after worker -> shared owned queue -> Stop effects."""
import copy,time
from action_queue import enqueue
from operation_engine import UpgradeSnapshot
from upgrade_packets import UpgradePacketObservation
from upgrade_start_frame import UpgradeStartFrameObservation
from upgrade_worker import UpgradeWorkerInput
from action_queue import QueueSample
from upgrade_parameter_ui import SCROLL_PATH,WAIT_PATH,ANVIL_PATH
from upgrade_editor import START_PATH,STOP_PATH,LIST_PATH
from smoke_upgrade_start_ui import receipts as start_capture
from smoke_upgrade_parameter_ui import capture as parameter_capture


def check_upgrade_worker_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();queue=p.flood_session.queue
    runner=p.source_upgrade_runner;parameters=p.source_upgrade_parameter_state
    cache=dict(p.source_upgrade_parameter_text_cache)
    ep=p.source_upgrade_provider;pp=p.source_upgrade_parameter_provider
    wp=p.source_upgrade_worker_provider;worker=p.source_upgrade_worker;wr=p.source_upgrade_worker_result
    def main():p.form.set('frmMain');p.render();p.section.set('Upgrade');p.select_sections()
    def pump(predicate):
        end=time.monotonic()+4
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'captured Upgrade worker timeout'
    def capture(packet=None,**changes):
        fields=dict(snapshot=UpgradeSnapshot(100,True,source_helper_returned=True,source_stamp_tick_dword=102),packet=packet)
        fields.update(changes);return UpgradeWorkerInput(**fields)
    try:
        p.reset_source_upgrade_editor('test_worker_start');main()
        p.lists[LIST_PATH]=[dict(caption='14',subitems=[],checked=True)];p.render()
        p.set_source_upgrade_parameter_provider(lambda context:parameter_capture())
        p.widgets[SCROLL_PATH].set('Scroll');p.widgets[SCROLL_PATH].event_generate('<<ComboboxSelected>>')
        p.variables[ANVIL_PATH].set('12');p.variables[WAIT_PATH].set('100')
        p.set_source_upgrade_editor_provider(lambda context:start_capture())
        p.widgets[START_PATH].invoke()
        shared=p.source_upgrade_runner
        assert shared.state==1 and shared.queue==(14,) and shared.queue_stamp_qword is None
        assert p.source_upgrade_worker_after_id is None and p.flood_session.queue==queue
        # Keep an unrelated record and continue its shared writer ID sequence.
        p.flood_session.queue=enqueue(queue,b'fixture prefix',14,0,1,90).state
        prefix=p.flood_session.queue
        p.set_source_upgrade_worker_provider(lambda context:capture(UpgradePacketObservation(scroll_item_dword=13),initial_stamp_qword=0))
        pump(lambda:p.source_upgrade_worker_result is not None and p.source_upgrade_worker_result.status=='needs_packet_observation')
        assert shared.queue_stamp_qword==0 and p.flood_session.queue==prefix
        p.set_source_upgrade_worker_provider(None)
        assert p.source_upgrade_worker_after_id is None
        # Completed scroll getter stays captured; Anvil remains fresh until the target getter.
        p.variables[ANVIL_PATH].set('99')
        p.set_source_upgrade_worker_provider(lambda context:capture(UpgradePacketObservation(target_item_dword=21),queue_sample=QueueSample(101,1)))
        pump(lambda:p.source_upgrade_worker_result.status=='local_upgrade_frame_complete')
        p.set_source_upgrade_worker_provider(None)
        assert shared.queue==() and shared.queue_stamp_qword==102
        records=p.flood_session.queue.records
        assert records[:-1]==prefix.records and records[-1].record_id==prefix.next_id
        assert int.from_bytes(records[-1].payload[3:7],'little')==99
        assert len(records[-1].payload)==57
        # A later empty-queue tick waits for source spans around unguarded Stop helper.
        def empty(**changes):
            return capture(snapshot=UpgradeSnapshot(202,True),**changes)
        p.set_source_upgrade_worker_provider(lambda context:empty())
        pump(lambda:p.source_upgrade_worker_result.status=='needs_stop_prefix')
        assert shared.state==1 and p.widgets[STOP_PATH].instate(['!disabled'])
        p.widgets[STOP_PATH].invoke()
        assert shared.state==1 and not p.source_upgrade_pending
        p.set_source_upgrade_worker_provider(lambda context:empty(stop_prefix_returned=True,
            stop_observation=UpgradeStartFrameObservation(gate_byte=0,start_ui_returned=True,stop_ui_returned=True)))
        pump(lambda:p.source_upgrade_worker_result.status=='needs_stop_suffix')
        assert shared.state==0 and p.source_upgrade_worker_after_id is not None
        assert p.widgets[START_PATH].instate(['!disabled']) and p.widgets[STOP_PATH].instate(['disabled'])
        p.set_source_upgrade_worker_provider(lambda context:empty(stop_suffix_returned=True))
        pump(lambda:p.source_upgrade_worker_result.status=='stopped')
        assert p.source_upgrade_worker_after_id is None and shared.queue_stamp_qword==102
        # Profile replacement inside a provider rejects its old observation.
        p.widgets[START_PATH].invoke()
        before=p.flood_session.queue
        def replaced(context):
            p.bind_document(dict(p.values),copy.deepcopy(p.lists))
            return capture(UpgradePacketObservation(13,21),initial_stamp_qword=0,queue_sample=QueueSample(301,1))
        p.set_source_upgrade_worker_provider(replaced)
        old_generation=p.source_upgrade_worker_generation
        p.advance_source_upgrade_worker()
        assert p.source_upgrade_worker_provider is None and p.source_upgrade_worker is None
        assert p.source_upgrade_worker_result is None and p.source_upgrade_worker_after_id is None
        assert p.flood_session.queue==before and p.source_upgrade_runner is not shared
        assert p.advance_source_upgrade_worker(old_generation) is None
        print('Upgrade worker UI passed: actual Start/cached fields -> explicit captured timer/initial stamp, late Anvil after getters, shared queue prefix/IDs, pause/resume, guarded writer, unguarded inner Stop UI and pre/post spans, no fabricated clock, stale profile rejection; no game IO')
    finally:
        p.reset_source_upgrade_editor('test_restore');p.flood_session.queue=queue
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.bind_document(app.values,app.lists)
        p.source_upgrade_runner=runner;p.source_upgrade_parameter_state=parameters
        p.source_upgrade_parameter_text_cache=cache;p.source_upgrade_worker=worker;p.source_upgrade_worker_result=wr
        p.set_source_upgrade_editor_provider(ep);p.set_source_upgrade_parameter_provider(pp)
        p.set_source_upgrade_worker_provider(wp)
        p.form.set(form);p.section.set(section);p.render()
