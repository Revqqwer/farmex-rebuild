"""Actual own save button -> own temporary file, no live identity provider."""
import copy,tempfile
from pathlib import Path
from merchant_txt_export import OwnedExportContext,BUTTON_PATH
from merchant_result_rows import MerchantDisplayRecord as D
from merchant_result_filter import MerchantResultRecord as F
from merchant_results_session import KIND_PATH,CATEGORY_PATH,TABLE_PATH,SEARCH_PATH
from merchant_txt_format import build_txt_header
from name_codec import WindowsNameCodec


def check_merchant_txt_export_ui(app):
    p=app.panel;saved=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get()
    provider=p.merchant_export_context_provider
    try:
        p.form.set('frmMain');p.render();p.section.set('Merchant Tarama');p.select_sections()
        p.widgets[KIND_PATH].current(0);p.widgets[KIND_PATH].event_generate('<<ComboboxSelected>>')
        p.widgets[CATEGORY_PATH].current(0);p.widgets[CATEGORY_PATH].event_generate('<<ComboboxSelected>>')
        p.accept_merchant_records((D(F(0,1,1,1,b'ITEM'),'Z','Item',1000,825,520),
                                   D(F(0,1,2,1,b'ITEM'),'A','Item',10,1,2),
                                   D(F(1,1,1,1,b'ITEM'),'Buy','Item',1,4,5)))
        p.merchant_export_context_provider=None
        p.widgets[BUTTON_PATH].invoke()
        assert p.merchant_export_result.status=='needs_export_context'
        assert not p.merchant_export_result.file_opened
        assert 'bağlamı bekleniyor' in p.list_help.get()
        with tempfile.TemporaryDirectory() as directory:
            calls=[]
            def context():
                calls.append(True)
                return OwnedExportContext(directory,b'Own fixture',(3,2,1,4,0,126,0,0,0),1254,1254)
            p.merchant_export_context_provider=context
            table=p.widgets[TABLE_PATH]
            table.tk.call(table.heading('0','command'))
            assert [r.caption for r in p.merchant_result_update.rows]==['A','Z']
            p.widgets[BUTTON_PATH].invoke()
            receipt=p.merchant_export_result
            assert receipt.complete,receipt
            assert receipt.rows_written==2 and receipt.file_closed
            data=Path(receipt.path).read_bytes()
            expected_header=WindowsNameCodec(1254).encode(build_txt_header(
                p.profiles.combo_text(p.values,KIND_PATH),p.profiles.combo_text(p.values,CATEGORY_PATH),p.values[SEARCH_PATH]))[0]
            assert data.startswith(expected_header.replace(b'\n',b'\r\n'))
            assert data.index(b'Sat\xfdc\xfd : A')<data.index(b'Sat\xfdc\xfd : Z')
            assert b'Buy' not in data and b'825' not in data
            assert len(data)==receipt.bytes_written and calls==[True]
            assert 'TXT kaydedildi' in p.list_help.get()
            # Source export uses the current displayed list, so a manually
            # stale view must not silently export a different cached snapshot.
            values=list(table.item('0','values'));values[0]='stale';table.item('0',values=values)
            p.widgets[BUTTON_PATH].invoke()
            assert p.merchant_export_result is None and calls==[True]
            assert Path(receipt.path).read_bytes()==data
            p.paint_merchant_results()
            p.render();assert p.merchant_export_context_provider is context
            p.widgets[BUTTON_PATH].invoke()
            assert p.merchant_export_result.complete and calls==[True,True]
            p.bind_document(app.values,app.lists)
            assert p.merchant_export_context_provider is None and p.merchant_export_result is None
        print('Merchant TXT UI passed: actual save command, missing-context gate, displayed filter/order to own file, stale-row rejection, rerender and profile invalidation')
    finally:
        app.values.clear();app.values.update(saved);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.bind_document(app.values,app.lists)
        p.merchant_export_context_provider=provider
