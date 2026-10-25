# Collection continuation — own replay

`MerchantCollectionFrame` retains one collection invocation across missing
observations. Each reached, non-unknown scalar is frozen separately. Unknown
fields and unreached probes can be provided on later calls. The original
immutable state is replayed so the source queue-clear does not erase already
collected records on resume, and completed records do not accumulate twice.
Explicit null probes, inactive actors, visited IDs, and both inclusive lookup
endpoints retain the existing collection semantics.

`advance` returns the existing `MerchantCollectionDecision`. `collected` is
terminal; `needs_observation` can resume. `abort` retains partial evidence and
reports `aborted`, never a normal source return. Each new invocation requires
a new frame. Consumed observations are exposed as a read-only copy.

This is a single-threaded owned observation replay. It executes no native
lookup, game read, queue send, or original helper. Invocation-level checkbox
values are frozen when consumed; changing native flags during a source loop
is outside this fixed-snapshot model. Scalar coordinate conversion and overflow
limitations of `collect_merchants` remain. Scheduler child composition, normal
return receipts, timer dispatch, and live acquisition are still open.

Validation: nine continuation/regression tests and the full 4,405-test Python
suite. No new GUI run or binary decompile was performed in this stage.
