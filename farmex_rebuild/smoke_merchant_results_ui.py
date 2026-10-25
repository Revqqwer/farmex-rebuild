"""Hidden own panel exercise; no game handles, accounts or bot runtime."""
from merchant_results_session import KIND_PATH, CATEGORY_PATH, SEARCH_PATH, TABLE_PATH
from merchant_result_rows import MerchantDisplayRecord as D
from merchant_result_filter import MerchantResultRecord as F
from merchant_search_field import PLACEHOLDER,GRAY_TEXT


def check_merchant_results_ui(app):
    panel=app.panel
    original_form=panel.form.get()
    factory=panel.merchant_text_factory;codepage_reader=panel.merchant_codepage_reader
    saved=dict(panel.values)
    saved_lists=__import__('copy').deepcopy(panel.lists)
    try:
        panel.form.set('frmMain');panel.render()
        panel.section.set('Merchant Tarama');panel.select_sections()
        records=(D(F(0,1,20,1,b'SWORD'),'Z','SWORD',2,0xffffffff,3),
                 D(F(0,2,2,1,b'AXE'),'A','AXE',10,1,2),
                 D(F(1,2,1,1,b'AXE'),'Buy','AXE',1,4,5))
        p=panel.accept_merchant_records(records)
        assert p.complete,p.status
        assert panel.values[SEARCH_PATH]==PLACEHOLDER and panel.merchant_search_color==GRAY_TEXT
        table=panel.widgets[TABLE_PATH]
        def captions():return [table.item(i,'values')[0] for i in table.get_children()]
        assert captions()==['Z','A'],captions()
        panel.widgets[SEARCH_PATH].event_generate('<FocusIn>')
        assert panel.values[SEARCH_PATH]=='' and panel.merchant_search_color==0
        assert captions()==['Z','A']
        assert table.item('0','values')[6:] == ('-1','3')
        assert not table.bind('<Double-1>'), 'Result rows must not open generic editable list dialog'
        # Invoke the actual heading Tcl command, not a Python sorting surrogate.
        table.tk.call(table.heading('0','command'))
        assert captions()==['A','Z']
        category=panel.widgets[CATEGORY_PATH]
        category.current(2);category.event_generate('<<ComboboxSelected>>')
        app.root.update()
        assert captions()==['A']
        kind=panel.widgets[KIND_PATH]
        kind.current(1);kind.event_generate('<<ComboboxSelected>>')
        app.root.update()
        assert captions()==['Buy']
        panel.variables[SEARCH_PATH].set('axe')
        assert panel.merchant_result_update.complete and captions()==['Buy']
        assert panel.merchant_result_update.text_observations[0][2].operation=='unicode_query'
        assert panel.merchant_text_policy is not None
        # A supplied missing capture remains missing; it does not silently use
        # the own host policy instead of the requested source observation.
        panel.merchant_search_observer=lambda query:None
        panel.refresh_merchant_results()
        assert not panel.merchant_result_update.complete
        assert panel.merchant_result_update.status=='needs_normalized_search'
        assert captions()==[]
        observations=[]
        def observed(query):
            observations.append(query)
            return b'AXE' if query=='axe' else b'EXPLICIT PLACEHOLDER OBSERVATION'
        panel.merchant_search_observer=observed
        panel.refresh_merchant_results()
        assert observations==['axe'] and captions()==['Buy']
        panel.variables[SEARCH_PATH].set('')
        panel.widgets[SEARCH_PATH].event_generate('<FocusOut>')
        assert panel.values[SEARCH_PATH]==PLACEHOLDER and panel.merchant_search_color==GRAY_TEXT
        # SetText triggers OnChange before SetColor; the explicit exit rebuild
        # then bypasses the placeholder search under gray text.
        assert observations==['axe',PLACEHOLDER],observations
        assert panel.merchant_result_update.complete and captions()==['Buy']
        panel.render()
        table=panel.widgets[TABLE_PATH]
        assert captions()==['Buy'], 'Rerender must preserve session results'
        # Feed the raw reply/metadata chain to the actual table with a display
        # decoder that cannot be used to recover the original ANSI name.
        from dataclasses import replace
        from merchant_item_metadata import project_merchant_scan_with_lookups
        from merchant_result_filter import MerchantFilterSelection
        from merchant_scan_results import MerchantActorMetadata
        from test_merchant_item_metadata import observed,packet
        result=project_merchant_scan_with_lookups(packet(),MerchantActorMetadata('Raw seller',1,2),
            {0:replace(observed(),normalized_final_name=None)},
            MerchantFilterSelection('Buying Merchant','Tümü',GRAY_TEXT),lambda raw:'Different display')
        panel.merchant_search_observer=None
        panel.merchant_codepage_reader=lambda:1254
        category=panel.widgets[CATEGORY_PATH];category.current(0);category.event_generate('<<ComboboxSelected>>')
        panel.accept_merchant_records(tuple(r.display for r in result.results.records))
        panel.widgets[SEARCH_PATH].event_generate('<FocusIn>')
        panel.variables[SEARCH_PATH].set('bow(+7)')
        assert panel.merchant_result_update.complete,panel.merchant_result_update.status
        assert captions()==['Raw seller']
        assert table.item('0','values')[1]=='Different display(+7) (Reverse)'
        assert [o[0] for o in panel.merchant_result_update.text_observations]==['query','name']
        panel.merchant_codepage_reader=lambda:0
        panel.refresh_merchant_results()
        assert not panel.merchant_result_update.complete and captions()==[]
        assert panel.merchant_result_update.status.startswith('local_text_policy:')
        panel.merchant_codepage_reader=lambda:1254
        assert panel.refresh_merchant_results().complete and captions()==['Raw seller']
        assert not p.live_compatibility_verified
        panel.bind_document(dict(saved),saved_lists)
        assert panel.merchant_results.records==()
        assert not panel.widgets[TABLE_PATH].get_children()
        print('Merchant result UI passed: actual filter/focus events, color gate, ordered SetText/SetColor/rebuild, heading sort, own query conversion, raw ANSI metadata names, explicit capture override, invalid-CP recovery and profile reset; no game actions')
    finally:
        panel.merchant_search_observer=None
        panel.merchant_text_factory=factory;panel.merchant_codepage_reader=codepage_reader
        app.values.clear();app.values.update(saved)
        app.lists.clear();app.lists.update(saved_lists)
        panel.form.set(original_form)
        panel.bind_document(app.values,app.lists)


if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_merchant_results_ui(Application(root))
    finally:root.destroy()
