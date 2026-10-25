# Event target preparation queue prefix

The worker's valid-target path calls004c8f7c before the event-specific request.
That helper copies a10-byte pinned template, overwrites four bytes at offset2
from its raw target argument, then calls004c7710 with delay0 and length10.
The template is `200100000000ffffffff`; target0x89abcdef yields
`2001efcdab89ffffffff`. No WORD truncation or inferred target-type restriction
is applied. The worker passes a third fresh target getter, independently from
the first unsigned3000 check and second nonzero check.

EventPacketFrame now supports kind `target_prepare` with a required target
DWORD. EventJoinObservation.packet_children accepts key `target_prepare`.
The worker binds exact source helper and context00561ef8, using physical PUSH
order `(fresh_target, context)`. Frame setup, template copy, target copy,
enqueue attempt, helper return and worker outer return remain distinct.
An incomplete child blocks the later event request/stamp; committed own
target records survive gaps without duplicate append.

The own panel's reached-only decoder accepts this optional child. Its explicit
synthetic second-group examples now include target preparation: FT and UTC
each produce two own records (target then event), Juraid three (target then
delay0 and delay200 event requests). Older captures without a detailed target
child retain the explicit opaque helper interface. The source profile guard,
runtime target identity and original scheduler are not inferred.

Seven new tests cover full DWORD byte layout, copy/gate ordering, fresh third
target, helper/outer gaps, request order, invalid-target skipping, panel partial
captures and late-binding rejection. Existing example assertions were updated
to include the newly modeled target record. The own hidden UI smoke checks
target-copy waiting and10-byte-before17-byte ordering through real FT controls.

The audit checks740 instruction records across two pinned versions, the
version-specific10-byte template, two fresh REA analyses and retained worker/
queue evidence. Only60 of these records are the newly modeled target helper;
the fallback's154 records now also have a conditional inert operand model;
see [fallback scope](EVENT_TARGET_FALLBACK.md).
Fallback00464a20 has profile-specific native calls, optional allocation and
component stores. Native effects remain unverified; absence of a direct4c7710 call is not
proof that indirect game/queue effects are absent.

All records are conditional own QueueState projections. Native memory,
allocation/protection, callback ABI, actual send/admission and live
compatibility remain unverified. No game action occurs.
