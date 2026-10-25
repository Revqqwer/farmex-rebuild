"""Local head -> combo -> selector composition; explicit observations, no IO."""
from dataclasses import dataclass,field
from alternate_dispatcher import AlternateState,dispatch_alternate
from rogue_combo import ComboState,plan_rogue_combo

@dataclass(frozen=True)
class RogueChainState:
    head: AlternateState = field(default_factory=AlternateState)
    combo: ComboState = field(default_factory=ComboState)

@dataclass(frozen=True)
class RogueChainPlan:
    status: str
    head: object
    combo: object
    state: RogueChainState
    independently_verified: bool = False

def replay_rogue_chain(head_snapshot,combo_observation=None,*,state=RogueChainState(),replies=None,
                       selector_snapshot=None,selector_ranges=None,selector_observation=None):
    if not isinstance(state,RogueChainState):raise ValueError('Typed chain state required')
    head=dispatch_alternate('rogue',head_snapshot,state.head,replies)
    current=RogueChainState(head.state,state.combo)
    if head.status!='complete':return RogueChainPlan('head_incomplete',head,None,current)
    if not head.calls or head.calls[-1]!='004db864':return RogueChainPlan('head_only',head,None,current)
    if combo_observation is None:return RogueChainPlan('needs_combo_observation',head,None,current)
    combo=plan_rogue_combo(state.combo,combo_observation,selector_snapshot=selector_snapshot,
                           selector_ranges=selector_ranges,selector_observation=selector_observation)
    # Unknown helper/clock results retain a prospective prefix in combo.state,
    # but do not turn it into the runner's committed next-invocation state.
    if combo.complete:current=RogueChainState(head.state,combo.state)
    return RogueChainPlan('local_chain_complete' if combo.complete else 'combo_incomplete',head,combo,current)
