"""One captured invite invocation with cached source prefix/local reply queue."""
from dataclasses import replace
from action_queue import QueueState
from party_invitation import PartyInviteConfiguration,PartyInviteObservation,plan_party_invitation
from party_replies import PartyReplyFrame

class PartyInvitationFrame:
    def __init__(self,configuration,captured,queue=None):
        if not isinstance(configuration,PartyInviteConfiguration) or type(captured) is not bytes:raise ValueError('Typed invite config and immutable captured bytes required')
        self.configuration=configuration;self.captured=captured;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own invite queue required')
        self.observation=PartyInviteObservation();self.reply_frame=None;self.final=None
    def advance(self,o,*,reply_gate=None,reply_tick=None):
        if not isinstance(o,PartyInviteObservation):raise ValueError('Typed invitation observations required')
        if self.final is not None:return self.final
        for _ in range(24):
            p=plan_party_invitation(self.configuration,self.captured,self.observation)
            if p.complete:self.final=p;return p
            if p.action is not None:
                if o.reply_execution is not None:raise ValueError('Owned invitation frame conflicts with external reply plan')
                if self.reply_frame is None:self.reply_frame=PartyReplyFrame(p.action,self.queue)
                child=self.reply_frame.advance(reply_gate,reply_tick);self.queue=self.reply_frame.queue
                self.observation=replace(self.observation,reply_execution=child)
                p=plan_party_invitation(self.configuration,self.captured,self.observation)
                if not child.complete:return p
            field={'0056228d BYTE':'blocked_byte_56228d','party-state EAX':'party_state_eax'}.get(p.missing)
            if field:
                value=getattr(o,field)
                if value is None:return p
                self.observation=replace(self.observation,**{field:value});continue
            if p.missing.endswith(' normal return'):
                label=p.missing[:-14]
                if o.helper_returns.get(label) is not True:return p
                self.observation=replace(self.observation,helper_returns={**self.observation.helper_returns,label:True});continue
            if p.missing=='name-filter EAX':
                if not o.use_owned_filter and o.filter_eax is None:return p
                self.observation=replace(self.observation,use_owned_filter=o.use_owned_filter,filter_eax=o.filter_eax);continue
            return p
        raise ValueError('Invitation frame exceeded source prefix budget')
