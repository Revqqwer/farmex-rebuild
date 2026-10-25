# Callback slot source path and owned x86 experiment

The initializer00412874 derives the callback slot from a profile root-slot
candidate: guarded root ->context field ->object's table pointer ->table+8c.
It stores that slot address in00554218 and calls0046b8fc with physical pushes
`(0x46f520,target_slot,0x554228)`. The replacement helper captures the old DWORD
only while the save cell is zero, then unconditionally copies four replacement
bytes into the target. Its protected-read side effects remain unverified.

The initializer tests probe AL and a signed stack output>90 before attempting
installation. Output units and purpose are unknown. It sets attempted byte
00553c84 even when those conditions skip installation. This is not a success
flag. Its other header gates and remaining181-instruction body are outside the
owned fixture's installation span.

Pinned source profile values differ:

| Module/profile | Root-slot candidate | Context field | Table slot |
|---|---|---|---|
| Legacy US | 0111563c | 370 | 8c |
| Current US | 01128a7c | 3b0 | 8c |
| Legacy Steam | 011ebab0 | 3b0 | 8c |
| Current Steam | 011eaab0 | 3b0 | 8c |

`versioned_callback_globals` requires the exact known Richard SHA256 and
explicit profile, returns an immutable projection, and rejects conflicting
captured overrides. These are source initializer candidates; the current
loaded game/profile/address validity is not certified.

`native/callback_slot_fixture.c` reuses our owned context wrapper and RET0
receiver. Its root/object/table, slot, saved target and replacements are all
created inside its own x86 process. It executes no vendor callback body and
has no game PID/address input or external-process access. The wrapper's
register/stack shape is exercised; the replacement is a pass-through fixture,
not the389-instruction bot callback.

Twelve owned native cases passed: slot derivation; signed90/91 boundary; lowAL
versus upper-only probe values; negative output; attempted-without-retry;
installed dispatch; saved-original retention across replacement; second
dispatch; zero original without dispatch; legacy US370 context dispatch.
Dispatch preserves EBX/EBP and stack, transfers the owned object into ECX,
and retains the receiver's EAX/ECX/EDX/carry effects. RET0 is the receiver's
explicit fixture contract, not proof of the original game callback ABI.

The sandbox rejected the x86 compiler at Windows DLL relocation before source
compilation. The same owned source compiled and ran successfully in the normal
host context with no UAC request. This is separate from the game's earlier
VM_READ issue and does not diagnose or solve it.

The audit checks2428 instruction records across both pinned initializer,
replacement, context-wrapper and profile-table bodies/callsites, and matches
two fresh REA bodies. Native fixture output is ordinary owned-process evidence,
not REA runtime Evidence. Three Python tests cover source-hash profile selection,
old/current mismatch rejection and immutable projections.

Only sources/build scripts are packaged. The compiled EXE stays under work.
Game mapping/protection, guarded-read effects, real callback signature/thread,
full hook lifecycle, loader/runtime integration and live compatibility remain
unverified. No game process, memory or action was accessed.
