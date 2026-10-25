# Owned coordinate getter continuation frames

CurrentAxisFrame and CurrentCoordinatesFrame advance one captured invocation.
They expose an explicit needed field path and freeze only reached raw values or
true normal-return receipts. Nested root/float samples are retained field by
field: a captured protection result does not freeze a value that has not yet
been read. Protection failure skips its unused raw value, while helper parent
return still needs an explicit receipt. Address mismatches are rejected before
mutating that cached field. False/absent receipts remain pending.

The pair advances X before Y. Completed X is terminal and cannot be replaced by
later captures while Y waits. Y data supplied before reaching Y is not cached.
An axis waiting for its parent return retains its own completed root/float/EAX.
Both complete before formatted parameters are published; a pending Y exposes
only the completed X prefix for inspection. A new invocation needs a new frame.

These are own captured-data continuation policies. Steps describe the canonical
source call path and are not executable native API requests. No native helper,
VirtualProtect, game memory access, FPU context acquisition or automatic provider
is implemented. Source click/list setter and actual coordinate button binding
remain open; this stage does not make current game coordinates available.

Eight new tests cover nested demand freezing, fresh offset/EAX, false receipts,
axis parent gaps, terminal X/pair behavior, unreached Y and wrong-address cache
isolation. CURRENT_COORDINATE_FRAMES_VALIDATION.json records4545 Python tests.
No new GUI run:327-module app/smoke_ui closure and prior full GUI log hashes are
unchanged from4529.383 retained source/CRT instruction records were rechecked;
no new REA decompile or native/live equivalence is claimed.
