# Actual owned manual item-break button

`frmMain/MainTab/sheetCrash/GroupBox14/Button5` now invokes the captured
`ItemBreakManualClickFrame` through `OwnedManualItemBreak`. Each actual click
queues its own ticket; the source manual path adds no automatic enable/work,
inventory-full or cooldown gates. Other Gem/Box/Narki modes remain unverified
and source-disabled design controls are not enabled by this adapter.

An optional synchronous `manual_item_break_provider(context)` returns typed
`ManualBreakInput`: source manual/NPC/request observations and a separate
handler-return receipt. Missing provider means missing helper entry/data, never
a guessed NPC, gem, source prologue or normal return. Original managed string,
lookup, coordinates, distance, selection and notice operations remain boundaries.

100ms Tk polling and per-click FIFO serialization are own asynchronous UI
policies, not recovered native timing. Rerender preserves pending work. Profile
change/destruction cancels polling, clears the provider and invalidates tickets.
Stale callbacks cannot cancel a newer timer, provider profile changes cannot
commit old data, and reentrant clicks queue another invocation without recursion.

Reached NPC stores update an own scalar shadow shared with the automatic path
in the panel. Each invocation applies only its new store prefix, so resuming
an old callback cannot overwrite the other path's newer NPC selection. Manual
work does not reset the automatic clock. An explicitly shared dictionary is
one owned state epoch; the panel resets both owners together on profile change.
Newly staged records
publish once into the latest shared queue with fresh own IDs, preserving
interleaved Merchant/Flood/PM entries. Target-prepare enqueue and the two6/19byte
requests retain delays0/200/250 and independent return receipts. A completed
manual child still requires the callback return. No queue publication proves
native writes, packet delivery, game inventory changes or server acceptance.

NPC/gem notice paths and nonzero-mode early exit leave the queue intact. Their
messages are presented as local observation status; original modal UI semantics
are not reproduced. Already published queue prefixes survive profile reset.

Evidence uses the retained REA manual/request assemblies, two pinned binaries
and862 selected instruction records. New actual-button tests cover missing
provider, rerender, manual use with auto disabled, partial enqueue, other writer,
callback-return gap, notices, reentrant FIFO and profile/stale callback behavior.
