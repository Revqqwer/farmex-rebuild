"""Source US/Steam storage constants, not verified live game profiles.

0049f061 passes00553e3c to004fd624/004e437c. These are literal game
addresses/structure offsets; no DLL relocation delta is applied.
This unversioned API is historical12f3e2dd fixture compatibility. For refreshed
febdac80 source use native_profile_versions with an explicit source hash.
"""
from types import MappingProxyType
from storage_native_plans import NativeHelperObservation
from npc_sell_packets import raw

_COMMON={0x5540c0:0x114,0x5540c4:0x414,0x5540cc:0x49c,0x5540d0:0x4a0,
         0x55412c:0x114,0x554130:0x414,0x554134:0x14c,0x554138:0x138,
         0x55413c:0x13c,0x554200:0x84}
STORAGE_PROFILE_GLOBALS=MappingProxyType({
    'us':MappingProxyType(_COMMON|{0x553e80:0x111563c,0x553f44:0x1116394,
        0x553f48:0x1114f7c,0x5540bc:0x22c,0x554128:0x230}),
    'steam':MappingProxyType(_COMMON|{0x553e80:0x11ebab0,0x553f44:0x11fe704,
        0x553f48:0x11e967c,0x5540bc:0x26c,0x554128:0x270})})

def storage_profile_globals(profile,runtime_globals=None):
    if profile not in STORAGE_PROFILE_GLOBALS:raise ValueError('Explicit source us/steam profile required')
    result=dict(STORAGE_PROFILE_GLOBALS[profile])
    for address,value in ({} if runtime_globals is None else runtime_globals).items():
        raw(address);raw(value)
        if address in result and value!=result[address]:raise ValueError('Observed global conflicts with source profile candidate')
        result[address]=value
    return MappingProxyType(result)

def make_profiled_native_observation(profile,helper,argument,*,runtime_globals=None,
                                     protected_words=None,direct_words=None):
    return NativeHelperObservation(helper,argument,storage_profile_globals(profile,runtime_globals),
        {} if protected_words is None else protected_words,{} if direct_words is None else direct_words,
        source_profile=profile)
