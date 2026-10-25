"""Actual own widgets/profile roundtrip, hidden without changing foreground."""
import copy,tempfile
from pathlib import Path
from flood_editor import *

def check_flood_editor(app):
    panel=app.panel;old_values=dict(app.values);old_lists=copy.deepcopy(app.lists);form=panel.form.get()
    codepage_reader=panel.flood_codepage_reader;codec_factory=panel.flood_codec_factory
    try:
        panel.flood_codepage_reader=lambda:1254
        panel.form.set('frmMain');panel.render()
        def click(action):
            path=next(p for p,a in BUTTON_ACTIONS.items() if a==action)
            widget=panel.widgets[path];assert not widget.instate(['disabled'])
            widget.invoke();return panel.flood_edit_result
        def text(path,value):
            panel.variables[path].set(value);assert app.values[path]==value
        assert click('clear').rows==()
        assert panel.current_flood_compilation().complete and panel.current_flood_compilation().rows==()
        combo=panel.widgets[CHANNEL_PATH];combo.current(1);combo.event_generate('<<ComboboxSelected>>')
        assert app.values[CHANNEL_PATH]==1
        text(MESSAGE_PATH,'Türkçe mesaj');text(DELAY_PATH,'4')
        assert click('add').status=='delay_rejected';assert app.lists[LIST_PATH]==[]
        text(DELAY_PATH,'4294967301');result=click('add')
        assert result.status=='added' and len(result.rows)==1
        table=panel.widgets[LIST_PATH]
        assert app.lists[LIST_PATH]==[dict(caption='Party',subitems=['Türkçe mesaj','5'],checked=False)]
        assert table.item('0','values')==('Party','Türkçe mesaj','5')
        compiled=panel.current_flood_compilation()
        assert compiled.complete and compiled.code_page==1254
        assert compiled.rows[0].channel_bytes==b'Party'
        assert compiled.rows[0].message_bytes=='Türkçe mesaj'.encode('cp1254') and compiled.rows[0].delay_dword==5000
        # Duplicate and empty source rows were not rejected by add-body code.
        text(MESSAGE_PATH,'');text(DELAY_PATH,'5');assert click('add').status=='added'
        assert len(app.lists[LIST_PATH])==2
        table.selection_remove(*table.selection());assert click('selected').status=='no_selection'
        table.selection_set('0');assert click('selected').status=='removed'
        assert app.lists[LIST_PATH][0]['subitems']==['','5']
        text(DELAY_PATH,'$10');assert click('add').status=='added'
        assert app.lists[LIST_PATH][-1]['subitems']==['','16']
        text(DELAY_PATH,'123z');assert click('add').status=='added'
        assert app.lists[LIST_PATH][-1]['subitems']==['','10']
        assert panel.current_flood_compilation().rows[-1].delay_dword==10000
        text(DELAY_PATH,'5 ');assert click('add').status=='added'
        assert app.lists[LIST_PATH][-1]['subitems']==['','10']
        # Load binds new document objects and discards the prior action result.
        with tempfile.TemporaryDirectory() as folder:
            profile=Path(folder)/'flood.json';app.profiles.save(profile,app.values,app.lists)
            assert click('clear').status=='cleared'
            values,lists=app.profiles.load_document(profile)
            app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
            panel.bind_document(app.values,app.lists)
            assert panel.flood_edit_result is None
            assert panel.current_flood_compilation().complete
            assert panel.widgets[LIST_PATH].item('0','values')==('Party','','5')
            assert click('clear').status=='cleared';assert click('clear').status=='already_empty'
        # External mutation cannot expose the previous sidecar as current.
        app.lists[LIST_PATH].append(dict(caption='Clan',subitems=['fresh','5'],checked=True))
        assert panel.current_flood_compilation() is None
        assert panel.compile_current_flood().rows[0].message_bytes==b'fresh'
        panel.flood_codepage_reader=lambda:65001
        assert panel.current_flood_compilation() is None
        assert panel.compile_current_flood().code_page==65001
        app.lists[LIST_PATH].append(dict(caption='Party',subitems=['missing'],checked=False))
        incomplete=panel.compile_current_flood()
        assert not incomplete.complete and len(incomplete.rows)==1
        # Worker/selected-chat/toggle actions remain unbound.
        assert not panel.widgets[PREFIX+'btnChatSelected'].instate(['disabled'])
        assert not panel.widgets[PREFIX+'btnAutoFlood'].instate(['disabled'])
        assert not panel.flood_session.state.enabled
        print('Flood editor UI passed:3 actual buttons,3 inputs,list mutation/selection,RTL scalar parser and fallback10,profile roundtrip; no worker/game actions')
        print('Flood compilation UI passed:actual list -> explicit Windows codepage byte rows,stale rejection,prefix failure,profile recompile; no native vector/game send')
    finally:
        app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
        panel.flood_codepage_reader=codepage_reader;panel.flood_codec_factory=codec_factory
        panel.form.set(form);panel.bind_document(app.values,app.lists)

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_flood_editor(Application(root))
    finally:root.destroy()
