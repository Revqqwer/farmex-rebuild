"""Confirmed parameter bridges. Runtime interval/target/stat inputs stay separate."""
from dataclasses import dataclass
from class_configuration import ClassConfiguration

def _field(config,job,mapping,offset):
    if not isinstance(config,ClassConfiguration) or config.job!=job:raise ValueError('Matching compiled class required')
    values=getattr(config,mapping)
    if offset not in values:raise ValueError('Missing source field +%x'%offset)
    return values[offset]

@dataclass(frozen=True)
class RogueVolleyRanges:
    triple: int
    quintuple: int

    def __post_init__(self):
        for value in (self.triple,self.quintuple):
            if type(value) is not int or not -0x80000000<=value<=0x7fffffff:raise ValueError('Signed DWORD range required')

def rogue_volley_ranges(config):
    return RogueVolleyRanges(_field(config,'rogue','parameters',0x10),_field(config,'rogue','parameters',0x14))

@dataclass(frozen=True)
class RogueAlternateBowRanges:
    triple: int
    quintuple: int
    combo: int

    def __post_init__(self):
        for value in (self.triple,self.quintuple,self.combo):
            if type(value) is not int or not -0x80000000<=value<=0x7fffffff:raise ValueError('Signed DWORD range required')

def rogue_alternate_bow_ranges(config):
    return RogueAlternateBowRanges(*(_field(config,'rogue','parameters',offset) for offset in (0x10,0x14,0x18)))

@dataclass(frozen=True)
class WarriorProvokeSettings:
    enabled: bool
    window_seconds: int
    start_delay_seconds: int
    skill_delay_seconds: int

    def __post_init__(self):
        if type(self.enabled) is not bool:raise ValueError('Boolean Provoke flag required')
        for value in (self.window_seconds,self.start_delay_seconds,self.skill_delay_seconds):
            if type(value) is not int or not -0x80000000<=value<=0x7fffffff:raise ValueError('Signed DWORD seconds required')

def warrior_provoke_settings(config):
    return WarriorProvokeSettings(_field(config,'warrior','flags',0x198),
        _field(config,'warrior','parameters',0x1a0),_field(config,'warrior','parameters',0x1a4),
        _field(config,'warrior','parameters',0x1a8))
