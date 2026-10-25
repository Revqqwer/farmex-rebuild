# Event join settings and worker

The six source controls in GroupBox40 map in producer read order to context
offsets Chaos68, FT69, UTC6a, Knight Royale6b, Juraid6c, BDW6d. The visual form
order differs. `compile_event_join` is an own strict checkbox-boolean adapter.
EventSettingsFrame models only00457c5f..00457d02: explicit reached entry,
six ordered getter normal/EAX receipts, low-byte stores and retained prefix.
It does not emulate the earlier vector rebuilds or the full settings producer.

Six published callbacks check source byte00561f55 before calling004576ec with
context00562194. The source46f520 callback also calls worker0045a4dc with that
context. This proves static edges, not native event dispatch or scheduling.

The worker's two groups share timestamp00553d04/08 and use signed QWORD
zero-extended GetTickCount subtraction. It does not use wrapped DWORD elapsed:

- Chaos/BDW/Royale initial flags short-circuit in that order. If enabled and
  elapsed is at most200, fresh priority flags choose at most one helper, then
  a separate fresh post tick stamps the shared timestamp. Negative elapsed
  also passes this source condition. All priority flags turning off still
  leads to the stamp.
- FT/UTC/Juraid initial flags short-circuit in that order. If enabled, elapsed
  must be strictly above200. Target first EAX uses unsigned3000 comparison;
  a distinct second getter must be nonzero, then a third fresh getter is
  passed to the preparation helper. A failed target calls an opaque fallback
  and still stamps. Fresh priority flags then choose FT, UTC or Juraid.
- FT prepares one17-byte request; UTC one18-byte request. Juraid chooses an
  18-byte template for exact nation EAX1, otherwise19 bytes, and prepares two
  requests with delays0 and200. Templates are copied to local stack buffers;
  their disk VAs are provenance, never asserted runtime buffer pointers.

EventJoinFrame retains only reached raw values and normal-return receipts.
Projected stamps and prepared requests survive gaps without reinterpreting
the earlier branch. Helper and enqueue calls are currently opaque normal
receipts. Requests are inert diagnostic plans: no local QueueState mutation,
native allocation/send, event admission or server acknowledgement is proved.
The two groups use fresh timestamp observations; concurrent/native helper
effects are not invented or replaced by an assumed clock interval.

Nine tests cover source order, raw AL producer stores, signed timing, inclusive
versus strict200 boundaries, fresh flags/targets, source priority, target
fallback, nation-dependent requests and delayed-helper prefix continuation.
The audit checks2962 instruction records across two pinned Richard versions,
the field/method records, version-specific template bytes, two new REA outputs
and the prior retained settings-producer REA output.

The six controls now feed the own panel execution trial; see
[panel binding scope](EVENT_JOIN_PANEL.md). Optional generated
packet/enqueue children now project the known own queue prefix; see
[event queue children](EVENT_PACKETS.md). Native helper effects, enclosing callback gates, actual scheduling,
runtime template identity and live compatibility remain open.
