"""Own stable pending snapshot composition; never live shared-memory execution."""
from dataclasses import dataclass,replace
from chat_skill_requests import ChatSkillPlan,PendingChatSkillRequest,SPECS
from chat_skill_consumers import ChatConsumerObservation,ChatConsumerFrame

MESSAGE_CONTEXT=0x569220
PENDING_FIELDS=((0x180,1),(0x184,4),(0x188,4))
FULL_SENDER_LABELS=('lookup_sender_dword','object_sender_dword','generic_sender_dword',
                    'stamp_sender_dword','direct_sender_dword')

def bind_stable_pending_observation(o,family,pending,kind,sender,lock_byte=None):
    """Explicit own snapshot policy; no native fresh-read equivalence claim."""
    if not isinstance(o,ChatConsumerObservation) or family not in ('Mage','Rogue','Priest'):raise ValueError('Typed selected consumer required')
    for v,width in ((pending,1),(kind,4),(sender,4)):
        if type(v) is not int or not 0<=v<1<<(8*width):raise ValueError('Raw pending snapshot field required')
    fixed={'pending_byte':pending,'direct_sender_word':sender&0xffff}
    if family=='Priest':fixed.update({'kind_%d_dword'%i:kind for i in range(1,7)})
    else:fixed.update(kind_dword=kind,kind_second_dword=kind)
    fixed.update({label:sender for label in FULL_SENDER_LABELS})
    if lock_byte is not None:
        if type(lock_byte) is not int or not 0<=lock_byte<=255:raise ValueError('Raw lock BYTE required')
        fixed['lock_byte']=lock_byte
    for label,value in fixed.items():
        if label in o.values and o.values[label]!=value:raise ValueError('Explicit stable pending snapshot conflicts at '+label)
    return replace(o,values={**o.values,**fixed})

@dataclass(frozen=True)
class PendingConsumerPlan:
    complete:bool
    status:str
    producer:ChatSkillPlan
    consumer:object=None
    pending_stores:tuple=()
    missing:str=''
    stable_pending_snapshot:bool=True
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class PendingConsumerFrame:
    def __init__(self,producer,family,actor_context_dword,*,message_context_base=MESSAGE_CONTEXT):
        if not isinstance(producer,ChatSkillPlan):raise ValueError('Typed producer result required')
        if family not in ('Mage','Rogue','Priest'):raise ValueError('Explicit consumer class selection required')
        if type(message_context_base) is not int or message_context_base!=MESSAGE_CONTEXT:
            raise ValueError('Only source-selected chat context569220 has proven global identity')
        if type(actor_context_dword) is not int or not 0<=actor_context_dword<=0xffffffff:
            raise ValueError('Separate raw actor context DWORD required')
        self.producer=producer;self.family=family;self.actor_context=actor_context_dword
        self.consumer=None;self.final=None;self.pending_stores=()
        if not producer.complete:return
        request=producer.queued_request
        if request is None:return
        if not isinstance(request,PendingChatSkillRequest):raise ValueError('Typed pending request required')
        spec=next((s for s in SPECS if s[0]==request.key),None)
        if spec is None or spec[1]!=family or spec[-1]!=request.kind:raise ValueError('Request family/kind differs from selected consumer')
        if type(request.sender_dword) is not int or not 0<=request.sender_dword<=0xffffffff:raise ValueError('Full parsed sender DWORD required')
        expected=((0x180,1,1),(0x184,4,request.kind),(0x188,4,request.sender_dword))
        if request.context_stores!=expected:raise ValueError('Producer pending store projection differs from source triplet')
        self.pending_stores=tuple((MESSAGE_CONTEXT+offset,width,value) for offset,width,value in expected)
        self.consumer=ChatConsumerFrame(family,actor_context_dword)

    def advance(self,o):
        if not isinstance(o,ChatConsumerObservation):raise ValueError('Typed consumer observation required')
        if self.final is not None:return self.final
        if not self.producer.complete:
            return PendingConsumerPlan(False,'producer_incomplete',self.producer,missing=self.producer.missing)
        if self.consumer is None:
            self.final=PendingConsumerPlan(True,'no_new_request',self.producer)
            return self.final
        request=self.producer.queued_request
        # These are explicitly stable own values between producer and consumer.
        # They are not inferred live values for independently timed native reads.
        p=self.consumer.advance(bind_stable_pending_observation(o,self.family,1,request.kind,request.sender_dword))
        result=PendingConsumerPlan(p.complete,'consumer_returned' if p.complete else 'consumer_incomplete',self.producer,p,self.pending_stores,p.missing)
        if p.complete:self.final=result
        return result
