"""Current source numeric INI wrappers; no actual profile API or file access."""
from dataclasses import dataclass
from jail_preload import JailPreloadFrame,MASK

CURRENT_SOURCE='febdac805f370fb3ecc1ba5bf76482eb1f3d9b52c080113eb1dc9f12d2e45759'


@dataclass(frozen=True)
class ProfileNumericPlan:
    complete: bool
    kind: str
    formal_arguments: tuple=()
    reads: tuple=()
    calls: tuple=()
    return_eax: object=None
    needed: object=None
    source_sha256: str=CURRENT_SOURCE
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False


class ProfileNumericFrame(JailPreloadFrame):
    """Convert formal strings, capture API EAX, cleanup, restore FS and return.

    Converted pointers are fresh observations after opaque self-assignment RTL
    calls; original pointer arguments never stand in for converted strings.
    """
    def __init__(self,kind,*,section,key,path,default,source_sha256=CURRENT_SOURCE):
        if kind not in ('boolean','dword') or source_sha256!=CURRENT_SOURCE:
            raise ValueError('Current pinned numeric wrapper required')
        if any(type(v) is not int or not 0<=v<=MASK for v in (section,key,path,default)):
            raise ValueError('Raw formal numeric/profile arguments required')
        self.kind=kind;self.formal=(section,key,path,default);self.default=default;self.return_eax=None
        self.slots={'section':8,'key':12,'path':16 if kind=='boolean' else 20}
        super().__init__()

    def _plan(self,complete=False):
        return ProfileNumericPlan(complete,self.kind,self.formal,tuple(self.reads),tuple(self.calls),
          self.return_eax,None if complete else self._needed)

    def _pointer(self,label,fallback):
        ref=('source_formal_slot',self.slots[label])
        self.reads.append((ref,4,label+'_test_pointer'))
        first=yield from self._value(label+'_test_pointer')
        if not first:return fallback
        self.reads.append((ref,4,label+'_value_pointer'))
        return (yield from self._value(label+'_value_pointer'))

    def _run(self):
        yield ('entry','0045f508' if self.kind=='boolean' else '0045f5f4')
        yield from self._call('prologue','source_SEH_setup_span')
        for label in ('path','key','section'):
            ref=('source_formal_slot',self.slots[label])
            yield from self._call(label+'_convert','00504ef8',(ref,ref))
        base=0x52348f if self.kind=='boolean' else 0x523492
        path=yield from self._pointer('path',base+2)
        key=yield from self._pointer('key',base+1)
        section=yield from self._pointer('section',base)
        default=self.default&255 if self.kind=='boolean' else self.default
        yield from self._call('profile_api','GetPrivateProfileIntA',(path,default,key,section))
        raw=yield from self._value('profile_api_eax')
        self.return_eax=int(raw!=0) if self.kind=='boolean' else raw
        for label in ('section','key','path'):
            yield from self._call(label+'_cleanup','004040f8',(2,('source_formal_slot',self.slots[label])))
        saved_fs=yield from self._value('saved_fs')
        yield from self._call('fs_restore','source_FS_restore_span',(saved_fs,))
        yield from self._call('epilogue','source_frame_restore_return_span')
