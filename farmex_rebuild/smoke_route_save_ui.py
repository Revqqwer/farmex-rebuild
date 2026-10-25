"""Actual source save button, owned temporary .R files and profile isolation."""
import copy,tempfile
from pathlib import Path
from route_save_runtime import NAME_PATH,BUTTON_PATH,LIST_PATH
from route_panel_runtime import OPEN_PATH
from source_route_ini import read_source_route_ini
from source_route_save import write_source_route_dynamic_calls


def check_source_route_save_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get()
    directory=app.route_page.supply_directory.get();codepage=app.route_page.source_codepage.get()
    context=p.route_save_context_reader;writer=p.route_save_writer;result=p.route_save_result
    geometry=dict(p.route_panel.geometry);visible=p.route_panel.visible;last=p.route_panel.last
    update=p.route_panel_update;queue=p.flood_session.queue
    def name(value):p.variables[NAME_PATH].set(value)
    try:
        with tempfile.TemporaryDirectory() as own_directory:
            app.route_page.supply_directory.set(own_directory);app.route_page.source_codepage.set('1254')
            p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections()
            p.widgets[OPEN_PATH].invoke()
            assert p.widgets[BUTTON_PATH].instate(['!disabled'])
            p.lists[LIST_PATH]=[];name('');p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result.status=='name_required' and not list(Path(own_directory).iterdir())
            name('own route');p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result.status=='empty_rows_preserve'
            own_rows=[{'caption':'Koordinat','subitems':['12.5','-3'],'checked':True},
                      {'caption':'NPC','subitems':['ışık','extra'],'checked':False}]
            p.lists[LIST_PATH]=copy.deepcopy(own_rows);p.render()
            app.route_page.supply_directory.set('');p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result.status=='directory_required'
            app.route_page.supply_directory.set(own_directory)
            path=Path(own_directory)/'own route.R';path.write_bytes(b'[stale]\nobsolete=value\n')
            p.widgets[BUTTON_PATH].invoke();saved=p.route_save_result
            assert saved.status=='write_calls_completed' and saved.write.writes_succeeded
            assert saved.notice_name=='own route' and Path(saved.path)==path
            assert read_source_route_ini(str(path)).rows==((b'Koordinat',b'12.5',b'-3'),(b'NPC',b'\xfd\xfe\xfdk',b'extra'))
            assert b'obsolete' not in path.read_bytes() and len(saved.write.calls)==8
            assert p.lists[LIST_PATH]==own_rows
            data=path.read_bytes();p.render();assert path.read_bytes()==data
            p.lists[LIST_PATH]=[];p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result.status=='empty_rows_preserve' and path.read_bytes()==data
            p.lists[LIST_PATH]=copy.deepcopy(own_rows);name('../outside');p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result.status=='save_incomplete' and path.read_bytes()==data
            name('missing-subitem');p.lists[LIST_PATH]=[{'caption':'Town','subitems':[],'checked':False}]
            p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result.status=='write_incomplete'
            assert not p.route_save_result.write.calls and 'iki ek' in p.route_save_result.error
            p.lists[LIST_PATH]=copy.deepcopy(own_rows);name('failed-bool')
            def bool_failure(path,count,row):
                return write_source_route_dynamic_calls(b'C:\\own-fixture.R',count,row,lambda _:-1,lambda *args:0)
            p.route_save_writer=bool_failure;p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result.status=='write_calls_completed' and not p.route_save_result.write.writes_succeeded
            assert 'doğrulanamadı' in p.list_help.get() and not (Path(own_directory)/'failed-bool.R').exists()
            p.route_save_writer=writer;name('stale-profile')
            def changed_profile():
                ctx=context();p.bind_document(dict(p.values),copy.deepcopy(p.lists));return ctx
            p.route_save_context_reader=changed_profile;p.widgets[BUTTON_PATH].invoke()
            assert p.route_save_result is None and not (Path(own_directory)/'stale-profile.R').exists()
            assert p.flood_session.queue==queue
            print('Source route-save UI passed: actual KAYDET, selected directory/codepage, real ANSI .R replacement/readback, empty/name/directory guards, path confinement, reached row gap, failed BOOL status, rerender and stale-profile isolation; no game actions')
    finally:
        p.route_save_context_reader=context;p.route_save_writer=writer
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last;p.route_panel_update=update
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        app.route_page.supply_directory.set(directory);app.route_page.source_codepage.set(codepage)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.route_save_result=result
