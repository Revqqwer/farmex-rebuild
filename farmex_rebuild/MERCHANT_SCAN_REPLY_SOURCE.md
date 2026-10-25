# Captured reply-source producer

`ScanReplyObservation.source` accepts a `ScanReplySource`: typed actor lookup,
coordinate/ftol, name-field/copy observations, per-slot base/extension/item-name
observations, and an explicit Windows codepage. Ready-made decoded metadata
remains supported as a separate mode; an in-flight source gap cannot be bypassed
by changing to that mode.

`MerchantReplySourceFrame` reuses the existing producer plans with private
demand readers. Known fields are frozen only when reached. Normal-return false
or unknown can become true later. Unreached EAX/slot/category fields remain
fresh; missing values can arrive without repeating prior fields. Completed
actor/item metadata is not produced again, and record prefixes do not duplicate.

Actor production precedes item production. Coordinate reader return, ftol
return and EAX are separate. Inline names retain the initial field read and
fresh inline offset. Item base/extension lookup, caller name category, the
name helper category and stored record category remain separate observations.
Zero lookup results retain existing fallback behavior; they do not fabricate
empty records or missing helper returns.

Only complete required byte ranges are cached. Short item captures can be
completed later; copied trailing bytes outside the requested item range are
not frozen. Actor copies retain their exact-range contract. Rejected reads
skip capture bytes. Unsupported native overflow/overread boundaries stay open.

Own Windows decoding is lazy and uses the explicit codepage with flags0.
No host/codepage fallback is selected. Empty byte strings need no conversion;
nonempty text waits for the codepage. Original ANSI item bytes are preserved
through source suffix/category formatting into the actual table pipeline.
This is an own conversion policy, not proof of original RTL/game codepage,
lifetime, native helper execution or automatic game acquisition.

Metadata completion still requires the independent original parser and finish
returns before dispatch clears busy. The actual timer/UI test supplies raw
copies and derives Turkish seller/item names after a missing-codepage hold;
it supplies no ready-made Unicode names for that source phase.
