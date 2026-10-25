# Panel allocation consumer and action trial

The existing Stat/Skill Ayarlari trial accepts an optional top-level
`consumer` object after the bounded panel producer completes. It has `values`,
`normal_returns`, and optional `action_children`. Child keys are reached row
actions such as `stat0.action` or `skill0.action`; each contains its own
`values` and `normal_returns` for AllocationActionObservation.

The adapter reads only the currently requested field. Unknown or malformed
future captures are ignored until reached. A present detailed child is bound
before accepting an opaque outer action return. Child completion and the
outer return remain separate; callback gaps cannot advance the cooldown
stamp. Partial captures can resume the same invocation. Use reset for a new
consumer invocation with unchanged panel settings.

Reached consumer enable bytes, row thresholds and action arguments must match
the produced panel rows. The same panel snapshot digest protects the sample;
changing meaningful panel settings resets producer and consumer frames.
Bad reached input clears the displayed consumer result while preserving the
consumed prefix for correction. Consumer observations are optional and are
not read while the producer is incomplete.

Example structure (empty objects intentionally wait for observations):

```json
{"consumer":{"values":{},"normal_returns":{},"action_children":{"stat0.action":{"values":{},"normal_returns":{}}}}}
```

Panel example generation still covers only producer receipts. It does not
invent consumer addresses, root chains, free-point getters or callback results.
The displayed action model is a local diagnostic result; no game point is
allocated. Native vector correspondence, stat name-pointer identity, callback
ABI, source scheduler reachability and live compatibility remain unverified.

Eight unit tests cover full stat/skill chains, partial JSON continuation,
separate outer return, panel mismatch rejection, reached-only validation and
snapshot invalidation. The real own hidden UI smoke also exercises panel ->
producer -> consumer -> detailed action, callback gap/resume and stale result
clearing. The evidence audit reuses and byte-checks 3314 unique instruction
records across both pinned Richard versions; it adds no binary coverage.
