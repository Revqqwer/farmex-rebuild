"""Actual own selected-message button, stable queue and no cycle mutation."""
import copy
from dataclasses import replace
from flood_editor import LIST_PATH
from flood_runtime import OwnedFloodSession,TOGGLE_PATH
from flood_selected import BUTTON_PATH

def check_flood_selected(app):
    p=app.panel;old_values=dict(app.values);old_lists=copy.deepcopy(app.lists);form=p.form.get()
    session=p.flood_session;clock=p.flood_clock;cp=p.flood_codepage_reader;p.cancel_flood_timer()
    try:
        p.flood_session=OwnedFloodSession();p.flood_codepage_reader=lambda:1254;p.form.set('frmMain')
        app.lists[LIST_PATH]=[dict(caption='Party',subitems=['hello','5000'],checked=False),
                              dict(caption='Clan',subitems=['world','-1'],checked=True)]
        p.render();p.compile_current_flood();table=p.widgets[LIST_PATH];button=p.widgets[BUTTON_PATH]
        assert not button.instate(['disabled'])
        table.selection_remove(*table.selection())
        def forbidden():raise AssertionError('no-selection must skip clock')
        p.flood_clock=forbidden;before=p.flood_session.state
        button.invoke();assert p.flood_selected_result.status=='no_selection'
        assert p.flood_session.queue.records==() and p.flood_session.state==before
        table.selection_set('1');ticks=[]
        def clock_read():ticks.append(1234);return 1234
        p.flood_clock=clock_read;button.invoke();plan=p.flood_selected_result
        assert plan.complete and plan.payload==b'\x10\x06\x05\x00world' and ticks==[1234]
        assert p.flood_session.state==before and len(p.flood_session.queue.records)==1
        assert 'Oyuna gönderim bağlı değil' in p.list_help.get()
        # Active source-shaped cycle state is also unchanged by manual click.
        p.widgets[TOGGLE_PATH].invoke();p.cancel_flood_timer()
        p.flood_session.state=replace(p.flood_session.state,index=1,timestamp=500)
        before=p.flood_session.state;table.selection_set('0');button.invoke()
        assert p.flood_session.state==before and len(p.flood_session.queue.records)==2
        assert p.flood_selected_result.payload==b'\x10\x03\x05\x00hello'
        p.widgets[TOGGLE_PATH].invoke();assert p.flood_after_id is None
        # Stale compiled UI cannot silently select an older byte record.
        app.lists[LIST_PATH][0]['subitems'][0]='changed'
        button.invoke();assert not p.flood_selected_result.complete
        assert len(p.flood_session.queue.records)==2
        print('Flood selected UI passed:actual button,selection guard,shared local queue,no cycle mutation,stale rejection; no game send')
    finally:
        p.cancel_flood_timer();p.flood_session=session;p.flood_clock=clock;p.flood_codepage_reader=cp
        app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
        p.form.set(form);p.bind_document(app.values,app.lists)

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_flood_selected(Application(root))
    finally:root.destroy()
