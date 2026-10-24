# Versioned client clock correction, before rerun

The v1 independent emitter starts server monotonic time12000 and wall-clock
112000. Its schema client helper still has welcome wall104000, before the
source-generated binding112003. Complete role traces validate, then the final
cross-role welcome/binding check rejects12 intended positives. This is a rig
clock mismatch, not a candidate defect. All26 v1 input/result artifacts and the
exact v1 runner remain unchanged. The14 matching outcomes include negatives and
UNKNOWN controls; they do not validate the malformed cross-role positive pair.

Minimum v2 correction: add9000 to every synthetic client's wall_unix_msec.
Its welcome becomes113000, after the initial binding112003 and before the
first disconnect/expiry in these traces. Keep all client monotonic/cache/latest
ages and authority inputs unchanged; no product expectation or analyzer guard
changes. Apply this consistently to every26-case pair before rerunning in a
fresh own-causal-v2 directory. This represents an independent process's wall
clock; no physical latency is inferred. The original v1 bytes stay historical.
