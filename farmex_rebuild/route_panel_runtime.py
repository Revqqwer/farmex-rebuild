"""Owned normal-value open/close behavior of the source RotaPanel callbacks.

This is panel layout/checkbox state only, not route drawing, Draki entry or
native VCL/recording-helper equivalence. Reads stay fresh between setters.
"""
from dataclasses import dataclass
from types import MappingProxyType

PANEL_PATH='frmMain/RotaPanel'
TABS_PATH='frmMain/MainTab'
OPEN_PATH='frmMain/MainTab/SheetKoruma/grpNoticeKontrol/Button21'
CLOSE_PATH=PANEL_PATH+'/btnRouteWindowClose'
GATES_PATH=PANEL_PATH+'/grpRouteAddAdvanced/chRouteSaveGates'


def signed32(value):
    if type(value) is not int or not -0x80000000<=value<=0xffffffff:raise ValueError('Own int32 geometry field required')
    value&=0xffffffff
    return value if value<0x80000000 else value-0x100000000


@dataclass(frozen=True)
class RoutePanelUpdate:
    complete:bool
    status:str
    geometry:object
    visible:object
    recording_reset:bool=False
    error:object=None
    native_execution_verified:bool=False
    route_editing_verified:bool=False
    live_compatibility_verified:bool=False


class OwnedRoutePanel:
    def __init__(self):
        self.geometry={};self.visible=None;self.last=None

    def _result(self,complete,status,recording_reset=False,error=None):
        self.last=RoutePanelUpdate(complete,status,MappingProxyType(dict(self.geometry)),
            self.visible,recording_reset,error)
        return self.last

    def open(self,read_tabs,write_panel):
        if not callable(read_tabs) or not callable(write_panel):raise ValueError('Own geometry reader/writer required')
        try:
            for field,source,delta in (('left','left',0),('top','top',20),('height','height',-20)):
                value=signed32((signed32(read_tabs(source))+delta)&0xffffffff)
                write_panel(field,value);self.geometry[field]=value
            write_panel('width',600);self.geometry['width']=600
            write_panel('visible',True);self.visible=True
            return self._result(True,'opened')
        except (ValueError,OSError) as error:return self._result(False,'open_incomplete',error=str(error))

    def close(self,uncheck_gate_recording,write_panel):
        if not callable(uncheck_gate_recording) or not callable(write_panel):raise ValueError('Own checkbox/panel writers required')
        reset=False
        try:
            uncheck_gate_recording();reset=True
            write_panel('visible',False);self.visible=False
            return self._result(True,'closed',True)
        except (ValueError,OSError) as error:return self._result(False,'close_incomplete',reset,str(error))
