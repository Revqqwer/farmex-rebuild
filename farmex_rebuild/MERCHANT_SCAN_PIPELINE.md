# Owned scheduler / child composition

`MerchantScanPipeline` connects one `MerchantScanFrame` invocation to a
`MerchantCollectionFrame` or `MerchantConsumeFrame`. The immutable entry
collection supplies pending-count and busy gates. Conflicting explicit values
are rejected. Full collection supplies its modeled EAX; a conflicting observed
EAX is rejected. Child completion cannot supply the independent parent normal
return. Missing post-consume clock still waits without repeating the child.

The consume child holds a stable own head and freezes reached kind/variant
choices. Explicit boundary receipts cover head capture, target write, packet
copy, erase iterator/move/tail and iterator cleanup. Target-write is an external
boundary for the pointer/read/write chain; its native operands are not modeled
here. Copy-helper targets differ between the pinned versions: 0050792a in the
older binary and 00507946 in the refreshed binary.

`EventEnqueueFrame` updates the shared inert packet queue once. Its partial
enqueue remains visible while its independent return is missing. The merchant
busy flag is set after that return, including the disconnected/no-enqueue path.
Vector head removal follows erase-tail return, before iterator cleanup. Own
partial effects survive missing observations and abort; they are not evidence
of native rollback, delivery, or an actual merchant reply.

Each terminal scheduler invocation requires a new pipeline for the next tick.
Waiting, busy, movement, export and stop keep their existing scheduler gates.
Export and stop are independent external observations, not newly executed
children. No automatic timer, GUI provider, native sender, live lookup or reply
dispatch is bound in this module. A reply cannot be invented to clear busy.
Original initialization, vector races, lifetime and SEH remain outside scope.

Validation: full 4,423-test Python run with nine collection-continuation and
18 pipeline/consume tests; retained scheduler and consumer bytes checked
against both pinned binaries (810 instruction records). No new decompile or
GUI run. Detailed scope is in `MERCHANT_SCAN_PIPELINE_VALIDATION.json`.
