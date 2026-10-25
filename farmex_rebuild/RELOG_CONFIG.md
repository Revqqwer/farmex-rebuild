# Relog configuration normal control model

`RelogConfigFrame` models the current febdac80...45759 source's normal control
at00412f48. Historical field catalog evidence is retained, but the model does
not silently retarget its current RTL helper addresses to the historical image.

The common CAPTCHA BYTE/DWORD fields precede managed DETAIL assignment and
cleanup. A fresh mode BYTE then selects exactly1 for USKO, every other value
for STEAMLOGIN. Scalar reads use distinct source physical push order for
0045f508 versus0045f5f4; each reads a fresh config handle. BYTE stores retain
low AL; DWORD indices remain raw with no invented clamp or conversion.

Unicode literal construction and its EAX dereference are explicit opaque spans
whose normal completion and captured pointer are separate. Profile/RTL helpers
are also opaque; this model does not implement Windows INI parsing, managed
string representation, native exception unwinding or string encoding behavior.

The optional `RelogConfigNumericFrame` binds scalar helper control and numeric
API return normalization, while leaving managed conversion spans explicit.
Its nested startup consumer is `RelogStartupNumericFrame`. See PROFILE_NUMERIC.md.
`RelogConfigProfileFrame`/`RelogStartupProfileFrame` additionally bind string
helper control and preserve the caller's unused helper EAX. See PROFILE_STRING.md.

The USKO branch projects both allocations regardless of login flags, then ID
and PW read/conversion/cleanup. It consumes no account text. Low-AL comparison
observations short-circuit, and comparison results are retained across cleanup
gaps. Only a permitted path obtains raw metadata lengths, stores50b2c4/c8,
captures fresh copy-source locals, reloads lengths/destinations and issues
inert _memcpy intentions. A null local gives length0 and an empty-literal
fallback. Allocation failure and oversized copy are preserved as source
intentions, never executed or treated as successful writes.

FS restoration requires a captured saved value and a distinct normal receipt;
frame return is a further boundary. Every gap retains the reached prefix.
The standalone startup treats00412f48 as opaque. The optional current-source
`RelogStartupConfigFrame` binds this model at the reached call and preserves
the independent caller return. No actual configuration, account value, process memory,
native allocator, CAPTCHA service or game action is accessed by this module.
