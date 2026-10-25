# Allocation stat-name and skill queries

00462ed8 treats the first stat row field as an ANSI string argument: copies
the argument, constructs literals and compares in order STR, HP, DEX, MP,
INT. Each literal cleanup happens before its result branch. A match reads the
guarded character root and selected field using these captured offset slots:

| Literal | Offset global |
|---|---|
| STR | 005540f4 |
| HP | 005540f8 |
| DEX | 005540fc |
| MP | 00554104 |
| INT | 00554100 |

The last two entries deliberately do not follow numeric address order. No
match returns zero. A matching DWORD is retained across argument cleanup;
source normal return is a separate receipt. String construction, copying,
comparison and cleanup are opaque normal-path observations, not a recreated
ANSI runtime or exception/refcount proof. The byte literals are pinned disk
facts; the live argument's managed-string pointer identity remains unverified.

00462d20 accepts raw skill index1..4, reading the guarded root at the slot
specified by 00553e80, context offset slot00554054 and field-offset slots
00554058/5c/60/64. Unsupported indices compare and return without assigning
EAX. The model requires the captured incoming EAX on that path; it does not
invent a zero default.

AutoAllocationObservation has optional `query_children` keyed by reached
`statN.query` or `skillN.query`, containing AllocationQueryObservation. A
generated child must complete, the outer helper must separately return, and
the captured caller query EAX must equal the child's full EAX. Incomplete
children block later threshold/action/stamp handling. A newly detailed child
cannot be bound after an opaque query return has already been consumed.

Ten tests cover five stat paths, no match, cleanup gaps, three guarded skill
reads, unsupported-index EAX preservation, reached parent binding and exact
EAX agreement. The audit checks846 instruction records across two pinned
Richard versions, including both complete query bodies and their caller,
and matches two fresh REA outputs to the current export.

The detailed query children are now optional in panel JSON; see
[panel query binding](ALLOCATION_QUERY_PANEL.md). No native memory/protection action, callback execution,
point mutation or live compatibility is certified.
