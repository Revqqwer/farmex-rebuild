# Source route add buttons

Actual Town, Gate Skill, (C) Otur, (C) Kalk and Bekle/EKLE now append to the own
source route table and profile list. The four constant captions are Town,
Gate Skill, Otur, Kalk, with two literal dash subitems. They do not use zeros.
The callbacks append via Add even when an existing row is selected; the source
disabled selected-position radio remains disabled. These are data edits, not
execution of movement, town, skill or posture actions in game.

Order is blank row Add, caption, first subitem, second subitem. Bekle reads its
current edit text after Add/caption. It uses the existing pinned scalar integer
model and default5 as own conversion policy, then signed64 decimal formatting;
the second subitem is dash. Native StrToInt64 catch/cleanup and CRT formatting
are not executed or certified. Source local formatting wrapper has UTF16 %lli.
Partial own setter/text errors retain
the completed row prefix rather than rolling it back.

The list sink is shared with source loading. Own document identity guards reject
stale callbacks; this is not native VCL lifetime/notification/SEH equivalence.
Full actual UI tests invoke all five buttons, preserve a selected old row,
exercise signed64 hex/default5, retain rows after rerender/profile binding and
save/clear/load them through the actual .R controls. No request queue changes.
Six new Python tests cover exact constants/order, fresh wait text, signed/default
policy, partial setter/text failures and unknown method rejection.

ROUTE_COMMAND_RUNTIME_VALIDATION.json records4522 Python tests and full GUI.
Source834 instruction records cover both pinned callback sets and local21-row
integer formatting wrappers, including independently read dash/format literals.
For subsequent camp/speed additions see ROUTE_ADVANCED_RUNTIME.md.
Coordinate/NPC additions and gate-recording remain open, along with
native runtime equivalence, other features and live compatibility.
