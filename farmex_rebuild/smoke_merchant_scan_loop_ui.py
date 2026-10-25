"""Actual hidden Tk after events with explicit owned captures; no game IO."""
import copy
import time
from merchant_scan import ScanSnapshot
from merchant_scan_collection import MerchantProbe
from merchant_scan_loop import ScanLoopInput
from merchant_scan_runtime import START_PATH,STOP_PATH,ROUTE_PATH,ROUTE_LIST,STATUS_PATH


def check_merchant_scan_loop_ui(app):
    p=app.panel;root=p.canvas.winfo_toplevel()
    saved=dict(p.values);lists=copy.deepcopy(p.lists);form=p.form.get()
    original_clock=p.flood_clock
    def pump_until(predicate):
        deadline=time.monotonic()+3
        while not predicate():
            if time.monotonic()>deadline:raise AssertionError('Owned Tk timer did not reach expected state')
            root.update()
            time.sleep(.005)
    def start():
        p.widgets[START_PATH].invoke()
        assert p.merchant_scan_after_id is not None
    try:
        p.form.set('frmMain');p.render();p.section.set('Merchant Tarama');p.select_sections()
        p.values[ROUTE_PATH]=False;p.configure_merchant_scan()
        start()
        pump_until(lambda:p.merchant_scan_loop_result is not None)
        assert p.merchant_scan_loop_result.status=='needs_child_observation'
        assert p.merchant_scan.state.vector_58==()
        assert p.merchant_scan_after_id is not None
        frame=p.merchant_scan_loop.pipeline
        generation=p.merchant_scan_loop.generation
        p.render()
        assert p.merchant_scan_loop.pipeline is frame
        p.widgets[STOP_PATH].invoke()
        assert p.merchant_scan_after_id is None
        assert not p.merchant_scan_loop.state.active
        assert p.advance_merchant_scan_loop(generation) is None

        # A real timer callback obtains a full, explicitly empty owned lookup
        # snapshot and a separate supplied parent return, then starts a new tick.
        contexts=[];empty={i:MerchantProbe(0) for i in range(5001)}
        def provider(context):
            contexts.append(context)
            return ScanLoopInput(ScanSnapshot(collect_returned=True),empty)
        p.merchant_scan_provider=provider
        start()
        pump_until(lambda:bool(contexts))
        assert p.merchant_scan_loop_result.status=='local_step'
        assert p.merchant_scan_loop.pipeline is None
        assert p.merchant_scan_after_id is not None
        assert not p.merchant_scan_loop_result.invocation.native_execution_verified
        p.widgets[STOP_PATH].invoke()

        # Reentrant stop invalidates the in-flight provider result.
        def stop_provider(context):
            p.stop_merchant_scan()
            return ScanLoopInput(ScanSnapshot(collect_returned=True),empty)
        p.merchant_scan_provider=stop_provider
        start();pump_until(lambda:not p.merchant_scan_loop.state.active)
        assert p.merchant_scan_loop_result is None
        assert p.merchant_scan_after_id is None

        # A stale callback must not cancel the newer generation's timer.
        p.merchant_scan_provider=provider;start()
        stale=p.merchant_scan_loop.generation
        p.stop_merchant_scan();start()
        current=p.merchant_scan_after_id
        assert p.advance_merchant_scan_loop(stale) is None
        assert p.merchant_scan_after_id==current
        p.stop_merchant_scan()

        # Invalid capture is held without claiming successful collection.
        p.merchant_scan_provider=lambda context:'invalid capture'
        start()
        pump_until(lambda:'Tarama verisi alınamadı' in p.list_help.get())
        assert p.merchant_scan_loop_result is None
        assert p.merchant_scan_after_id is not None
        p.stop_merchant_scan()

        # Own route completion updates actual label/buttons only after the
        # separately supplied stop receipt. No export/native action is run.
        from merchant_scan_runtime import SAVE_PATH
        p.values[ROUTE_PATH]=True;p.values[SAVE_PATH]=False;p.configure_merchant_scan()
        p.lists[ROUTE_LIST]=[dict(caption='',subitems=['1','2'],checked=False)]
        def finish_provider(context):
            return ScanLoopInput(ScanSnapshot(distance_returned=True,selected_point_distance=0,
                actor_raw_byte_554020=0,collect_returned=True,stop_returned=True),empty)
        p.merchant_scan_provider=finish_provider;start()
        pump_until(lambda:not p.merchant_scan_loop.state.active)
        assert p.merchant_scan_loop_result.status=='completed'
        assert p.widgets[STATUS_PATH].cget('text')=='Tarama Tamamlandi !'
        assert p.widgets[START_PATH].instate(['!disabled'])
        assert p.merchant_scan_after_id is None

        p.values[ROUTE_PATH]=False;p.configure_merchant_scan();start()
        generation=p.merchant_scan_loop.generation
        p.bind_document(dict(saved),copy.deepcopy(lists))
        assert p.merchant_scan_provider is None
        assert p.merchant_scan_after_id is None
        assert p.merchant_scan_loop_result is None
        assert p.advance_merchant_scan_loop(generation) is None
        print('Merchant scan timer UI passed: real after callbacks, missing captures, complete owned collection, rerender, stop, stale generation, reentrant provider, invalid captures, route completion and profile invalidation')
    finally:
        p.flood_clock=original_clock
        app.values.clear();app.values.update(saved)
        app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.bind_document(app.values,app.lists)
