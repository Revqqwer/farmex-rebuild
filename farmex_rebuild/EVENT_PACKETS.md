# Event packet and queue children

The three first-group helper models now generate pinned payloads into an own
QueueState. Chaos uses `5f081800`; Royale uses `b70701`. BDW calls its own
separate nation getter: exact full EAX2 chooses `5f080200`, every other DWORD
chooses `5f080100`. This differs from the Juraid worker's exact nation1 test.

EventPacketObservation separates frame setup, nation return/EAX, copied-byte
span, enqueue QueueAttempt, and helper return receipts. EventEnqueueFrame
retains the full DWORD connection gate before waiting for GetTickCount. It
commits at most one own record; a missing enqueue/helper/outer return does not
cause a repeated append. Gate0 is a known skip, still requiring return receipts.

EventJoinObservation accepts optional `packet_children` for chaos_join,
bdw_join, royale_join; values are EventPacketObservation. Optional
`enqueue_children` for ft_enqueue, utc_enqueue, jr_enqueue0 and jr_enqueue200
are QueueAttempt objects. The direct requests use the pinned17/18/18/19-byte
copied templates and worker delays. Both groups and existing seeded records
share the same own queue; each enqueue clock is a distinct explicit capture.
Source context is00561ef8. Template VAs identify byte provenance, not runtime
stack buffers.

Optional target preparation now contributes a10-byte record before second-group
event requests; see [target prefix](EVENT_TARGET_PREPARATION.md).

The inner generated child must complete before accepting the separate worker
outer normal receipt. An incomplete child blocks the post stamp. A detailed
child cannot be added retroactively after its opaque call return was consumed.
Default unbound calls remain opaque, preserving their previous interface.

Eleven tests cover payloads, BDW nation alternatives, full gate retention,
known skip, helper-return gaps, two-group seeded queue sharing, Juraid's two
enqueue clocks/delays, no duplicate prefix, late binding rejection and ignored
unreached children. The audit checks670 instruction records across both pinned
Richard versions, eight version-specific data templates, three fresh REA helper
analyses and two retained worker/queue analyses.

`queue_effect_verified=False` refers to native queue effects. Own QueueState
records are conditional local projections. Opaque fallback and any unbound
target preparation or other helper side effects are outside this generated prefix. No native
allocation, memory access/write, drain, network transmission, server admission
or live compatibility is certified. The own panel execution trial now binds
these children through reached-only observations; see [panel scope](EVENT_JOIN_PANEL.md).
