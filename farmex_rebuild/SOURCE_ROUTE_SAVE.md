# Raw source .R writer API

source_route_save.write_source_route_ini accepts an explicit absolute filename
and immutable tuples of three raw ANSI byte strings (command, subitem0,
subitem1). The caller chooses text encoding; the adapter does not guess the
original RTL codepage or convert raw values to JSON.

For nonempty rows, own msvcrt.remove runs first. Its return does not stop the
write sequence. Each row writes Count/Value with the cached total, followed by
ROUTE/ISLEMindex, ROUTE/Sub1index, ROUTE/Sub2index. Indices start at0; Count is
repeated per row. Real Windows WritePrivateProfileStringA receives these bytes.
BOOL0 does not prevent later calls, matching the source's lack of a return-value
branch. The result distinguishes completed calls from writes_succeeded.
No original success notice is generated. A Python backend exception records
the attempted/completed prefix as incomplete; it is not source SEH equivalence.

Empty rows preserve existing files. Parent existence, absolute/NUL-free path,
host-ACP filename validation and immutable input are own adapter policies.
Missing parents are not created. Native A API NUL-prefix and quote behavior
are covered by actual write/read fixtures. File replacement removes stale
sections when remove succeeds; a failed remove is reported and writes continue.
There is no atomic-save or native CRT identity guarantee.

Source004ea01c and refreshed004ea038 were resolved independently via their
actual callback calls. Their repeated writes and remove prefix are pinned by
the retained6538-instruction callback/helper audit. The four-argument wrapper
0045f114 adds186 verified instruction records across both binaries and resolves
to WritePrivateProfileStringA. These are partial data/API semantics, not full
source helper certificates.

Seven new tests cover exact call order/count repetition, failed BOOL continuation,
backend exception prefixes, invalid/empty inputs, real roundtrip/replacement,
missing parent and NUL/quote behavior. SOURCE_ROUTE_SAVE_VALIDATION.json records
4499 full Python tests. No new GUI execution occurred: the319-module app/smoke_ui
import closure is unchanged from4492 ROUTE_LIST_EDIT_VALIDATION.json, and the
new writer/test modules are outside it.

This document describes the4499 API stage. The subsequent actual KAYDET
integration, fresh names/cached count/reached rows and full GUI evidence are
documented in ROUTE_SAVE_RUNTIME.md and ROUTE_SAVE_RUNTIME_VALIDATION.json.
Original directory/prefix/string/notice/exception equivalence remains open,
along with load/choice and command-addition callbacks.
