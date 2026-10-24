# Independent actual R2 verdict

FAILED at exact source `216d39ada8f9d11e2d8544d01fde42da49607b14`. The single
actual supervisor exits 1 in the artifact phase with `JSONDecodeError: Extra data:
line 4 column 1 (char 26)`. Registered headless import and debug export return
zero with no strict log failure, but the payload inspector rejects the first
packed import remap. Seal, Xvfb, all four conditions, samples and H1 are UNREACHED.

The largest remaining deficiency is the inspector's handling of actual packed
remap text. The exact packed `assets/icon.svg.import` contains a final NUL byte.
The frozen section reader includes it in the last metadata JSON value. This
diagnoses the acquisition failure; it supplies no gameplay cause, profiler-cost,
optimization, physical FPS, shipping-performance or release-gate result.
Original Linux gameplay failures and original R1 import failure remain FAILED.
This review releases no retry, repair or manual continuation.

## Exact failure input

[Independent reconstruction](locate_payload_failure.py) imports no builder
module and executes no engine. It reads the actual embedded pack, verifies all
94 resource MD5s and records their offsets/SHA-256s in
[the readback](payload-failure-readback.json). The first staged `.import` parses;
its packed form fails at the final `remap/metadata` value:

```text
'{\n"vram_texture": false\n}\n\x00'
Extra data: line 4 column 1 (char 26)
```

The [exact packed input](failure-input/packed-assets-icon.svg.import) is 193
bytes, SHA-256 `e8717d3311cb7cd3fb716324b219d948e6f7d68fbae1b33d9163add59b4c2203`.
The [original staged input](failure-input/staged-assets-icon.svg.import) is
1,020 bytes, SHA-256 `9b48fb27282e20a5408a15c911b83134130c1fa359d172c35d02d46a7690d76f`.
It has no NUL. Removing only the packed input's last byte is a diagnostic positive
control; it is not an approved parser repair. The original bytes remain intact.

Frozen reader `scripts/linux_profile_payload.py:207–235` accumulates section
values, then calls strict JSON at line 217. `inspect()` first parses the staged
import at line 284 and then the packed bytes at line 287. The NUL-only line
joins the pending metadata value. The independently reproduced error matches
both the original failed artifact phase and outer wrapper stdout exactly.

The actual exported ELF is 84,426,000 bytes, SHA-256
`a6128f8ee82951c406d223fe3699c799df055f3cb92b224d2064504e3351f7c6`.
Its pack starts at byte 73,703,800 and is 10,722,188 bytes, SHA-256
`5a9f4147a9b9225b877739912b0af1bda00cb040e0e271c06a35e0915f5eb99a`.
Independent ELF/pack checks establish x86_64 little-endian headers, template
prefix equality outside the registered pack-section fixup, format-4 header,
resource bounds/nonoverlap, safe unique paths, all MD5s and staged text/cache
identities. They do not convert the failed complete semantic artifact gate into
a pass. Full remap/class/UID/ECFG acceptance and payload sealing were not reached.

## Actual admission, preparation and stop boundary

Preregistration `2082e964` and source/observer checkpoint `fee67503` were pushed
before ROOT ONE release `90a9cab61a554672306d5a630e15e25ea93c8dd0`. Complete original
preservation and fresh candidate/output admission preceded activation. The
unchanged observer started at 11:21:04.888317 UTC on CPU 4. Root verified its
retained start row before the one actual supervisor launch. Exact source acceptance
`f8659bba` remains a separate source verdict.

The original [outer receipt](original-logs/outer-tool-receipt.json) separately
preserves root's shell-redirection failure at 11:21:25 UTC: `.local` was absent,
so Bash returned 1 before starting Python or creating an attempt claim. Root
created the required directory, then launched the sole actual supervisor at
11:21:35 UTC, tool session 95035. Its original terminal response is exit 1,
chunk `04b86a`, observed at 11:23:26 UTC. The later poll observation is not whole
execution time. No native attempt, import/export or condition was repeated.

The registered phase results are:

| Phase | Elapsed seconds | Original cap | Actual result |
| --- | ---: | ---: | --- |
| Preflight | 7.723124 | 60 | PASS, scoped preparation |
| Stage/amendment | 0.327492 | 45 | PASS, scoped staging |
| Version | 0.135142 | 15 | PASS, pinned version readback |
| Import | 7.897394 | 120 | PASS, registered exit/log gate |
| Import inventory | 0.315681 | 30 | PASS, registered source/UID gate |
| Export | 4.016087 | 120 | PASS, registered exit/log gate |
| Artifact | 0.870518 | 60 | FAIL, packed metadata JSON |

All reached phases end strictly before their original phase/whole deadlines.
The 1,320-second whole deadline remains start + 1320. Normal successful phase
files retain the frozen pre-return `passed:false` snapshot; the overall receipt
contains the later true verdicts. No phase is inferred from a child exit alone.

The last stored budget observation is `source inventory`, 20.744016 seconds
after start; it precedes artifact failure/publication. Independent live polling
finds the exact supervisor absent by 21.436067 seconds after that start and
0.150593 seconds after the recorded failed-phase end. This bounds termination
and failure preservation below the original whole and ten-second failure
publication caps. It does not measure the exact publication start/end or return
instant. The five-second cleanup bound never extends acceptance.

## Source, staging, tools and strict logs

The [independent actual auditor](verify_actual.py), adapted from the original
independent critic's read-only auditor, imports no builder module. It completes
in 25.147 seconds with [2,436 passing integrity predicates](audit-results.json)
and empty [stderr](audit.stderr). Auditor exit 0 verifies this FAILED acquisition.
[Raw auditor output](audit.stdout) records the counts and archive identity.

All 430 tracked game/script files, including 136 UIDs, match the original
preflight inventory, exact frozen Git blobs and the independent post-failure
read. Candidate HEAD stays clean; shipping game tree remains
`55691684d31d44f1680141954bbe530443de9d1f`. Controller, scene and evaluator remain
equal to their accepted fixture base; the GDScript differs only by the reviewed
explicit Array declaration. The finite later read cannot replace the unreached
final source/publication-source gate or claim perpetual immutability.

Independent reconstruction verifies all 128 stock non-test paths, the diagnostic
main scene/safe-thread/profiling overlay, and the registered external text-script
packaging amendment. Both stage records contain exactly 131 declared source
files. Import, export and terminal inventories each contain 194 paths; all 131
source entries and generated fixture UID stay exact. The only generated paths
are the 62 root cache files and fixture UID. All three retained UID copies match
`uid://debn3akk42wyt`.

One earlier cache version is an evidence limit. Between import and export,
`.godot/editor/filesystem_cache10` changes from SHA-256 `b5d37799554cc64705360c9568c1ae120f8d442a3aea2d8ca128e2f930886f13`
to `d2071c2b26135cfc034c709acc882c12b2e040791d52d0fe1cd5b6137a4c9051`.
The original import inventory binds its earlier hash, but those earlier bytes
were overwritten and not separately retained. The archive includes all actual
terminal cache bytes. Independent historical byte readback for that earlier
cache version is UNVERIFIED; no inventory is rewritten or rebaselined.

All 11 pinned tools, both official archive SHA-512 pins and selected official
editor/template members rehash correctly. Installed/private template copies
match. Version stdout is exactly `4.7.2.stable.official.ed1daf0bf`. The actual
version/import/export argv retain taskset CPUs `0,1`; preparation retains LP2,
private XDG/Android/Mesa/export state and explicit root-banner suppression.
Source-pinned libraries still match. No Xvfb or runtime Mesa rendering occurred.

All [26 original command streams](original-logs/) were independently scanned,
including empty stderr and zero-exit commands. No registered strict error,
warning, parse/load, leak or StringName form occurs. Import and export stderr
each preserve the 48-byte `Unable to open Android 'build-tools' directory.`
diagnostic. It has no registered error/warning prefix and is not the artifact
JSON failure. Focused controls reject standalone `Orphan StringName`, positive
prefix/suffix `unclaimed string names` forms and accept zero counts/clean lines.
No profile block is emitted.

## Independent live ownership and its limits

The [unchanged observer timeline](live-observer.jsonl) contains 497 samples over
62.844 seconds. It discovers exact supervisor PID 159836/start ticks 2687284,
PGID/SID 159835 at 11:21:36.170565 UTC, 31.282248 seconds after observer start.
The fresh claim contains only the full candidate SHA plus newline. Actual import
and export identity, argv, CPU `[0,1]`, LP2 and software-render/cache environment
are independently observed. Their threads retain the selected affinity.

The 0.134-second version process and several short Git roots escape live polling.
Their recorded roots/logs/cleanup and later exact-identity absence are checked;
their live argv/affinity/environment cannot be independently reconstructed.
Some terminal per-process detail reads also lose races with exit. These gaps
remain explicit. Five exact identities were observed live; they do not describe
every child that existed or guarantee arbitrary escaped-descendant tracking.

All 13 command receipts record natural zero exits, no signals, reaped roots,
empty original groups/sessions/observed identities and cleanup below five
seconds. Later independent `/proc` reads confirm every declared exact identity
and original group/session absent. The observer sees the supervisor absent at
11:21:57.588948 UTC; its ten-second terminal check at 11:22:07.705032 UTC finds
all five observed identities, observed groups and sessions absent. Fixed display
socket/lock are absent and listener state matches the start observation.
Observer tool exit 0 establishes observation completion only. A later
[independent process readback](terminal-process-readback.json) also checks the
supervisor's original PGID/SID 159835 and all 13 command roots/groups/sessions;
all are absent at that finite observation.

## Complete retained bytes and next boundary

[The raw registry](raw-registry.json) binds all 247 actual files, 263,338,336 bytes,
and three external outer records. All 171 first-validated identities remain
equal. Failure-only files are separately bound. Normal closed success output
manifest, final source/host observations, payload seal, block receipt and all
conditions are absent. There are zero actual cadence samples, proof PNGs or H1
ratios. Every registered formula/drift/threshold remains unchanged and unexecuted.

[The complete retained archive](retained-actual.tar.gz) is 52,818,307 bytes,
SHA-256 `cd9bd47fea39a056bcf27e0b6f3950fab46a5418fb2c61d10005927c67ca154d`.
Its [254-member index](archive-members.json) includes the actual ELF, all available
generated cache/UID/stage/source/log/receipt bytes, original outer records and
seven frozen source files. Only three independently verified official private
template copies are excluded, retaining their exact archive/member bindings.
Every archived member was reopened and rehashed, then all original raw and outer
files were rehashed again without change. No original attempt byte was deleted
or edited. A separate [post-R2 preservation replay](original-preservation-after-r2.json)
again passes all 940 original R1 raw/archive/official-member predicates. The
[post-R2 original-source read](original-source-after-r2.json) independently
checks all 430 old source/UID files against their frozen Git and original ledger
with 861 predicates. Original R1 source, raw bytes and archive remain unchanged.

Two failed auditor assumptions remain in the [setup note](AUDITOR-SETUP-NOTE.md)
and original first/second outputs: full cache equality across export, then live
observation of the short version process. Their corrections preserve original
bytes and expose the limitations above; neither failed run is counted as passing.

The next component is a separately registered source correction for the packed
text boundary, followed by fresh exact-source review. This actual failure and
its archive remain frozen. No new native attempt follows from this verdict.
