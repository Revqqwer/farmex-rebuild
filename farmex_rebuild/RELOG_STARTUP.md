# Relog startup normal control

`00424924` has 47 instructions in both pinned bot images. The first ready
check precedes SleepEx. Each iteration freshly reads `553f3c`, guards its
value, reads `5541a0`, and guards root+offset. A zero result calls SleepEx with
physical pushes `(0,1)` and repeats; the model invents no retry limit.

After readiness, four opaque preparation calls run in source order. A new
root/object chain then guards the object to obtain a table. The table plus
fresh `554204` is stored in `554210`, which is independently reloaded for the
replacement call `(412adc,freshSlot,554220)` in physical push order. There is
no additional zero-object check on this second chain.

The replacement's normal return precedes `00412f48`, the 719-instruction
configuration routine. It stays opaque in the base/two-child APIs; the current
three-child API below binds its control model. No saved account data or actual
config is read. Next is code-state helper(mode1), followed by direct
`553f68` value plus a fresh `554204` stored in `554214`. This prepares a later
controller installation slot; this startup function does not itself install
the gate callback. Two final helpers and frame return follow.

Source identity selects current `004e30c8`/`004e2a88` or historical
`004e30ac`/`004e2a6c`. It is not a live game-profile selection.

`RelogStartupChildrenFrame` binds replacement and code-state children only at
reached calls. Arguments are derived from source call records. A child must
complete, then the caller's separate normal-return receipt must arrive before
the parent advances. Parent and child prefixes survive gaps; no child effects
are silently applied to subsequent fresh memory observations. Independent raw
parent API remains available. Native helpers, exceptions, actual writes,
configuration content, installation success and live compatibility remain
unverified.

`RelogStartupConfigFrame` adds the current-source config child between the
other two children. Its observation extends the earlier three positional
fields with an appended `config` field. A reached00412f48 call with no arguments
creates the child and derives entry. Completed config/FS/frame observations
still do not imply the parent call returned. Code-state is not constructed
until that outer return is received. All child traces remain immutable plan
snapshots, and no projected config store is silently applied to subsequent
parent reads. Historical source is rejected because the config model pins
current RTL addresses; the original two-child versioned API remains usable.
