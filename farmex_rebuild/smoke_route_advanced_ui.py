"""Actual camp/speed radio and add buttons, persisted through own .R file."""
import copy,tempfile
from route_command_runtime import (ADVANCED_BUTTON_METHODS,CAMP_RANDOM,CAMP_MANUAL,CAMP_TEXT,SPEED_FLAGS)
from route_panel_runtime import OPEN_PATH
from route_save_runtime import NAME_PATH,BUTTON_PATH as SAVE_PATH,LIST_PATH
from route_load_runtime import EDITOR_PATH
from panel_ui import SOURCE_ROUTE_CLEAR


def check_source_route_advanced_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get();section=p.section.get()
    directory=app.route_page.supply_directory.get();codepage=app.route_page.source_codepage.get()
    metadata=(copy.deepcopy(p.profiles.route_choices),dict(p.profiles.bounds),p.profiles.route_directory,p.profiles.route_codepage)
    geometry=dict(p.route_panel.geometry);visible=p.route_panel.visible;last=p.route_panel.last;update=p.route_panel_update
    results=(p.route_command_result,p.route_save_result,p.route_load_result);catalog=p.route_catalog_last;queue=p.flood_session.queue
    buttons={method:path for path,method in ADVANCED_BUTTON_METHODS.items()}
    def add(method,caption,first):
        p.widgets[buttons[method]].invoke();assert p.route_command_result.complete
        expected.append(dict(caption=caption,subitems=[first,'-'],checked=False))
        assert p.lists[LIST_PATH]==expected
    try:
        with tempfile.TemporaryDirectory() as own_directory:
            app.route_page.supply_directory.set(own_directory);app.route_page.source_codepage.set('1254')
            p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections();p.widgets[OPEN_PATH].invoke()
            p.lists[LIST_PATH]=[];p.render();expected=[]
            for path in buttons.values():assert p.widgets[path].instate(['!disabled'])
            p.widgets[CAMP_RANDOM].invoke();add('camp','Change Camp','Randomize')
            p.widgets[CAMP_MANUAL].invoke();p.variables[CAMP_TEXT].set('$100000000');add('camp','Change Camp','Randomize')
            p.variables[CAMP_TEXT].set('$FFFFFFFF');add('camp','Change Camp','-1')
            p.variables[CAMP_TEXT].set('invalid');add('camp','Change Camp','1')
            assert p.route_command_result.integer.used_default
            for path,number in zip(SPEED_FLAGS,('0','1','3')):
                p.widgets[path].invoke();add('speed','Change Speed Hack',number)
            for path in SPEED_FLAGS:p.apply_boolean_updates({path:False})
            add('speed','Change Speed Hack','0')
            p.render();assert p.lists[LIST_PATH]==expected
            p.variables[NAME_PATH].set('advanced');p.widgets[SAVE_PATH].invoke();assert p.route_save_result.write.writes_succeeded
            p.widgets[SOURCE_ROUTE_CLEAR].invoke();assert p.lists[LIST_PATH]==[]
            combo=p.widgets[EDITOR_PATH];combo.tk.call(combo.cget('postcommand'))
            combo.current(tuple(combo.cget('values')).index('advanced.R'));combo.event_generate('<<ComboboxSelected>>')
            assert p.route_load_result.status=='rows_loaded' and p.lists[LIST_PATH]==expected
            p.bind_document(dict(p.values),copy.deepcopy(p.lists));assert p.route_command_result is None and p.lists[LIST_PATH]==expected
            assert p.flood_session.queue==queue
            print('Source route-advanced UI passed: actual camp/speed radios and add buttons, Randomize/lowDWORD/signed32/default1, speed0/1/3/none, rerender/profile and actual .R save-clear-load roundtrip; command data only, no game actions')
    finally:
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last;p.route_panel_update=update
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        app.route_page.supply_directory.set(directory);app.route_page.source_codepage.set(codepage)
        p.profiles.route_choices,p.profiles.bounds,p.profiles.route_directory,p.profiles.route_codepage=metadata
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.route_command_result,p.route_save_result,p.route_load_result=results;p.route_catalog_last=catalog
