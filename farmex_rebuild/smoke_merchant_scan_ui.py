"""Invoke actual own buttons/checkboxes; no game process or fabricated replies."""
import copy
from merchant_scan_runtime import (SELL_PATH,BUY_PATH,ROUTE_PATH,ROUTE_LIST,
    START_PATH,STOP_PATH,QUICK_PATH,STATUS_PATH)
from merchant_results_session import KIND_PATH,TABLE_PATH


def check_merchant_scan_ui(app):
    p=app.panel;saved=dict(p.values);lists=copy.deepcopy(p.lists)
    original_form=p.form.get()
    try:
        p.form.set('frmMain');p.render();p.section.set('Merchant Tarama');p.select_sections()
        def check(path,value):
            if p.values[path]!=value:p.widgets[path].invoke()
            assert p.values[path] is value
        check(SELL_PATH,False);check(BUY_PATH,True);check(ROUTE_PATH,True)
        p.lists[ROUTE_LIST]=[dict(caption='',subitems=['$FFFFFFFF','2'],checked=False),
                             dict(caption='',subitems=['3','-4'],checked=False)]
        p.widgets[START_PATH].invoke()
        assert p.merchant_scan_update.complete
        assert p.merchant_scan.state.route_points==((0xffffffff,2),(3,0xfffffffc))
        assert p.values[KIND_PATH]==1 and p.widgets[KIND_PATH].current()==1
        assert not p.widgets[TABLE_PATH].get_children()
        assert p.widgets[START_PATH].instate(['disabled'])
        assert p.widgets[STOP_PATH].instate(['!disabled'])
        assert p.widgets[QUICK_PATH].instate(['disabled'])
        assert p.widgets[STATUS_PATH].cget('text')=='Taraniyor...'
        assert 'Oyun verisi' in p.list_help.get()
        p.render()
        assert p.widgets[START_PATH].instate(['disabled'])
        assert p.widgets[STOP_PATH].instate(['!disabled'])
        assert p.widgets[STATUS_PATH].cget('text')=='Taraniyor...'
        p.widgets[STOP_PATH].invoke()
        assert p.merchant_scan.state.active_byte==0
        assert len(p.merchant_scan.state.route_points)==2
        assert p.widgets[STATUS_PATH].cget('text')=='Hazır'
        assert p.widgets[START_PATH].instate(['!disabled'])
        # Source reader is not called by combo OnChange. A checkbox click
        # refreshes all five owned settings, including the current combo.
        p.widgets[KIND_PATH].current(0);p.widgets[KIND_PATH].event_generate('<<ComboboxSelected>>')
        assert p.merchant_scan.state.options.view_mode_dword==1
        p.widgets[BUY_PATH].invoke()
        assert p.merchant_scan.state.options.view_mode_dword==0
        p.lists[ROUTE_LIST][1]['subitems'][1]='invalid'
        p.widgets[START_PATH].invoke()
        assert not p.merchant_scan_update.complete
        assert p.merchant_scan_update.failed_coordinate=='y'
        assert p.merchant_scan.state.route_points==((0xffffffff,2),)
        assert p.merchant_scan.state.active_byte==0
        assert p.widgets[STOP_PATH].instate(['!disabled'])
        p.widgets[STOP_PATH].invoke()
        p.bind_document(dict(saved),copy.deepcopy(lists))
        assert p.merchant_scan.state.active_byte==0 and p.merchant_scan.state.route_points==()
        print('Merchant scan UI passed: real start/stop/checkbox commands, route prefix errors, cached mode, rerender and profile reset')
    finally:
        app.values.clear();app.values.update(saved)
        app.lists.clear();app.lists.update(lists)
        p.form.set(original_form);p.bind_document(app.values,app.lists)
