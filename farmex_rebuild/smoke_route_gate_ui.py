"""Actual local gate checkbox/list/timers, captured synthetic packets only."""
import copy,time
from route_gate_record import GateRecordObservation
from route_npc_click import NpcValueCapture as C
from route_panel_runtime import OPEN_PATH,CLOSE_PATH,GATES_PATH
from panel_ui import SOURCE_ROUTE_LIST,SOURCE_ROUTE_CLEAR


def capture(*,clock=123,format_returned=True):
    return GateRecordObservation(recording_byte=1,zone_first=C(32,True),zone_second=C(33,True),
        clock=C(clock,True),reader_returned=True,actor=C(0x1000,True),
        name_setup_returned=True,name_storage=C(15,True),name_ansi=C(b'[Teleport Gate]',True),
        comparison_returned=True,format_returned=format_returned)


def check_source_route_gate_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get();geometry=dict(p.route_panel.geometry)
    visible=p.route_panel.visible;last=p.route_panel.last;update=p.route_panel_update
    provider=p.source_gates.provider;result=p.source_gates.result;clock=dict(p.source_gates.clock_shadow)
    queue=p.flood_session.queue
    def main():
        p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections();p.widgets[OPEN_PATH].invoke()
    def enabled(value):
        if p.values[GATES_PATH]!=value:p.widgets[GATES_PATH].invoke()
        assert p.values[GATES_PATH] is value
    def empty():p.widgets[SOURCE_ROUTE_CLEAR].invoke();assert not p.lists[SOURCE_ROUTE_LIST]
    def pump(predicate):
        end=time.monotonic()+3
        while not predicate() and time.monotonic()<end:app.root.update();time.sleep(.01)
        assert predicate(),'own gate-record UI timeout'
    try:
        main();empty();enabled(False);p.set_source_gate_provider(None)
        assert p.submit_source_gate_packet(b'\x33').status=='recording_disabled'
        assert not p.lists[SOURCE_ROUTE_LIST] and p.source_gate_after_id is None
        enabled(True);p.submit_source_gate_packet(b'\x33\x01\0\0\0')
        assert not p.source_gates.result.done and not p.lists[SOURCE_ROUTE_LIST]
        assert p.source_gate_after_id is not None
        # Installing a provider invalidates the pending old invocation.
        p.set_source_gate_provider(lambda context:capture())
        assert not p.source_gates.pending and p.source_gate_after_id is None
        for packet in (b'\x20\x01\x01\0',b'\x33\xff\xff\xff\xff',
                       b'\x4b\0\0\0\x80',b'\x55\xff'):
            assert p.submit_source_gate_packet(packet).complete
        expected=[dict(caption=caption,subitems=subitems,checked=False) for caption,subitems in (
            ('Delos Gate Open',['-','-']),('Gate Open',['4294967295','-']),
            ('Gate',['2147483648','-']),('Delos Gate',['255','-']))]
        assert p.lists[SOURCE_ROUTE_LIST]==expected
        p.render();assert tuple(p.widgets[SOURCE_ROUTE_LIST].item('2','values'))==('Gate','2147483648','-')
        # Provider cannot turn recording on;4b still updates owned clock.
        enabled(False);before=copy.deepcopy(p.lists[SOURCE_ROUTE_LIST])
        p.set_source_gate_provider(lambda context:capture(clock=77))
        assert p.submit_source_gate_packet(b'\x4b').status=='recording_disabled'
        assert p.source_gates.clock_shadow=={0x561f74:77,0x561f78:0}
        assert p.lists[SOURCE_ROUTE_LIST]==before
        # Read flag only after delayed clock; route close unchecks the real box.
        enabled(True);ready=[False]
        def clock_provider(context):
            data=capture(clock=88)
            return GateRecordObservation(**{**vars(data),'clock':C(88,ready[0])})
        p.set_source_gate_provider(clock_provider);p.submit_source_gate_packet(b'\x4b\x01\0\0\0')
        assert p.source_gates.result.needed=='clock.returned'
        p.widgets[CLOSE_PATH].invoke();assert p.values[GATES_PATH] is False
        ready[0]=True;pump(lambda:not p.source_gates.pending)
        assert p.source_gates.result.status=='recording_disabled' and p.lists[SOURCE_ROUTE_LIST]==before
        # A flag already consumed before close is retained while formatter waits.
        main();empty();enabled(True);ready[0]=False
        p.set_source_gate_provider(lambda context:capture(format_returned=ready[0]))
        p.submit_source_gate_packet(b'\x33\x01\0\0\0')
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='Gate Open',subitems=[],checked=False)]
        p.widgets[CLOSE_PATH].invoke();p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:not p.source_gates.pending)
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='Gate Open',subitems=['1','-'],checked=False)]
        # Deleted token never commits into the replacement row.
        main();empty();enabled(True);ready[0]=False
        p.submit_source_gate_packet(b'\x33\x02\0\0\0');empty()
        p.lists[SOURCE_ROUTE_LIST]=[dict(caption='replacement',subitems=['a','b'],checked=False)];p.render()
        ready[0]=True;pump(lambda:not p.source_gates.pending)
        assert not p.source_gates.result.complete and p.lists[SOURCE_ROUTE_LIST][0]['caption']=='replacement'
        # A provider reentrant packet is separate FIFO work, serviced by timer.
        empty();entered=[False]
        def reentrant(context):
            if not entered[0]:entered[0]=True;p.submit_source_gate_packet(b'\x33\x02\0\0\0')
            return capture()
        p.set_source_gate_provider(reentrant);p.submit_source_gate_packet(b'\x33\x01\0\0\0')
        pump(lambda:not p.source_gates.pending)
        assert [r['subitems'][0] for r in p.lists[SOURCE_ROUTE_LIST]]==['1','2']
        # Profile generation prevents delayed capture from writing new document.
        empty();p.set_source_gate_provider(lambda context:capture(format_returned=False))
        p.submit_source_gate_packet(b'\x33\x01\0\0\0');old=p.source_gates.generation
        new=copy.deepcopy(p.lists);new[SOURCE_ROUTE_LIST]=[dict(caption='new profile',subitems=['x','y'],checked=False)]
        p.bind_document(dict(p.values),new)
        assert not p.source_gates.pending and p.source_gates.provider is None and p.source_gates.result is None
        assert p.source_gate_after_id is None and p.advance_source_gates(old) is None
        assert p.lists[SOURCE_ROUTE_LIST][0]['caption']=='new profile' and p.flood_session.queue==queue
        print('Source gate recording UI passed: actual checkbox/list/close, four captured packet branches, provider cannot override flag, timestamp before disabled gate, fresh flag after delayed clock, cached flag before hidden formatter, deleted token, FIFO/reentrant timer and profile generation; no game/network IO')
    finally:
        p.reset_source_gates('test_restore')
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last;p.route_panel_update=update
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.set_source_gate_provider(provider);p.source_gates.result=result;p.source_gates.clock_shadow.clear();p.source_gates.clock_shadow.update(clock)
