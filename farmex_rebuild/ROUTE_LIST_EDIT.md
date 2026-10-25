# Source route list clear and selected deletion

The actual source RotaPanel TEMIZLE (Button122Click004ac6d4) and SIL
(Button48Click004ac6f8) buttons now operate on the own route table and its
profile rows. Both source callbacks load form+9a8 (lstRota). Retained VCL260
TListView VMT13c identifies TCustomListView.Clear; VMT148 identifies
TCustomListView.DeleteSelected. The installed original runtime is not observed.

The own table selection identifies rows by current index, never by caption or
row equality. Duplicate rows can be removed independently. Survivors retain
caption, subitems and checked metadata; UI IDs are rebuilt for later deletion.
No selection and clearing an empty list are no-ops. The own table uses browse
selection. Native list notifications, selection/lifetime and exception behavior
are not certified by this own Tk implementation.

Closing/reopening or rerendering the panel preserves edits. Profile binding
uses the supplied document rows and resets the previous edit status. Other
lists and inert request queues are untouched. No route commands are executed.

ROUTE_LIST_EDIT_VALIDATION.json records the full Python regression and hidden
actual GUI test, including duplicate-row identity, survivor metadata, consecutive
reindexed deletion, no-selection/empty no-ops, close/open/rerender/profile
persistence and isolation of other lists and queue.

For subsequent KAYDET integration see ROUTE_SAVE_RUNTIME.md. The source route
command-addition buttons, load/choice callbacks and gate recording global/game
capture remain open work. The callback/helper identity
audit covers16 events,3 helper bodies and6538 instruction records across two
pinned binaries. Identity/byte verification is not completed helper semantics;
the independent JSON route editor is not a substitute for those source events.
