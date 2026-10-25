# String profile wrapper and complete config-helper binding

`ProfileStringFrame` follows current0045f228's120-instruction normal control.
Four explicit RTL self-conversions occur in default/path/key/section order.
Later converted-pointer tests and value loads are independent; nulls select
four source empty literals. Original formal pointers never substitute for the
post-conversion observations.

The physical GetPrivateProfileStringA arguments are(path,255,stackBuffer,
default,key,section). The source does not consume its returned character count:
EAX is replaced by the stack-buffer address before managed construction.
Buffer construction00505bb8 and output assignment00505c88 are opaque normal
boundaries. Assignment is only an intent. A fresh formal-output-slot read
supplies the eventual return EAX; it is captured before temporary/formal cleanup,
saved FS restoration and frame return. No actual buffer text or account string
is represented or read by this model.

`RelogConfigProfileFrame` extends the numeric composition with reached DETAIL,
ID and PW helpers. It derives all five formal arguments from each actual
source call. A string helper's EAX is not injected into the parent because the
caller ignores it; parent Unicode-to-ANSI conversion still needs its own
normal receipt. Steam creates8 helpers; USKO creates10. Unreached branches
create none. Child completion and outer helper return remain independent.

`RelogStartupProfileFrame` binds this config composition between replacement
and code-state. Missing string conversion/API/cleanup stops that path. Existing
raw, numeric and earlier startup APIs remain available.

Five retained owned-native ASCII string cases confirm the capacity/NUL/count
observations used at the API boundary. They do not certify original Delphi
construction/encoding, output assignment, exceptions or ABI. The fixture was
not rerun for this stage. No original INI, stored account data, game process,
native memory or API is accessed by these Python models.
