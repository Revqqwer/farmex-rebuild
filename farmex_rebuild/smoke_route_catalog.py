"""Own hidden UI route directory -> combo -> profile -> local .R import."""
import copy,tempfile
from pathlib import Path
from route_catalog import ROUTE_COMBO_PATHS,RouteCatalogEntry,plan_route_catalog
from dataclasses import replace
from profiles import Profiles
from unittest.mock import patch
from route_ui import ROUTE_KIND_LABELS

def check_route_catalog_ui(app):
    panel=app.panel;route=app.route_page
    old_values=dict(app.values);old_lists=copy.deepcopy(app.lists)
    old_choices=dict(app.profiles.route_choices);old_bounds=dict(app.profiles.bounds)
    old_directory=route.supply_directory.get();old_form=panel.form.get()
    old_codepage=route.source_codepage.get();old_binding=route.use_panel_route_text.get();old_kind=route.supply_kind.get()
    old_steps=list(route.steps);old_help=panel.list_help.get();old_status=route.status.get()
    try:
        with tempfile.TemporaryDirectory() as directory:
            for name,wait in (('one.R',1),('İsim.R',2)):
                (Path(directory)/name).write_bytes(('[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=%d\n'%wait).encode('ascii'))
            (Path(directory)/'ignored.r').write_bytes(b'')
            route.supply_directory.set(directory);route.source_codepage.set('1254');route.use_panel_route_text.set(True)
            panel.form.set('frmMain');panel.render()
            for kind in ROUTE_COMBO_PATHS:
                label=next(label for label,value in ROUTE_KIND_LABELS.items() if value==kind)
                filename='İsim.R' if kind=='supply' else 'one.R'
                path=ROUTE_COMBO_PATHS[kind];catalog=panel.refresh_route_combo(path)
                assert catalog.complete and set(catalog.rows)=={'one.R','İsim.R'}
                w=panel.widgets[path];assert w['postcommand'] and w.current()==-1
                w.current(catalog.rows.index(filename));w.event_generate('<<ComboboxSelected>>');app.root.update_idletasks()
                assert panel.combo_texts()[path]==filename
                route.supply_kind.set(label)
                result=route.load_panel_route()
                assert result.ready and result.choice.filename==filename.encode('cp1254')
                assert route.steps[0].seconds==(2 if kind=='supply' else 1)
            route.source_codepage.set('65001')
            profile=Path(directory)/'own.json';app.profiles.save(profile,app.values,app.lists)
            other=Profiles(app.catalog);values,lists=other.load_document(profile)
            assert other.combo_text(values,ROUTE_COMBO_PATHS['supply'])=='İsim.R'
            assert other.combo_text(values,ROUTE_COMBO_PATHS['return'])=='one.R'
            assert all(other.combo_text(values,ROUTE_COMBO_PATHS[k])=='one.R' for k in ROUTE_COMBO_PATHS if k!='supply')
            assert other.route_directory==directory
            # Real rendering after loading must use persisted choices, not DFM's sole placeholder.
            route.source_codepage.set('1254')
            with patch('app.filedialog.askopenfilename',return_value=str(profile)):app.load()
            assert panel.widgets[ROUTE_COMBO_PATHS['supply']].get()=='İsim.R'
            assert all(panel.widgets[ROUTE_COMBO_PATHS[k]].get()=='one.R' for k in ROUTE_COMBO_PATHS if k!='supply')
            assert route.source_codepage.get()=='65001' and route.supply_directory.get()==directory
            path=ROUTE_COMBO_PATHS['supply'];old=app.profiles.combo_items(path)
            route.supply_directory.set(str(Path(directory)/'missing'))
            failed=panel.refresh_route_combo(path)
            assert failed.complete and not failed.enumeration_verified and failed.failed_operation=='scandir_open'
            assert app.profiles.combo_items(path)==('Rota Seciniz !',) and app.values[path]==-1
            assert app.profiles.combo_items(path)!=old and 'açılamadı' in panel.list_help.get()
            partial=replace(plan_route_catalog((RouteCatalogEntry(b'one.R','one.R',True),),
                enumeration_complete=False,terminal_reason='read_stopped'),
                failed_operation='scandir_next',local_error='owned read-error fixture')
            with patch.object(panel,'route_catalog_reader',return_value=partial):
                assert panel.refresh_route_combo(path) is partial
                assert app.profiles.combo_items(path)==('one.R',) and app.values[path]==-1
                assert 'Tarama kesildi' in panel.list_help.get() and not panel.route_catalog_last.enumeration_verified
            route.supply_directory.set(directory);panel.refresh_route_combo(path)
            assert app.values[path]==-1 and panel.combo_texts()[path]==''
            before=app.profiles.combo_items(path)
            with patch.object(panel,'route_catalog_reader',side_effect=ValueError('unresolved conversion')):
                assert panel.refresh_route_combo(path) is None and panel.route_catalog_last is None
                assert app.profiles.combo_items(path)==before
            route.supply_kind.set('Tedarik');assert route.load_panel_route().stop_required
    finally:
        app.profiles.route_choices=old_choices;app.profiles.bounds=old_bounds
        app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
        route.supply_directory.set(old_directory);route.source_codepage.set(old_codepage)
        route.use_panel_route_text.set(old_binding);route.supply_kind.set(old_kind)
        route.steps=old_steps;route.refresh();panel.form.set(old_form);panel.bind_document(app.values,app.lists)
        panel.list_help.set(old_help);route.status.set(old_status)
