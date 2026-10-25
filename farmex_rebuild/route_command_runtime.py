"""Own route-editor add events; list data only, never game actions."""
from dataclasses import dataclass
from rtl_integer import rtl_integer_or_default

PREFIX='frmMain/RotaPanel/grpRouteAddCommand/'
BUTTON_METHODS={PREFIX+name:method for name,method in (
    ('btnRouteAddTown','town'),('btnRouteAddGateSkill','gate_skill'),
    ('btnRouteAddCSit','sit'),('btnRouteAddCStandUp','stand'),('btnRouteAddWait','wait'))}
WAIT_PATH=PREFIX+'txtRouteAddWait'
CAPTIONS={'town':'Town','gate_skill':'Gate Skill','sit':'Otur','stand':'Kalk','wait':'Bekle'}
CAMP_PREFIX='frmMain/RotaPanel/grpRouteAddAdvanced/grpRouteChangeCamp/'
SPEED_PREFIX='frmMain/RotaPanel/grpRouteAddAdvanced/grpRouteSH/'
CAMP_RANDOM=CAMP_PREFIX+'rdRouteChangeCampRandom'
CAMP_MANUAL=CAMP_PREFIX+'rdRouteChangeCampManuel'
CAMP_TEXT=CAMP_PREFIX+'txtRouteChangeCampNo'
SPEED_FLAGS=tuple(SPEED_PREFIX+name for name in ('rdRouteAddShOff','rdRouteAddSHSw','rdRouteAddSHLf'))
ADVANCED_BUTTON_METHODS={CAMP_PREFIX+'btnRouteAddChangeCamp':'camp',SPEED_PREFIX+'btnRouteAddSHCommand':'speed'}
ADVANCED_CAPTIONS={'camp':'Change Camp','speed':'Change Speed Hack'}


@dataclass(frozen=True)
class RouteCommandResult:
    complete:bool
    phase:str
    row:object=None
    integer:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def append_source_route_command(method,sink,read_wait=None):
    """Add first, caption, then two subitems; preserve completed own prefix.

    Constants use '-' placeholders (not zero). Wait reads current text after
    setting caption and uses pinned scalar parser/default5 as own conversion
    policy; this is not a native StrToInt64 exception/cleanup receipt.
    """
    if method not in CAPTIONS:raise ValueError('Known source route add event required')
    phase='add';row=None;integer=None
    try:
        row=sink.add_row()
        phase='caption';sink.set_caption(row,CAPTIONS[method])
        first='-'
        if method=='wait':
            phase='wait_text'
            if not callable(read_wait):raise ValueError('Current wait text reader required')
            text=read_wait()
            if type(text) is not str:raise ValueError('Current Unicode wait text required')
            phase='integer';integer=rtl_integer_or_default(text,5)
            value=integer.result_qword
            first=str(value if value<1<<63 else value-(1<<64))
        phase='sub1';sink.add_subitem(row,first)
        phase='sub2';sink.add_subitem(row,'-')
        return RouteCommandResult(True,'returned',row,integer)
    except (OSError,ValueError,IndexError) as error:
        return RouteCommandResult(False,phase,row,integer,str(error))


def append_source_route_advanced(method,sink,read_value):
    """Lazy priority flags/number before Add; own scalar/default policy only.

    Speed priority Off/Swift/LightFeet maps0/1/3, none maps0. Camp random
    preempts manual; manual parse/default1 keeps only lowDWORD, zero maps
    Randomize and other values format signed32. Both have second subitem '-'.
    """
    if method not in ADVANCED_CAPTIONS:raise ValueError('Known advanced route event required')
    phase='entry';row=None;integer=None
    try:
        def flag(path):
            value=read_value(path)
            if type(value) is not bool:raise ValueError('Current route radio boolean required')
            return value
        if method=='speed':
            value=0
            for path,number in zip(SPEED_FLAGS,(0,1,3)):
                phase='flag_'+path.rsplit('/',1)[-1]
                if flag(path):value=number;break
            first=str(value)
        else:
            value=0;phase='flag_random'
            if not flag(CAMP_RANDOM):
                phase='flag_manual'
                if flag(CAMP_MANUAL):
                    phase='camp_text';text=read_value(CAMP_TEXT)
                    if type(text) is not str:raise ValueError('Current camp number text required')
                    phase='integer';integer=rtl_integer_or_default(text,1)
                    value=integer.result_qword&0xffffffff
            first='Randomize' if value==0 else str(value if value<1<<31 else value-(1<<32))
        phase='add';row=sink.add_row()
        phase='caption';sink.set_caption(row,ADVANCED_CAPTIONS[method])
        phase='sub1';sink.add_subitem(row,first)
        phase='sub2';sink.add_subitem(row,'-')
        return RouteCommandResult(True,'returned',row,integer)
    except (OSError,ValueError,IndexError) as error:
        return RouteCommandResult(False,phase,row,integer,str(error))
