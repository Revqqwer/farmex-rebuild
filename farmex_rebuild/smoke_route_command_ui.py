"""Actual source add buttons through own .R save/load roundtrip."""
import copy,tempfile
from route_command_runtime import BUTTON_METHODS,WAIT_PATH
from route_panel_runtime import OPEN_PATH
from route_save_runtime import NAME_PATH,BUTTON_PATH as SAVE_PATH,LIST_PATH
from route_load_runtime import EDITOR_PATH
from panel_ui import SOURCE_ROUTE_CLEAR


def check_source_route_command_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get()
    directory=app.route_page.supply_directory.get();codepage=app.route_page.source_codepage.get()
    metadata=(copy.deepcopy(p.profiles.route_choices),dict(p.profiles.bounds),p.profiles.route_directory,p.profiles.route_codepage)
    geometry=dict(p.route_panel.geometry);visible=p.route_panel.visible;last=p.route_panel.last;update=p.route_panel_update
    results=(p.route_command_result,p.route_save_result,p.route_load_result);catalog=p.route_catalog_last
    queue=p.flood_session.queue
    try:
        with tempfile.TemporaryDirectory() as own_directory:
            app.route_page.supply_directory.set(own_directory);app.route_page.source_codepage.set('1254')
            p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections();p.widgets[OPEN_PATH].invoke()
            p.lists[LIST_PATH]=[dict(caption='existing',subitems=['x','y'],checked=False)];p.render()
            p.widgets[LIST_PATH].selection_set('0')
            for path,method in BUTTON_METHODS.items():
                assert p.widgets[path].instate(['!disabled'])
                if method=='wait':continue
                p.widgets[path].invoke();assert p.route_command_result.complete
            expected=[dict(caption='existing',subitems=['x','y'],checked=False)]+[
                dict(caption=caption,subitems=['-','-'],checked=False) for caption in ('Town','Gate Skill','Otur','Kalk')]
            assert p.lists[LIST_PATH]==expected and p.widgets[LIST_PATH].selection()==('0',)
            assert p.widgets['frmMain/RotaPanel/RadioButton3'].instate(['disabled'])
            wait=next(path for path,method in BUTTON_METHODS.items() if method=='wait')
            p.variables[WAIT_PATH].set('$FFFFFFFFFFFFFFFF');p.widgets[wait].invoke()
            assert p.route_command_result.complete and not p.route_command_result.integer.used_default
            expected.append(dict(caption='Bekle',subitems=['-1','-'],checked=False))
            p.variables[WAIT_PATH].set('invalid');p.widgets[wait].invoke()
            assert p.route_command_result.complete and p.route_command_result.integer.used_default
            expected.append(dict(caption='Bekle',subitems=['5','-'],checked=False))
            assert p.lists[LIST_PATH]==expected
            p.render();assert p.lists[LIST_PATH]==expected and len(p.widgets[LIST_PATH].get_children())==7
            p.variables[NAME_PATH].set('commands');p.widgets[SAVE_PATH].invoke()
            assert p.route_save_result.write.writes_succeeded
            p.widgets[SOURCE_ROUTE_CLEAR].invoke();assert p.lists[LIST_PATH]==[]
            combo=p.widgets[EDITOR_PATH];combo.tk.call(combo.cget('postcommand'))
            combo.current(tuple(combo.cget('values')).index('commands.R'));combo.event_generate('<<ComboboxSelected>>')
            assert p.route_load_result.status=='rows_loaded' and p.lists[LIST_PATH]==expected
            p.bind_document(dict(p.values),copy.deepcopy(p.lists))
            assert p.route_command_result is None and p.lists[LIST_PATH]==expected
            assert p.flood_session.queue==queue
            print('Source route-command UI passed: actual Town/Gate Skill/Otur/Kalk/Bekle buttons, dash placeholders, append despite selected row, disabled insert mode preserved, signed64/default5 own parse, rerender/profile and actual .R save-clear-load roundtrip; no game actions')
    finally:
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last;p.route_panel_update=update
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        app.route_page.supply_directory.set(directory);app.route_page.source_codepage.set(codepage)
        p.profiles.route_choices,p.profiles.bounds,p.profiles.route_directory,p.profiles.route_codepage=metadata
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.route_command_result,p.route_save_result,p.route_load_result=results;p.route_catalog_last=catalog
