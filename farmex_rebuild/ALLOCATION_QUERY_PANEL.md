# Allocation query children in the panel trial

The optional `consumer` JSON now accepts `query_children`, alongside
`action_children`. Keys are reached `statN.query` or `skillN.query` labels.
Each child has `values` and `normal_returns` objects, read only as the source
model reaches them. Query cleanup, source helper return and caller outer
return remain separate observations; caller full EAX must equal the detailed
child result. A completed query does not imply a completed action.

The panel rejects a reached skill `query_argument` differing from the
producer's caption-derived action DWORD, as it already does for action
arguments and thresholds. Stat's first field is still an explicit captured
managed-string value/pointer; the adapter does not invent its runtime address
from the panel name bytes.

Unsupported skill query indices preserve incoming EAX. In caller00458df8,
00458ef7 loads row index into EAX and00458efa computes three times that index.
The subsequent MOVs use EDX/ECX; the PUSH and CALL leave EAX intact. The bound
query therefore derives incoming EAX as low32(3*row_index): first row0,
second row3. Contradictory unconsumed captures are rejected; later captures
cannot overwrite a value already consumed. The standalone helper's incoming
EAX remains an explicit observation because it has no caller binding.

UI reporting separates detailed query count from detailed action count.
Existing opaque query captures remain available when no child is supplied.
Reset starts a fresh invocation; changing panel settings invalidates both
producer and consumer snapshots as before.

Eight new tests exercise first/second unsupported-index rows, contradictory
versus consumed incoming EAX, full panel query/action composition, separate
cleanup and outer return, caller EAX disagreement, panel query-argument
identity and reached-only field validation. The own hidden UI smoke checks
query cleanup and action callback gaps in order and resumes both.

The audit byte-checks846 prior caller/query instruction records across two
Richard versions and matches one fresh REA caller analysis. This adds no
binary coverage. Native ANSI runtime, managed-string/vector pointer identity,
callback ABI, point effects and live compatibility remain unverified.
