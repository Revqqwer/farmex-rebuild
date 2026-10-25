# Callback replacement source scope

`0046b8fc` has three formal DWORD arguments: saved-original cell, target slot,
replacement. Callers push them in reverse order. A nonzero saved cell bypasses
the guarded reader. A zero cell causes `0045dc44(slot)` and stores its captured
EAX, even when zero. The helper then copies four bytes from its replacement
stack argument to the target slot through imported `CC32260MT.DLL!_memcpy`.

`CallbackReplacementFrame` projects these ordered reads, calls, stores and copy
intent. The reader, copy, prologue and return each require separate normal
completion observations. No native pointer is dereferenced by this model.
Aliased cells retain source ordering; no synthetic pointer validity checks are
substituted for native behavior.

`RelogReplacementFrame` binds either the controller bootstrap call or the gate
installation call. All arguments come from the reached parent call; a child is
never created for an unreached branch. Child completion and parent helper return
are separate observations. Original parent APIs remain available independently.

This is a normal-path behavioral model. It does not prove guarded-read behavior,
native memcpy failure/partial effects, exception unwinding, target writability,
hook installation or compatibility with a running game. Previously recorded
owned-slot fixture results remain historical and are not new live evidence.
