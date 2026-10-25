"""Bounded normal chat-segment composition; no whole-handler/native claim."""
from dataclasses import dataclass
from action_queue import QueueState
from chat_party_invite import parse_chat_prefix,ChatPartyInvitationFrame,ChatPartyObservation
from chat_prelude import ChatPreludeFrame,ChatPreludeObservation
from chat_commands import ChatCommandsFrame,ChatCommandsObservation
from chat_skill_requests import ChatSkillFrame,ChatSkillObservation
from chat_cleanup import ChatCleanupFrame,ChatCleanupObservation

@dataclass(frozen=True)
class ChatHandlerSegmentsPlan:
    complete:bool
    status:str
    prefix:object
    prelude:object=None
    commands:object=None
    party:object=None
    skills:object=None
    cleanup:object=None
    queue:object=None
    missing:str=''
    full_handler_verified:bool=False
    returned_EAX_verified:bool=False
    native_execution_verified:bool=False

class ChatHandlerSegmentsFrame:
    def __init__(self,commands_configuration,party_configuration,skills_configuration,captured,chat_log_byte,queue=None):
        self.prefix=parse_chat_prefix(captured);self.command_c=commands_configuration;self.party_c=party_configuration;self.skill_c=skills_configuration
        self.initial_queue=QueueState() if queue is None else queue
        if not isinstance(self.initial_queue,QueueState):raise ValueError('Typed initial own queue required')
        self.prelude_frame=None;self.command_frame=None;self.party_frame=None;self.skill_frame=None;self.cleanup_frame=None
        self.pre=None;self.cmd=None;self.party=None;self.skill=None;self.cleanup=None;self.final=None;self.queue=self.initial_queue
        if self.prefix.complete and self.prefix.message is not None:self.prelude_frame=ChatPreludeFrame(self.prefix.message,chat_log_byte)
    def _result(self,status,missing='',complete=False):
        return ChatHandlerSegmentsPlan(complete,status,self.prefix,self.pre,self.cmd,self.party,self.skill,self.cleanup,self.queue,missing)
    def advance(self,*,prelude=None,commands=None,party=None,party_enqueue=None,skills=None,cleanup_args=None,cleanup=None,after_commands_queue=None):
        if self.final is not None:return self.final
        if not self.prefix.complete:return self._result('needs_bytes',self.prefix.missing)
        if self.prefix.message is None:return self._result('outside_opcode10_scope','No bounded chat message')
        message=self.prefix.message
        if self.pre is None or not self.pre.complete:
            self.pre=self.prelude_frame.advance(ChatPreludeObservation() if prelude is None else prelude)
            if not self.pre.complete:return self._result('needs_prelude',self.pre.missing)
        if self.command_frame is None:self.command_frame=ChatCommandsFrame(self.command_c,message)
        if self.cmd is None or not self.cmd.complete:
            self.cmd=self.command_frame.advance(ChatCommandsObservation() if commands is None else commands)
            if not self.cmd.complete:return self._result('needs_commands',self.cmd.missing)
        if self.party_frame is None:
            if self.cmd.actions:
                if after_commands_queue is None:return self._result('needs_post_command_queue','Explicit post-command own queue snapshot')
                if not isinstance(after_commands_queue,QueueState):raise ValueError('Typed post-command own queue required')
                n=len(self.initial_queue.records)
                if after_commands_queue.records[:n]!=self.initial_queue.records or after_commands_queue.next_id<self.initial_queue.next_id:
                    raise ValueError('Post-command queue loses initial prefix')
                self.queue=after_commands_queue
            self.party_frame=ChatPartyInvitationFrame(self.party_c,message,self.queue)
        if self.party is None or not self.party.complete:
            if party_enqueue is not None and type(party_enqueue) is not dict:raise ValueError('Reached party enqueue options must be a dict')
            self.party=self.party_frame.advance(ChatPartyObservation() if party is None else party,**({} if party_enqueue is None else party_enqueue))
            self.queue=self.party_frame.queue
            if not self.party.complete:return self._result('needs_party',self.party.missing)
        if self.skill_frame is None:self.skill_frame=ChatSkillFrame(self.skill_c,message)
        if self.skill is None or not self.skill.complete:
            self.skill=self.skill_frame.advance(ChatSkillObservation() if skills is None else skills)
            if not self.skill.complete:return self._result('needs_skills',self.skill.missing)
        if self.skill.next_address!='0045730e':
            return self._result('unmodeled_notice_tail','Unmodeled source span '+self.skill.next_address+'..0045730e')
        if self.cleanup_frame is None:
            if cleanup_args is None:return self._result('needs_cleanup_snapshot','Original cleanup frame/local snapshot')
            self.cleanup_frame=ChatCleanupFrame(cleanup_args)
        self.cleanup=self.cleanup_frame.advance(ChatCleanupObservation() if cleanup is None else cleanup)
        if not self.cleanup.complete:return self._result('needs_cleanup',self.cleanup.missing)
        self.final=self._result('normal_segments_returned',complete=True);return self.final
