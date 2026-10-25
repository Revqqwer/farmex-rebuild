"""0045f228 source string profile control; no native memory or file access."""
from dataclasses import dataclass
from jail_preload import JailPreloadFrame,MASK
from profile_numeric import CURRENT_SOURCE


@dataclass(frozen=True)
class ProfileStringPlan:
    complete: bool
    formal_arguments: tuple=()
    reads: tuple=()
    calls: tuple=()
    assignment_intents: tuple=()
    return_eax: object=None
    needed: object=None
    source_sha256: str=CURRENT_SOURCE
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    assignment_effects_verified: bool=False
    live_compatibility_verified: bool=False


class ProfileStringFrame(JailPreloadFrame):
    def __init__(self,*,section,key,path,default,output,source_sha256=CURRENT_SOURCE):
        if source_sha256!=CURRENT_SOURCE:raise ValueError('Current string profile source required')
        if any(type(v) is not int or not 0<=v<=MASK for v in (section,key,path,default,output)):
            raise ValueError('Raw string profile formal arguments required')
        self.formal=(section,key,path,default,output);self.output=output
        self.slots={'section':12,'key':16,'path':20,'default':24}
        self.assignment_intents=[];self.return_eax=None
        super().__init__()

    def _plan(self,complete=False):
        return ProfileStringPlan(complete,self.formal,tuple(self.reads),tuple(self.calls),tuple(self.assignment_intents),
          self.return_eax,None if complete else self._needed)

    def _pointer(self,label,fallback):
        ref=('source_formal_slot',self.slots[label])
        self.reads.append((ref,4,label+'_test_pointer'))
        if not (yield from self._value(label+'_test_pointer')):return fallback
        self.reads.append((ref,4,label+'_value_pointer'))
        return (yield from self._value(label+'_value_pointer'))

    def _run(self):
        yield ('entry','0045f228')
        yield from self._call('prologue','source_SEH_setup_span')
        for label in ('default','path','key','section'):
            ref=('source_formal_slot',self.slots[label])
            yield from self._call(label+'_convert','00504ef8',(ref,ref))
        path=yield from self._pointer('path',0x52348a)
        default=yield from self._pointer('default',0x523489)
        key=yield from self._pointer('key',0x523488)
        section=yield from self._pointer('section',0x523487)
        yield from self._call('profile_api','GetPrivateProfileStringA',
                             (path,255,'source_profile_stack_buffer',default,key,section))
        # API's count EAX is not used by this source; managed construction reads buffer.
        yield from self._call('buffer_construct','00505bb8',('source_profile_stack_buffer','source_unicode_temp'))
        temp=yield from self._value('buffer_construct_eax')
        self.assignment_intents.append((self.output,temp))
        yield from self._call('output_assign','00505c88',(temp,self.output))
        self.reads.append((('source_formal_slot',8),4,'output_slot_return'))
        self.return_eax=yield from self._value('output_slot_return')
        yield from self._call('temp_cleanup','00505c64',(2,'source_unicode_temp'))
        for label in ('section','key','path','default'):
            yield from self._call(label+'_cleanup','004040f8',(2,('source_formal_slot',self.slots[label])))
        saved_fs=yield from self._value('saved_fs')
        yield from self._call('fs_restore','source_FS_restore_span',(saved_fs,))
        yield from self._call('epilogue','source_frame_restore_return_span')
