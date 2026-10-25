"""Four source Clear/DeleteSelected callers; observations only, no native IO."""
from dataclasses import dataclass
from source_name_lists import NameListRefreshPlan
from source_unicode import utf16_key
from vcl_list_mutation import VclMutationPlan

CALLERS={('white','clear'):0x423cac,('black','clear'):0x423cd8,
         ('white','remove'):0x423d04,('black','remove'):0x423d30}

def _rows(value):
    if type(value) is not tuple:raise ValueError('Immutable Unicode rows required')
    for text in value:utf16_key(text)

@dataclass(frozen=True)
class NameMutationObservation:
    mutation_returned:object=None
    rows_after_mutation:object=None
    refresh_execution:object=None
    refresh_returned:object=None
    mutation_execution:object=None
    def __post_init__(self):
        for value in (self.mutation_returned,self.refresh_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
        if self.rows_after_mutation is not None:_rows(self.rows_after_mutation)
        if self.refresh_execution is not None and not isinstance(self.refresh_execution,NameListRefreshPlan):
            raise ValueError('Typed refresh plan required')
        if self.mutation_execution is not None and not isinstance(self.mutation_execution,VclMutationPlan):
            raise ValueError('Typed VCL mutation required')

@dataclass(frozen=True)
class NameMutationPlan:
    complete:bool
    kind:str
    action:str
    caller:int
    entry:tuple
    state:tuple
    prospective:tuple
    steps:tuple
    refresh_execution:object=None
    missing:str=''
    native_execution_verified:bool=False

def plan_name_mutation(kind,action,rows,o):
    if (kind,action) not in CALLERS or not isinstance(o,NameMutationObservation):
        raise ValueError('Known mutation and typed observations required')
    _rows(rows)
    prospective=rows;steps=[];bound=None
    class Missing(Exception):pass
    def normal(value,label):
        steps.append(('normal_return',label))
        if value is not True:raise Missing(label)
    def result(complete,missing=''):
        return NameMutationPlan(complete,kind,action,CALLERS[kind,action],rows,
            prospective if complete else rows,prospective,tuple(steps),bound,missing)
    try:
        steps.append(('virtual_call',kind,0x3d4 if kind=='white' else 0x3f0,
                      0x13c if action=='clear' else 0x148))
        mutation=o.mutation_execution
        if mutation is not None:
            if mutation.action!=action or mutation.entry!=rows:raise ValueError('Bound VCL mutation identity mismatch')
            if o.rows_after_mutation is not None:raise ValueError('Raw post-state conflicts with bound VCL mutation')
            if not mutation.complete:raise Missing('bound VCL mutation: '+mutation.missing)
        normal(o.mutation_returned,'Clear/DeleteSelected normal return')
        # A virtual return alone does not establish private class mutation effects.
        if mutation is None and o.rows_after_mutation is None:raise Missing('post-mutation Unicode rows')
        prospective=mutation.state if mutation is not None else o.rows_after_mutation
        steps.append(('call',0x46c3b8,0x5690f8))
        # The caller refreshes unconditionally, even for an unchanged/empty list.
        # Refresh getter samples are fresh, not equated to post-mutation rows.
        bound=o.refresh_execution
        if bound is not None and not bound.complete:raise Missing('bound refresh: '+bound.missing)
        normal(o.refresh_returned,'0046c3b8 independent normal return')
        return result(True)
    except Missing as error:return result(False,str(error))
