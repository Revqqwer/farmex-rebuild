"""Own selected panel names reach three real configuration consumers."""
from unittest.mock import patch
from route_catalog import ROUTE_COMBO_PATHS
from merchant_configuration import SELL_STOP,STOP

def check_engine_route_inputs(app):
    engine=app.engine_page;panel=app.panel;route=app.route_page
    old_values=dict(app.values);old_choices=dict(app.profiles.route_choices);old_bounds=dict(app.profiles.bounds)
    old_form=panel.form.get();old_case=engine.case.get();old_panel=engine.use_class_panel.get()
    old_cp=route.source_codepage.get();old_scheduler=engine.mining_scheduler_fixture.get()
    try:
        names={'SMerchant':'Satış.R','BMerchant':'Alış.R','Mine':'Maden Ş.R'}
        for kind,name in names.items():app.profiles.install_route_choices(app.values,ROUTE_COMBO_PATHS[kind],(name,))
        app.profiles.update(app.values,SELL_STOP,True);app.profiles.update(app.values,STOP,True)
        panel.form.set('frmMain');panel.render()
        for kind in names:
            w=panel.widgets[ROUTE_COMBO_PATHS[kind]];w.current(0);w.event_generate('<<ComboboxSelected>>')
        engine.use_class_panel.set(True);route.source_codepage.set('1254')
        engine.case.set('Sell Merchant');engine.reset();engine.tick(1)
        assert engine.sell_merchant_compiled.route_text==names['SMerchant']
        assert not any(': GetText' in m for m in engine.sell_merchant_compiled.missing)
        engine.case.set('Buy Merchant');engine.reset();engine.tick(1)
        assert engine.buy_merchant_compiled.route_text==names['BMerchant']
        assert not any(': GetText' in m for m in engine.buy_merchant_compiled.missing)
        engine.case.set('Maden');engine.mining_scheduler_fixture.set(False);engine.reset();engine.tick(1)
        assert engine.mining_compiled.manual_route_ansi==names['Mine'].encode('cp1254')
        assert not engine.mining_frame_last.complete # Known filename does not fill missing game observations.
        route.source_codepage.set('65001');engine.tick(1)
        assert engine.mining_compiled.manual_route_ansi==names['Mine'].encode('utf-8')
        with patch.object(engine,'route_configuration_reader',None):
            engine.case.set('Buy Merchant');engine.reset();engine.tick(1)
            assert engine.buy_merchant_compiled.route_text is None
            assert any(': GetText' in m for m in engine.buy_merchant_compiled.missing)
        engine.use_class_panel.set(False)
        with patch.object(engine,'route_configuration_reader',side_effect=AssertionError('unreached panel read')):
            engine.case.set('Sell Merchant');engine.reset();engine.tick(1)
            assert engine.sell_merchant_compiled is None
    finally:
        app.profiles.route_choices=old_choices;app.profiles.bounds=old_bounds
        app.values.clear();app.values.update(old_values)
        route.source_codepage.set(old_cp);panel.form.set(old_form);panel.render()
        engine.mining_scheduler_fixture.set(old_scheduler)
        engine.use_class_panel.set(old_panel);engine.case.set(old_case);engine.reset()
