"""Incremental004f7af8 start/stop ->shared own source-clock runner.

No game reads/sends. Own sink applies UI effects; captured source normal
receipts gate subsequent phases. Prefix mode/queue changes are not rolled back.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping
from operation_engine import UpgradeRunner
from upgrade_parameter_frame import UpgradeParameterState
from upgrade_scroll_frame import UpgradeScrollFrame
from name_codec import WindowsNameCodec
from rtl_integer32 import parse_rtl_integer32

START_PATH='frmMain/MainTab/SheetUpgrade/grpUpgradeItems/btnUpgradeAll'
STOP_PATH='frmMain/MainTab/SheetUpgrade/grpUpgradeItems/btnUpgradeStop'


@dataclass(frozen=True)
class UpgradeStartFrameObservation:
    gate_byte:object=None
    start_ui_returned:object=None
    stop_ui_returned:object=None
    vector_end_returned:object=None
    vector_begin_returned:object=None
    vector_erase_returned:object=None
    scroll_conversion_returned:object=None
    scroll_lookup:object=None
    scroll_lookup_returned:object=None
    scroll_cleanup_returned:object=None
    caption_returns:object=field(default_factory=dict)
    caption_cleanup_returns:object=field(default_factory=dict)
    append_returns:object=field(default_factory=dict)


@dataclass(frozen=True)
class UpgradeStartFrameResult:
    complete:bool
    done:bool
    status:str
    needed:object=None
    index:int=0
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class UpgradeStartFrame:
    def __init__(self,method,runner,parameters,sink,*,entry='callback'):
        if method not in ('start','stop'):raise ValueError('Start/stop method required')
        if entry not in ('callback','helper'):raise ValueError('Explicit callback or inner helper entry required')
        if not isinstance(runner,UpgradeRunner) or not runner.source_clock:raise ValueError('Shared source-clock runner required')
        if runner.source_pending is not None:raise ValueError('Own in-flight worker must finish before rebinding start/stop')
        if not isinstance(parameters,UpgradeParameterState):raise ValueError('Cached parameter state required')
        self.method=method;self.runner=runner;self.parameters=parameters;self.sink=sink
        self.phase='gate' if entry=='callback' else 'helper_entry';self.cache={};self.scroll=UpgradeScrollFrame();self.scroll_text=None;self.index=0
        self.captions={};self.keys={};self.busy=False;self.result=UpgradeStartFrameResult(False,False,'queued')
    def _out(self,status,complete=False,done=False,needed=None,error=None):
        self.result=UpgradeStartFrameResult(complete,done,status,needed,self.index,error);return self.result
    def cancel(self,reason):
        if not self.result.done:self._out('cancelled',done=True,error=reason)
        return self.result
    def hold(self,error):
        if not self.result.done:self._out('needs_observation',needed=self.result.needed,error=str(error))
        return self.result
    def advance(self,o=None):
        if self.result.done or self.busy:return self.result
        o=UpgradeStartFrameObservation() if o is None else o
        if not isinstance(o,UpgradeStartFrameObservation):raise ValueError('Typed Upgrade start observations required')
        self.busy=True
        class Missing(Exception):pass
        def normal(field,group=None):
            key=(group,field)
            if self.cache.get(key) is True:return
            data=getattr(o,group) if group else None
            if group and not isinstance(data,Mapping):raise ValueError('Indexed source normal receipts required')
            value=data.get(field) if group else getattr(o,field)
            if value is not None and type(value) is not bool:raise ValueError('Explicit source normal receipt required')
            if value is not True:raise Missing(key)
            self.cache[key]=True
        def ui(name,value):
            self.sink.set_enabled(name,value)
            previous=getattr(self.runner,'source_start_ui',(None,None))
            self.runner.source_start_ui=(value,previous[1]) if name=='start' else (previous[0],value)
        try:
            for _ in range(128):
                if self.result.done:return self.result
                self._out('advancing',needed=('phase',self.phase,self.index))
                if self.phase=='gate':
                    gate=o.gate_byte
                    if gate is None:raise Missing(('gate_byte',))
                    if type(gate) is not int or not 0<=gate<=255:raise ValueError('Raw561f55 BYTE required')
                    if gate==0:return self._out('gate_closed',True,True)
                    if self.method=='stop':self.runner.state=0
                    self.phase='start_ui'
                elif self.phase=='helper_entry':
                    if self.method=='stop':self.runner.state=0
                    self.phase='start_ui'
                elif self.phase=='start_ui':ui('start',self.method=='stop');self.phase='start_ui_return'
                elif self.phase=='start_ui_return':normal('start_ui_returned');self.phase='stop_ui'
                elif self.phase=='stop_ui':ui('stop',self.method=='start');self.phase='stop_ui_return'
                elif self.phase=='stop_ui_return':
                    normal('stop_ui_returned')
                    if self.method=='stop':return self._out('stopped',True,True)
                    self.phase='vector_end'
                elif self.phase=='vector_end':normal('vector_end_returned');self.phase='vector_begin'
                elif self.phase=='vector_begin':normal('vector_begin_returned');self.phase='vector_erase'
                elif self.phase=='vector_erase':normal('vector_erase_returned');self.runner.queue=();self.phase='cached_scroll'
                elif self.phase=='cached_scroll':
                    if self.scroll_text is None:
                        if 'scroll_bytes' not in self.cache:
                            data=self.parameters.scroll_bytes
                            if data is None:raise Missing(('cached_scroll_bytes',))
                            if type(data) is not bytes:raise ValueError('Cached immutable ANSI scroll required')
                            self.cache['scroll_bytes']=data
                        data=self.cache['scroll_bytes']
                        if not data:self.scroll_text=''
                        else:
                            cp=self.parameters.scroll_codepage
                            if cp is None:raise Missing(('cached_scroll_codepage',))
                            self.scroll_text=WindowsNameCodec(cp).decode(data)
                    normal('scroll_conversion_returned');self.phase='scroll'
                elif self.phase=='scroll':
                    p=self.scroll.advance(o.scroll_lookup)
                    if not p.complete:raise Missing(('scroll',p.needed))
                    normal('scroll_lookup_returned')
                    self.runner.source_scroll_index=p.relative_index;self.phase='scroll_cleanup'
                elif self.phase=='scroll_cleanup':normal('scroll_cleanup_returned');self.phase='count'
                elif self.phase=='count':
                    count=self.sink.count()
                    if type(count) is not int or not -0x80000000<=count<0x80000000:raise ValueError('Fresh signed row count required')
                    if count<=self.index:self.runner.state=1;return self._out('started',True,True)
                    self.phase='checked'
                elif self.phase=='checked':
                    checked=self.sink.checked(self.index)
                    if type(checked) is not bool:raise ValueError('Own checked boolean required')
                    self.phase='caption' if checked else 'next'
                elif self.phase=='caption':
                    if self.index not in self.captions:
                        caption=self.sink.caption(self.index)
                        if type(caption) is not str:raise ValueError('Own caption Unicode required')
                        self.captions[self.index]=caption
                    parser=parse_rtl_integer32(self.captions[self.index])
                    if not parser.accepted:raise Missing(('caption_exception_outcome',self.index,parser.code))
                    normal(self.index,'caption_returns');self.keys[self.index]=parser.dword;self.phase='caption_cleanup'
                elif self.phase=='caption_cleanup':normal(self.index,'caption_cleanup_returns');self.phase='append'
                elif self.phase=='append':
                    normal(self.index,'append_returns')
                    self.runner.queue=self.runner.queue+(self.keys[self.index],);self.phase='next'
                elif self.phase=='next':self.index+=1;self.phase='count'
                else:raise ValueError('Unknown Upgrade start frame phase')
            return self._out('continuation',needed=('own_chunk',))
        except Missing as error:return self._out('needs_observation',needed=error.args[0])
        finally:self.busy=False
