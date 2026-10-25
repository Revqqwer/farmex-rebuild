# Automatic stat/skill action operands

The optional generated children now connect the selected raw row argument in
00458df8 to the operand models for stat helper 004650d8 and skill helper
00465ec4. They do not allocate points or execute native callbacks.

Stat helper: four opaque 0045dc44 normal/EAX receipts form the guarded chain.
The raw argument is shifted left two bits and added to the third result and
captured table offset with DWORD wrapping. Its selected entry is retained.
The helper then independently reloads the root slot and two direct offsets,
reads the resulting object's vtable and callback slot, and prepares physical
PUSH order `(1, selected_entry)` with the freshly derived ECX.

Skill helper: the raw argument plus four wraps to DWORD. A fresh root and
captured context offset produce ECX; the target comes from global 00553f0c.
The physical push is the wrapped argument plus four. No stat enumeration,
native signature, successful point change or server ACK is inferred.

AllocationActionFrame caches only reached inputs across gaps. Optional
AutoAllocationFrame action children must finish before the separately
observed outer helper return can advance the cooldown timestamp. They retain
the selected row argument across subsequent changed observations. Binding a
new detailed child after an opaque action has already returned is rejected.
Unbound callers retain their explicit opaque normal-return interface.

Nine tests cover ordered guarded/direct reads, fresh chains, wrapping,
callback versus helper return, reached-only caching, stat/skill parent
binding, late-binding rejection and input validation. Two fresh REA analyses
are matched to pinned exports; 380 instruction records are checked against
two binary versions (126 helper records plus 254 caller records).

Native guarded helper side effects, callback ABI/identity, actual allocation,
runtime memory and live compatibility remain unverified. The panel now exposes
these optional detailed action children through explicit consumer observations;
see [panel consumer scope](ALLOCATION_CONSUMER_PANEL.md).
