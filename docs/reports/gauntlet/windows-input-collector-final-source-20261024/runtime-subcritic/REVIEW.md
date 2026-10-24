# Independent narrow runtime source critic

Target: `c32415148db1f110bbc7eadfca3793d4693429ff`.
Root: `11c5773eff6888c5157784c272aca144614338d4`.

No concrete source defect found in the four runtime diffs. This is a narrow static finding for the parent review, not approval of builder evidence or a native/runtime qualification.

## Source findings

- All four files recover their exact root bytes after removal of marked additive observation blocks/hooks. `source-controls-first-run.txt` retains SHA-256 equality for each file. The independent controls reject an altered protected tick initializer, a removed release guard, and replacement of the applied-snapshot actor traversal guard.
- `game/scripts/gameplay/match.gd:1233` requires a debug build, explicit user flag, guest/account-free settings, and an exact loopback address. Offline and normal dedicated modes are denied; the server additionally needs a boolean fixture marker. The real dedicated startup in `game/scripts/main.gd:114` supplies no marker. `scripts/fixtures/export_integration.gd:57` enables the special server path only for the flag, while the debug gate still applies.
- The empty default state returns before time, Input, controller or gameplay reads (`match.gd:1267`). Added hooks do not choose inputs, update actors, invoke prediction, change stream admission, change authority/economy/physics/RNG, or publish new network data. The observer writes only its own diagnostic dictionary; its merge target is a newly projected controls dictionary (`match.gd:1278`). Byte erasure also confirms the runner schedules, deadlines, gates and existing OS-input implementation remain byte-identical to root outside the additive flag/result/command blocks.
- Snapshot rejection and welcome observation read only integer-guarded tick/epoch fields (`match.gd:1281`). They never traverse malformed actors. Actor traversal occurs only for `snapshot_applied`, after the existing schema check (`match.gd:1164` and `match.gd:1283`). The schema bounds actors to ten dictionaries, requires integer IDs and validates optional integer acknowledgments (`game/scripts/network/snapshot_schema.gd:11`, `:36`, `:52`). This is source reasoning, not a malformed-payload runtime test.
- Packet projection examines at most `SBInputStream.MAX_BATCH` (12), copies scalar summaries, and ignores arbitrary packet/command fields (`match.gd:1243`, `:1249`). Observations do not retain source packet dictionaries. Snapshot projection keeps its header and the local actor acknowledgment, while client actor telemetry uses `local_actor()` (`match.gd:1285`, `:1304`); it omits aim, names, account data, reconnect credentials, arbitrary snapshot bodies and other actors' private state. The special authority fixture logs its selected guest actor locally. Output is stdout JSON, with no RPC or file writer added to the collector.
- Call sites use a finite set of literal reasons; each reason replaces its latest projection/edge. The recorder caps output at 1024 lines and returns immediately thereafter (`match.gd:1269`, `:1307`, `:1319`). Bounds apply per configuration, since reconfiguration resets the dictionary (`match.gd:1238`).

## Limits and largest gap

Enabled `_native_input_observe` was not executed. The added GDScript checks cover admission and pure projections, then call only the inactive recorder (`game/tests/movement_prediction_test.gd:76`). They cannot establish enabled-path API compatibility or error freedom. The enabled observer polls Input and serializes its edge on every hook before the emission throttle (`match.gd:1290` through `:1300`). No source control can establish its wall-clock interference, overhead, real OS delivery, rendered results or physical latency. This is the largest remaining gap. Capped/throttled observations also do not establish complete event coverage. No reader/analyzer acceptance follows.

No Godot/native program, compile/export/render/CI, real OS input, service/account/model/environment change, branch change, or source edit was performed. Reports were written only inside this report subdirectory.

## Procedure deviations retained

The first read-only discovery/instruction commands (`pwd`/`rg`/`cat`) and one `git status --short` plus `git diff --name-status` identity/path command omitted CPU affinity. This was reported to the parent immediately. All later review commands and the independent controls used `taskset -c 4`; the controls assert affinity `{4}`. This note does not retroactively claim full CPU4 compliance. Two early dependency reads used incorrect paths (`game/scripts/snapshot_schema.gd` and `game/scripts/input_stream.gd`) and returned Git path errors; corrected exact-target paths under `game/scripts/network/` were then read. No source control failed, and no usage-limit error occurred.
