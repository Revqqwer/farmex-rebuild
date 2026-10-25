"""Own UI failed SELL -> selected file -> gated local route simulator handoff."""
import copy,json,tempfile
from pathlib import Path
from unittest.mock import patch
from route_catalog import ROUTE_COMBO_PATHS
from merchant_configuration import SELL_BANK,SELL_COIN_ALARM,SELL_EXTRA
from merchant_sell_preparation import SELL_LIST_PATH

def check_sell_bank_route_ui(app):
    e=app.engine_page;r=app.route_page;p=app.panel
    values=dict(app.values);lists=copy.deepcopy(app.lists);choices=dict(app.profiles.route_choices);bounds=dict(app.profiles.bounds)
    form=p.form.get();directory=r.supply_directory.get();cp=r.source_codepage.get();steps=list(r.steps)
    case=e.case.get();panel=e.use_class_panel.get();ready=e.ready.get()
    variables=(e.sell_preparation_fixture,e.sell_cost_fixture,e.sell_wait_fixture,e.sell_failure_fixture,
        e.sell_failure_json,e.sell_setup_cost,e.sell_setup_matches,e.sell_setup_coins)
    previous=tuple(v.get() for v in variables)
    try:
        with tempfile.TemporaryDirectory() as d:
            route_file=Path(d)/'bank.R';route_file.write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=2\n')
            r.supply_directory.set(d);r.source_codepage.set('1254');r.stop()
            path=ROUTE_COMBO_PATHS['SMerchant'];app.profiles.install_route_choices(app.values,path,('bank.R',))
            app.profiles.update(app.values,SELL_BANK,True);app.profiles.update(app.values,SELL_COIN_ALARM,False)
            app.profiles.update(app.values,SELL_EXTRA,'0')
            app.lists[SELL_LIST_PATH]=[]
            p.form.set('frmMain');p.render();p.widgets[path].current(0);p.widgets[path].event_generate('<<ComboboxSelected>>')
            e.case.set('Sell Merchant');e.use_class_panel.set(True);e.ready.set(True)
            e.sell_preparation_fixture.set(True);e.sell_cost_fixture.set(False);e.sell_wait_fixture.set(False)
            e.sell_failure_fixture.set(True);e.sell_failure_json.set('invalid JSON not reached yet')
            e.sell_setup_cost.set('0');e.sell_setup_matches.set('0');e.sell_setup_coins.set('0')
            e.reset();e.tick(1);e.tick(1);e.tick(1)
            assert e.merchant.phase==2 and e.merchant.last_sell_failure_plan is None
            assert 'Deneme değeri geçersiz' not in e.output.get('1.0','end')
            e.sell_failure_json.set('{}')
            with patch.object(e,'bank_route_reader',side_effect=AssertionError('early bank input')):
                e.tick(61000)
            assert e.merchant.phase==2 and e.merchant.last_sell_setup_plan.result_dword==1
            assert not e.merchant.last_sell_failure_plan.complete and not r.runner.active
            raw=dict(header_span_returns=[True,True],alarm_byte=0,policy_results=[2,2,2],
                status_byte_90=0,setup_gate_byte=0,branch_span_returns=[True,True])
            e.sell_failure_json.set(json.dumps(raw));e.tick(1)
            assert e.merchant.last_sell_failure_plan.route_plan.ready
            assert not e.merchant.last_sell_failure_plan.complete and e.merchant.phase==2
            assert e.sell_bank_handoff_last is None and not r.runner.active
            raw['route_span_returned']=True;e.sell_failure_json.set(json.dumps(raw));e.tick(1)
            assert e.merchant.phase==0 and e.merchant.restarting
            assert e.sell_bank_handoff_last['local_simulation_started'] and r.runner.active
            assert r.steps[0].seconds==2 and not e.sell_bank_handoff_last['live_compatibility_verified']
            for _ in range(8):
                if not r.runner.active:break
                r.tick(1000)
            assert r.runner.reason=='Tamamlandı'
            # A later failed file import cannot reuse the earlier ready/handoff.
            route_file.unlink()
            raw['setup_gate_byte']=int(e.merchant.setup_seen)
            raw['bank_error_returns']=dict(error_message_returned=True,path_cleanup_returned=True,
                error_stop_returned=True,error_notification_returned=True,error_final_cleanup_returned=True)
            e.sell_failure_json.set(json.dumps(raw))
            for _ in range(4):
                if not e.merchant.active:break
                e.tick(1)
            assert e.merchant.reason=='bank_route_load_failed' and not e.merchant.active
            assert e.sell_bank_handoff_last is None and not r.runner.active
            assert e.merchant.last_sell_failure_plan.route_plan.error_kind=='file_missing'
    finally:
        app.profiles.route_choices=choices;app.profiles.bounds=bounds
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        for v,value in zip(variables,previous):v.set(value)
        r.supply_directory.set(directory);r.source_codepage.set(cp);r.steps=steps;r.stop();r.refresh()
        p.form.set(form);p.bind_document(app.values,app.lists)
        e.use_class_panel.set(panel);e.ready.set(ready);e.case.set(case);e.reset()
