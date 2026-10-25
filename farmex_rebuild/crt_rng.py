"""Offline replay for the exact discovered CRT file, assuming stable thread data.

No DLL is loaded and no runtime RNG is executed. File identity is not proof of
the DLL loaded in the game. Caller normal-return observations remain separate.
"""
from dataclasses import dataclass

CRT_SOURCE_SHA256='45b21b5cb5d13af35bdc3a5c5ca058a8df679e579bed95c19aad0ac2dd423b8e'

def _dword(value):
    if type(value) is not int or not 0<=value<1<<32:raise ValueError('Explicit seed DWORD required')

@dataclass(frozen=True)
class CrtRandStep:
    seed_before:int
    seed_after:int
    result_eax:int

@dataclass(frozen=True)
class CrtSeededPair:
    warmup:CrtRandStep
    output:CrtRandStep
    thread_auxiliary_dword_after:int=0
    source_sha256:str=CRT_SOURCE_SHA256
    loaded_game_runtime_verified:bool=False
    native_execution_verified:bool=False

def replay_crt_rand_step(seed):
    _dword(seed)
    after=(seed*0x15a4e35+1)&0xffffffff
    return CrtRandStep(seed,after,(after>>16)&0x7fff)

def replay_crt_seeded_pair(seed):
    # _srand stores seed/+4c=0, calls _rand once and discards that result.
    # The caller's subsequent _rand therefore consumes the second step.
    warmup=replay_crt_rand_step(seed)
    return CrtSeededPair(warmup,replay_crt_rand_step(warmup.seed_after))
