"""0040a39c/0040ab58 active bot fields. No timer, family dispatch or game IO.

Strict decimal parsing is our policy; source fallback/runtime defaults are not
invented. Range stays signed; active interval has DWORD consumer representation.
"""
import re
from dataclasses import dataclass

PREFIX='frmMain/MainTab/SheetBot/GroupBox34/'
BOT_COMBAT_INPUTS=tuple(PREFIX+group+'/'+name for group,names in (
    ('GroupBox35',('txtNMobSelectSpeed','txtNMobSelectDistance','txtNAtackDistance',
                   'chNManuelAtackSpeed','txtNiManuelAtackSpeed')),
    ('GroupBox38',('txtLMobSelectSpeed','txtLMobSelectDistance','txtLAtackDistance',
                   'chLManuelAtackSpeed','txtLiManuelAtackSpeed'))) for name in names)+(PREFIX+'rdUseLegalSkill',)

@dataclass(frozen=True)
class BotCombatConfiguration:
    legal_mode: bool
    target_select_ms: int
    target_range: int
    attack_interval_ms: int
    attack_range: int

def compile_bot_combat(values,*,mode_byte_override=None):
    def get(path):
        if path not in values:raise ValueError('Missing bot panel control: '+path)
        return values[path]
    def flag(path):
        value=get(path)
        if type(value) is not bool:raise ValueError('Boolean bot mode/speed flag required')
        return value
    def number(path):
        value=get(path)
        if type(value) is not str or not re.fullmatch(r'[+-]?[0-9]+',value.strip()):
            raise ValueError('Decimal bot parameter required: '+path)
        parsed=int(value.strip())
        if not -0x80000000<=parsed<=0x7fffffff:raise ValueError('Signed DWORD bot parameter required')
        return parsed
    normal=PREFIX+'GroupBox35/';legal=PREFIX+'GroupBox38/'
    n=(number(normal+'txtNMobSelectSpeed'),number(normal+'txtNMobSelectDistance'),
       flag(normal+'chNManuelAtackSpeed'),number(normal+'txtNiManuelAtackSpeed'),number(normal+'txtNAtackDistance'))
    l=(number(legal+'txtLMobSelectSpeed'),number(legal+'txtLMobSelectDistance'),
       flag(legal+'chLManuelAtackSpeed'),number(legal+'txtLiManuelAtackSpeed'),number(legal+'txtLAtackDistance'))
    # Source normal parser0045f010 uses bounds0..99999 and an unknown runtime default.
    if n[2] and not 0<=n[3]<=99999:raise ValueError('Normal manual speed needs source fallback outside0..99999')
    mode=flag(PREFIX+'rdUseLegalSkill')
    if mode_byte_override is not None:
        if type(mode_byte_override) is not int or not 0<=mode_byte_override<=255:raise ValueError('Raw mode BYTE required')
        mode=mode_byte_override!=0
    selected=l if mode else n
    interval=selected[3] if selected[2] else (250 if mode else 1250)
    return BotCombatConfiguration(mode,selected[0],selected[1],interval&0xffffffff,selected[4])
