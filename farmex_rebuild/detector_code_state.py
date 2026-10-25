"""Version-pinned detector code arithmetic and inert normal-path call plans."""
from dataclasses import dataclass
from types import MappingProxyType
from jail_preload import JailPreloadFrame,MASK

LEGACY='12f3e2dd13836b4f9ffec77c71cf04e505e7e92a2d5a527abf78aa566f359a54'
CURRENT='febdac805f370fb3ecc1ba5bf76482eb1f3d9b52c080113eb1dc9f12d2e45759'
REGIONS=MappingProxyType({LEGACY:(0x4e1464,0x4e2a64,'004e2a6c'),
                         CURRENT:(0x4e1464,0x4e2a80,'004e2a88')})


def transform_owned_bytes(data,mode):
    """Arithmetic for an owned immutable byte string starting at region offset0.

    This does not model guard failures, aliasing, concurrent writes or native
    executable state. It never reads or writes process memory.
    """
    if type(data) is not bytes or type(mode) is not int or mode not in (0,1):
        raise ValueError('Owned bytes and mode0/1 required')
    sign=1 if mode else -1
    return bytes((b+sign*(0x28 if i%2==0 else 0x40))&255 for i,b in enumerate(data))


@dataclass(frozen=True)
class DetectorCodeStatePlan:
    complete: bool
    reads: tuple=()
    calls: tuple=()
    stores: tuple=()
    byte_write_intents: tuple=()
    needed: object=None
    source_sha256: str=''
    native_execution_verified: bool=False
    byte_effects_verified: bool=False
    live_compatibility_verified: bool=False


class DetectorCodeStateFrame(JailPreloadFrame):
    """Opaque byte helpers may return without any successful memory effect.

    Mode is a raw DWORD, not a Boolean. The source ignores the outer
    VirtualProtect EAX and never restores its old protection in this body.
    Each reader full EAX is independently captured; ADD AL preserves upper bits.
    """
    def __init__(self,source_sha256,mode):
        if source_sha256 not in REGIONS:raise ValueError('Pinned source identity required')
        if type(mode) is not int or not 0<=mode<=MASK:raise ValueError('Raw mode DWORD required')
        self.source_sha256=source_sha256;self.mode=mode
        self.start,self.end,self.entry=REGIONS[source_sha256]
        self.stores=[];self.byte_write_intents=[]
        super().__init__()

    def _plan(self,complete=False):
        return DetectorCodeStatePlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.stores),
          tuple(self.byte_write_intents),None if complete else self._needed,self.source_sha256)

    def _run(self):
        yield ('entry',self.entry)
        yield from self._call('prologue','source_frame_setup_span')
        old=yield from self._read('state',0x56ff38)
        if self.mode!=old:
            yield from self._call('protect','VirtualProtect',
                ('source_old_protection_local',0x40,self.end-self.start,self.start))
            if self.mode in (0,1):
                for i in range(self.end-self.start):
                    label='byte%d'%i;address=self.start+i
                    yield from self._call(label+'.read','0045dbdc',(address,))
                    raw=yield from self._value(label+'.eax')
                    delta=(0x28 if i%2==0 else 0x40)*(1 if self.mode else -1)
                    full=(raw&0xffffff00)|(((raw&255)+delta)&255)
                    self.byte_write_intents.append((address,1,full&255,full))
                    yield from self._call(label+'.write','0045de4c',(full,address))
                self.stores.append((0x56ff38,4,self.mode))
        yield from self._call('epilogue','source_frame_restore_return_span')
