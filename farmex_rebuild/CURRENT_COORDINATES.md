# Captured current-coordinate getter contracts

The source coordinate-add event creates/captions its row, calls004625ac for
route X, then004625d8 for route Y, and only after both returns appends signed32
parameters using local %i formatting. Each getter independently reads bot global
553e7c and calls guarded DWORD helper0045dc44, then reads offset554008 or554010,
adds it with DWORD wrap and calls guarded float0045ddb8, then CRT __ftol.
The helper retains only EAX lowDWORD from its signed64 conversion result.
These are pinned bot-image globals, not verified current-game absolute addresses.

plan_current_coordinates models one explicitly captured replay. Subsequent
owned continuation frames are documented in CURRENT_COORDINATE_FRAMES.md;
neither interface is a process reader. Root, guarded float, __ftol and axis parent returns
are separate receipts. Float bits do not infer __ftol EAX, even for zero.
Both axes must complete before parameters are exposed; a pending Y preserves
the completed X prefix for inspection without publishing half a row.

Null guarded-float address or failed protection yields positive-zero float
bits. Root null/protection failure does not short-circuit the coordinate getter:
it still adds the reached offset and can attempt the float helper at that
nonzero address. No root or converted coordinate is shared between the axes.

The original guarded helpers call VirtualProtect(address,4,0x40,oldProtect).
Their checked bodies contain no protection restoration. The own plans execute
neither that API nor any process access; original page-protection side effects
and loaded CRT identity remain unverified. Source __ftol disk bytes show its
CW/FISTP/FCLEX path, but this API requires explicit captured normal results and
does not assume an FPU context or synthesize conversion/exception outcomes.

Eight new tests cover zero/protection/observed float paths, address wrap,
dependency order, root0 plus nonzero offset, fresh per-axis roots/offsets,
partial pair/normal-return gaps and wrong types/addresses.383 source/CRT
instruction records were checked across both pins and the retained CRT image.
CURRENT_COORDINATES_VALIDATION.json records4537 Python tests. No new GUI run:
the327-module app/smoke_ui closure matches the4529 full GUI stage and the new
API/test modules are outside that closure.

The coordinate button is still unbound. A resumable click/frame, automatic data
and normal-return provider, NPC additions/gate recording and wider native/game
compatibility remain required. A complete captured replay is not a certificate
of actual game position or original native execution.
