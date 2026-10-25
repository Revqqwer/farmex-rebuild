"""Actual own Tk events in an offscreen transparent layout phase; no game."""
import copy
import ctypes,os
from merchant_results_session import TABLE_PATH
from merchant_result_rows import MerchantDisplayRecord as D
from merchant_result_filter import MerchantResultRecord as F
from merchant_cell_actions import MerchantCellState
from action_queue import QueueState,enqueue
from merchant_scan_runtime import START_PATH,STOP_PATH


def check_merchant_cells_ui(app):
    p=app.panel;old_values=dict(app.values);old_lists=copy.deepcopy(app.lists);form=p.form.get()
    queue=p.flood_session.queue;clock=p.flood_clock;cp=p.merchant_codepage_reader
    if app.root.state()!='withdrawn':raise ValueError('Own UI smoke requires a withdrawn root')
    alpha=app.root.attributes('-alpha');override=app.root.overrideredirect()
    try:
        p.form.set('frmMain');p.render();p.section.set('Merchant Tarama');p.select_sections()
        p.flood_session.queue=enqueue(QueueState(),b'seed',4,0,1,10).state
        p.merchant_codepage_reader=lambda:1254;ticks=[]
        def tick():ticks.append(1234);return 1234
        p.flood_clock=tick
        p.widgets[START_PATH].invoke()
        assert p.merchant_scan.state.active_byte==1
        p.accept_merchant_records((D(F(0,1,1,1),'First','Item',1,825,520),
                                   D(F(0,1,1,1),'Seller','Other',2,16777217,0x80000000)))
        # Ttk has no cell parcel before its first real layout. This phase is
        # transparent, borderless and offscreen. Tk may activate its own root;
        # it is withdrawn again before the rest of the broad smoke test.
        app.root.overrideredirect(True);app.root.attributes('-alpha',0.0)
        app.root.geometry('1120x740+32000+32000');app.root.deiconify();app.root.update()
        table=p.widgets[TABLE_PATH]
        assert table.column('6','width')==0 and table.column('7','width')==0
        def click(item,column):
            app.root.update_idletasks()
            # Coordinates come from actual widget hit-testing; no mock of
            # identify_* and no fabricated source screen-X observations.
            ys=[y for y in range(table.winfo_height()) if table.identify_row(y)==item]
            assert ys,(item,'no own row hit area')
            y=ys[len(ys)//2]
            xs=[x for x in range(1,table.winfo_width()-1)
                if table.identify_column(x)=='#'+str(column+1) and table.identify_region(x,y)=='cell']
            assert xs,(column,'no own cell hit area')
            x=xs[len(xs)//2]
            table.event_generate('<ButtonPress-1>',x=x,y=y)
            table.event_generate('<ButtonRelease-1>',x=x,y=y)
            return p.merchant_cell_result
        before=p.flood_session.state
        result=click('1',4)
        assert result is not None and result.complete,result
        assert result.payload==b'\x35\x01\x06\x00Seller'
        assert [r.payload for r in p.flood_session.queue.records]==[b'seed',result.payload]
        assert ticks==[1234] and p.flood_session.state==before
        assert 'Gönderim bağlantısı bekliyor' in p.list_help.get()
        assert not result.source_cell_frame_executed and not result.delivery_verified
        assert p.merchant_scan.state.active_byte==1,'PM must not stop scan'
        p.merchant_cells.state=MerchantCellState(7,8)
        result=click('1',5)
        assert result.complete and result.movement_push_order==(0xcf000000,0x4b800000)
        assert result.state==MerchantCellState(0,0)
        assert p.merchant_scan.state.active_byte==0 and p.merchant_scan.state.busy_byte_0f==0
        assert p.widgets[START_PATH].instate(['!disabled']) and p.widgets[STOP_PATH].instate(['disabled'])
        assert len(p.flood_session.queue.records)==2 and ticks==[1234]
        assert 'Hareket bağlantısı bekliyor' in p.list_help.get()
        # A changed visible row cannot silently act on an older own snapshot.
        values=list(table.item('1','values'));values[0]='stale caption';table.item('1',values=values)
        assert click('1',4) is None
        assert len(p.flood_session.queue.records)==2 and ticks==[1234]
        p.paint_merchant_results()
        p.merchant_codepage_reader=lambda:0
        result=click('0',4)
        assert not result.complete and result.status.startswith('local_caption_conversion:')
        assert len(p.flood_session.queue.records)==2 and ticks==[1234]
        p.merchant_codepage_reader=lambda:1254
        result=click('0',4)
        assert result.complete and result.payload.endswith(b'First')
        assert len(p.flood_session.queue.records)==3 and ticks==[1234,1234]
        p.bind_document(app.values,app.lists)
        assert p.merchant_cell_result is None and p.merchant_cells.movements==()
        assert len(p.flood_session.queue.records)==3
        print('Merchant cell UI passed: actual PM/GIT press-release hits, shared own queue, canonical float target, stale-row rejection, invalid-CP recovery, hidden coordinates and profile reset; no native source frame or game delivery')
    finally:
        app.root.withdraw();app.root.update()
        app.root.overrideredirect(override);app.root.attributes('-alpha',alpha)
        app.root.geometry('1120x740+0+0')
        user=ctypes.WinDLL('user32');user.GetForegroundWindow.restype=ctypes.c_void_p
        user.GetWindowThreadProcessId.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint)]
        foreground_pid=ctypes.c_uint()
        user.GetWindowThreadProcessId(user.GetForegroundWindow(),ctypes.byref(foreground_pid))
        assert foreground_pid.value!=os.getpid(),'Own QA must not retain foreground after withdrawal'
        p.flood_session.queue=queue;p.flood_clock=clock;p.merchant_codepage_reader=cp
        app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
        p.form.set(form);p.bind_document(app.values,app.lists)


if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_merchant_cells_ui(Application(root))
    finally:root.destroy()
