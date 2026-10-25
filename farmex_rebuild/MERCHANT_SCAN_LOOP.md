# Owned timer and scan lifecycle

The actual configuration panel schedules a Tk `after` callback every100ms
while its owned scan loop is active. This cadence is a local UI policy; the
source timer period has not been recovered. The callback obtains immutable
`ScanLoopInput` from an optional explicit provider. Without a provider it holds
at the missing observation; no empty lookup, helper return or game connection
is fabricated.

Start initializes a new generation from the owned control state. Stop, GIT,
profile changes and canvas destruction cancel the timer and invalidate in-flight
work. Rerender preserves the invocation. Stale callbacks cannot cancel a newer
timer; a provider that stops/restarts or changes the profile cannot commit its
old result. Profiles clear the provider. Bounds failure stops the owned loop;
route completion updates real buttons/label only after the supplied stop return.

The owned collection and scan index/busy fields are reflected into control
state. The last DWORD clock stamp survives stop/restart. Own Windows clock
reads occur only when the scheduler reaches a missing pre/post clock value;
the calls remain separate. Clock failure preserves and publishes reached child
prefix effects so retry cannot duplicate a packet.

The child queue is a staging snapshot. Newly appended records are published
once into the latest shared Flood/PM queue with fresh own record IDs, preserving
interleaved writers and existing records. Staging and published record IDs can
differ; they are process-local bookkeeping, never native handles or ACKs.

The provider is synchronous and runs on the Tk thread. Real acquisition must
therefore provide bounded captures without blocking the event loop. Independent
parent/helper normal receipts remain required. Source vector races, native
pointer operands, exceptions, game effects and automatic capture are outside
this adapter. Reply dispatch/busy clearing and actual movement/export execution
are still open.

Tests cover actual hidden Tk callbacks, missing/invalid captures, collection,
stop, reentrant provider, stale generation, rerender, route completion and profile
invalidation, in addition to pure lifecycle/clock/shared-queue regressions.
The validation JSON records the full-suite and full-GUI evidence separately.
