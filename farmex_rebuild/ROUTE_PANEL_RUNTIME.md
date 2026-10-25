# Source shared route-panel open/close

`Button21Click`004aead0 is shared by Koruma's active ROTA ÇİZ button and the
design-disabled Draki route button. It reads MainTab left, then top+20, then
height-20, sets panel width600 and finally Visible=true. The reads occur between
setters; no one-time bounds snapshot replaces that order. Integer arithmetic
retains lowDWORD/signed32 behavior before the own widget sizing policy.

`btnRouteWindowCloseClick`004aae6c first sets chRouteSaveGates unchecked, then
hides RotaPanel. The retained VCL260 TCheckBox/TCustomCheckBox VMT slot134
resolves to TCustomCheckBox.SetChecked. This identifies the pinned package's
setter, not the original process's currently loaded runtime or native side effects.

The actual own buttons now update Tk placement and the own checkbox value.
Hidden geometry remains in the controller until visibility is set; it does not
accidentally show the widget during a geometry setter. Rerender/profile overlay
retention is an own UI policy. Completed geometry/checkbox prefixes remain
inspectable if a later own setter fails. Native VCL bounds clamping, exception
and lifetime semantics are not certified.

This stage opens/closes the source panel only. Its route command/edit/load/save
callbacks and game gate-recorder hookup remain separate work. The standalone
route editor elsewhere in the workbench is not claimed as those source callbacks.

All16 Draki interactive controls remain design-disabled,15 with no event. The
sole route event references MainTab/RotaPanel and VCL layout/visibility setters;
it does not establish Draki entry automation. The21 published field records were
matched in both pinned binaries. Searching all published assembly for these
offsets found15/13 raw literal hits and zero non-stack register-memory candidates.
That search cannot exclude computed/indirect/RTTI/undiscovered accesses or later
runtime enabling; it is not proof that all Draki runtime code is absent.

Actual hidden UI tests cover fresh geometry, width600, gate checkbox reset
before close, rerender placement, disabled Draki controls and an inert disabled
Draki route button, without queue or game effects. Full regression and source
scope are recorded in ROUTE_PANEL_RUNTIME_VALIDATION.json.
