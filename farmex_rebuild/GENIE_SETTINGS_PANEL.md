# Five Genie settings in the own panel

The current producer header004580ac..00458143 has35 instructions. Five fresh
virtual getters store low AL in context562194, in this source order:

| Control | Context member |
|---|---|
| chGenieWithBot | B8 |
| chGenieStopWithBot | B9 |
| chAutoGenieCoupon | BA |
| chNoRemainGenieTimeTown | BB |
| chNoRemainGenieTimeAlarm | BC |

`GenieSettingsFrame` explicitly starts at the middle-span boundary and ends
before the next guarded coupon-byte synchronization at458143. It does not add
a synthetic function prologue or claim that the1219-instruction parent finished.
The source worker uses these context fields in separate control paths; this
panel trial binds only their producer header and local shadow.

`GenieSettingsTrial` reads five actual checkbox values, fixes a snapshot, rejects
conflicting/stale captures and preserves accepted prefixes across gaps or later
invalid data. Replaying a completed snapshot is idempotent; explicit reset clears
the local shadow. The example getter returns are synthetic and explicit.
The Genie Ayarları EnginePage case and own profile roundtrip exercise the widgets.
No native worker, coupon sync, coupon use, start/stop or game action is dispatched.

`chGenieStartStopNoMob` and its time editor are excluded: earlier analysis found
profile save/load but no runtime consumer in the discovered direct-reference
scope. This remains unresolved, not proof the original feature cannot work.
The separate Free Genie control is also outside this five-field binding.

Compiler input coverage grows368→373; outside-inventory editable paths decrease
155→150. These control counts do not measure completed gameplay features.
