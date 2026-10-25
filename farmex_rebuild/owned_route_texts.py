"""Bind optional OWN route-text comparison fixtures without inventing span returns.

This compiler validates the entire template and rejects mixed raw comparison
results. It is not the source dispatcher or a runtime text/locale observer.
"""
from dataclasses import dataclass,replace
from collections.abc import Mapping
from types import MappingProxyType
from source_unicode import UnicodeEqualityObservation,plan_unicode_equality
from source_route_step import SourceRouteStepObservation
from source_route_coordinate import RouteCoordinateObservation
from source_route_commands import SourceRouteCommandsObservation
from source_route_gates import SourceRouteGatesObservation
from source_route_delos import SourceDelosObservation
from source_route_finish import SourceRouteFinishObservation

LITERALS={'Town':'Town','Koordinat':'Koordinat','Bekle':'Bekle',
    'Otur_predicate':'Otur','Kalk_predicate':'Kalk','Otur_action':'Otur','Kalk_action':'Kalk',
    'Gate Skill':'Gate Skill','Gate Open':'Gate Open','Gate':'Gate',
    'Delos Gate Open':'Delos Gate Open','Delos Gate':'Delos Gate',
    'Change Camp':'Change Camp','Randomize':'Randomize','NPC':'NPC'}

@dataclass(frozen=True)
class OwnedRouteTextBinding:
    observation:SourceRouteStepObservation
    equality_plans:Mapping
    posture_match_byte:object=None
    provenance:str='owned_route_text_model'
    native_runtime_verified:bool=False
    def __post_init__(self):
        object.__setattr__(self,'equality_plans',MappingProxyType(dict(self.equality_plans)))

def owned_stable_route_texts(command_name,parameter_text=None,*,stable_same_invocation=False):
    """Explicit stable own-row fixture; Randomize uses parameter column224."""
    if stable_same_invocation is not True:raise ValueError('Explicit stable own-row contract required')
    if command_name is not None and type(command_name) is not str:raise ValueError('Own Unicode command name required')
    if parameter_text is not None and type(parameter_text) is not str:raise ValueError('Own Unicode parameter required')
    return {key:parameter_text if key=='Randomize' else command_name for key in LITERALS}

def bind_owned_route_texts(observation,texts):
    if not isinstance(observation,SourceRouteStepObservation) or not isinstance(texts,Mapping):raise ValueError('Typed source template and own text samples required')
    if set(texts)-set(LITERALS):raise ValueError('Unknown route comparison site')
    # Every source comparison may read a fresh index/name. No same-name
    # fallback exists here; callers select the stable-row fixture explicitly.
    plans={key:plan_unicode_equality(UnicodeEqualityObservation(helper_returned=True,use_owned_text_model=True,
        left_text=texts.get(key),right_text=literal)) for key,literal in LITERALS.items()}
    def al(key):return plans[key].al
    def empty(*values):
        if any(v is not None for v in values):raise ValueError('Owned compiler cannot mix supplied raw comparison results')
    c=observation.coordinate or RouteCoordinateObservation()
    m=observation.commands or SourceRouteCommandsObservation()
    g=m.gates or SourceRouteGatesObservation()
    d=g.delos or SourceDelosObservation()
    f=d.finish or SourceRouteFinishObservation()
    empty(observation.comparison_al,c.comparison_al,m.wait_comparison_al,m.posture_match_byte,
          m.sit_comparison_al,m.stand_comparison_al,f.random_comparison_al)
    def comparisons(rows,kinds):
        if len(rows)>len(kinds):raise ValueError('Extra comparison observations in owned template')
        result=[]
        for i,kind in enumerate(kinds):
            if i<len(rows):
                name,returned,raw=rows[i]
                if name!=kind:raise ValueError('Owned comparison template order mismatch')
                empty(raw)
            else:returned=None
            result.append((kind,returned,al(kind)))
        return tuple(result)
    posture=None
    if al('Otur_predicate') is not None:
        posture=1 if al('Otur_predicate') else al('Kalk_predicate')
    f=replace(f,comparisons=comparisons(f.comparisons,('Change Camp','NPC')),random_comparison_al=al('Randomize'))
    d=replace(d,comparisons=comparisons(d.comparisons,('Delos Gate Open','Delos Gate')),finish=f)
    g=replace(g,comparisons=comparisons(g.comparisons,('Gate Skill','Gate Open','Gate')),delos=d)
    m=replace(m,wait_comparison_al=al('Bekle'),posture_match_byte=posture,
        sit_comparison_al=al('Otur_action'),stand_comparison_al=al('Kalk_action'),gates=g)
    c=replace(c,comparison_al=al('Koordinat'))
    bound=replace(observation,comparison_al=al('Town'),coordinate=c,commands=m)
    return OwnedRouteTextBinding(bound,plans,posture)
