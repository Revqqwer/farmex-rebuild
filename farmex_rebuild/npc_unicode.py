"""Captured late NPC ANSI-to-Unicode continuation; no game/native calls.

Own Windows flags0 decoding has a finite pinned RTL reference. Source helper
normal returns remain independent observations. No implicit host codepage.
"""
from dataclasses import dataclass
from name_codec import WindowsNameCodec
from route_npc_click import NpcValueCapture


@dataclass(frozen=True)
class NpcUnicodeObservation:
    ansi_is_null:object=None
    codepage_word:object=None
    effective_codepage:object=None
    rtl_returned:object=None
    wrapper_returned:object=None
    constructor_returned:object=None


@dataclass(frozen=True)
class NpcUnicodePlan:
    complete:bool
    status:str
    needed:object=None
    capture:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class NpcUnicodeFrame:
    """One late conversion, with reached values and True receipts retained.

    ANSI bytes are the completed source name producer's PChar contents, not
    fresh provider text. Nullness is explicit even for empty contents. A zero
    header codepage needs an explicit effective codepage only on conversion.
    """
    def __init__(self,ansi_bytes):
        if type(ansi_bytes) is not bytes or b'\0' in ansi_bytes:
            raise ValueError('Completed NUL-free ANSI name bytes required')
        self.ansi_bytes=ansi_bytes;self.cache={};self.text=None;self.final=None

    def advance(self,incoming=None):
        if self.final is not None:return self.final
        incoming=NpcUnicodeObservation() if incoming is None else incoming
        if not isinstance(incoming,NpcUnicodeObservation):raise ValueError('Typed Unicode observations required')
        class Missing(Exception):pass
        def need(field,kind):
            if field in self.cache:return self.cache[field]
            value=getattr(incoming,field)
            if value is None:raise Missing(field)
            if kind=='word':
                if type(value) is not int or not 0<=value<=65535:raise ValueError('Raw codepage WORD required')
            elif type(value) is not kind:raise ValueError('Explicit reached observation required: '+field)
            if field=='ansi_is_null' and value and self.ansi_bytes:
                raise ValueError('Null ANSI pointer cannot contain nonempty name bytes')
            if field=='effective_codepage' and value==0:raise ValueError('Concrete nonzero effective codepage required')
            if field.endswith('_returned') and value is not True:raise Missing(field)
            self.cache[field]=value;return value
        try:
            null=need('ansi_is_null',bool)
            cp=None if null else need('codepage_word','word')
            if self.text is None:
                # Nil clears directly; a nonnil counted empty string also
                # clears before calling the locale conversion wrapper.
                if not self.ansi_bytes:self.text=''
                else:
                    if cp==0:cp=need('effective_codepage','word')
                    self.text=WindowsNameCodec(cp).decode(self.ansi_bytes)
            for field in ('rtl_returned','wrapper_returned','constructor_returned'):need(field,bool)
            self.final=NpcUnicodePlan(True,'captured_unicode',capture=NpcValueCapture(self.text,True))
            return self.final
        except Missing as error:return NpcUnicodePlan(False,'needs_observation',needed=(str(error),))
