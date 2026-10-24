# Additive root binding and reaping obligations before edits

Existing independent critic confirms missing child-list interface can masquerade
as empty and requires explicit direct Popen root binding plus known root reaping.
Record this additive scope before changing those paths. Original source550 and
failed attempt remain untouched; no new native/retry is authorized.

After immediate pipe retention, bind the known Popen PID by direct current PID/
birth/parent readback, pidfd and second identical birth/parent check. Parent must
be this supervisor. Keep subsequent existing descendant discovery, session,
executable and affinity checks. Direct root binding never replaces required
child-list capability or allows unavailable discovery to pass.

Cleanup must separately account for the known Popen root: observe/poll and wait
its terminal status even if discovery is empty. A still-running known Popen root
cannot disappear from accounting; safety-kill through the owned Popen handle/API
if unavailable to the tree, retain that forced-cleanup signal, and fail acceptance.
No known root birth means no whole cleanup pass. Unknown descendant state remains
failure. Pure tests add live root+emptydiscovery, exited root+explicitreaping,
wrongparent/birth races, and retained intended PID on early readback failure.
