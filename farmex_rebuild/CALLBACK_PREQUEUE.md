# Callback entry and prequeue control flow

CallbackPreQueueFrame now replays the normal control paths across224 source
instructions0046f520..0046f8be. It requires explicit helper normal/EAX receipts
and raw global observations. No helper, callback, native memory or queue
operation is executed.

Both guarded header chains are captured before readiness. Readiness tests
lowAL; the later connection test requires full EAX exactly1. The two prelude
helpers and optional profile refresh precede it. Other connection values call
the disconnected worker then branch to cleanup0046fb09.

Pending562208 uses the two cached header DWORDs. If both are zero, it projects
pending clear, a fresh QWORD timestamp, an opaque UI setter and recovery flag1.
Either pending path restores SEH through an explicit receipt and branches to
direct epilogue0046fb2f, skipping the common cleanup path. UI setter descriptors
contain form field offset and source DL1, not a certified runtime object or ABI.

Recovery56221d uses signed QWORD GetTickCount subtraction and strictly greater
than5000ms. Negative/wrapped elapsed does not become a positive DWORD interval.
The source writes only CL before PUSH ECX: captured full push must have the
same low byte as56228c; its upper24 bits are not assumed zero. Fresh mode reads,
setup, exclusive/combat/coordinate flags select separate start/stop/exit paths.

Distance uses captured FILD/FSTP push bits, an opaque metric/ftol return and
captured FNSTSW AX. First TEST AH45 plus signed distance<50 selects movement
with a second fresh coordinate pair. The second TEST AH05 uses exact even
parity for JP, without inventing a floating comparison. Actor state tests AL;
notice construction/dispatch/cleanup and recovery clear retain source order.
No FPU rounding, exceptions, native movement or notice effect is certified.

The non-recovery path conditionally calls the fixed guard, then work helper
00458c70 and queue consumer004c79a0. Helper/consumer normal returns are separate.
The post-queue boundary is0046f8be. No queue result is invented from these
receipts.

CallbackEntryEventFrame composes this prefix with EventCallbackFrame. It only
derives the post segment's entry after the prefix reaches0046f8be and receives
an explicit fresh own post-drain QueueState. Early exits require neither that
state nor event inputs. It does not substitute an empty queue or reuse an
unproved pre-call queue. Later callback tail/cleanup and native return remain
outside the composed model.

Thirteen tests cover source header/readiness order, exact connection1, pending
prefix gaps, strict recovery timing, partial-register push capture, fresh mode
reads, recovery branch differences, independent coordinate bits, FPU parity,
fixed guard/queue return gaps and generated entry/event composition. The audit
checks778 records across two pinned callback bodies,448 modeled prefix records,
the FPU constant and one retained complete REA body. These are scoped normal
paths, not a full function/native scheduler/ABI/live compatibility certificate.

The API is not yet used by the own panel execution page. Existing direct event
trial remains explicitly entered and does not assert source callback entry.
