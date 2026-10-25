"""Ordered004f7620 parameter producer; captured normal spans, no game IO.

The source updates cached ANSI scroll, then Anvil lowDWORD, then interval
lowDWORD. Prefix effects survive later gaps. No native catch is synthesized
for scalar text rejected by the pinned normal RTL parser.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping
from name_codec import WindowsNameCodec
from rtl_integer import parse_rtl_integer


@dataclass
class UpgradeParameterState:
    scroll_bytes:object=None
    scroll_codepage:object=None
    anvil_dword:object=None
    interval_dword:object=None

    def __post_init__(self):
        if self.scroll_bytes is not None and type(self.scroll_bytes) is not bytes:raise ValueError('Immutable cached scroll bytes required')
        if self.scroll_codepage is not None and (type(self.scroll_codepage) is not int or not 1<=self.scroll_codepage<=65535):raise ValueError('Concrete scroll codepage required')
        for value in (self.anvil_dword,self.interval_dword):
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('Raw cached parameter DWORD required')


@dataclass(frozen=True)
class UpgradeParameterObservation:
    gate_byte:object=None
    text_init_returns:object=field(default_factory=dict)
    text_get_returns:object=field(default_factory=dict)
    effective_codepage:object=None
    scroll_conversion_returned:object=None
    scroll_assignment_returned:object=None
    scroll_ansi_cleanup_returned:object=None
    scroll_unicode_cleanup_returned:object=None
    scalar_qwords:object=field(default_factory=dict)
    scalar_returns:object=field(default_factory=dict)
    number_cleanup_returns:object=field(default_factory=dict)


@dataclass(frozen=True)
class UpgradeParameterResult:
    complete:bool
    done:bool
    status:str
    needed:object=None
    writes:tuple=()
    requests:tuple=()
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class UpgradeParameterFrame:
    method='parameters'
    def __init__(self,state,read_text):
        if not isinstance(state,UpgradeParameterState) or not callable(read_text):raise ValueError('Own parameter state and text reader required')
        self.state=state;self.read_text=read_text;self.phase='gate';self.field='scroll'
        self.cache={};self.texts={};self.parsers={};self.qwords={};self.encoded=None
        self.codepage=None;self.used_default=None;self.writes=[];self.requests=[];self.busy=False
        self.result=UpgradeParameterResult(False,False,'queued')

    def _out(self,status,complete=False,done=False,needed=None,error=None):
        self.result=UpgradeParameterResult(complete,done,status,needed,tuple(self.writes),tuple(self.requests),error)
        return self.result

    def cancel(self,reason):
        if not self.result.done:self._out('cancelled',done=True,error=reason)
        return self.result

    def hold(self,error):
        if not self.result.done:self._out('needs_observation',needed=self.result.needed,error=str(error))
        return self.result

    def advance(self,o=None):
        if self.result.done or self.busy:return self.result
        o=UpgradeParameterObservation() if o is None else o
        if not isinstance(o,UpgradeParameterObservation):raise ValueError('Typed parameter producer observations required')
        self.busy=True
        class Missing(Exception):pass
        def grouped(group,name):
            value=getattr(o,group)
            if not isinstance(value,Mapping):raise ValueError('Indexed reached parameter observations required')
            return value.get(name)
        def normal(field,group=None):
            key=(group,field)
            if self.cache.get(key) is True:return
            value=getattr(o,field) if group is None else grouped(group,field)
            if value is not None and type(value) is not bool:raise ValueError('Explicit parameter normal receipt required')
            if value is not True:raise Missing(key)
            self.cache[key]=True
        try:
            for _ in range(48):
                if self.result.done:return self.result
                self._out('advancing',needed=('phase',self.phase,self.field))
                if self.phase=='gate':
                    value=o.gate_byte
                    if value is None:raise Missing(('gate_byte',))
                    if type(value) is not int or not 0<=value<=255:raise ValueError('Raw561f55 gate BYTE required')
                    self.cache['gate']=value
                    if value==0:return self._out('gate_closed',True,True)
                    self.phase='text_init'
                elif self.phase=='text_init':normal(self.field,'text_init_returns');self.phase='text'
                elif self.phase=='text':
                    if self.field not in self.texts:
                        value=self.read_text(self.field)
                        if type(value) is not str:raise ValueError('Reached immutable Unicode Text required')
                        self.texts[self.field]=value
                    self.phase='text_return'
                elif self.phase=='text_return':
                    normal(self.field,'text_get_returns')
                    self.phase='scroll_convert' if self.field=='scroll' else 'scalar'
                elif self.phase=='scroll_convert':
                    if self.encoded is None:
                        if not self.texts['scroll']:
                            self.encoded=b'';self.codepage=None;self.used_default=False
                        else:
                            cp=o.effective_codepage
                            if cp is None:raise Missing(('effective_codepage',))
                            codec=WindowsNameCodec(cp)
                            self.encoded,self.used_default=codec.encode(self.texts['scroll']);self.codepage=cp
                    normal('scroll_conversion_returned');self.phase='scroll_assign'
                elif self.phase=='scroll_assign':
                    normal('scroll_assignment_returned')
                    self.state.scroll_bytes=self.encoded;self.state.scroll_codepage=self.codepage
                    self.writes.append(('scroll_ansi',self.encoded,self.codepage));self.phase='scroll_ansi_cleanup'
                elif self.phase=='scroll_ansi_cleanup':normal('scroll_ansi_cleanup_returned');self.phase='scroll_unicode_cleanup'
                elif self.phase=='scroll_unicode_cleanup':
                    normal('scroll_unicode_cleanup_returned');self.field='anvil';self.phase='text_init'
                elif self.phase=='scalar':
                    name=self.field;default=0 if name=='anvil' else 2000
                    if name not in self.parsers:
                        self.parsers[name]=parse_rtl_integer(self.texts[name])
                        self.requests.append(('0045ef80',name,self.texts[name],default))
                    parser=self.parsers[name]
                    if name not in self.qwords:
                        observed=grouped('scalar_qwords',name)
                        if observed is not None and (type(observed) is not int or not 0<=observed<(1<<64)):
                            raise ValueError('Raw captured helper QWORD required')
                        if parser.accepted:
                            if observed is not None and observed!=parser.qword:raise ValueError('Captured helper result conflicts with accepted scalar model')
                            self.qwords[name]=parser.qword
                        elif observed is None:raise Missing(('scalar_qwords',name))
                        else:self.qwords[name]=observed
                    normal(name,'scalar_returns')
                    value=self.qwords[name]&0xffffffff
                    if name=='anvil':self.state.anvil_dword=value
                    else:self.state.interval_dword=value
                    self.writes.append((name+'_dword',value));self.phase='number_cleanup'
                elif self.phase=='number_cleanup':
                    normal(self.field,'number_cleanup_returns')
                    if self.field=='wait':return self._out('parameters_updated',True,True)
                    self.field='wait';self.phase='text_init'
                else:raise ValueError('Unknown Upgrade parameter phase')
            raise ValueError('Own parameter continuation phase bound exceeded')
        except Missing as error:return self._out('needs_observation',needed=error.args[0])
        finally:self.busy=False
