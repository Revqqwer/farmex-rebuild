# Transformation/direct skill queue prefix

The captured 004c7710 helper tests the full connection EAX at 004c771c,
branches at 004c771e, and only later calls GetTickCount at 004c774f.
TransformationFrame and inherited DirectSkillFrame now retain that consumed
gate when a clock observation is missing. A later zero or unknown gate cannot
change the earlier branch. Gates supplied before the copy prefix completes
remain unconsumed. A zero gate remains a known skip.

Three regression tests exercise both entry paths, high-byte-only nonzero
DWORD gates, repeated clock gaps, unreached observations, and exactly one
local record across a separate cast-return gap. Before the fix, these tests
exposed seven failing subcases. After the fix, all 3178 tests passed.

The source audit rechecks 268 instruction records across two pinned Richard
versions and matches the two retained REA bodies to the current export.
This does not certify native allocation, helper exceptions, queue memory,
packet transmission, or live game compatibility. No game action is executed.
