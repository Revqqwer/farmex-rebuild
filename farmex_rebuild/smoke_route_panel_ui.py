"""Actual shared route-panel open/close; Draki design remains disabled."""
import copy
from route_panel_runtime import OPEN_PATH,CLOSE_PATH,PANEL_PATH,TABS_PATH,GATES_PATH
from panel_ui import SOURCE_ROUTE_LIST,SOURCE_ROUTE_CLEAR,SOURCE_ROUTE_DELETE


def check_source_route_panel_ui(app):
    p=app.panel;values=dict(p.values);lists=copy.deepcopy(p.lists)
    form=p.form.get();section=p.section.get()
    geometry=dict(p.route_panel.geometry);visible=p.route_panel.visible;last=p.route_panel.last
    update=p.route_panel_update;queue=p.flood_session.queue
    list_result=p.route_list_edit_result
    def actual():
        info=p.widgets[PANEL_PATH].place_info()
        return tuple(int(info[k]) for k in ('x','y','height','width'))
    try:
        p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections()
        assert p.widgets[OPEN_PATH].instate(['!disabled'])
        tabs=p.widgets[TABS_PATH].place_info()
        p.widgets[OPEN_PATH].invoke()
        assert p.route_panel_update.complete
        assert actual()==(int(tabs['x']),int(tabs['y'])+20,int(tabs['height'])-20,600)
        assert p.widgets[CLOSE_PATH].instate(['!disabled'])
        if not p.values[GATES_PATH]:p.widgets[GATES_PATH].invoke()
        assert p.values[GATES_PATH] is True
        p.widgets[CLOSE_PATH].invoke()
        assert p.route_panel_update.complete and p.route_panel_update.recording_reset
        assert p.values[GATES_PATH] is False and p.variables[GATES_PATH].get() is False
        assert not p.widgets[PANEL_PATH].place_info()
        p.widgets[TABS_PATH].place_configure(x=317,y=11,height=510,width=700)
        p.widgets[OPEN_PATH].invoke();assert actual()==(317,31,490,600)
        p.render();assert actual()==(317,31,490,600)
        own_rows=[{'caption':'Town','subitems':['0','0'],'checked':True},
            {'caption':'Town','subitems':['0','0'],'checked':True},
            {'caption':'Bekle','subitems':['5','0'],'checked':False}]
        p.lists[SOURCE_ROUTE_LIST]=copy.deepcopy(own_rows);p.render()
        untouched={k:copy.deepcopy(v) for k,v in p.lists.items() if k!=SOURCE_ROUTE_LIST}
        table=p.widgets[SOURCE_ROUTE_LIST]
        assert p.widgets[SOURCE_ROUTE_CLEAR].instate(['!disabled'])
        assert p.widgets[SOURCE_ROUTE_DELETE].instate(['!disabled'])
        p.widgets[SOURCE_ROUTE_DELETE].invoke()
        assert p.route_list_edit_result['status']=='unchanged' and p.lists[SOURCE_ROUTE_LIST]==own_rows
        table.selection_set('1');p.widgets[SOURCE_ROUTE_DELETE].invoke()
        expected=[own_rows[0],own_rows[2]]
        assert p.lists[SOURCE_ROUTE_LIST]==expected and len(table.get_children())==2
        assert tuple(table.item('1','values'))==('Bekle','5','0')
        assert p.route_list_edit_result['removed']==1 and not table.selection()
        p.render();table=p.widgets[SOURCE_ROUTE_LIST]
        assert p.lists[SOURCE_ROUTE_LIST]==expected and len(table.get_children())==2
        table.selection_set('1');p.widgets[SOURCE_ROUTE_DELETE].invoke()
        assert p.lists[SOURCE_ROUTE_LIST]==[own_rows[0]] and tuple(table.get_children())==('0',)
        p.widgets[CLOSE_PATH].invoke();p.widgets[OPEN_PATH].invoke()
        assert p.lists[SOURCE_ROUTE_LIST]==[own_rows[0]]
        p.widgets[SOURCE_ROUTE_CLEAR].invoke()
        assert p.lists[SOURCE_ROUTE_LIST]==[] and not p.widgets[SOURCE_ROUTE_LIST].get_children()
        assert p.route_list_edit_result['removed']==1
        p.widgets[SOURCE_ROUTE_CLEAR].invoke();assert p.route_list_edit_result['status']=='unchanged'
        p.render();assert p.lists[SOURCE_ROUTE_LIST]==[] and not p.widgets[SOURCE_ROUTE_LIST].get_children()
        assert {k:v for k,v in p.lists.items() if k!=SOURCE_ROUTE_LIST}==untouched
        expected_bounds=actual()
        p.section.set('MS - Draki');p.select_sections()
        prefix='frmMain/MainTab/sheetMSDraki/GroupBox16/'
        disabled=[n for n in p.catalog if n['path'].startswith(prefix) and n['class'] in
            ('TCheckBox','TRadioButton','TEdit','TComboBox','TButton')]
        assert len(disabled)==16
        for node in disabled:assert p.widgets[node['path']].instate(['disabled']),node['path']
        prior=p.route_panel_update
        p.widgets[prefix+'GroupBox64/Button17'].invoke()
        assert p.route_panel_update is prior and actual()==expected_bounds
        p.widgets[CLOSE_PATH].invoke()
        assert not p.widgets[PANEL_PATH].place_info()
        p.bind_document(dict(p.values),copy.deepcopy(p.lists))
        assert not p.widgets[PANEL_PATH].place_info()
        assert p.lists[SOURCE_ROUTE_LIST]==[] and p.route_list_edit_result is None
        assert p.flood_session.queue==queue
        print('Source route-panel UI passed: actual Koruma shared open, fresh MainTab geometry/order, width600, gate checkbox reset before close, rerender overlay, all16 Draki controls disabled and disabled route button inert; no route drawing or game actions')
        print('Source route-list edits UI passed: actual clear/delete buttons, no selection no-op, duplicate-row identity, refreshed row indices, checked/subitems preserved, close/open/rerender/profile persistence, empty clear and other lists/queue unchanged; no route file/game actions')
    finally:
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last
        p.route_panel_update=update
        app.values.clear();app.values.update(values)
        app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.route_list_edit_result=list_result
