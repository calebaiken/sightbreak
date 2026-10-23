# Independent actual acquisition verdict

FAILED at exact `f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9`. The single actual
import exits 0 but the pinned Godot compiler rejects the frozen diagnostic
fixture. The supervisor correctly stops at `Strict native log gate: 06-import`
and exits 1. No export, Xvfb or OFF/ON condition runs. H1 has no data.

The largest remaining deficiency is the fixture's actual GDScript parse failure.
The earlier source/pure ACCEPT `26095386` did not establish compilation and is
not relabeled as actual acceptance. Original Linux gameplay failures remain
failed. No retry or engine operation was performed by this reviewer.

## Actual failure and prior registration

Reviewer preregistration `4e97721be122bf3bd9db4937e153576f30aa40af` was pushed
before root release `e587392d` and this acquisition. I first inspected actual
output only after root reported terminal exit 1 and explicitly released the CPU
lane. The previous source rejections `ff4cc71` and `c339065` remain retained in
the original source package. Repository instructions and the original quality
skills apply. The identified logs prevent a blind OFF/ON comparison; no invented
score or comparative winner is assigned.

The [complete original import stderr](original-logs/06-import.stderr.log) is
404 bytes, SHA-256
`905897b593b3f4061a9adf7f095d6a55749ccca2fd1cf7a796cf3a47b6db6274`:

```text
Unable to open Android 'build-tools' directory.
SCRIPT ERROR: Parse Error: Cannot infer the type of "keys" variable because the value doesn't have a set type.
          at: GDScript::reload (res://diagnostics/linux_profile_overhead.gd:107)
ERROR: Failed to load script "res://diagnostics/linux_profile_overhead.gd" with error "Parse error".
   at: load (modules/gdscript/gdscript_resource_format.cpp:46)
```

The retained [stdout](original-logs/06-import.stdout.log), 10,492 bytes, includes
the original engine/import progress through editor layout loading. Exit 0 and
those progress lines do not override the two explicit compiler/load failures.
The staged fixture is byte identical to frozen source, SHA-256
`1e3f4094f2439a7ae054455c5f7e2ca4a993a15067affebce57e760569ee1dae`.
[Frozen line 107](https://github.com/calebaiken/sightbreak/blob/f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9/scripts/diagnostics/linux_profile_overhead.gd#L107)
is `var keys := value.keys()`. This is direct compiler evidence about the
diagnostic fixture; it identifies no gameplay or rendering-cost cause. The
separate Android directory diagnostic is preserved verbatim. It has no
registered error/warning prefix and is not assigned as the cause of the parse
failure.

The [root-retained outer receipt](original-logs/outer-tool-receipt.json) binds
the exact command, cwd, source and exec session 55816 to terminal exit 1. Its
terminal response was transcribed by root after context recovery; this is
reported explicitly in that original receipt. Wrapper stdout agrees with the
failed overall receipt; wrapper stderr is empty. Terminal observation was
09:28:33 UTC. The polling response's wall time is not whole wrapper runtime.

## Verified preparation and stop boundary

The [independent auditor](verify_actual.py) imports no builder module and invokes
only read-only Git commands, hashes, archive reads/writes and `/proc` observations.
It completes in 12.663 seconds with [1,695 passing integrity predicates](audit-results.json).
That auditor exit 0 verifies the recorded FAILED acquisition. It is not a native
pass. [Original auditor output](audit.stdout.txt) and empty [stderr](audit.stderr.txt)
are retained.

| Actual phase | Recorded elapsed seconds | Original cap | Verdict |
| --- | ---: | ---: | --- |
| Admission/preflight | 9.964004 | 60 | PASS, bounded preparation scope |
| Stage and explicit packaging amendment | 0.425972 | 45 | PASS, bounded staging scope |
| Engine version | 0.117310 | 15 | PASS, exact pinned version |
| Import | 8.602531 | 120 | FAIL, strict compiler/load errors |

The original monotonic whole deadline remains start + 1320 seconds. Each reached
phase finishes before its original phase/whole deadline. The last budget
observation is 19.109790 seconds at `06-import:logs hashed`; it precedes the
failed-stage inventory and failure publication. No exact whole-return or
failure-publication elapsed time is retained, so neither is inferred from the
last observation or the outer polling response. The failure is a strict-log
rejection, with no recorded timeout or late success.

Exactly six owned commands occur: three Git reads, original stage, one engine
version query and one headless editor import. Both engine commands request
`taskset -c 0,1`; the import argv is exactly the registered
`--headless --editor --path PROJECT --import --quit`. No manual continuation or
second engine import appears. Original successful phase files contain the
documented pre-return `passed:false` snapshot; the overall phase records carry
the later three true values. This is the frozen publication contract, not a
second failed attempt.

Import-inventory, export, artifact, seal, block and finalize are unreached.
Their commands, phase receipts, exported executable, embedded PCK, payload
inspection, seal, native-block directory and normal output manifest are absent.
The normal final source/host observations and publication-source boundary are
also absent. All four strict 180-second native-condition gates remain
unexecuted. There are zero actual condition receipts, cadence samples, proof
images or emitted profiler blocks. ELF/PCK/resource MD5/ECFG/filtered UID gates,
same-payload validation, render/pixel/scene fingerprints, frame clocks and H1
are UNREACHED, never passing or failing by proxy.

## Source, amendment, tools and ownership

The actual attempt claim names the exact frozen source. All 430 tracked
game/script files, including 136 UIDs, match the original preflight manifest,
frozen Git blobs and the independent finite post-failure read. The source
checkout remains clean at `f242a2f`; game tree remains
`55691684d31d44f1680141954bbe530443de9d1f`. Accepted controller/fixture/scene/tests
remain equal to `3fd9718`. This later observation has its own recorded monotonic
interval; it does not manufacture the wrapper's unreached final-source gate or
claim perpetual immutability.

The original stock game's 128 non-test paths bind the source ledger. The stage
contains exactly 131 declared files. Independent reconstruction from frozen
stock bytes verifies the diagnostic main scene, safe thread selection,
profiling false, diagnostic JSON include filter and unchanged graphics. The
subsequent external amendment changes only the Linux text script mode from 2
to 0 and adds `editor/export/convert_text_resources_to_binary=false`. Original
before/after text and both stage records remain retained. Shipping files are
unchanged. No actual exported representation is qualified.

The failed-stage inventory matches all 194 actual staged files. Every one of
the 131 declared source files remains unchanged; the only additions are 62
root `.godot/` cache files and the declared fixture UID. The generated UID is
`uid://dm66yeunf5ph4`; its original 20-byte file and retained failure copy match.
All generated cache bytes are preserved. This independent post-failure equality
does not promote the skipped import-inventory phase or qualify cache semantics.

All 11 pinned tools rehash correctly. Both official archives independently
match the SHA-512 constants in the frozen toolchain. Their selected editor,
version, Linux debug and Linux release members match the installed bytes; the
three private copied template files match those members too. Actual version
stdout is `4.7.2.stable.official.ed1daf0bf`. The receipts retain the exact private
XDG/Android/Mesa/export paths, LP2, software-rendering selection and explicit
root-banner environment choice.

Host admission records allowed CPUs 0–4, nice 0, scheduler 0 and cgroup quota
`400000 100000`, with selected CPUs 0,1 and fixed display `:99127`. The import's
31 observed mapped-file hashes and supervisor's ten mapped-file hashes still
match. Taskset and LP2 are recorded selections; preparation does not retain
per-child actual affinity/environment readbacks. No Xvfb, runtime Mesa renderer,
per-condition CPU/library evidence or end-host/quota observation exists.
Nothing here qualifies comparable native conditions or absence of shared-host
interference.

All six roots exit naturally with code 0. Their receipts retain exact PID/start
identities, original group/session and observed identities; none records a
signal or forced cleanup. Each root is reaped, terminal original group/session
and observed identities are empty, and recorded cleanup is below five seconds.
A later independent `/proc` snapshot confirms those exact identities/groups/
sessions and the supervisor identity absent. No recognized native process name
or fixed display socket/lock remains at that observation. The declared polling
scope excludes an unobserved escaped/reparented descendant; complete arbitrary
descendant cleanup is not claimed.

## Original bytes and strict review

[All twelve original command streams](original-logs/) were scanned, including
empty stderr files and zero-exit commands. Only the import stderr has strict
failures: the two quoted parse/load lines. The independent scanner explicitly
adds standalone `Orphan StringName` and positive `unclaimed string names` counts
omitted by the frozen acquisition matcher. Focused scanner controls reject
those positive forms and accept a zero count/clean engine line. No additional
StringName forms occur in the actual logs. These controls are synthetic scanner
checks, not native evidence or evidence about earlier audio leak causes.

The [complete raw registry](raw-registry.json) binds all 224 original attempt
files, 178,615,722 bytes, plus the three external outer records. Every one of the
148 first-validated evidence identities remains equal; failure-generated files
are separately bound without replacing those identities. The failed attempt
did not create the normal closed success registry or manifest.

[Retained original evidence](retained-actual.tar.gz) is 19,739,886 bytes, SHA-256
`0f3717340bebc35313e89da57c805c016b1a4b7f8a5a45b8eb565f39d7450a6a`.
Its [231-member index](archive-members.json) contains all 221 attempt files
apart from the three independently verified official template copies, the
original outer receipt/streams and seven exact frozen source files. All members
were independently reopened and rehashed; the original raw root and outer
records were rehashed afterward and remain unchanged. The three excluded
official copies total 147,223,229 bytes and retain exact identities and archive
member verification. No original generated cache/source/UID/log/receipt bytes
were deleted or changed.

No OFF/ON comparison can be computed. This attempt supplies no profiler-cost,
physical FPS, shipping performance, gameplay-cause or optimization result. The
next component is a separately registered source correction and fresh review
of the actual fixture parse boundary; this report authorizes no new acquisition.
