"""Explicit source-hash-bound storage/skill fixtures, not live game profiles.

Legacy unversioned APIs retain their historical behavior. New consumers use
this registry to bind current literals and source helper addresses explicitly.
"""
from dataclasses import dataclass
from types import MappingProxyType
from storage_profiles import STORAGE_PROFILE_GLOBALS
from skill_native_plans import SOURCE_GLOBALS,SkillObservation,plan_alternate_skill
from storage_native_plans import NativeHelperObservation,plan_native_helper

LEGACY_SOURCE_SHA256='12f3e2dd13836b4f9ffec77c71cf04e505e7e92a2d5a527abf78aa566f359a54'
CURRENT_SOURCE_SHA256='febdac805f370fb3ecc1ba5bf76482eb1f3d9b52c080113eb1dc9f12d2e45759'

_CALLBACK_PROFILE_GLOBALS={
 LEGACY_SOURCE_SHA256:{'us':{0x553e80:0x111563c,0x5540d4:0x370,0x554204:0x8c},
                       'steam':{0x553e80:0x11ebab0,0x5540d4:0x3b0,0x554204:0x8c}},
 CURRENT_SOURCE_SHA256:{'us':{0x553e80:0x1128a7c,0x5540d4:0x3b0,0x554204:0x8c},
                        'steam':{0x553e80:0x11eaab0,0x5540d4:0x3b0,0x554204:0x8c}}}

def versioned_callback_globals(module_sha256,profile,*,runtime_globals=None):
    """Pinned source initializer projection only; no loaded-game profile proof."""
    if module_sha256 not in _CALLBACK_PROFILE_GLOBALS or profile not in ('us','steam'):
        raise ValueError('Explicit known callback source hash and profile required')
    result=dict(_CALLBACK_PROFILE_GLOBALS[module_sha256][profile])
    for slot,value in ({} if runtime_globals is None else runtime_globals).items():
        if type(slot) is not int or not 0<=slot<=0xffffffff or type(value) is not int or not 0<=value<=0xffffffff:
            raise ValueError('Raw callback fixture global DWORD pair required')
        if slot in result and value!=result[slot]:raise ValueError('Callback runtime fixture conflicts with pinned source profile')
        result[slot]=value
    return MappingProxyType(result)

_common={0x5540c0:0x114,0x5540c4:0x414,0x5540cc:0x49c,0x5540d0:0x4a0,
         0x55412c:0x114,0x554130:0x414,0x554134:0x14c,0x554138:0x138,
         0x55413c:0x13c,0x554200:0x84,0x5540bc:0x26c,0x554128:0x270}
CURRENT_STORAGE_GLOBALS=MappingProxyType({
    'us':MappingProxyType(_common|{0x553e80:0x1128a7c,0x553f44:0x11297dc,0x553f48:0x11283bc}),
    'steam':MappingProxyType(_common|{0x553e80:0x11eaab0,0x553f44:0x11fd704,0x553f48:0x11e867c})})
CURRENT_SKILL_GLOBALS=MappingProxyType({
    'us':MappingProxyType({0x553e46:1,0x553e80:0x1128a7c,0x553eb8:0,
                          0x553ebc:0x5066b0,0x553ee4:0x88eb50,0x5540a0:0x4a8}),
    'steam':MappingProxyType({0x553e46:2,0x553e80:0x11eaab0,0x553eb8:0x11e950c,
                             0x553ebc:0x634020,0x553ee4:0x7df2d0,0x5540a0:0x4a8})})
SOURCE_NATIVE_TABLES=MappingProxyType({
    LEGACY_SOURCE_SHA256:MappingProxyType({'storage':STORAGE_PROFILE_GLOBALS,'skill':SOURCE_GLOBALS}),
    CURRENT_SOURCE_SHA256:MappingProxyType({'storage':CURRENT_STORAGE_GLOBALS,'skill':CURRENT_SKILL_GLOBALS})})
_legacy_helpers={k:k for k in ('004fe274','004fe2fc','0046fc78','0046fd04','004653a8','00465334','0046fdf8')}
_current_helpers={**{k:k for k in ('0046fc78','0046fd04','004653a8','00465334','0046fdf8')},
                  '004fe290':'004fe274','004fe318':'004fe2fc'}
STORAGE_HELPER_IDENTITIES=MappingProxyType({LEGACY_SOURCE_SHA256:MappingProxyType(_legacy_helpers),
                                          CURRENT_SOURCE_SHA256:MappingProxyType(_current_helpers)})

def versioned_profile_globals(module_sha256,profile,kind,*,runtime_globals=None):
    if module_sha256 not in SOURCE_NATIVE_TABLES or kind not in ('storage','skill') or profile not in ('us','steam'):
        raise ValueError('Explicit known source hash, profile and fixture kind required')
    result=dict(SOURCE_NATIVE_TABLES[module_sha256][kind][profile])
    for slot,value in ({} if runtime_globals is None else runtime_globals).items():
        if type(slot) is not int or not 0<=slot<=0xffffffff or type(value) is not int or not 0<=value<=0xffffffff:
            raise ValueError('Raw fixture global DWORD pair required')
        if slot in result and value!=result[slot]:
            raise ValueError('Runtime fixture conflicts with selected source initializer projection')
        result[slot]=value
    return MappingProxyType(result)

@dataclass(frozen=True)
class VersionedNativeObservation:
    module_sha256:str
    profile:str
    kind:str
    source_helper:str
    modeled_helper:str
    observation:object

    def __post_init__(self):
        expected=versioned_profile_globals(self.module_sha256,self.profile,self.kind)
        o=self.observation
        if self.kind=='storage':
            helper=STORAGE_HELPER_IDENTITIES[self.module_sha256].get(self.source_helper)
            if not isinstance(o,NativeHelperObservation) or helper is None or helper!=self.modeled_helper or o.helper!=helper or o.source_profile!=self.profile:
                raise ValueError('Storage helper address/source identity mismatch')
        elif not isinstance(o,SkillObservation) or self.source_helper!='00465640' or self.modeled_helper!='00465640':
            raise ValueError('Typed source skill wrapper required')
        if any(o.globals.get(slot)!=value for slot,value in expected.items()):
            raise ValueError('Fixture globals differ from selected source hash/profile')

@dataclass(frozen=True)
class VersionedNativePlan:
    module_sha256:str
    profile:str
    kind:str
    source_helper:str
    modeled_helper:str
    plan:object
    game_image_verified:bool=False
    native_execution_verified:bool=False

def make_versioned_storage_observation(module_sha256,profile,source_helper,argument,*,runtime_globals=None,
                                       protected_words=None,direct_words=None,normal_returned=None):
    globals=versioned_profile_globals(module_sha256,profile,'storage',runtime_globals=runtime_globals)
    helper=STORAGE_HELPER_IDENTITIES[module_sha256].get(source_helper)
    if helper is None:raise ValueError('Storage helper does not belong to selected source image')
    obs=NativeHelperObservation(helper,argument,globals,{} if protected_words is None else protected_words,
                                {} if direct_words is None else direct_words,source_profile=profile,
                                normal_returned=normal_returned)
    return VersionedNativeObservation(module_sha256,profile,'storage',source_helper,helper,obs)

def make_versioned_skill_observation(module_sha256,profile,action_id,actor_id,*,direct_words=None,
                                     lookup_return=None,native_return=None):
    obs=SkillObservation(action_id,actor_id,versioned_profile_globals(module_sha256,profile,'skill'),
                         {} if direct_words is None else direct_words,lookup_return,native_return)
    return VersionedNativeObservation(module_sha256,profile,'skill','00465640','00465640',obs)

def plan_versioned_native(o):
    if not isinstance(o,VersionedNativeObservation):raise ValueError('Source-bound native fixture required')
    p=plan_native_helper(o.observation) if o.kind=='storage' else plan_alternate_skill(o.observation)
    return VersionedNativePlan(o.module_sha256,o.profile,o.kind,o.source_helper,o.modeled_helper,p)
