# Event callback post-drain segment

EventCallbackFrame models the44 instructions0046f8be..0046f97d, with explicit
entry after the source004c79a0 queue consumer returned. Its queue argument is
an own post-drain observation. This does not establish prior callback entry,
readiness/connection, pause/recovery, fixed guard or queue execution.

The source selects VIP storage first, Inn storage second. A completed storage
helper falls through to the event worker without reading the later worker
flag. Otherwise an active00568dbc worker branch performs VIP/Inn probes,
exclusive-mode and signed-positive health checks. Failed checks reset phase14
and clear the worker byte, then branch toward0046fb09. A worker-step call stores
full EAX to00568dc0, then a fresh full-DWORD memory comparison tests43. Exact43
causes a second phase14 store and byte clear; every worker path exits before
the event call. Helper return and subsequent memory read are not collapsed.

When no worker early-exit path applies, source0046f977 calls0045a4dc with
context00562194. The bot-enabled flag00561f60 is checked at0046f97d afterward,
outside this modeled span. Thus this span does not gate event calls on that
flag. Earlier opaque readiness helpers may still depend on other state.

Optional EventCallbackObservation.event_child binds the generated EventJoinFrame
with the same own post-drain queue. An incomplete child blocks the independent
outer event return; queued child prefixes persist across observation gaps.
This segment does not consume newly appended event records again. Unknown
native helper effects and later callback work are not inferred.

Boundary outcomes report0046f97d for event fallthrough or0046fb09 for a worker
exit toward cleanup. Neither outcome proves a native callback return: cleanup
and its final indirect call are outside the model. The whole389-instruction
callback is not certified. VIP helper target004ff934 is the current pinned
version; the audit records the older version's004ff918 role explicitly.

Eleven tests cover explicit entry, storage priority/return gaps, event ordering,
low-AL probes, signed health, fresh phase comparison, exact43 versus high-byte
variants, generated child/outer returns, prefix retention and rejected late
binding. A composed own drain->event test proves new local records remain in
the modeled post-drain queue. The audit checks1134 instruction records across
two versions, including88 modeled callback-span records, one fresh callback
REA body and one retained worker body.

The API is not yet wired into the panel's callback trial. Existing direct
event trial remains an explicitly entered worker model. Original timer/hook
entry, helper/storage/native callback effects, scheduler integration and live
compatibility remain unverified.
