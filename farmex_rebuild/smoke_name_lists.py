"""Hidden own-widget action/profile check; no original app automation."""
import copy,tempfile
from pathlib import Path
from name_list_controls import LIST_PATHS,TEXT_PATHS,ROOT

def check_name_list_ui(app):
    panel=app.panel;old_form=panel.form.get();saved_lists=copy.deepcopy(app.lists);saved_values=dict(app.values)
    saved_documents=dict(panel.name_cfg_documents);saved_kind=panel.name_cfg_kind.get();saved_cp=panel.name_cfg_codepage.get()
    try:
        panel.form.set('frmBlackList');panel.render()
        white,black=(LIST_PATHS[k] for k in ('white','black'))
        for button in ('Button1','Button2'):
            assert 'disabled' not in panel.widgets[ROOT+button].state()
            panel.widgets[ROOT+button].invoke()
        for kind,text,button in (('white','ABC','btnAddTextWhiteList'),('white','ABC','btnAddTextWhiteList'),
                                 ('white','abc','btnAddTextWhiteList'),('black','İsim ŞĞ','btnAddTextBlackList')):
            panel.variables[TEXT_PATHS[kind]].set(text);panel.widgets[ROOT+button].invoke()
        assert [r['caption'] for r in app.lists[white]]==['ABC','abc']
        assert panel.widgets[white].get(0,'end')==('ABC','abc')
        assert [r['caption'] for r in app.lists[black]]==['İsim ŞĞ']
        panel.variables[TEXT_PATHS['white']].set('');panel.widgets[ROOT+'btnAddTextWhiteList'].invoke()
        assert not panel.name_list_result.changed and len(app.lists[white])==2
        panel.widgets[white].selection_set(1)
        assert panel.widgets[white].bind('<Double-1>')
        assert panel.edit_name_control('white','remove')=='break'
        assert panel.widgets[white].get(0,'end')==('ABC',)
        assert [r['caption'] for r in app.lists[black]]==['İsim ŞĞ']
        assert 'disabled' in panel.widgets[ROOT+'btnAddWhiteListTarget'].state()
        assert 'disabled' in panel.widgets[ROOT+'btnAddBlackListTarget'].state()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'own-name-profile.json'
            app.profiles.save(path,app.values,app.lists)
            values,lists=app.profiles.load_document(path)
            assert lists[white]==app.lists[white] and lists[black]==app.lists[black]
            assert values[TEXT_PATHS['black']]=='İsim ŞĞ'
            cfg=Path(directory)/'own-import.cfg';cfg.write_bytes(b'\xef\xbb\xbf'+b'ABC\nABC\n')
            panel.name_cfg_kind.set('Beyaz liste');panel.name_cfg_codepage.set('1254')
            assert panel.import_name_cfg_path(str(cfg)).complete
            assert panel.widgets[white].get(0,'end')==('ABC','ABC')
            assert app.lists[black][0]['caption']=='İsim ŞĞ'
            assert not panel.import_name_cfg_path(str(Path(directory)/'absent.cfg')).complete
            assert app.lists[white]==[] and panel.widgets[white].size()==0
            assert app.lists[black][0]['caption']=='İsim ŞĞ'
            assert panel.import_name_cfg_path(str(cfg)).complete
            out=Path(directory)/'own-export.cfg'
            assert panel.export_name_cfg_path(str(out)).complete
            assert out.read_bytes()==b'\xef\xbb\xbfABC\r\nABC\r\n'
            # Successful clear/edit uses current rows and imported encoding.
            panel.widgets[ROOT+'Button1'].invoke()
            assert panel.export_name_cfg_path(str(out)).complete and out.read_bytes()==b'\xef\xbb\xbf'
        panel.widgets[ROOT+'Button1'].invoke();panel.widgets[ROOT+'Button1'].invoke()
        assert app.lists[white]==[] and panel.widgets[white].size()==0
        assert app.lists[black][0]['caption']=='İsim ŞĞ'
    finally:
        app.values.clear();app.values.update(saved_values)
        app.lists.clear();app.lists.update(saved_lists)
        panel.name_cfg_documents=saved_documents;panel.name_cfg_kind.set(saved_kind);panel.name_cfg_codepage.set(saved_cp)
        panel.form.set(old_form);panel.render()

if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:
        check_name_list_ui(Application(root));print('Hidden name-list widgets/profile: OK')
    finally:root.destroy()
