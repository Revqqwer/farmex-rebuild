"""004c80e4 immutable request/queue replay; no game IO.

RTL comparison results must come from the fresh name produced after 0046fb38,
not the earlier ore-name gate. NPC WORD is unused by this helper. Its caller's
context preparation has separate memory effects, never executed here.

00505138 is != and00505118 is == through505158/402e18/402e30 and
imported System::LStrCmp. Byte-name adapter uses documented AnsiString byte
comparison; it does not claim an observed loaded runtime or codepage.
"""
from dataclasses import dataclass
from typing import Optional
from action_queue import QueueState, QueueSample, enqueue
from mining_engine import OreSlotTick

OPEN_TEMPLATE=bytes.fromhex('6407544e00000000')
SCRIPT_TEMPLATE=bytes.fromhex('55001033313531315f5069746d616e2e6c7561')
GOLD_NAME=b'Mysterious gold mine'
ORE_NAME=b'Mysterious Ore'

@dataclass(frozen=True)
class OreRequestObservation:
    first_505138:Optional[bool]=None
    second_505138:Optional[bool]=None
    gold_505118:Optional[bool]=None

    def __post_init__(self):
        for value in (self.first_505138,self.second_505138,self.gold_505118):
            if value is not None and type(value) is not bool:
                raise ValueError('Explicit normalized fresh-name RTL result required')

@dataclass(frozen=True)
class OreRequestPlan:
    status:str
    packets:tuple=()
    missing:str=''
    complete:bool=False
    context_preparation_verified:bool=False
    server_acknowledged:bool=False

def plan_ore_request(observation):
    if not isinstance(observation,OreRequestObservation):raise ValueError('Typed observation required')
    if observation.first_505138 is None:
        return OreRequestPlan('needs_fresh_name_comparison',missing='first_505138')
    if observation.first_505138:
        if observation.second_505138 is None:
            return OreRequestPlan('needs_fresh_name_comparison',missing='second_505138')
        if observation.second_505138:
            return OreRequestPlan('source_early_return',complete=True)
    if observation.gold_505118 is None:
        return OreRequestPlan('needs_fresh_name_comparison',missing='gold_505118')
    script=bytearray(SCRIPT_TEMPLATE)
    if observation.gold_505118:script[1]=1
    return OreRequestPlan('locally_serialized',((OPEN_TEMPLATE,300),(bytes(script),600)),complete=True)

def plan_slot_request(slot,observation=None):
    """Bind only an actual child request intent; never infer fresh RTL results."""
    if not isinstance(slot,OreSlotTick):raise ValueError('Typed ore slot result required')
    if not any(i.name=='ore_crash_request_attempt' for i in slot.intents):
        return OreRequestPlan('request_not_reached',complete=True)
    return plan_ore_request(observation if observation is not None else OreRequestObservation())

def plan_ore_request_name(fresh_ansi_name):
    """Fresh managed ANSI contents, length preserved; no decode/strip/casefold.

None is missing, b'' is a real empty name and takes the early return. These
bytes must be the post-preparation name, not an earlier inventory snapshot.
"""
    if fresh_ansi_name is None:
        return OreRequestPlan('needs_fresh_ansi_name',missing='post0046fb38 fresh00463670 ANSI bytes')
    if type(fresh_ansi_name) is not bytes:raise ValueError('Immutable fresh ANSI bytes required')
    first=fresh_ansi_name!=GOLD_NAME
    second=fresh_ansi_name!=ORE_NAME if first else None
    gold=fresh_ansi_name==GOLD_NAME if not (first and second) else None
    return plan_ore_request(OreRequestObservation(first,second,gold))

def plan_slot_request_name(slot,fresh_ansi_name=None):
    if not isinstance(slot,OreSlotTick):raise ValueError('Typed ore slot result required')
    if not any(i.name=='ore_crash_request_attempt' for i in slot.intents):
        return OreRequestPlan('request_not_reached',complete=True)
    return plan_ore_request_name(fresh_ansi_name)

@dataclass(frozen=True)
class OreRequestQueuePlan:
    status:str
    state:QueueState
    complete:bool
    completed_calls:int=0
    missing:str=''
    server_acknowledged:bool=False

def enqueue_ore_request(state,plan,samples):
    """Ordered calls with separate gates/ticks; incomplete state is prefix only.

No GameIO and no context preparation. Completion means both enqueue helpers
modeled (including disconnected skips), never that packets were sent.
"""
    if not isinstance(state,QueueState) or not isinstance(plan,OreRequestPlan):
        raise ValueError('Typed queue/request required')
    if not plan.complete:return OreRequestQueuePlan(plan.status,state,False,missing=plan.missing)
    samples=tuple(samples)
    for index,(payload,delay) in enumerate(plan.packets):
        if index>=len(samples):return OreRequestQueuePlan('needs_queue_observation',state,False,index,str(index))
        sample=samples[index]
        if not isinstance(sample,QueueSample):raise ValueError('Typed per-call sample required')
        result=enqueue(state,payload,len(payload),delay,sample.connection_gate,sample.tick)
        if result.state is None:return OreRequestQueuePlan(result.status,state,False,index,result.missing)
        state=result.state
    return OreRequestQueuePlan('locally_queued',state,True,len(plan.packets))
