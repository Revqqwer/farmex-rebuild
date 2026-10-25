"""Richard0040d554 family routing. No game calls; supplied job is already resolved.

UI compiler0040a39c reads Main+644 into config+dc;0040ab58 copies
that byte to config+54 (00561f88). Runtime0046d30c may override it.
Class-name comparison helpers and UI side-effect ordering are not replayed here.
"""
from dataclasses import dataclass
from typing import Optional
from job_dispatcher import HEADS, JobState, dispatch_job
from alternate_dispatcher import AlternateSnapshot, AlternateState, dispatch_alternate

LEGAL_PATH = 'frmMain/MainTab/SheetBot/GroupBox34/rdUseLegalSkill'
LEGAL_HEADS = {'rogue': '004dc544', 'priest': '004d1d88',
               'warrior': '00501dbc', 'mage': '0049b928', 'kurian': '00471a28'}


@dataclass(frozen=True)
class FamilySelection:
    status: str
    family: Optional[str] = None
    head: Optional[str] = None
    origin: str = ''


def select_class_family(job, values, *, runtime_byte=None, blocked_74=None,
                        normal_guard_45dc44=None):
    """Select only after the outer guard is observed; unknown stays unknown.

    runtime_byte is an observed config+54 byte, not a predicted override.
    The normal-only helper is the second0045dc44 return used for comparison6.
    """
    if job not in HEADS:
        raise ValueError('Resolved known class required')
    if blocked_74 is not None and type(blocked_74) is not bool:
        raise ValueError('Outer guard must be bool or unknown')
    if normal_guard_45dc44 is not None and type(normal_guard_45dc44) is not int:
        raise ValueError('Normal helper return must be integer or unknown')
    if runtime_byte is not None and (type(runtime_byte) is not int or not 0 <= runtime_byte <= 255):
        raise ValueError('Runtime mode must be a byte or unknown')
    if blocked_74 is None:
        return FamilySelection('needs_observation', origin='config+74')
    if blocked_74:
        return FamilySelection('blocked', origin='config+74')
    if runtime_byte is None:
        value = values.get(LEGAL_PATH)
        if type(value) is not bool:
            raise ValueError('Legal Skill checkbox must be boolean')
        legal = value
        origin = 'ui_candidate'
    else:
        legal = runtime_byte != 0
        origin = 'observed_config+54'
    if legal:
        return FamilySelection('selected', 'legal', LEGAL_HEADS[job], origin)
    if normal_guard_45dc44 is None:
        return FamilySelection('needs_observation', 'normal', origin='0045dc44 second return')
    if normal_guard_45dc44 == 6:
        return FamilySelection('blocked', 'normal', origin='0045dc44 second return')
    return FamilySelection('selected', 'normal', HEADS[job], origin)


def dispatch_class_family(job, selection, snapshot, *, normal_state=None,
                          legal_state=None, replies=None):
    """Route a proven local selection into the existing class-head models.

    Separate family states retain their distinct timer layouts. Returns None
    when a guard or observation prevents dispatch; callers retain both states.
    """
    if selection.status != 'selected':
        return None
    if selection.family == 'normal' and selection.head == HEADS.get(job):
        return dispatch_job(job, snapshot, JobState() if normal_state is None else normal_state, replies)
    if selection.family == 'legal' and selection.head == LEGAL_HEADS.get(job):
        if not isinstance(snapshot, AlternateSnapshot):
            raise ValueError('Legal family requires its additional observations')
        return dispatch_alternate(job, snapshot,
                                  AlternateState() if legal_state is None else legal_state, replies)
    raise ValueError('Family/head does not match resolved class')
