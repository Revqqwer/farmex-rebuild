# Detector code state

Current `004e2a88` covers the exclusive interval `[004e1464,004e2a80)`:
5660 bytes. Historical `004e2a6c` ends at `004e2a64`: 5632 bytes.
The model requires the exact bot source hash and never selects a game profile.

The source first compares its raw DWORD argument with `0056ff38`. Equality
skips all work. Inequality calls VirtualProtect with physical PUSH order
`(oldProtectionLocal,0x40,length,start)` and ignores its EAX. Mode1 then adds
`0x28` at even offsets and `0x40` at odd offsets, modifying AL only. Mode0
subtracts those amounts modulo256. Other unequal modes call VirtualProtect
but perform neither byte loop nor state store. There is no protection-restore
call in this body.

Every byte uses `0045dbdc` and `0045de4c`; the writer receives the complete
EAX after ADD AL. The reader can return zero on protection failure, and the
writer can return normally without copying. Consequently the frame records
write intentions, not successful changes. Its final state DWORD store follows
all writer returns and does not certify successful transformation. Per-byte
observations, partial progress and the final return remain separate.

Startup function `00424924` calls mode1 at `004249ad`, after callback setup
and `00412f48`, before computing the next slot. This is a static call-order
finding, not evidence that this startup path or transformation ran in a game.
The normal probe brackets each detector with mode0/mode1. Disk detector
disassembly must therefore be interpreted with actual code state and helper
effects established; a linear disk body alone is insufficient for a live claim.

`transform_owned_bytes` is only the arithmetic on caller-owned immutable bytes.
The audit transforms each preserved source region and inverts it locally,
checking exact roundtrip bytes. It neither changes executable pages nor proves
that a native transformation succeeds. No game memory, executable allocation,
protection change, hook, detector call or process action is performed.
