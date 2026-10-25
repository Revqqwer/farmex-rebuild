"""Typed owned interlude observations; input cannot assert live verification."""
import json
from dataclasses import dataclass
from callback_interlude import CallbackInterludeState,CallbackInterludeObservation
from callback_predicate import CallbackPredicateObservation
from source_random import SourceRandomObservation

@dataclass(frozen=True)
class InterludeSample:
    initial_state:object
    observation:CallbackInterludeObservation
    independently_verified:bool=False

def parse_interlude_sample(text):
    if type(text) is not str:raise ValueError('Owned interlude observation JSON text required')
    def object_pairs(pairs):
        out={}
        for key,value in pairs:
            if key in out:raise ValueError('Duplicate interlude observation field')
            out[key]=value
        return out
    data=json.loads(text,object_pairs_hook=object_pairs)
    if not isinstance(data,dict) or set(data)-{'initial_state','observation'}:
        raise ValueError('Unknown interlude fields; verification claims are not accepted')
    initial=data.get('initial_state');observed=data.get('observation',{})
    if ('initial_state' in data and not isinstance(initial,dict)) or not isinstance(observed,dict):
        raise ValueError('Interlude state/observation objects required')
    try:
        def random_snapshot(value):
            if not isinstance(value,dict):raise ValueError('Random helper snapshot object required')
            return SourceRandomObservation(**value)
        observed=dict(observed)
        for key in ('initial_random_inputs','final_random_inputs'):
            if key in observed:observed[key]=random_snapshot(observed[key])
        if 'predicate_inputs' in observed:
            nested=observed['predicate_inputs']
            if not isinstance(nested,dict):raise ValueError('Predicate snapshot object required')
            if 'random_inputs' in nested:nested=dict(nested,random_inputs=random_snapshot(nested['random_inputs']))
            observed=dict(observed,predicate_inputs=CallbackPredicateObservation(**nested))
        state=CallbackInterludeState(**initial) if initial is not None else None
        observation=CallbackInterludeObservation(**observed)
    except TypeError as error:raise ValueError('Unknown interlude source observation field') from error
    return InterludeSample(state,observation)
