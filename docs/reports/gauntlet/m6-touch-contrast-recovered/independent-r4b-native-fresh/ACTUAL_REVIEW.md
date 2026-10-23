# R4B R2 actual failed-attempt verdict

**ACQUISITION FAIL. Candidate native import readiness FAIL.** The candidate
cannot reach the registered render comparison. Its three recorded errors begin
with a GDScript type-inference failure for `compact` at touch_controls.gd:214,
followed by dependent main-script compile/load failures. Godot's import exit 0
does not override the errors; the unchanged controller correctly stops with
exit 1. No contrast, ownership, input-regression or visual winner is observed.

**Failed-attempt preservation ACCEPT.** Independent source/log/archive/process
audit passes. This accepts the retained evidence, not the candidate product.
The source admission `9b8424a` preceded runtime and remains an admission verdict,
not native compilation acceptance. Earlier R3 FAIL, R4 NO GO and R4B receipt
REJECT remain unchanged.

Reviewed pushed handoff `384d17d0b44c5e5c46178023e52009010bc280f7`, candidate/
method `b001fc5087960729535f63c896b40d6dc25bd272`, baseline
`a52022169241df9ff662039547a375e1c46ac1c5`, recipe `2ecc3083` and sole root
release `ea4db3b`. Original raw root:
`/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2`.

## Actual execution and failure

The retained root release at 08:39:24Z precedes admission at
08:40:32.995347+00:00. Original engine version is
`4.7.2.stable.official.ed1daf0bf`. The three ordered native invocations are:

| Producer | PID | Native exit | Wait seconds | Original log finding |
| --- | --- | --- | --- | --- |
| Engine version | 96995 | 0 | 0.065499 | Exact pinned version |
| Baseline import | 96998 | 0 | 6.567399 | No strict-scan error/warning/leak match |
| Candidate import | 97238 | 0 | 6.388473 | Parse error, dependent compile error, load error |

The candidate log's first error at line 259 names the exact original source:

```gdscript
var compact := key != "fire" and r < 32.0
```

The next two errors are at log lines 261 and 263. Candidate source SHA-256 is
`afa8fa5b311e20eca4f71fc8d3e46a5f7adb8fce65e0c5dfda4c53851c9219de`;
the staged file, Git source and archived snapshot agree. The failure is not
explained by altered source/UIDs or a different engine. Baseline import has no
recorded errors, but no broader baseline test is claimed.

Controller end is 08:41:14.919600+00:00, exit-1 receipt
08:41:14.960559+00:00. Original 30/300/600-second caps and controller bytes are
unchanged; these observed waits did not approach their caps. Receipts show one
ordered attempt with no retry, repair or later manual producer. Commands retain
CPU 0-3, thread selectors 2, :131 and distinct per-producer private XDG/state
paths. Wrapper admission records affinity 0-4 and the expected cgroup values;
the commands specify child affinity, but live child-affinity/PGID observations
were not captured. Binary SHA-256, archive SHA-512 and archive-member identity
independently match the pinned toolchain without executing it again.

Xvfb never started. Backgrounds, both controls runs, all four regressions and
the analyzer never ran. There are zero PNGs, no native renderer identity and no
pixel/replay/contour/font/affordance rows to judge. I did not run an analyzer on
missing images or create a blind packet. The required 5,648-image comparison,
608 candidate gates, 48 retained intermediate rows, complete ownership replay
and separate blind image review remain unobserved.

## Independent preservation and terminal checks

`actual_checks.py` completed in 3.88 seconds under root's pure-audit clearance.
It verified all 628 original payload paths, sizes and SHA-256 values, totaling
10,619,634 bytes. It independently read all 629 unique archive members, checked
the embedded manifest byte for byte, the single <=24 MiB committed part, its
ordered reassembly and the 3,662,336-byte full archive. Every hash agrees with:

`9e5cfa76aaffc0b4c41b9bbead37c2e872c983545eff24117a99118e890d46e6`

The manifest truthfully records `acquisition_complete: false` and the original
candidate-import error. Packaging exit 0 preserves that failure. Post-source
exit 1 retains five expected failures: absent background freeze, three image
count shortfalls and incomplete acquisition. No source mutation is concealed.

All 22 frozen files equal the accepted exact method Git bytes and current
hashes. Both stages retain all 327 source/fixture/UID paths, all 323 original
paths equal their original Git source, and each retains 138 unique UIDs. All
initial/import-before/import-after/post-source receipts reconcile. All 578
archived source-snapshot files also equal their declared originals and hashes.
The imported `.godot` caches do not change these original source/UID paths.

Independent recursive scanning of all six original `.log` files reproduces the
three candidate errors exactly, with no orphan/unclaimed StringName or leak
matches. There are no additional private-state `.log` files. Strict log
cleanliness is false because the candidate errors remain present.

Original cleanup receipts show all three leaders already exited normally and
no cleanup signals. The retained 08:42:32 and 08:45:51 terminal scans report no
members of expected PGIDs 96995, 96998 or 97238. My independent current `/proc`
scan reads every available PID stat, finds no members and no leaders, with no
unreadable PID records; :131 socket and lock are absent. PGIDs derive from
recorded PIDs and unchanged `start_new_session=True`, not a live launch
`getpgid` observation. This supports terminal absence with that disclosed
observation limit. The audit leaves all original raw files unchanged.

## Next isolated component and unchanged limits

The biggest immediate deficiency is native compilation. The log and preserved
source support a narrow next hypothesis: declare `compact` explicitly as bool
while preserving the expression. Do not describe that annotation as a verified
fix before the pinned engine observes it. A new source preregistration, freeze,
fresh stages, independent review and separate root runtime release are required;
this failed directory must remain immutable. No code was patched in this audit.

The retained analyzer/final-wait/archive lack of a whole-operation timeout and
leader-only controller cleanup limits remain documented. The final-contour
identifiability falsifiers and dark-surround, heavy-plate, glyph-collision,
truthful-ownership and scene-occlusion questions remain unresolved because no
image exists. Live HUD, dynamic joystick/custom layouts, physical touch/reach,
human play, complete accessibility and RC acceptance remain open. Recorded CS2
reference-host restrictions still block shipped-game comparison. No subjective
score or visual preference can be inferred from this failed import.

Read-only reproduction:

```sh
python3 docs/reports/gauntlet/m6-touch-contrast-recovered/independent-r4b-native-fresh/actual_checks.py
```

Complete independent observations are in `actual-checks.json`. Only this review
directory changed; no engine, import, render, OCR, UID generation, CI, service,
analyzer replay, source correction or nested agent ran during the audit.
