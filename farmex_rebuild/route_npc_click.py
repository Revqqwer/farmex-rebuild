"""Captured route-NPC data continuation; no game reads or native calls.

Name bytes are the explicitly captured final std::string contents, after the
source copy/assignment. Trade text is the separate source Unicode conversion.
This layer does not implement either producer or native cleanup/SEH/return.
"""
from dataclasses import dataclass

BUTTON_PATH='frmMain/RotaPanel/grpRouteAddNPC/btnRouteAddNPC'
OWN_TIMER_PERIOD_MS=100
NAME_RULES=((b'otion','Potion'),(b'DC','DC Sundries'),
            (b'undries','Sundries'),(b'rmor','Armor'),(b'eapon','Weapon'))


@dataclass(frozen=True)
class NpcValueCapture:
    value:object=None
    returned:object=None


@dataclass(frozen=True)
class NpcClickInput:
    target_gate:object=None
    target_lookup:object=None
    actor:object=None
    name_bytes:object=None
    target_classify:object=None
    dialog_text:object=None
    trade_text:object=None


@dataclass(frozen=True)
class NpcCaptureContext:
    invocation:int
    generation:int
    phase:str
    needed:object


@dataclass(frozen=True)
class NpcClickResult:
    complete:bool
    done:bool
    status:str
    needed:object=None
    row:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class NpcClickFrame:
    """Three fresh target captures, ordered name branches and prefix retention.

    Only reached valid values/True receipts are retained. No row exists until
    the source branch permits Add; User Trade conversion is demanded only
    after Add/caption. Own sink errors are terminal and retain written prefix.
    `complete` certifies this data-layer outcome, never native callback return.
    """
    def __init__(self,sink):
        self.sink=sink;self.cache={};self.phase='target_gate';self.row=None
        self.caption=None;self.first=None;self.second='-';self.busy=False
        self.result=NpcClickResult(False,False,'queued')

    def _result(self,status,complete=False,done=False,needed=None,error=None):
        self.result=NpcClickResult(complete,done,status,needed,self.row,error)
        return self.result

    def cancel(self,reason):
        if not self.result.done:self._result('cancelled',done=True,error=reason)
        return self.result

    def hold(self,error):
        if not self.result.done:
            self._result('needs_capture',needed=self.result.needed,error=str(error))
        return self.result

    def _capture(self,capture,name,kind):
        cached=self.cache.setdefault(name,{})
        supplied=getattr(capture,name)
        if supplied is not None and not isinstance(supplied,NpcValueCapture):
            raise ValueError('Typed reached capture required: '+name)
        if 'value' not in cached:
            value=None if supplied is None else supplied.value
            if value is None:return False,name+'.value',None
            if kind=='dword':
                if type(value) is not int or not 0<=value<=0xffffffff:
                    raise ValueError('Raw reached DWORD required: '+name)
            elif type(value) is not kind:
                raise ValueError('Reached value type differs: '+name)
            cached['value']=value
        if 'returned' not in cached:
            returned=None if supplied is None else supplied.returned
            if returned is not None and type(returned) is not bool:
                raise ValueError('Explicit normal receipt required: '+name)
            if returned is not True:return False,name+'.returned',None
            cached['returned']=True
        return True,None,cached['value']

    def advance(self,capture=None):
        if self.result.done or self.busy:return self.result
        self.busy=True
        try:
            if capture is None:capture=NpcClickInput()
            if not isinstance(capture,NpcClickInput):
                return self._result('needs_capture',needed=self.phase,error='Typed NPC input required')
            if self.row is not None:
                validate=getattr(self.sink,'validate',None)
                if callable(validate):validate(self.row)
            for _ in range(16):
                if self.result.done:return self.result
                if self.phase in ('target_gate','target_lookup','actor','name_bytes','target_classify','dialog_text','trade_text'):
                    field=self.phase
                    kind=bytes if field=='name_bytes' else str if field in ('dialog_text','trade_text') else 'dword'
                    try:ready,needed,value=self._capture(capture,field,kind)
                    except ValueError as error:
                        return self._result('needs_capture',needed=field,error=str(error))
                    if not ready:return self._result('needs_capture',needed=needed)
                    if field=='target_gate':
                        if value==0:return self._result('no_selection',True,True)
                        self.phase='target_lookup'
                    elif field=='target_lookup':self.phase='actor'
                    elif field=='actor':
                        if value==0:return self._result('lookup_empty',True,True)
                        self.phase='name_bytes'
                    elif field=='name_bytes':self.phase='target_classify'
                    elif field=='target_classify':
                        name=self.cache['name_bytes']['value']
                        if value<=3000:self.caption='User Trade';self.phase='add'
                        elif b'Royal National' in name:self.phase='dialog_text'
                        else:
                            self.caption='NPC'
                            self.first=next((label for needle,label in NAME_RULES if needle in name),None)
                            if self.first is None and (b'Inn' in name or b'Kronil' in name):self.first='Inn Hostess'
                            if self.first is None:return self._result('name_unmatched',True,True)
                            self.phase='add'
                    elif field=='dialog_text':
                        if value not in ('0','1','2','3','4'):return self._result('dialog_rejected',True,True)
                        self.caption='NPC';self.first='Royal National Enchanter';self.second=value;self.phase='add'
                    else:self.first=value;self.phase='sub1'
                elif self.phase=='add':self.row=self.sink.add_row();self.phase='caption'
                elif self.phase=='caption':
                    self.sink.set_caption(self.row,self.caption)
                    self.phase='trade_text' if self.caption=='User Trade' else 'sub1'
                elif self.phase=='sub1':self.sink.add_subitem(self.row,self.first);self.phase='sub2'
                elif self.phase=='sub2':
                    self.sink.add_subitem(self.row,self.second)
                    if not self.result.done:self._result('row_completed',True,True)
                    return self.result
                else:raise ValueError('Unknown own NPC phase')
            raise ValueError('Own NPC continuation exceeded finite phase bound')
        except (OSError,ValueError,IndexError) as error:
            if self.result.done:return self.result
            return self._result('row_incomplete',done=True,error=str(error))
        finally:self.busy=False
