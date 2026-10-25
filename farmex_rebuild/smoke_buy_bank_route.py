"""Own BUY result1 -> separate fresh observations -> BMerchant simulator."""
import copy,json,tempfile
from pathlib import Path
from unittest.mock import patch
from route_catalog import ROUTE_COMBO_PATHS
from merchant_configuration import BANK,EXTRA,THRESHOLD
from merchant_preparation import BUY_LIST_PATH

def check_buy_bank_route_ui(app):
    e=app.engine_page;r=app.route_page;p=app.panel
    values=dict(app.values);lists=copy.deepcopy(app.lists);choices=dict(app.profiles.route_choices);bounds=dict(app.profiles.bounds)
    form=p.form.get();directory=r.supply_directory.get();cp=r.source_codepage.get();steps=list(r.steps)
    case=e.case.get();panel=e.use_class_panel.get();ready=e.ready.get()
    variables=(e.buy_merchant_fixture,e.buy_reply_fixture,e.buy_failure_fixture,e.buy_failure_json,e.buy_merchant_free,e.buy_merchant_coins)
    previous=tuple(v.get() for v in variables)
    try:
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'buy.R';file.write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=3\n')
            (Path(d)/'sell.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=9\n')
            r.supply_directory.set(d);r.source_codepage.set('1254');r.stop()
            for kind,name in (('BMerchant','buy.R'),('SMerchant','sell.R')):
                app.profiles.install_route_choices(app.values,ROUTE_COMBO_PATHS[kind],(name,))
            for path,value in ((BANK,True),(EXTRA,'0'),(THRESHOLD,'28')):app.profiles.update(app.values,path,value)
            app.lists[BUY_LIST_PATH]=[]
            p.form.set('frmMain');p.render()
            for kind in ('BMerchant','SMerchant'):
                w=p.widgets[ROUTE_COMBO_PATHS[kind]];w.current(0);w.event_generate('<<ComboboxSelected>>')
            e.case.set('Buy Merchant');e.use_class_panel.set(True);e.ready.set(True)
            e.buy_merchant_fixture.set(True);e.buy_reply_fixture.set(False);e.buy_failure_fixture.set(True)
            e.buy_merchant_free.set('28');e.buy_merchant_coins.set('1000');e.buy_failure_json.set('not reached JSON')
            e.reset();e.tick(1);e.tick(1);e.tick(1)
            assert e.merchant.phase==2 and e.merchant.last_buy_failure_plan is None
            assert 'Deneme değeri geçersiz' not in e.output.get('1.0','end')
            e.buy_failure_json.set('{}')
            with patch.object(e,'buy_bank_route_reader',side_effect=AssertionError('early BUY route read')):e.tick(61000)
            assert e.merchant.last_buy_setup_plan.result_dword==1 and e.merchant.last_buy_setup_plan.inventory_plan.free_count==28
            assert not e.merchant.last_buy_failure_plan.complete and not r.runner.active
            raw=dict(inventory_returned=True,free_count_dword=0,threshold_dword=0,alarm_byte=0,
                policy_results=[2,2,2],bank_count_returned=True,bank_count_dword=1,
                setup_gate_byte=0,branch_span_returns=[True,True])
            e.buy_failure_json.set(json.dumps(raw));e.tick(1)
            assert e.merchant.last_buy_failure_plan.route_plan.ready and not e.merchant.last_buy_failure_plan.complete
            assert e.merchant.phase==2 and e.buy_bank_handoff_last is None and not r.runner.active
            raw['route_span_returned']=True;e.buy_failure_json.set(json.dumps(raw));e.tick(1)
            assert e.merchant.phase==0 and r.runner.active and r.steps[0].seconds==3
            assert e.buy_bank_handoff_last['kind']=='BMerchant'
            assert e.merchant.last_buy_failure_plan.route_plan.filename_global==0x569908
            for _ in range(9):
                if not r.runner.active:break
                r.tick(1000)
            assert r.runner.reason=='Tamamlandı'
            file.unlink();raw['setup_gate_byte']=int(e.merchant.setup_seen)
            raw['bank_error_returns']=dict(error_message_returned=True,path_cleanup_returned=True,
                error_stop_returned=True,error_notification_returned=True,error_final_cleanup_returned=True)
            e.buy_failure_json.set(json.dumps(raw))
            for _ in range(4):
                if not e.merchant.active:break
                e.tick(1)
            assert e.merchant.reason=='bank_route_load_failed' and e.buy_bank_handoff_last is None
            assert not r.runner.active and e.merchant.last_buy_failure_plan.route_plan.kind=='BMerchant'
    finally:
        app.profiles.route_choices=choices;app.profiles.bounds=bounds
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        for variable,value in zip(variables,previous):variable.set(value)
        r.supply_directory.set(directory);r.source_codepage.set(cp);r.steps=steps;r.stop();r.refresh()
        p.form.set(form);p.bind_document(app.values,app.lists)
        e.use_class_panel.set(panel);e.ready.set(ready);e.case.set(case);e.reset()
