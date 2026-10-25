"""Decode owned control observation JSON. Input is never live-verified evidence."""
import json
from dataclasses import dataclass
from types import MappingProxyType
from party_help import PartyHelpState,PartyHelpObservation,TEXT_PATHS
from control_alarms import LootActivityState,ControlAlarmObservation
from control_frame import ControlFrameState

@dataclass(frozen=True)
class ControlSample:
    initial_state:object
    observed_ansi:object
    party_help:PartyHelpObservation
    alarms:ControlAlarmObservation
    independently_verified:bool=False

def parse_control_sample(text):
    if type(text) is not str:raise ValueError('Owned control observation JSON text required')
    data=json.loads(text)
    if not isinstance(data,dict) or set(data)-{'initial_state','observed_ansi_hex','party_help','alarms'}:
        raise ValueError('Unknown control observation fields; verification claims are not accepted')
    def obj(value):
        if not isinstance(value,dict):raise ValueError('Observation object required')
        return value
    def key(value):
        if type(value) is int:return value
        if type(value) is not str:raise ValueError('Integer/hex observation key required')
        return int(value,16 if value.lower().startswith('0x') else 10)
    def mapping(value):
        out={}
        for k,v in obj(value).items():
            k=key(k)
            if k in out:raise ValueError('Duplicate normalized observation key')
            out[k]=v
        return out
    seed=None
    if 'initial_state' in data:
        initial=obj(data['initial_state'])
        if set(initial)-{'timers','last_activity_qword'}:raise ValueError('Unknown initial state field')
        seed=ControlFrameState(PartyHelpState(mapping(initial.get('timers',{}))),LootActivityState(initial.get('last_activity_qword')))
    ansi={}
    for path,value in obj(data.get('observed_ansi_hex',{})).items():
        if path not in TEXT_PATHS or type(value) is not str:raise ValueError('Known party-help text path and exact hex bytes required')
        ansi[path]=bytes.fromhex(value)
    help_data=dict(obj(data.get('party_help',{})))
    for field in ('feature_ticks','predicate_returns','request_returns','post_request_ticks','swift_globals'):
        if field in help_data:help_data[field]=mapping(help_data[field])
    if 'swift_samples' in help_data:
        rows=help_data['swift_samples']
        if not isinstance(rows,list) or any(not isinstance(r,list) or len(r)!=2 for r in rows):raise ValueError('Ordered Swift samples required')
        help_data['swift_samples']=tuple((key(row[0]),row[1]) for row in rows)
    alarm_data=dict(obj(data.get('alarms',{})));names={}
    rows=alarm_data.pop('name_samples',[])
    if not isinstance(rows,list):raise ValueError('Ordered fresh-name sample records required')
    for row in rows:
        if (not isinstance(row,list) or len(row)!=3 or type(row[2]) is not str
                or type(row[0]) is not int or type(row[1]) is not int):raise ValueError('[slot,comparison,hex] record required')
        sample=(row[0],row[1])
        if sample in names:raise ValueError('Duplicate fresh-name observation')
        names[sample]=bytes.fromhex(row[2])
    alarm_data['name_samples']=names
    try:help_obs=PartyHelpObservation(**help_data);alarm_obs=ControlAlarmObservation(**alarm_data)
    except TypeError as error:raise ValueError('Unknown/invalid source observation field') from error
    return ControlSample(seed,MappingProxyType(ansi),help_obs,alarm_obs)
