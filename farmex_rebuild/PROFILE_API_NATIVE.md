# Owned native profile API evidence

The fixture creates one new ASCII INI in its own workspace directory and reads
only that generated file. It accepts no arguments, account values or game PID.
Ten numeric and five string cases passed using actual Win32 profile APIs.

Source BYTE wrapper0045f508 first zero-extends its default BYTE, calls
GetPrivateProfileIntA, then TEST EAX/SETNZ AL/AND EAX,1. Its return is
normalized0/1, unlike truncating raw API EAX. The caller stores low AL of that
wrapper result. The config frame's raw helper-result API remains opaque; an
API-child binding must apply this normalization rather than pass API EAX directly.
The optional binding now exists in [PROFILE_NUMERIC.md](PROFILE_NUMERIC.md).

Observed examples: API256 andFFFFFFFF map to boolean1; missing boolean default
256 becomes API default0, while default257 becomes1. DWORD wrapper0045f5f4
keeps the complete default/result. The fixture confirmed hex42, negative
DWORDFFFFFFFF and case-insensitive ASCII key lookup for its declared cases.

Source string wrapper0045f228 passes capacityFF to GetPrivateProfileStringA.
The owned fixture confirmed plain/quoted/empty/default strings and a300-character
input returning254 data bytes plus a NUL. This does not prove Delphi Unicode/ANSI
conversion, locale-sensitive text behavior or the original managed string ABI.

The C fixture implements the API call and derived return arithmetic. It does
not execute the original DLL or transplanted wrapper instructions. No game,
process memory, protection change, original INI, CAPTCHA service, login or
stored account data was accessed. No Windows RunAs/UAC was requested; execution
was on the host outside the tool sandbox, with host elevation not measured.
Fixture source is packaged; its EXE and generated INI are excluded.

Python runtime files were unchanged, so the prior3738-test result is retained
rather than rerun. Native cases and Python tests are separate evidence; neither
establishes live compatibility or complete wrapper behavior.
