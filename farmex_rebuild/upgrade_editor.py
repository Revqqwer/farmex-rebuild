"""Actual Upgrade select-all/target-ID data continuations; no game IO.

Own UI setters replace local frontend effects only. Runtime gate/target and
format/cleanup normal receipts are explicit captured observations.
"""
from dataclasses import dataclass
from target_id_frames import TargetIdFrame

GROUP='frmMain/MainTab/SheetUpgrade/grpUpgradeItems/'
SELECT_PATH=GROUP+'btnUpgradeSelectAll'
ID_PATH='frmMain/MainTab/SheetUpgrade/GroupBox44/btnSetUpgradeAnvilID'
REFRESH_PATH=GROUP+'btnUpgradeRefresh'
ANVIL_PATH='frmMain/MainTab/SheetUpgrade/GroupBox44/txtUpgradeAnvilID'
LIST_PATH=GROUP+'LwUpgradeItems'
START_PATH=GROUP+'btnUpgradeAll'
STOP_PATH=GROUP+'btnUpgradeStop'
ARMOR_PATH='frmMain/MainTab/SheetUpgrade/GroupBox23/btnUpgradeArmorAl'
METHODS={SELECT_PATH:'select_all',ID_PATH:'target_id',REFRESH_PATH:'refresh',START_PATH:'start',STOP_PATH:'stop',ARMOR_PATH:'armor'}
OWN_TIMER_PERIOD_MS=100


@dataclass(frozen=True)
class UpgradeEditorObservation:
    gate_byte:object=None
    target:object=None
    format_returned:object=None
    cleanup_returned:object=None


@dataclass(frozen=True)
class UpgradeEditorContext:
    invocation:int
    generation:int
    method:str
    phase:str
    needed:object


@dataclass(frozen=True)
class UpgradeEditorResult:
    complete:bool
    done:bool
    status:str
    needed:object=None
    selected_rows:int=0
    text:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class UpgradeEditorFrame:
    def __init__(self,method,sink):
        if method not in ('select_all','target_id'):raise ValueError('Known Upgrade editor event required')
        self.method=method;self.sink=sink;self.target=TargetIdFrame();self.target_value=None
        self.phase='gate' if method=='select_all' else 'target'
        self.index=0;self.text=None;self.cache={};self.busy=False
        self.result=UpgradeEditorResult(False,False,'queued')

    def _out(self,status,complete=False,done=False,needed=None,error=None):
        self.result=UpgradeEditorResult(complete,done,status,needed,self.index,self.text,error)
        return self.result

    def cancel(self,reason):
        if not self.result.done:self._out('cancelled',done=True,error=reason)
        return self.result

    def hold(self,error):
        if not self.result.done:self._out('needs_observation',needed=self.result.needed,error=str(error))
        return self.result

    def advance(self,o=None):
        if self.result.done or self.busy:return self.result
        o=UpgradeEditorObservation() if o is None else o
        if not isinstance(o,UpgradeEditorObservation):raise ValueError('Typed Upgrade editor observation required')
        self.busy=True
        def normal(field):
            if self.cache.get(field) is True:return True
            value=getattr(o,field)
            if value is not None and type(value) is not bool:raise ValueError('Explicit source normal return required')
            if value is True:self.cache[field]=True;return True
            return False
        try:
            for _ in range(64):
                if self.result.done:return self.result
                if self.phase=='gate':
                    gate=o.gate_byte
                    if gate is None:return self._out('needs_observation',needed=('gate_byte',))
                    if type(gate) is not int or not 0<=gate<=255:raise ValueError('Raw source561f55 BYTE required')
                    self.cache['gate_byte']=gate
                    if gate==0:return self._out('gate_closed',True,True)
                    self.phase='rows'
                elif self.phase=='rows':
                    try:
                        count=self.sink.count()
                        if type(count) is not int or not -0x80000000<=count<0x80000000:raise ValueError('Signed32 fresh row count required')
                        if count<=self.index:return self._out('selected_all',True,True)
                        self.sink.set_checked(self.index,True);self.index+=1
                    except (OSError,ValueError,IndexError) as error:
                        if self.result.done:return self.result
                        return self._out('selection_incomplete',done=True,error=str(error))
                elif self.phase=='target':
                    p=self.target.advance(o.target)
                    if not p.complete:return self._out('needs_observation',needed=('target',p.needed))
                    self.target_value=p.value
                    if self.target_value==0:return self._out('no_target',True,True)
                    self.phase='format'
                elif self.phase=='format':
                    if not normal('format_returned'):return self._out('needs_observation',needed=('format_returned',))
                    value=self.target_value
                    self.text=str(value if value<0x80000000 else value-(1<<32));self.phase='text'
                elif self.phase=='text':
                    try:self.sink.set_anvil_text(self.text)
                    except (OSError,ValueError,IndexError) as error:
                        if self.result.done:return self.result
                        return self._out('text_incomplete',done=True,error=str(error))
                    self.phase='text_return'
                elif self.phase=='text_return':
                    ready=getattr(self.sink,'anvil_text_ready',None)
                    try:returned=True if ready is None else ready()
                    except (OSError,ValueError,IndexError) as error:
                        if self.result.done:return self.result
                        return self._out('text_incomplete',done=True,error=str(error))
                    if returned is not True:return self._out('needs_observation',needed=('nested_parameters',))
                    self.phase='cleanup'
                elif self.phase=='cleanup':
                    if not normal('cleanup_returned'):return self._out('needs_observation',needed=('cleanup_returned',))
                    return self._out('target_id_set',True,True)
                else:raise ValueError('Unknown Upgrade editor phase')
            return self._out('continuation',needed=('own_chunk',))
        finally:self.busy=False
