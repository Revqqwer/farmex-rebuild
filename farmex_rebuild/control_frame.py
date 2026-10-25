"""Compose the recovered00458f98 decision ranges; no callback/game execution.

String allocation/cleanup and native helper effects remain outside scope.
Unknown reached stages preserve accepted state and expose only a plan prefix.
"""
from dataclasses import dataclass
from control_guards import plan_control_guards
from control_continuation import plan_control_continuation
from party_help import PartyHelpState,plan_party_help
from control_alarms import LootActivityState,plan_control_alarm_tail

@dataclass(frozen=True)
class ControlFrameConfiguration:
    entry:object
    clock_party:object=None
    party_help:object=None
    alarms:object=None

@dataclass(frozen=True)
class ControlFrameState:
    party_help:PartyHelpState
    loot_activity:LootActivityState

@dataclass(frozen=True)
class ControlFrameObservation:
    entry:object
    clock_party:object=None
    party_help:object=None
    alarms:object=None

@dataclass(frozen=True)
class ControlFramePlan:
    status:str
    complete:bool
    state:ControlFrameState
    prospective_state:ControlFrameState
    entry:object=None
    clock_party:object=None
    party_help:object=None
    alarms:object=None
    calls:tuple=()
    missing:str=''
    source_return_planned:bool=False
    termination_call_planned:bool=False
    native_execution_verified:bool=False

def replay_control_frame(configuration,state,observation):
    if not isinstance(configuration,ControlFrameConfiguration) or not isinstance(state,ControlFrameState) or not isinstance(observation,ControlFrameObservation):
        raise ValueError('Typed control frame config/state/observations required')
    c=configuration;o=observation;entry=follow=help=alarms=None;calls=[];prospective=state
    def result(status,complete=False,missing='',returned=False,termination=False):
        return ControlFramePlan(status,complete,prospective if complete else state,prospective,entry,follow,help,alarms,tuple(calls),missing,returned,termination)
    entry=plan_control_guards(c.entry,o.entry);calls.extend(entry.calls)
    if not entry.complete:return result('needs_entry_observation',missing=entry.missing)
    if entry.source_return_planned:return result(entry.status,True,returned=True)
    if c.clock_party is None or o.clock_party is None:return result('needs_clock_party_observation',missing='clock/party stage')
    follow=plan_control_continuation(c.clock_party,o.clock_party);calls.extend(follow.calls)
    if not follow.complete:return result('needs_clock_party_observation',missing=follow.missing)
    if follow.termination_call_planned:return result(follow.status,True,termination=True)
    if follow.source_return_planned:return result(follow.status,True,returned=True)
    if follow.next_address==0x4592a7:
        if c.party_help is None or o.party_help is None:return result('needs_party_help_observation',missing='party-help stage')
        help=plan_party_help(c.party_help,state.party_help,o.party_help);calls.extend(help.calls)
        prospective=ControlFrameState(help.prospective_state,state.loot_activity)
        if not help.complete:return result('needs_party_help_observation',missing=help.missing)
        alarm_entry=0x459496
    elif follow.next_address==0x459519:alarm_entry=0x459519
    else:raise ValueError('Unexpected recovered continuation address')
    if c.alarms is None or o.alarms is None:return result('needs_alarm_observation',missing='alarm-tail stage')
    alarms=plan_control_alarm_tail(c.alarms,state.loot_activity,o.alarms,entry_address=alarm_entry);calls.extend(alarms.calls)
    if not alarms.complete:return result('needs_alarm_observation',missing=alarms.missing)
    return result('control_return_planned',True,returned=True)
