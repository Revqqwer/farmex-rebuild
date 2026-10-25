# Relog configuration source fields

The 719-instruction `00412f48` routine reads these 15 fields. The table contains
source key names and destinations, not actual configuration values.

| Branch | Section | Key | Source destination / kind |
|---|---|---|---|
| Common | CAPTCHA | ENABLED | 561ed0, low AL byte |
| Common | CAPTCHA | SERVICE | 561ed4, full DWORD |
| Common | CAPTCHA | DETAIL | 561ed8, managed string assignment |
| mode=1 | USKO | LOGIN | 50b2d8, low AL byte |
| mode=1 | USKO | FULLLOGIN | 50b2d9, low AL byte |
| mode=1 | USKO | SERVERINDEX | 50b2cc, full DWORD |
| mode=1 | USKO | CHANNELINDEX | 50b2d0, full DWORD |
| mode=1 | USKO | CHARINDEX | 50b2d4, full DWORD |
| mode=1 | USKO | ID | local string, then conditional buffer through 553c5c |
| mode=1 | USKO | PW | local string, then conditional buffer through 553c60 |
| mode!=1 | STEAMLOGIN | ENABLED | 50b2d8, low AL byte |
| mode!=1 | STEAMLOGIN | FULLLOGIN | 50b2d9, low AL byte |
| mode!=1 | STEAMLOGIN | SERVERINDEX | 50b2cc, full DWORD |
| mode!=1 | STEAMLOGIN | CHANNELINDEX | 50b2d0, full DWORD |
| mode!=1 | STEAMLOGIN | CHARINDEX | 50b2d4, full DWORD |

The source branch compares the BYTE at553e46 with exactly1. All other BYTE
values take STEAMLOGIN; the routine does not independently require mode2.
Numeric defaults are zero and string defaults are empty source literals.
The numeric wrappers import GetPrivateProfileIntA; the string wrapper imports
GetPrivateProfileStringA. A BYTE store retains low AL, without a new Boolean
normalization or an index range/one-based adjustment at that store.

The BYTE helper itself DOES normalize its raw API integer to0/1 before that
store. Its default is truncated to BYTE before the API call. See
[owned native API evidence](PROFILE_API_NATIVE.md); raw API EAX and the helper's
returned EAX are distinct observations.

The USKO branch allocates two0x32-byte regions using VirtualAlloc with
physical pushes(0x40,0x1000,0x32,0). This happens before reading ID/PW and
does not depend on the two login-enable flags. Following two short-circuited
string-comparison results, the source can store lengths at50b2c4/50b2c8 and
copy through553c5c/553c60 using _memcpy. The visible copy span does not test
allocation success or bound those lengths to0x32. This records original
behavior; it is not an instruction to reproduce unchecked copies in a native
implementation. String comparison/RTL behavior and complete state transitions
remain to be modeled before any runtime claim.

The catalog does not open INI files, read stored account data, call a CAPTCHA
service, log in, allocate native buffers or dispatch game actions. CAPTCHA
field names alone do not prove a working challenge-solving feature. Key
inventory, loader implementation, and live behavior are separate milestones.

Evidence: `FarmexBot_relog_ayar_alanlari_kaniti.json` verifies2000 instruction
records across the two source images, four helper bodies and four import
identities per version, plus all literal/key/call/store anchors. The new REA
analysis covers00412f48. The machine-readable catalog is
`relog_config_fields.json`; all runtime verification flags remain false.
