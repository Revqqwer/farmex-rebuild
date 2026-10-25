"""00412f48 normal configuration control; all reads/calls are inert observations.

Unicode construction/dereference spans and RTL/string/profile helpers remain
opaque. This module never opens config files or materializes account strings.
"""
from dataclasses import dataclass
from jail_preload import JailPreloadFrame,MASK

CURRENT_SOURCE='febdac805f370fb3ecc1ba5bf76482eb1f3d9b52c080113eb1dc9f12d2e45759'

COMMON=(('captcha_enabled',0x50b356,0x50b34e,0x561ed0,1),
        ('captcha_service',0x50b366,0x50b35e,0x561ed4,4))
USKO=(('usko_login',0x50b382,0x50b37d,0x50b2d8,1),
      ('usko_full',0x50b38d,0x50b388,0x50b2d9,1),
      ('usko_server',0x50b39c,0x50b397,0x50b2cc,4),
      ('usko_channel',0x50b3ad,0x50b3a8,0x50b2d0,4),
      ('usko_character',0x50b3bf,0x50b3ba,0x50b2d4,4))
STEAM=(('steam_enabled',0x50b3e8,0x50b3dd,0x50b2d8,1),
       ('steam_full',0x50b3fb,0x50b3f0,0x50b2d9,1),
       ('steam_server',0x50b410,0x50b405,0x50b2cc,4),
       ('steam_channel',0x50b427,0x50b41c,0x50b2d0,4),
       ('steam_character',0x50b43f,0x50b434,0x50b2d4,4))


@dataclass(frozen=True)
class RelogConfigPlan:
    complete: bool
    reads: tuple=()
    calls: tuple=()
    stores: tuple=()
    string_assignments: tuple=()
    copy_intents: tuple=()
    branch: object=None
    needed: object=None
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False
    source_sha256: str=CURRENT_SOURCE


class RelogConfigFrame(JailPreloadFrame):
    def __init__(self,source_sha256=CURRENT_SOURCE):
        if source_sha256!=CURRENT_SOURCE:raise ValueError('Current pinned config source required')
        self.stores=[];self.string_assignments=[];self.copy_intents=[];self.branch=None
        super().__init__()

    def _plan(self,complete=False):
        return RelogConfigPlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.stores),
          tuple(self.string_assignments),tuple(self.copy_intents),self.branch,None if complete else self._needed)

    def _construct(self,label,literal):
        yield from self._call(label,'source_unicode_ctor_and_EAX_dereference_span',(literal,))
        return (yield from self._value(label+'_pointer'))

    def _cleanup(self,label,ref,unicode=False):
        yield from self._call(label,'00505c64' if unicode else '004040f8',(2,ref))

    def _scalar(self,label,key,section,dest,width):
        handle=yield from self._read(label+'.handle',0x553e58)
        kp=yield from self._construct(label+'.key',key)
        sp=yield from self._construct(label+'.section',section)
        # The two source wrappers have distinct physical push arrangements.
        args=(0,handle,kp,sp) if width==1 else (handle,0,kp,sp)
        yield from self._call(label+'.read','0045f508' if width==1 else '0045f5f4',args)
        raw=yield from self._value(label+'.eax')
        self.stores.append((dest,width,raw&255 if width==1 else raw))
        yield from self._cleanup(label+'.section_cleanup',('source_section_temp',label))
        yield from self._cleanup(label+'.key_cleanup',('source_key_temp',label))

    def _string(self,label,key,section,destination=None):
        default=yield from self._construct(label+'.default',0x50b314)
        handle=yield from self._read(label+'.handle',0x553e58)
        kp=yield from self._construct(label+'.key',key)
        sp=yield from self._construct(label+'.section',section)
        yield from self._call(label+'.output_prepare','00404a78',(('source_unicode_output',label),))
        out=yield from self._value(label+'.output_eax')
        yield from self._call(label+'.read','0045f228',(default,handle,kp,sp,out))
        yield from self._call(label+'.convert','004073a0',
                             (('source_unicode_output',label),('source_ansi_output',label)))
        if destination is not None:
            yield from self._call(label+'.assign','005050e4',(('source_ansi_output',label),destination))
            self.string_assignments.append((destination,('source_ansi_output',label)))
            yield from self._cleanup(label+'.ansi_cleanup',('source_ansi_output',label))
        yield from self._cleanup(label+'.output_cleanup',('source_unicode_output',label),True)
        yield from self._cleanup(label+'.section_cleanup',('source_section_temp',label))
        yield from self._cleanup(label+'.key_cleanup',('source_key_temp',label))
        yield from self._cleanup(label+'.default_cleanup',('source_default_temp',label))

    def _local(self,label,local):
        self.reads.append((('source_ansi_local',local),4,label))
        return (yield from self._value(label))

    def _length(self,label,local,dest):
        pointer=yield from self._local(label+'.pointer',local)
        length=0
        if pointer:
            yield from self._call(label+'.metadata','00413a04',(('source_ansi_output',local),))
            metadata=yield from self._value(label+'.metadata_eax')
            length=yield from self._read(label+'.length',(metadata+8)&MASK)
        self.stores.append((dest,4,length))

    def _source(self,label,local,fallback):
        pointer=yield from self._local(label+'.test',local)
        if pointer:return (yield from self._local(label+'.value',local))
        return fallback

    def _credentials(self):
        # Allocation returns are stored even if zero. No allocation is executed.
        for label,dest in (('id_alloc',0x553c5c),('pw_alloc',0x553c60)):
            yield from self._call(label,'VirtualAlloc',(0x40,0x1000,0x32,0))
            self.stores.append((dest,4,(yield from self._value(label+'_eax'))))
        yield from self._string('id',0x50b3ce,0x50b3c9)
        yield from self._string('pw',0x50b3d6,0x50b3d1)
        yield from self._call('id_empty','source_ansi_literal_construct_span',(0x50b3d9,))
        yield from self._call('id_compare','00505154',('source_id_empty_temp',('source_ansi_output','id')))
        id_result=(yield from self._value('id_compare_eax'))&255
        permitted=False
        if id_result:
            yield from self._call('pw_empty','source_ansi_literal_construct_span',(0x50b3da,))
            yield from self._call('pw_compare','00505154',('source_pw_empty_temp',('source_ansi_output','pw')))
            permitted=bool((yield from self._value('pw_compare_eax'))&255)
            yield from self._cleanup('pw_empty_cleanup','source_pw_empty_temp')
        yield from self._cleanup('id_empty_cleanup','source_id_empty_temp')
        if permitted:
            yield from self._length('id_length','id',0x50b2c4)
            yield from self._length('pw_length','pw',0x50b2c8)
            source_id=yield from self._source('id_copy_source','id',0x50b3db)
            source_pw=yield from self._source('pw_copy_source','pw',0x50b3dc)
            for label,source,length_slot,destination_slot in (
                ('id_copy',source_id,0x50b2c4,0x553c5c),('pw_copy',source_pw,0x50b2c8,0x553c60)):
                length=yield from self._read(label+'.length',length_slot)
                dest=yield from self._read(label+'.destination',destination_slot)
                self.copy_intents.append((dest,source,length))
                yield from self._call(label,'_memcpy',(length,source,dest))
        yield from self._cleanup('pw_cleanup',('source_ansi_output','pw'))
        yield from self._cleanup('id_cleanup',('source_ansi_output','id'))

    def _run(self):
        yield ('entry','00412f48')
        yield from self._call('prologue','source_SEH_setup_span')
        for row in COMMON:yield from self._scalar(*row)
        yield from self._string('captcha_detail',0x50b376,0x50b36e,0x561ed8)
        self.reads.append((0x553e46,1,'mode_byte'))
        mode=yield from self._value('mode_byte')
        self.branch='USKO' if mode==1 else 'STEAMLOGIN'
        for row in USKO if mode==1 else STEAM:yield from self._scalar(*row)
        if mode==1:yield from self._credentials()
        saved_fs=yield from self._value('saved_fs')
        yield from self._call('fs_restore','source_FS_restore_span',(saved_fs,))
        yield from self._call('epilogue','source_frame_restore_return_span')
