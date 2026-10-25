# Readiness, session stamp and future callback-slot switch

The entry model now accepts optional typed `lifecycle_children` at ready,
prelude1 and prelude2, mapping respectively to0046edb0,0046eccc and0046ed60.
An inner helper must finish before its separate caller normal receipt is
accepted. Readiness caller AL must agree; known full-zero paths also reject
an inconsistent full EAX. Late detailed binding after an opaque call returned
is rejected. Existing unbound raw-helper captures remain available.

Readiness first calls the opaque object check at0055424c. Its AL0 path returns
full EAX0. Otherwise it conditionally checks high/low session stamp, notice
enable, active state, done flag and a second fresh notice-enable byte before
the notice helper/store. Success sets AL1 without certifying upper EAX.
These object/notice helpers remain observations; no authentication or
eligibility outcome is inferred or bypassed.

The session helper distinguishes its special flag path from first initialization
and later profile-refresh paths. High stamp nonzero short-circuits the low
read. A zero stamp receives an explicit clock result. Initialization/tick
stores and done/reset flags retain source order; later refresh has a different
done flag and optional profile helper.

The switch helper skips mode4 with its special byte. Otherwise an enabled
sleep flag calls the import-table-confirmed KERNEL32.SleepEx. Physical PUSH
order is `(0,milliseconds)`; the source global00553e40 is the duration operand,
not a wait-object handle. No real sleep is performed by the model.

Switch predicate0046eb8c returns false/full0 only when its first five bytes
555e1d..21 are all nonzero and the final555e22 is zero. Every other reached
path sets AL1 with upper EAX unspecified. An optional generated predicate
child binds this result to the switch caller before the separate outer return.

A true result invokes the replacement helper with physical pushes
`(0x46eca8,captured_target_slot,0x554228)`. Its optional scoped replace child
captures original target only while saved cell0, then plans the four-byte
pass-through pointer copy. Source protected-read/copy/return receipts remain
separate and no native pointer is written. This child is for this fixed
callback role, not a claim to emulate every use of the generic helper.

Changing the future callback slot does not terminate the current callback.
After the switch helper and caller return receipts, the entry model continues
to connection checks and queue work. Real future thread/dispatch behavior,
hook lifetime and native storage/protection/ABI are not proved.

Twelve new tests cover AL/full-zero distinctions, fresh flags, session branches,
predicate truth table, SleepEx operands, save-once/copy gaps, nested children,
continued caller flow and rejected retroactive bindings. The audit checks1032
records across both pinned versions,254 helper records, four fresh REA helper
bodies plus one retained replacement body, and both SleepEx import identities.
UI remains unchanged; these are source/API normal-path models with opaque
lower helpers and unverified native effects.
