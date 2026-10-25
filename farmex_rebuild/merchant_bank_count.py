"""0046ff6c normal192slot zero-result count; no memory/native effects."""
from dataclasses import dataclass
from source_bank_item import BankItemObservation,plan_bank_item

@dataclass(frozen=True)
class BankCountObservation:
    item_results:tuple=()
    item_returned:tuple=()
    item_inputs:tuple=()
    def __post_init__(self):
        if any(type(v) is not tuple for v in (self.item_results,self.item_returned,self.item_inputs)) or max(len(self.item_results),len(self.item_returned),len(self.item_inputs))>192:
            raise ValueError('At most192 ordered slot observations required')
        for v in self.item_results:
            if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw item EAX required')
        for v in self.item_returned:
            if v is not None and type(v) is not bool:raise ValueError('Separate item helper return required')
        if any(v is not None and not isinstance(v,BankItemObservation) for v in self.item_inputs):raise ValueError('Typed independent bank item inputs required')

@dataclass(frozen=True)
class BankCountPlan:
    complete:bool
    count_dword:object
    zero_slots:tuple
    calls:tuple
    missing:str=''
    independently_verified:bool=False
    item_plans:tuple=()

def plan_bank_count(o):
    if not isinstance(o,BankCountObservation):raise ValueError('Typed bank count observations required')
    calls=[];zeros=[];plans=[]
    def result(ok,count=None,missing=''):
        return BankCountPlan(ok,count,tuple(zeros),tuple(calls),missing,item_plans=tuple(plans))
    for slot in range(192):
        calls.append(('0046fed8',slot))
        if slot>=len(o.item_returned) or o.item_returned[slot] is not True:
            return result(False,missing='slot%d helper normal return'%slot)
        raw=o.item_results[slot] if slot<len(o.item_results) else None
        bound=o.item_inputs[slot] if slot<len(o.item_inputs) else None
        if bound is not None:
            if raw is not None:raise ValueError('Reached raw item EAX conflicts with bound bank slot')
            p=plan_bank_item(slot,bound);plans.append(p)
            if not p.complete:return result(False,missing='slot%d: '%slot+p.missing)
            raw=p.result_dword
        if raw is None:return result(False,missing='slot%d fresh item EAX'%slot)
        if raw==0:zeros.append(slot)
    return result(True,len(zeros))
