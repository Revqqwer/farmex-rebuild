# Relog installation status dispatcher

Current `004e2bc8` and historical `004e2bac` each contain 93 instructions.
The DWORD at `0056ff3c` selects between two detector groups. Initial zero enters
the first group after a distinct INC read/modify/write. Initial nonzero causes
a fresh comparison: exactly one clears the DWORD and enters the second group;
any other value returns EAX zero without writing the caller output.

Each detector is bracketed by normal calls to `004e2a88(0)` and
`004e2a88(1)`. Its AL is captured before the second call. First-group results
are code1 for first nonzero, code2 for second zero, code3 for third nonzero;
otherwise code91 and full EAX zero. Second-group results are code4 or code5
for the first nonzero detector, otherwise code92 and full EAX zero.
Codes1..5 return AL1; upper EAX is not established by that assignment.
The detector internals and bracket helper effects remain opaque.

Thus callers' signed `output > 90` comparison accepts failure/status91 and92,
not a measured delay. Invalid state leaves the local unwritten; its actual
captured value is required if the caller subsequently compares it. No zero
initialization or valid state invariant is invented.

`RelogProbeBindingFrame` derives a child only from a reached controller/gate
probe call. The output store and full-zero return are bound to caller inputs;
conflicting observations are rejected. Success still requires a raw caller EAX
with matching AL. Child completion, caller return, and subsequent callback
replacement remain separate boundaries. These are inert normal-path models;
native detector execution, exceptions, hook success and live compatibility are
unverified.
