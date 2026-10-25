"""Actual source combo postcommand/change and own streaming row sink."""
import copy,tempfile
from pathlib import Path
from route_load_runtime import EDITOR_PATH,LIST_PATH
from route_save_runtime import RouteSaveContext
from route_panel_runtime import OPEN_PATH
from name_codec import WindowsNameCodec


def check_source_route_load_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists)
    form=p.form.get();section=p.section.get()
    directory=app.route_page.supply_directory.get();codepage=app.route_page.source_codepage.get()
    metadata=(copy.deepcopy(p.profiles.route_choices),dict(p.profiles.bounds),p.profiles.route_directory,p.profiles.route_codepage)
    factory=p.route_load_reader_factory;context=p.route_save_context_reader
    result=p.route_load_result;save_result=p.route_save_result;catalog=p.route_catalog_last
    geometry=dict(p.route_panel.geometry);visible=p.route_panel.visible;last=p.route_panel.last
    update=p.route_panel_update;queue=p.flood_session.queue
    def refresh():
        combo=p.widgets[EDITOR_PATH];combo.tk.call(combo.cget('postcommand'));return combo
    def select(name):
        combo=p.widgets[EDITOR_PATH];combo.current(tuple(combo.cget('values')).index(name))
        combo.event_generate('<<ComboboxSelected>>')
    try:
        with tempfile.TemporaryDirectory() as own_directory:
            directory_path=Path(own_directory)
            (directory_path/'A.R').write_bytes(b'[Count]\nValue=2\n[ROUTE]\nISLEM0=CustomUnknown\nSub10=\xfd\xfe\xfd\nISLEM1=Bekle\nSub11=5\nSub21=ignored\n')
            (directory_path/'zero.R').write_bytes(b'[Count]\nValue=0\n')
            (directory_path/'negative.R').write_bytes(b'[Count]\nValue=-1\n')
            (directory_path/'missing.R').write_bytes(b'')
            (directory_path/'ignore.r').write_bytes(b'');(directory_path/'.R').write_bytes(b'')
            app.route_page.supply_directory.set(own_directory);app.route_page.source_codepage.set('1254')
            p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections();p.widgets[OPEN_PATH].invoke()
            combo=refresh();choices=tuple(combo.cget('values'))
            assert set(choices)=={'A.R','zero.R','negative.R','missing.R'} and p.values[EDITOR_PATH]==-1
            p.lists[LIST_PATH]=[dict(caption='old',subitems=['keep','old'],checked=True)];p.render()
            (directory_path/'missing.R').unlink()
            old=copy.deepcopy(p.lists[LIST_PATH]);select('missing.R')
            assert p.route_load_result.status=='file_missing_preserve' and p.lists[LIST_PATH]==old
            for file in ('zero.R','negative.R'):
                select(file);assert p.route_load_result.status=='nonpositive_count_preserve' and p.lists[LIST_PATH]==old
            other={k:copy.deepcopy(v) for k,v in p.lists.items() if k!=LIST_PATH}
            select('A.R');loaded=copy.deepcopy(p.lists[LIST_PATH])
            assert p.route_load_result.status=='rows_loaded' and p.route_load_result.completed_rows==2
            assert loaded==[dict(caption='CustomUnknown',subitems=['ışı',''],checked=False),
                            dict(caption='Bekle',subitems=['5','ignored'],checked=False)]
            assert tuple(p.widgets[LIST_PATH].item('0','values'))==('CustomUnknown','ışı','')
            p.render();assert p.lists[LIST_PATH]==loaded and p.widgets[EDITOR_PATH].get()=='A.R'
            p.bind_document(dict(p.values),copy.deepcopy(p.lists))
            assert p.route_load_result is None and p.lists[LIST_PATH]==loaded and p.widgets[EDITOR_PATH].get()=='A.R'
            class PrefixReader:
                def __init__(self,path):pass
                def exists(self):return True
                def count(self):return 2
                def value(self,index,prefix):
                    if index==1:raise OSError('own later read failure')
                    return {b'ISLEM':b'Town',b'Sub1':b'1',b'Sub2':b'2'}[prefix]
            p.route_load_reader_factory=PrefixReader;select('A.R')
            assert p.route_load_result.status=='load_incomplete' and p.route_load_result.completed_rows==1
            assert p.lists[LIST_PATH]==[dict(caption='Town',subitems=['1','2'],checked=False)]
            class FailingCodec(WindowsNameCodec):
                def decode(self,value):
                    if value==b'2':raise ValueError('own second subitem conversion gap')
                    return super().decode(value)
            class PartialReader(PrefixReader):
                def count(self):return 1
            p.route_load_reader_factory=PartialReader
            p.route_save_context_reader=lambda:RouteSaveContext(own_directory,FailingCodec(1254))
            select('A.R')
            assert p.route_load_result.phase=='sub2_0' and p.lists[LIST_PATH]==[dict(caption='Town',subitems=['1'],checked=False)]
            assert tuple(p.widgets[LIST_PATH].item('0','values'))==('Town','1')
            p.route_save_context_reader=context
            class ChangedProfileReader(PrefixReader):
                def exists(self):p.bind_document(dict(p.values),copy.deepcopy(p.lists));return True
            before=copy.deepcopy(p.lists[LIST_PATH]);p.route_load_reader_factory=ChangedProfileReader;select('A.R')
            assert p.route_load_result is None and p.lists[LIST_PATH]==before
            p.route_load_reader_factory=factory
            empty=directory_path/'empty';empty.mkdir();app.route_page.supply_directory.set(str(empty))
            combo=refresh();assert tuple(combo.cget('values'))==('Rota Seciniz !',)
            select('Rota Seciniz !');assert p.route_load_result.status=='file_missing_preserve' and p.lists[LIST_PATH]==before
            assert {k:v for k,v in p.lists.items() if k!=LIST_PATH}==other and p.flood_session.queue==queue
            print('Source route-load UI passed: actual combo postcommand/change, exact .R choices, real ANSI rows/unknown commands, missing/zero/negative preserve, clear/add row order, partial read/conversion prefixes, rerender/profile/stale isolation and empty placeholder; no game actions')
    finally:
        p.route_load_reader_factory=factory;p.route_save_context_reader=context
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last;p.route_panel_update=update
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        app.route_page.supply_directory.set(directory);app.route_page.source_codepage.set(codepage)
        p.profiles.route_choices,p.profiles.bounds,p.profiles.route_directory,p.profiles.route_codepage=metadata
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.route_load_result=result;p.route_save_result=save_result;p.route_catalog_last=catalog
