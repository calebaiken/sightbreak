# R4B R2 released native attempt: failed candidate import

The single authorized attempt **FAILED during candidate import**. Godot 4.7.2
could not infer the type of `compact` at
`res://scripts/ui/touch_controls.gd:214`. Import exited 0, but the unchanged
controller caught three script/compile/load errors and stopped with exit 1.
No background, control capture, regression or analyzer producer ran. There are
zero PNGs and no new contrast, ownership, input or visual results.

Exact candidate/method: `b001fc5087960729535f63c896b40d6dc25bd272`;
baseline: `a52022169241df9ff662039547a375e1c46ac1c5`;
recipe: `2ecc3083c149cfcbb035d113fbc1a4b40a10f27b`;
independent source acceptance: `abb837b4`;
independent admission/preregistration: `9b8424a`;
explicit root release: `ea4db3b`.
The actual release and preregistration are retained in this report and the raw
archive. Prior source acceptance did not certify native compilation.
R3 FAIL, R4 NO GO and the rejected R4B receipt method remain unchanged.

Admission passed at **2026-10-23T08:40:32.995347+00:00**, after the committed
08:39:24Z release. Source/UID fences matched all 22 frozen files and both
327-path prepared projects before native work. Engine binary/archive/member
hashes matched the pinned Godot 4.7.2 toolchain; actual version was
`4.7.2.stable.official.ed1daf0bf`. Commands retained taskset CPU 0–3, two thread
selectors, fresh per-producer private userdata and display selector :131.
The actual cgroup limits were `400000 100000` and `17179869184` bytes.

| Original producer | PID / launch PGID | Exit | Actual wait | Result |
| --- | --- | --- | --- | --- |
| Engine version | 96995 | 0 | 0.065499 s | Expected version |
| Baseline import | 96998 | 0 | 6.567399 s | No caught engine errors |
| Candidate import | 97238 | 0 | 6.388473 s | Three caught errors; controller STOP |

The original 30/300/600-second caps were unchanged. No timeout, retry, cap
extension, later manual producer or source repair occurred. The controller
finished at **08:41:14.919600+00:00**; its exit-1 receipt was recorded at
08:41:14.960559+00:00. No renderer identity can be reported because Xvfb and
the render producers never started. The 3,330-second sum of engine wait caps
does not establish a whole-operation bound; analyzer, final wait and archive
remain without a hard whole-operation timeout.

The preserved source line is:

```gdscript
var compact := key != "fire" and r < 32.0
```

[Candidate import log](import-candidate.log) and
[source witness](compile-failure-source-witness.json) retain the exact failure
and original bytes. No type correction has been made in this attempt.

[Post-source checks](post-source.json), exit 1, retain the absent background
freeze, zero/zero/zero expected image shortfalls and incomplete acquisition.
They report no source/hash/UID changes. Post-archive checks again matched all
22 frozen files and both 327-path stages. Imported caches remain separate from
the unchanged original source paths. Exact staged GDScript, copied UID,
project/fixture and frozen method bytes are preserved in the raw source
snapshot; existing art assets were not duplicated.

[Recursive strict-log review](strict-log-review-complete.json) scanned all six
original logs, including private userdata logs. It retained the candidate
parse/compile/load failures and found no orphan/unclaimed StringName or
resource-leak lines. Strict log cleanliness is false. An exit-zero import
cannot override those errors.

[Terminal cleanup](terminal-pgid-display.json) at 08:42:32.924662+00:00 found
no current members in any owned group, no leader or controller process and no
:131 socket/lock. The final post-archive scan at 08:45:51.858549+00:00 again
found no members of groups 96995, 96998 or 97238 and both display paths absent.
The launch PGIDs derive from the unchanged `start_new_session=True` behavior
and actual recorded child PIDs. This short attempt ended before a live
`getpgid` observation was captured; that observation limit is explicit rather
than invented. No cleanup signal or display-lock deletion was needed.

The original raw root is
`/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2`; its contents
were frozen before packaging and remain untouched. Packaging exited 0 at
08:44:36.874327+00:00 and preserved the explicit failed acquisition status.
[Payload manifest](payload-manifest.json) covers **628 files / 10,619,634
bytes / zero PNGs**. The archive has 629 unique members including the embedded
manifest, **3,662,336 bytes** and one part below 24 MiB. Full and ordered-part
SHA-256:

`9e5cfa76aaffc0b4c41b9bbead37c2e872c983545eff24117a99118e890d46e6`

[Archive receipt](ARCHIVE.json) and
[post-archive verification](ARCHIVE_VERIFICATION.json) retain part hashes,
exact raw path/size/hash equality, embedded manifest identity and every archive
member. The complete archive remains at
`/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2.tar.xz`.
Packaging stdout/exit are outside the frozen raw payload and copied here.

Root's fresh actual critic must audit this failed attempt before any next
source correction or lane release. Missing captures cannot support a blind
image comparison or numeric approval. The immediate blocker is candidate
compilation; any correction requires a separate preregistration, source freeze,
fresh prepared stages and review. No runtime retry is authorized by this report.
Live HUD, physical touch/reach, custom layouts, accessibility, shipped-title
parity and release acceptance remain open. CS2 reference-host restrictions
remain explicit; no parity claim follows from this bounded failed acquisition.
