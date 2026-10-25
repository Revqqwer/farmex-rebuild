# Disconnect/relog settings producer span

The model explicitly starts at00457d02 and stops at004580ac:241 instructions
inside the1219-instruction004576ec producer. It does not imply that the earlier
list rebuilding or the later protection settings ran normally. No synthetic
function prologue/return is added to this middle span.

| Source control | Context member | Behavior |
|---|---|---|
| chDCControl | +8a | low AL flag |
| dcDCControlAlarm | +8b | low AL flag |
| chDCControlProc | +8c | low AL flag |
| cmbDCControlProcIndex | +90 | full raw DWORD index |
| txtDCAutoLoginWaitSeconds | +94 | numeric helper low DWORD; fallback30 |
| chDCControlStartBot | +98 | low AL flag |
| chRelogAfterReturnSlot | +99 | low AL flag |
| No control read | +9a | unconditional byte1 |
| cmbRelogAfterReturnRouteName | +9c | actual Text string assignment |
| chRelogAfterSendChat | +a0 | low AL flag |
| txtRelogAfterChatText | +a4 | string assignment |
| cmbRelogAfterSendChat | +a8 | full raw DWORD index |
| chRelogAfterSendPM | +ac | low AL flag |
| txtRelogAfterPMNick | +b0 | string assignment |
| txtRelogAfterPMText | +b4 | string assignment |

The source does not read chDCControlWaitSecond or chRelogAfterUseManuelRoute
in this producer. Both controls have event handlers, but those handlers call
the shared producer; their presence is not an independent setting read.
All16 primary panel handlers check561f55 before calling004576ec with562194.
The static method records, published field bytes and UI paths are corroborated
in both preserved bot images. Runtime form identity is not certified.

The bounded model reuses typed settings/SourceInteger observations. A captured
normal/catch route and separate parser return are required; text is not guessed
into a numeric result. No clamp, unit scaling, index fallback or string encoding
equivalence is invented. Context wrap, partial prefixes and captured ANSI byte
assignments are preserved as local projections. It executes no shutdown, game
close, relog, chat, PM or memory operation.

These14 input paths are now connected to the own DC / Relog Ayarları preview.
Thirteen were new compiler-inventory entries; route selection was already
present. The inventory is368 compiled inputs and155 outside-inventory editable
paths. This is a local UI/model binding, not complete feature/live proof. See
DISCONNECT_PANEL.md for snapshot, conversion and validation limits.
