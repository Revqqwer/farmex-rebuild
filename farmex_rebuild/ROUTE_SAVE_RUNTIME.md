# Source panel KAYDET integration

The actual source GroupBox21/Button27 now saves the own route list as .R via
the real Windows A profile writer. Application supplies the selected route
directory and explicit source text codepage from the existing route editor.
No original bot context directory or game data is inferred.

The own callback reads the name to test emptiness, then captures list count.
Count0 preserves files and exits before looking up a directory. After checking
the selected directory it reads the name again for the filename and appends
.R without trimming or extension deduplication. Basename confinement rejects
paths outside the selected directory; that is an own policy.

The writer removes the explicit target first, then reads each reached row using
the cached count. Rows can change before their iteration; the count is not
recomputed. It encodes current caption and two subitems using the explicit
Windows codepage. Missing later rows/subitems retain already executed remove
and write prefixes. Conversion of each triple before Count is own policy;
native managed-string allocation/conversion exception points are not certified.

Each row writes Count/Value, then zero-based ISLEM/Sub1/Sub2. API BOOL0 does
not stop subsequent calls. A third fresh name read supplies own status/notice
text after completed calls. The status distinguishes actual observed write
failure from successful writes; it does not execute the original notice helper
or reproduce its unqualified success message. Backend exceptions and stale
profile rejection are own policies, not source VCL/SEH/lifetime proof.

Actual GUI tests invoke KAYDET and use only owned temporary files: existing-file
replacement and ANSI readback, blank name, empty rows preserving an existing
file, missing directory, traversal rejection, missing subitems, failed BOOL
status, rerender without another write and profile change during context lookup.
Other request queues remain unchanged. Eight new Python tests include three
fresh name values, count/row freshness and normal/failure boundaries.

ROUTE_SAVE_RUNTIME_VALIDATION.json records full tests and a new full GUI run.
The source callback/save body evidence totals1510 checked instruction records
across two pinned binaries; prior186 wrapper and6538 callback/helper evidence
remain separate dependencies. The refreshed helper004ea038 is independently
resolved from its callback, rather than inferred by shifting old004ea01c.

For subsequent source load/choice integration see ROUTE_LOAD_RUNTIME.md.
Command-addition and gate-recording callbacks remain open.
Original runtime context+57c, default CP, CRT/RTL string effects, notice helper,
native reentrancy/exception semantics and live compatibility are unverified.
