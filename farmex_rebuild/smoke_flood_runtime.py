"""Actual own toggle widget/timer registration/queue; hidden, no game actions."""
import copy
from flood_runtime import *
from flood_editor import LIST_PATH

def check_flood_runtime(app):
    panel=app.panel;old_values=dict(app.values);old_lists=copy.deepcopy(app.lists);form=panel.form.get()
    session=panel.flood_session;clock=panel.flood_clock;cp=panel.flood_codepage_reader
    panel.cancel_flood_timer()
    try:
        panel.flood_session=OwnedFloodSession();panel.flood_codepage_reader=lambda:1254
        panel.form.set('frmMain');panel.render()
        app.lists[LIST_PATH]=[dict(caption='Party',subitems=['hello','5'],checked=False)]
        panel.compile_current_flood()
        button=panel.widgets[TOGGLE_PATH];assert not button.instate(['disabled'])
        button.invoke();assert panel.flood_session.state.enabled
        assert button.cget('text')==STOP_TEXT and panel.flood_after_id is not None
        assert 'Oyuna gönderim bağlı değil' in panel.list_help.get()
        ticks=iter((6000,6010,6020));panel.flood_clock=lambda:next(ticks)
        plan=panel.advance_flood_loop();assert plan.complete
        assert plan.queue.records[0].payload==b'\x10\x03\x05\x00hello'
        assert plan.state.timestamp==6020 and len(plan.queue.records)==1
        assert not plan.delivery_verified and not plan.live_compatibility_verified
        # Rerender/profile rebinding preserves local caption/state/queue.
        panel.render();assert panel.widgets[TOGGLE_PATH].cget('text')==STOP_TEXT
        panel.bind_document(app.values,app.lists);assert panel.widgets[TOGGLE_PATH].cget('text')==STOP_TEXT
        panel.flood_clock=lambda:6021
        scheduled=panel.flood_after_id
        app.root.after(150,app.root.quit);app.root.mainloop()
        assert panel.flood_runtime_result.status=='waiting'
        assert panel.flood_after_id is not None and panel.flood_after_id!=scheduled
        assert len(panel.flood_session.queue.records)==1
        panel.widgets[TOGGLE_PATH].invoke();assert not panel.flood_session.state.enabled
        assert panel.flood_after_id is None and panel.flood_session.state.timestamp==0
        assert len(panel.flood_session.queue.records)==1
        # Empty list is not an invented start gate and needs no clock.
        app.lists[LIST_PATH]=[];panel.compile_current_flood()
        panel.widgets[TOGGLE_PATH].invoke();assert panel.flood_session.state.enabled
        def forbidden():raise AssertionError('empty list must skip clock')
        panel.flood_clock=forbidden;assert panel.advance_flood_loop().status=='empty'
        panel.widgets[TOGGLE_PATH].invoke();assert panel.flood_after_id is None
        assert panel.widgets[TOGGLE_PATH].cget('text')==START_TEXT
        print('Flood runtime UI passed:actual toggle/timer,source-shaped single-row packet queue,clock wait,caption/profile persistence,empty start,stop keeps queue; no game send')
    finally:
        panel.cancel_flood_timer();panel.flood_session=session;panel.flood_clock=clock;panel.flood_codepage_reader=cp
        app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
        panel.form.set(form);panel.bind_document(app.values,app.lists)

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_flood_runtime(Application(root))
    finally:root.destroy()
