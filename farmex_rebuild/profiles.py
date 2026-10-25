"""Versioned, atomic profiles for this application, independent of Farmex INI."""
import json
import os
import tempfile
import copy
from collections.abc import Mapping
from pathlib import Path
from route_catalog import ROUTE_COMBO_PATHS
from route_load_runtime import EDITOR_PATH as ROUTE_EDITOR_PATH


def atomic_json_write(path, data):
    destination = Path(path).absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, scratch = tempfile.mkstemp(prefix='.profile-', dir=str(destination.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(scratch, str(destination))
    finally:
        if os.path.exists(scratch):
            os.unlink(scratch)


class Profiles:
    def __init__(self, catalog):
        self.defaults = {}
        self.bounds = {}
        self.radio_groups = {}
        self.list_defaults = {}
        self.combo_defaults = {}
        self.route_choices = {}
        self.route_directory = ''
        self.route_codepage = 1254
        for node in catalog:
            cls, props = node['class'], node['properties']
            if cls in ('TListView', 'TListBox'):
                rows = props.get('DecodedListItems', [])
                if cls == 'TListBox':
                    rows = [{'caption': item, 'subitems': []} for item in props.get('Items.Strings', [])]
                self.list_defaults[node['path']] = [dict(caption=row['caption'],
                    subitems=list(row.get('subitems', [])), checked=False) for row in rows]
            if cls in ('TCheckBox', 'TRadioButton'):
                value = props.get('Checked', False)
                if cls == 'TRadioButton':
                    parent = node['path'].rsplit('/', 1)[0]
                    self.radio_groups.setdefault(parent, []).append(node['path'])
            elif cls == 'TComboBox':
                value = props.get('ItemIndex', -1)
                self.combo_defaults[node['path']] = tuple(props.get('Items.Strings', []))
                self.bounds[node['path']] = (-1, len(props.get('Items.Strings', [])) - 1)
            elif cls in ('TEdit', 'TRichEdit'):
                value = props.get('Text', '')
            elif cls == 'TScrollBar':
                value = props.get('Position', 0)
                self.bounds[node['path']] = (props.get('Min', 0), props.get('Max', 100))
            else:
                continue
            self.defaults[node['path']] = value
        self.static_bounds = dict(self.bounds)

    def combo_items(self,path):
        return self.route_choices.get(path,self.combo_defaults.get(path,()))

    def combo_text(self,values,path):
        items=self.combo_items(path);index=values[path]
        return items[index] if 0<=index<len(items) else ''

    def install_route_choices(self,values,path,choices):
        """Clear-and-repopulate own runtime combo, resetting selection explicitly."""
        candidate=self.validate_route_choices({path:choices})
        if path not in self.defaults:raise ValueError('Rota kontrolü katalogda yok')
        trial=dict(values);trial[path]=-1
        bounds=dict(self.bounds);bounds[path]=(-1,len(candidate[path])-1)
        self.validate({'version':1,'values':trial},bounds=bounds)
        self.route_choices[path]=candidate[path];self.bounds=bounds
        values.clear();values.update(trial)

    def validate_route_choices(self,choices):
        if (type(choices) is not dict or set(choices)-(set(ROUTE_COMBO_PATHS.values())|{ROUTE_EDITOR_PATH})
                or set(choices)-set(self.combo_defaults)):raise ValueError('Bilinmeyen rota seçimi')
        result={}
        for path,items in choices.items():
            if type(items) not in (tuple,list) or len(items)>10000 or any(type(s) is not str or '\0' in s for s in items):
                raise ValueError('Rota seçenekleri geçersiz')
            result[path]=tuple(items)
        return result

    def validate(self, data,*,bounds=None):
        if not isinstance(data, dict) or set(data) != {'version', 'values'}:
            raise ValueError('Geçersiz profil yapısı')
        if type(data['version']) is not int or data['version'] != 1:
            raise ValueError('Desteklenmeyen profil sürümü')
        values = data['values']
        if not isinstance(values, dict) or set(values) - set(self.defaults):
            raise ValueError('Profil bilinmeyen ayarlar içeriyor')
        result = dict(self.defaults)
        bounds=self.bounds if bounds is None else bounds
        for key, value in values.items():
            if type(value) is not type(self.defaults[key]):
                raise ValueError('Ayar türü geçersiz: ' + key)
            result[key] = value
        for key,(low,high) in bounds.items():
            if not low<=result[key]<=high:raise ValueError('Ayar aralık dışında: '+key)
        for group in self.radio_groups.values():
            if sum(result[key] for key in group) > 1:
                raise ValueError('Bir seçim grubunda birden fazla seçenek etkin')
        return result

    def update(self, values, key, value):
        candidate = dict(values)
        candidate[key] = value
        if value is True:
            pool_prefix='frmMain/MainTab/SheetBot/GroupBox5/'
            pool_group=(pool_prefix+'chOnlyMobSelect',pool_prefix+'chOnlyPlayerSelect')
            if key in pool_group and all(p in self.defaults for p in pool_group):
                for sibling in pool_group:candidate[sibling]=sibling==key
            for group in self.radio_groups.values():
                if key in group:
                    for sibling in group:
                        candidate[sibling] = sibling == key
                    break
        validated = self.validate({'version': 1, 'values': candidate})
        values.clear()
        values.update(validated)

    def load(self, path):
        return self.load_document(path)[0]

    def apply_boolean_updates(self, values, updates):
        """Atomic derived UI effects; keep shared values identity and radio rules."""
        if not isinstance(updates,Mapping):raise ValueError('Boolean update mapping required')
        for key,value in updates.items():
            if key not in self.defaults or type(self.defaults[key]) is not bool or type(value) is not bool:
                raise ValueError('Known boolean control required: '+str(key))
        for group in self.radio_groups.values():
            if sum(updates.get(key) is True for key in group)>1:
                raise ValueError('Conflicting derived radio effects')
        prefix='frmMain/MainTab/SheetBot/GroupBox5/'
        if all(updates.get(prefix+n) is True for n in ('chOnlyMobSelect','chOnlyPlayerSelect')):
            raise ValueError('Conflicting derived pool effects')
        candidate=dict(values)
        for key,value in updates.items():self.update(candidate,key,value)
        values.clear();values.update(candidate)

    def validate_lists(self, lists):
        if not isinstance(lists, dict) or set(lists) - set(self.list_defaults):
            raise ValueError('Bilinmeyen liste')
        result = copy.deepcopy(self.list_defaults)
        for key, rows in lists.items():
            if not isinstance(rows, list):
                raise ValueError('Liste satırları geçersiz')
            for row in rows:
                if not isinstance(row, dict) or set(row) != {'caption', 'subitems', 'checked'}:
                    raise ValueError('Liste satırı yapısı geçersiz')
                if not isinstance(row['caption'], str) or type(row['checked']) is not bool:
                    raise ValueError('Liste satırı türü geçersiz')
                if not isinstance(row['subitems'], list) or any(not isinstance(v, str) for v in row['subitems']):
                    raise ValueError('Liste sütunları geçersiz')
            result[key] = copy.deepcopy(rows)
        return result

    def load_document(self, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        choices={};directory='';codepage=1254;bounds=dict(self.static_bounds)
        if isinstance(data, dict) and type(data.get('version')) is int and data['version'] in (2,3):
            keys={'version','values','lists'} if data['version']==2 else {'version','values','lists','route_choices','route_directory'}
            if set(data) != keys and not (data['version']==3 and set(data)==keys|{'route_codepage'}):
                raise ValueError('Geçersiz profil yapısı')
            if data['version']==3:
                choices=self.validate_route_choices(data['route_choices']);directory=data['route_directory']
                if type(directory) is not str or '\0' in directory:raise ValueError('Rota klasörü geçersiz')
                codepage=data.get('route_codepage',1254)
                if type(codepage) is not int or not 1<=codepage<=65535:raise ValueError('Rota kod sayfası geçersiz')
                for key,items in choices.items():bounds[key]=(-1,len(items)-1)
            values = self.validate({'version': 1, 'values': data['values']},bounds=bounds)
            lists=self.validate_lists(data['lists'])
        else:
            values=self.validate(data,bounds=bounds);lists=copy.deepcopy(self.list_defaults)
        # Commit metadata only after every value/list/choice has validated.
        self.route_choices=choices;self.route_directory=directory;self.route_codepage=codepage;self.bounds=bounds
        return values,lists

    def save(self, path, values, lists=None):
        self.validate({'version': 1, 'values': values})
        if type(self.route_directory) is not str or '\0' in self.route_directory:raise ValueError('Rota klasörü geçersiz')
        if type(self.route_codepage) is not int or not 1<=self.route_codepage<=65535:raise ValueError('Rota kod sayfası geçersiz')
        if self.route_choices or self.route_directory or self.route_codepage!=1254:
            choices=self.validate_route_choices(self.route_choices)
            bounds=dict(self.static_bounds)
            for key,items in choices.items():bounds[key]=(-1,len(items)-1)
            self.validate({'version':1,'values':values},bounds=bounds)
            validated_lists=self.validate_lists({} if lists is None else lists)
            atomic_json_write(path,dict(version=3,values=values,lists=validated_lists,
                route_choices=choices,route_directory=self.route_directory,route_codepage=self.route_codepage))
        elif lists is None:
            atomic_json_write(path, {'version': 1, 'values': values})
        else:
            validated_lists = self.validate_lists(lists)
            atomic_json_write(path, {'version': 2, 'values': values, 'lists': validated_lists})
