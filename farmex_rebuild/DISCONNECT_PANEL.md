# Own DC/relog panel binding

The EnginePage DC / Relog Ayarları case consumes14 existing source-named
controls. The route combo uses its displayed Text, other text editors use
their current strings, flags use booleans, and combo indices remain signed UI
indices mapped to raw DWORD. An index of-1 is not silently changed to an action.
Two source-unread checkboxes are excluded from the snapshot and compiler inputs.

The stable snapshot includes all14 values, actual route Text and explicit
Windows codepage. A changed snapshot requires new observations, even when the
route index is unchanged. Reached getter/text observations cannot override
panel values. Typed integer and ANSI capture boundaries remain explicit.
The convenience example uses only an owned signed-decimal64 subset and local
Windows encoding; it is not original RTL equivalence.

Accepted scalar/string prefixes persist in a local shadow across incomplete
captures and later invalid data. Explicit reset clears the shadow. Replaying a
completed snapshot is idempotent. Profile save/load retains the14 values and
dynamic route choices. No source event, native worker, process shutdown/close,
relog, chat/PM or game operation is dispatched.

The14 fields add13 previously outside-inventory paths. Compiler coverage grows
355→368; outside-inventory editable paths decrease168→155. These are control
counts, not percentages of completed features. The bounded source producer
remains241 of its parent1219 instructions; full-function/live certificates are
unchanged. Hidden UI tests preserve the user's foreground application.
