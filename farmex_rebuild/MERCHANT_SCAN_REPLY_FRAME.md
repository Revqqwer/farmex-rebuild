# Active scan reply composition

`MerchantScanReplyFrame` composes the active-scan opcode68 slice with explicit
decoded actor/item metadata and the inert shared packet queue. Non-scan branches
are reported outside scope; this frame installs no packet hook or game sender.

Subtypes27/02/11 clear the pending scan flag without metadata or finish helper.
For05/23, status byte1 reaches the metadata projection and separately requires
the original parser normal return. Other statuses skip that parser. Completed
metadata records are retained across missing later metadata; reached actor and
completed slot metadata remain frozen. Neutral own row projection is followed
by the actual UI's current filter/search/sort, not certified source interleaving.

Finish mode1 emits6808, mode2 emits6827, length2/delay0. Setup return, local
enqueue/its return, and the original finish return remain separate. A partial
enqueue is visible once; waiting never appends another copy. Only the finish
return allows the dispatcher to clear busy. Disconnected enqueue may complete
without a record and still clear busy after the independent finish return.
Other helper modes, source pointer operands and lifetime/SEH remain unmodeled.

`receive_merchant_scan_reply` accepts explicitly supplied immutable bytes only
while the owned loop is active. Tickets include the generation. Replies wait
FIFO until the in-flight scheduler invocation returns, then take priority over
the next tick. This is an explicit own single-thread policy, not a reconstruction
of native hook races. Stop/restart/profile/destroy invalidate pending replies.
Malformed packets retain busy; later queued valid replies remain available.

The timer provider receives `context.reply` with ticket/payload/pending result
when that reply can be processed; it returns `ScanLoopInput(reply=...)`.
New records and finish queue entries publish once into current owned state,
preserving interleaved Flood/PM writers. Partial records do not certify parser
completion. Native capture, automatic lower-level metadata acquisition, game
delivery, and other merchant dispatch branches remain open.

Validation separately records15 Python frame/loop scenarios, full regressions,
actual timer -> request queue -> supplied reply -> visible table -> finish queue
checks, and two pinned binary active-dispatch/finish sections (244 records).
