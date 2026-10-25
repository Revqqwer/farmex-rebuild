"""Compile proven class UI mappings; no game IO or timer fabrication.

List rows retain source index semantics. Edited/reordered captions are rejected
because the profile schema has no immutable source-row ID. Integer parsing uses
our strict decimal signed32 policy, not a full emulation of Delphi StrToInt64.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Tuple

_MAP = json.loads((Path(__file__).parent / 'class_configuration_map.json').read_text(encoding='utf-8'))


@dataclass(frozen=True)
class ClassConfiguration:
    job: str
    producer: str
    flags: Mapping[int, bool]
    parameters: Mapping[int, int]
    unresolved: Tuple[str, ...]
    texts: Mapping[int, str] = field(default_factory=lambda: MappingProxyType({}))
    ui_updates: Mapping[str, bool] = field(default_factory=lambda: MappingProxyType({}))


def compile_class_configuration(job, values, lists):
    if job not in _MAP or not isinstance(values, Mapping) or not isinstance(lists, Mapping):
        raise ValueError('Known class and value/list mappings required')
    schema = _MAP[job]
    flags, parameters, unresolved, texts, ui_updates = {}, {}, [], {}, {}
    for path, offsets in schema['lists'].items():
        rows = lists.get(path)
        captions = schema['captions'][path]
        if not isinstance(rows, list) or len(rows) != len(captions):
            raise ValueError('Missing or changed source list: ' + path)
        for index, (row, caption) in enumerate(zip(rows, captions)):
            if (not isinstance(row, dict) or row.get('caption') != caption
                    or type(row.get('checked')) is not bool):
                raise ValueError('Changed row identity or checked type: ' + path)
            if index < len(offsets):
                flags[offsets[index]] = row['checked']
            else:
                unresolved.append('%s[%d]: producer does not read this row; checked=%s' % (path, index, row['checked']))
    for path, offset in schema['booleans'].items():
        value = values.get(path)
        if type(value) is not bool:
            raise ValueError('Missing/invalid checkbox: ' + path)
        flags[offset] = value
    for path, offset in schema['integers'].items():
        value = values.get(path)
        if not isinstance(value, str) or not re.fullmatch(r'[+-]?[0-9]+', value.strip()):
            raise ValueError('Decimal integer text required: ' + path)
        integer = int(value.strip())
        if not -(1 << 31) <= integer < (1 << 31):
            raise ValueError('Integer outside our signed32 policy: ' + path)
        parameters[offset] = integer
    for path, spec in schema['combos'].items():
        value = values.get(path)
        if type(value) is not int or value < -1:
            raise ValueError('Missing/invalid combo index: ' + path)
        if value < 1:
            parameters[spec['offset']] = spec['less_than_one']
        elif str(value) in spec['indices']:
            parameters[spec['offset']] = spec['indices'][str(value)]
        else:
            # Source retains prior struct field for an unmatched positive index.
            # No previous struct was supplied, so do not invent a zero value.
            unresolved.append(path + ': unmatched index retains previous source field')
    for offset, inputs in schema.get('derived_any', {}).items():
        flags[int(offset)] = any(flags[o] for o in inputs)
    for path, offset in schema.get('texts', {}).items():
        value=values.get(path)
        if not isinstance(value,str):
            raise ValueError('Missing/invalid text: '+path)
        # Preserve UI Unicode text in the independent model; no guessed game codec.
        texts[offset]=value
    for path,spec in schema.get('ui_effects', {}).items():
        if flags[spec['when_flag']]:
            ui_updates[path]=spec['value']
    return ClassConfiguration(job, schema['producer'], MappingProxyType(flags),
                              MappingProxyType(parameters), tuple(unresolved),
                              MappingProxyType(texts),MappingProxyType(ui_updates))


def compile_priest(values, lists):
    return compile_class_configuration('priest', values, lists)


def compile_warrior(values, lists):
    return compile_class_configuration('warrior', values, lists)


def compile_mage(values, lists):
    return compile_class_configuration('mage', values, lists)


def compile_rogue(values, lists):
    return compile_class_configuration('rogue', values, lists)


def compile_kurian(values, lists):
    return compile_class_configuration('kurian', values, lists)
