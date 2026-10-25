"""Actual own Tara command with explicit captured-value fixtures, not a game."""
import copy
from dataclasses import replace
from merchant_quick_scan import QuickActorObservation as A,QuickItemObservation as M
from merchant_quick_table import QuickScanSnapshot
from merchant_quick_source import QuickSourceSnapshot
from merchant_scan_runtime import QUICK_PATH,START_PATH,STOP_PATH
from merchant_results_session import KIND_PATH,CATEGORY_PATH,SEARCH_PATH,TABLE_PATH
from merchant_result_rows import MerchantDisplayRecord as D
from merchant_result_filter import MerchantResultRecord as F


def check_merchant_quick_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get()
    provider=p.merchant_quick_provider;cp=p.merchant_codepage_reader
    try:
        p.form.set('frmMain');p.render();p.section.set('Merchant Tarama');p.select_sections()
        p.merchant_codepage_reader=lambda:1254
        for path in (KIND_PATH,CATEGORY_PATH):
            p.widgets[path].current(0);p.widgets[path].event_generate('<<ComboboxSelected>>')
        p.accept_merchant_records((D(F(0,1,1,1,b'OLD'),'Old','Old',1,1,1),))
        assert p.widgets[QUICK_PATH].instate(['!disabled'])
        p.merchant_quick_provider=None;p.widgets[QUICK_PATH].invoke()
        assert p.merchant_quick_result.status=='needs_quick_scan_provider'
        assert not p.widgets[TABLE_PATH].get_children() and p.merchant_results.records==()
        assert p.merchant_result_update is None
        assert 'veri bağlantısı gerekli' in p.list_help.get()
        actor=A(pointer=0x1000,active_eax=1,buy_first_eax=0,buy_second_eax=0,entity_id_eax=7,
                x_ftol_eax=0xffffffff,y_ftol_eax=520,seller_ansi=b'Sat\xfdc\xfd',slot_base_word=0x100,
                slot_ids=(10,11,0,0),items={0:M(2,1,15,b'K\xfdl\xfdc'),1:M(1,2,2,b'EXT')})
        p.merchant_quick_provider=lambda:QuickScanSnapshot({1:actor},1254)
        p.widgets[QUICK_PATH].invoke()
        assert not p.merchant_quick_result.complete
        assert len(p.merchant_quick_result.quick_values.records)==2
        assert not p.widgets[TABLE_PATH].get_children() and p.merchant_result_update is None
        data={i:A(pointer=0) for i in range(1,5001)};data[1]=actor
        data[2]=replace(actor,buy_first_eax=1,buy_second_eax=1,slot_ids=(20,0,0,0),items={0:M(0,1,0,b'Buy')})
        calls=[]
        def captured():calls.append(True);return QuickScanSnapshot(data,1254)
        p.merchant_quick_provider=captured
        p.merchant_scan.state=replace(p.merchant_scan.state,busy_byte_0f=9)
        before=p.merchant_scan.state;p.widgets[QUICK_PATH].invoke()
        assert p.merchant_quick_result.complete and p.merchant_result_update.complete
        assert p.merchant_scan.state==before,'Quick scan does not reset scan lifecycle fields'
        rows=p.merchant_result_update.rows
        assert {r.subitems[0] for r in rows}=={'Kılıc(+5)','EXT'}
        assert all(r.caption=='Satıcı' and r.subitems[1:3]==('0','0') for r in rows)
        assert all(r.subitems[5:]==('-1','520') for r in rows)
        assert len(p.merchant_results.records)==3 and calls==[True]
        p.widgets[CATEGORY_PATH].current(1);p.widgets[CATEGORY_PATH].event_generate('<<ComboboxSelected>>')
        assert len(p.merchant_result_update.rows)==1
        assert p.merchant_result_update.rows[0].subitems[0]=='Kılıc(+5)'
        p.widgets[CATEGORY_PATH].current(0);p.widgets[CATEGORY_PATH].event_generate('<<ComboboxSelected>>')
        p.widgets[SEARCH_PATH].event_generate('<FocusIn>');p.variables[SEARCH_PATH].set('EXT')
        assert p.merchant_result_update.complete and len(p.merchant_result_update.rows)==1
        assert p.merchant_result_update.rows[0].subitems[0]=='EXT'
        p.render();assert p.merchant_quick_provider is captured and len(p.merchant_result_update.rows)==1
        p.widgets[START_PATH].invoke()
        assert p.widgets[QUICK_PATH].instate(['disabled'])
        p.widgets[STOP_PATH].invoke();assert p.widgets[QUICK_PATH].instate(['!disabled'])
        p.widgets[QUICK_PATH].invoke();assert p.merchant_quick_result.complete and len(calls)==2
        # Lower-level captured lookups, read values and exact memcpy ranges
        # must also reach the actual button without hand-built final names.
        from test_merchant_quick_source import actor as source_actor,all_sources
        source_data=all_sources();source_data[1]=source_actor()
        p.variables[SEARCH_PATH].set('')
        p.merchant_quick_provider=lambda:QuickSourceSnapshot(source_data,1254)
        p.widgets[QUICK_PATH].invoke()
        produced=p.merchant_quick_result
        assert produced.complete and produced.source_production.complete
        assert p.merchant_result_update.complete and len(p.merchant_result_update.rows)==1
        assert p.merchant_result_update.rows[0].subitems[0]=='Bow(+5)'
        assert produced.source_production.actor_plans[0][1].item_plans[0][1].text_copy.ansi_bytes==b'Bow'
        assert p.merchant_results.records[0].filter_record.original_name_ansi==b'Bow(+5)'
        assert not produced.source_helper_returns_verified
        p.bind_document(app.values,app.lists)
        assert p.merchant_quick_provider is None and p.merchant_quick_result is None
        print('Merchant quick UI passed: actual Tara command, clear-before-provider, unknown lookup hold, four-cache records, explicit CP, filter/search, source lookup/copy producer, scan button gates and profile invalidation; no game provider')
    finally:
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.bind_document(app.values,app.lists)
        p.merchant_quick_provider=provider;p.merchant_codepage_reader=cp
