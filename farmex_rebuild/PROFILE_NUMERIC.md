# Numeric profile wrappers and config composition

`ProfileNumericFrame` models current0045f508(boolean) and0045f5f4(DWORD).
It requires separate normal RTL conversion receipts for path, key and section.
The source passes each formal slot address twice to00504ef8. Converted pointers
are independently observed after all conversions; original arguments do not
stand in for converted strings. Null tests and subsequent value loads are
distinct; null pointers select the source empty-literal addresses.

The inert GetPrivateProfileIntA call records physical pushes(path,default,key,
section). The boolean wrapper zero-extends default BYTE and normalizes the full
API EAX to0/1. The DWORD wrapper retains raw32-bit default/result. API return,
captured EAX, three cleanups, saved FS restoration and frame return are distinct
boundaries. Captured result survives cleanup gaps. Managed RTL and API effects
remain observations, not locally executed implementations.

`RelogConfigNumericFrame` binds reached scalar calls in00412f48. Formal arguments
derive from their different physical push order. A completed child supplies the
helper EAX; conflicting caller observations are rejected. The outer helper's
return remains separate. Only two common plus five chosen-branch children are
created, and later config observations remain required. The legacy `.handle`
label is the raw source argument from553e58, not a Win32 HANDLE; it reaches the
path-string formal and is converted inside the helper model.

`RelogStartupNumericFrame` binds this nested config model between replacement
and code-state children. It derives config entry from the reached startup call
without bypassing numeric conversion/API/cleanup boundaries. Existing raw and
two/three-child APIs remain available independently.

The audit compares10 previously captured owned-native numeric cases against
the Python helper's API arguments and return. That is agreement with owned
Win32 API observations, not execution of original managed wrappers or a game.
No original INI, account strings, game process or native memory is accessed.
