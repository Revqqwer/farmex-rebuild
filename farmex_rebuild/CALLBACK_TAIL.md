# Callback tail and composed normal control flow

CallbackTailFrame models121 source instructions0046f97d..0046fb33. Its known
entries are after event0046f97d, common cleanup0046fb09, or direct epilogue
0046fb2f. Cleanup entry skips control/timers/dispatch; direct epilogue skips
cleanup and SEH restoration already handled by the preceding source path.

After-event flow reads bot enable before the optional control helper, then
fresh attack-lock state. Lock expiration uses wrapped DWORD subtraction and
inclusive duration. The interlude uses one captured local clock, initial
zero-difference check, optional random return/store, then separate fresh
session/interval and attempt/interval reads. Session elapsed must be strictly
greater than signed interval; attempt elapsed may equal it. Predicate AL and
its conditionally reached fresh flag gate the pointer-replacement helper.
The local initial clock is stored before the final random helper result.

Random/control/predicate/replacement effects remain explicit helper captures.
Physical random PUSH order is `(300000,60000)`; replacement order is
`(0x46eca8,captured_target,0x554228)`. These source operands do not certify
native helper ABI or pointer identity.

Dispatch rereads mode00561f58 for each0/2/3/4/5 comparison. Mode0 optionally
binds MainWorkerFrame with the same own queue; child completion and caller
normal return remain separate. Other mode helpers retain explicit opaque
return receipts. Cleanup independently reads root slot/root/offset/ECX/target,
then requires callback, SEH-restore and epilogue normal receipts. A completed
cleanup helper is not assumed to prove callback return.

SourceCallbackFrame composes entry/prequeue ->post-drain/event ->tail. If the
earlier path has no known own queue, a fresh `early_tail_queue` is mandatory.
This applies to early cleanup and direct-epilogue paths; it does not invent an
empty queue or assume opaque prelude helpers leave one unchanged. Completed
post-drain paths carry their generated own event queue into the tail.

The three source partitions contain224,44,121 instructions: together all389
records of0046f520. This is a normal-control model partition, not proof that
every native instruction/helper/exception behavior was reproduced. The
`normal_return_receipt` flag records supplied model receipts. Whole callback
semantics, return registers/ABI, hooks, native memory/queue effects, scheduler
and live compatibility remain unverified.

Thirteen tests cover distinct entries, control/lock order, wrapped inclusive
unlock, signed/fresh interlude thresholds, random gaps, predicate short-circuit,
fresh modes, main-child/outer return gates, cleanup/epilogue separation and
full segment composition. The audit checks1274 records across two pinned
callback/main-worker versions,242 tail records and two retained REA bodies.
These APIs are not yet bound to the own panel's callback execution trial.
