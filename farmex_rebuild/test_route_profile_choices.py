import copy,json,tempfile,unittest
from pathlib import Path
from profiles import Profiles
from route_catalog import ROUTE_COMBO_PATHS,read_local_route_catalog
from name_codec import WindowsNameCodec
from route_load_runtime import EDITOR_PATH

class RouteProfileChoicesTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads(Path(__file__).with_name('ui_model.json').read_text(encoding='utf-8'))
        self.p=Profiles(self.catalog);self.values=dict(self.p.defaults)
        self.supply=ROUTE_COMBO_PATHS['supply'];self.returning=ROUTE_COMBO_PATHS['return']
    def install(self):
        self.p.install_route_choices(self.values,self.supply,('B.R','İsim.R','B.R'))
        self.p.update(self.values,self.supply,1)
    def test_dynamic_selection_is_bound_to_actual_items(self):
        self.install();self.assertEqual(self.p.combo_text(self.values,self.supply),'İsim.R')
        self.assertEqual(self.p.combo_items(self.supply),('B.R','İsim.R','B.R'))
        self.assertEqual(self.p.combo_items(self.returning),('Rota Seciniz !',))
        with self.assertRaises(ValueError):self.p.update(self.values,self.supply,3)
    def test_codepage_only_profile_persists_without_choices_or_directory(self):
        self.p.route_codepage=65001
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cp.json';self.p.save(path,self.values)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['version'],3)
            other=Profiles(self.catalog);values,_=other.load_document(path)
        self.assertEqual(other.route_codepage,65001);self.assertEqual(other.route_choices,{})
        self.assertEqual(values,self.values)
    def test_refresh_resets_selection_and_preserves_other_combo(self):
        self.install();identity=id(self.values)
        self.p.install_route_choices(self.values,self.supply,('new.R',))
        self.assertEqual(self.values[self.supply],-1);self.assertEqual(self.p.combo_text(self.values,self.supply),'')
        self.assertEqual(self.values[self.returning],0);self.assertEqual(id(self.values),identity)
    def test_v3_roundtrip_preserves_items_index_directory_and_lists(self):
        self.install();self.p.route_directory=r'C:\owned routes';self.p.route_codepage=65001
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'profile.json';self.p.save(path,self.values,{})
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['version'],3)
            other=Profiles(self.catalog);values,lists=other.load_document(path)
        self.assertEqual(other.combo_text(values,self.supply),'İsim.R')
        self.assertEqual(other.route_directory,r'C:\owned routes');self.assertEqual(lists,other.list_defaults)
        self.assertEqual(other.combo_items(self.supply),('B.R','İsim.R','B.R'))
        self.assertEqual(other.route_codepage,65001)
    def test_invalid_v3_is_atomic_across_metadata_values_and_lists(self):
        self.install();self.p.route_directory='old'
        before=(dict(self.p.route_choices),dict(self.p.bounds),self.p.route_directory,dict(self.values))
        base=dict(version=3,values=self.values,lists={},route_choices={self.supply:['new.R']},route_directory='new')
        cases=(base,dict(base,values=dict(self.values,**{self.supply:0}),lists={'unknown':[]}),
            dict(base,route_choices={self.supply:[3]}),dict(base,route_choices={'unknown':['x']}),
            dict(base,route_directory=5),dict(base,unexpected=True),dict(base,route_codepage=True))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.json'
            for data in cases:
                path.write_text(json.dumps(data),encoding='utf-8')
                with self.assertRaises(ValueError):self.p.load_document(path)
                self.assertEqual((self.p.route_choices,self.p.bounds,self.p.route_directory,self.values),before)
    def test_legacy_load_clears_dynamic_metadata_and_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'old.json'
            for version in (1,2):
                self.install();self.p.route_directory='old'
                data=dict(version=version,values=dict(self.p.defaults))
                if version==2:data['lists']={}
                path.write_text(json.dumps(data),encoding='utf-8')
                values,_=self.p.load_document(path)
                self.assertEqual(self.p.route_choices,{});self.assertEqual(self.p.route_directory,'')
                self.assertEqual(self.p.bounds,self.p.static_bounds)
                self.assertEqual(self.p.combo_text(values,self.supply),'Rota Seciniz !')
    def test_invalid_save_preserves_existing_profile_bytes(self):
        self.install()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'p.json';self.p.save(path,self.values,{})
            previous=path.read_bytes();self.p.route_directory=5
            with self.assertRaises(ValueError):self.p.save(path,self.values,{})
            self.assertEqual(path.read_bytes(),previous)
    def test_dynamic_empty_and_omitted_selection_are_validated(self):
        self.p.install_route_choices(self.values,self.supply,())
        self.assertEqual(self.p.combo_text(self.values,self.supply),'')
        with self.assertRaises(ValueError):self.p.update(self.values,self.supply,0)
        with self.assertRaises(ValueError):self.p.validate({'version':1,'values':{}})
    def test_route_metadata_cannot_change_unrelated_combo_ranges(self):
        other=next(k for k in self.p.combo_defaults if k not in ROUTE_COMBO_PATHS.values() and k!=EDITOR_PATH)
        before=copy.deepcopy(self.p.bounds)
        with self.assertRaises(ValueError):self.p.install_route_choices(self.values,other,('x',))
        self.assertEqual(self.p.bounds,before)
    def test_source_editor_choices_index_and_route_list_roundtrip(self):
        self.p.install_route_choices(self.values,EDITOR_PATH,('first.R','second.R'))
        self.p.update(self.values,EDITOR_PATH,1)
        route='frmMain/RotaPanel/lstRota'
        rows={route:[dict(caption='CustomUnknown',subitems=['x','y'],checked=False)]}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'editor.json';self.p.save(path,self.values,rows)
            other=Profiles(self.catalog);values,lists=other.load_document(path)
        self.assertEqual(other.combo_text(values,EDITOR_PATH),'second.R')
        self.assertEqual(lists[route],rows[route]);self.assertEqual(other.combo_items(self.supply),self.p.combo_items(self.supply))

class LocalRouteCatalogTests(unittest.TestCase):
    def test_real_owned_directory_extension_and_directory_entry(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ('A.R','b.r','.R','İsim.R'):(Path(d)/n).write_bytes(b'')
            (Path(d)/'sub.R').mkdir()
            p=read_local_route_catalog(d,WindowsNameCodec(1254))
            self.assertTrue(p.complete);self.assertEqual(set(p.rows),{'A.R','İsim.R','sub.R'})
    def test_empty_missing_relative_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read_local_route_catalog(d,WindowsNameCodec(1254)).rows,('Rota Seciniz !',))
            missing=read_local_route_catalog(str(Path(d)/'missing'),WindowsNameCodec(1254))
            self.assertTrue(missing.complete);self.assertEqual(missing.rows,('Rota Seciniz !',))
            self.assertFalse(missing.enumeration_verified);self.assertEqual(missing.failed_operation,'scandir_open')
            self.assertTrue(missing.local_error)
            for n in ('a.R','b.R'):(Path(d)/n).write_bytes(b'')
            with self.assertRaises(ValueError):read_local_route_catalog(d,WindowsNameCodec(1254),max_entries=1)
        with self.assertRaises(ValueError):read_local_route_catalog('relative',WindowsNameCodec(1254))
    def test_lossy_filename_is_not_replaced_with_question_mark_path(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'😀.R').write_bytes(b'')
            with self.assertRaises(ValueError):read_local_route_catalog(d,WindowsNameCodec(1254))
            self.assertEqual(read_local_route_catalog(d,WindowsNameCodec(65001)).rows,('😀.R',))

if __name__=='__main__':unittest.main()
