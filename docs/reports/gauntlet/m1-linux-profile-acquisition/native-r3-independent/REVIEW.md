# Independent actual R3 verdict

FAILED at exact source `ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef`. The single
supervisor exits 1 with `Command exit/timeout: 15-accepted-block`. Its first OFF
client exits 2 before readiness. Original client and private Godot logs contain
both the strict V-Sync warning and
`ERROR: LINUX_PROFILE_OVERHEAD Pinned synchronous safe render-thread argument required`.
There is no cold anchor, warm/measured sample, proof PNG or H1 result. ON2,
ON3, OFF4, comparison and finalization are unreached.

The largest remaining deficiency is the mismatch between the fixture's runtime
argument guard and its recorded complete process argv, followed by the separate
strict V-Sync warning. Launch and independent live argv contain `--render-thread
safe` before `--`; frozen `_run` lines 267–270 search `OS.get_cmdline_args()`
and reject. That returned array and actual thread/V-Sync getter values were not
retained. These bytes establish the failure boundary, not a consumed-option
cause, renderer-thread state or an approved correction. No retry or continuation
is released here. Original R1/R2 and Linux gameplay failures remain FAILED.

## Admission, sole attempt and actual stop

Actual preregistration `fd378ab0` and conditional admission `39674b4f` preceded
source acceptance `12b88814` and root ONE release
`801e4514ab869ad6869e5631dc303f58ca28772f`. Fresh admission rechecks all 3,975
source/preservation/freshness predicates. The prescribed non-symlink `.local`
directory was present before observer activation and wrapper redirection.
The corrected release prose time is preserved by root; it grants one permission.

The CPU 4 observer starts 11:49:57.726604 UTC. Root reads its original start row
at chunk `75b5c2` before the sole invocation, prelaunch tool clock 11:50:35 UTC,
initial session 86980/chunk `308db7`. Exact supervisor PID/start
168507/2861205 is independently discovered 37.716363 seconds after observer
start, within 60 seconds. Actual terminal response is exit 1/chunk `f1d054`,
observed by root's clock at 11:51:07 UTC. Original [outer receipt](failure-input/outer-outer-tool-receipt.json)
and copied [failure packet](INITIAL_FAILURE.md) preserve these records. Unlike
R2, no shell setup failure occurred in R3. Tool polling duration is not runtime.

The independently checked reached phases are:

| Phase | Seconds | Original cap | Actual scoped result |
| --- | ---: | ---: | --- |
| Preflight | 9.942262 | 60 | PASS preparation |
| Stage | 0.371656 | 45 | PASS exact overlay/amendment |
| Version | 0.151588 | 15 | PASS recorded pinned version |
| Import | 7.050584 | 120 | PASS compiler/import exit and strict logs |
| Import inventory | 0.348356 | 30 | PASS source/UID inventory |
| Export | 3.827352 | 120 | PASS registered export exit and strict logs |
| Artifact | 0.941354 | 60 | PASS bounded actual ELF/PCK/resource gate |
| Seal | 0.329198 | 30 | PASS bounded source/stage/payload seal |
| Block | 1.467634 | 750 | FAIL first OFF readiness |

All reached phases end strictly before their original phase and 1,320-second
whole deadlines. Successful phase files retain the frozen pre-return
`passed:false` snapshot; overall contains the later true results. First OFF
retains its original 180-second deadline and rejects after 1.008370 seconds.
Xvfb ownership readiness completes in 0.050886 seconds under its five-second cap.

The last original budget observation is `15-accepted-block:logs hashed`,
24.429974 seconds after start. The observer sees supervisor absence by
24.569872 seconds after that start, 0.139813 seconds after block-phase end.
This bounds failure preservation/return below the original whole and ten-second
failure-publication caps. Exact publication start/end and process return instant
were not retained. Five-second cleanup never extends acceptance. Final source,
host, closed output-manifest and normal success-publication gates are unreached.

## Independent artifact, source and strict-log checks

The [payload auditor](verify_payload.py) imports no builder module and runs no
engine. Its [original output](payload-audit.stdout) passes 5,811 predicates with
empty stderr. Independent reconstruction exactly matches the complete original
`independent-payload.json`, retained PCK and seal: x86_64 little-endian ELF,
pinned debug-template prefix outside the single PCK section fixup, embedded
format 4 header/flags/reserved fields/trailer, bounds/nonoverlap, safe unique
closed set of all 94 resources and every resource MD5/SHA-256. MD5 checks resource
integrity; exact source/template/stage/ledger comparisons provide the remaining
binding. MD5 alone is not an authenticity guarantee.

Every packed script/scene/resource, remap, selected cache and ledger matches
frozen staged bytes. Actual packed import metadata has exactly the registered
single NUL after LF; staged metadata has none. Strict UTF-8/control/duplicate/
finite-value checks and exact remap/source/cache equality pass. The independent
decoder verifies all critical ECFG values and feature selectors, diagnostic main
scene, 1280x720, Compatibility, 2x MSAA, safe project thread value, profile false
and text-resource conversion false; it verifies filtered 62 UID and 38 class
entries and exact fixture/scene/ledger pins. This reached preparation does not
prove runtime thread/settings/fingerprint or overhead comparability.

The exported ELF is 84,426,016 bytes, SHA-256
`a4c655dcd132fd02d0af29a50242aa2fcc62a31ebe9daedabe5feb2870ed7f0b`.
The retained embedded PCK is 10,722,204 bytes, SHA-256
`31cf317e5d5c87df8e3a9e2c57f11d936b0bd078c8bc108593325585d4d1449b`.

The [full actual auditor](verify_actual.py) completes in 20.127 seconds with
[2,311 passing integrity predicates](audit-results.json) and empty
[stderr](audit-initial.stderr). [Original stdout](audit-initial.stdout) verifies
this FAILED acquisition. All 431 tracked game/script files and 136 UIDs match
frozen Git and the original preflight ledger at a finite independent post-failure
read. Candidate HEAD remains exact and clean; shipping game tree remains
`55691684d31d44f1680141954bbe530443de9d1f`. That later read cannot replace the
unreached final-source publication gate or prove perpetual immutability.

Exact overlays and the two external text-packaging amendments remain as
registered. Both source-stage records have 131 paths, including 128 stock paths;
complete import/export/terminal stage inventories have 194 paths. Only 62 root
cache files and one fixture UID are generated. Import/export legitimately changes
`.godot/editor/filesystem_cache10`, from SHA-256
`52c0147189099b02af9050ca68b830775c5f0486c7d03eb2897109d5e27a9cb0`
to `38b59451a98f19c7952ca59ad91cc2e471fb14f2ae0718e690bc97a33bd082b5`.
Only terminal bytes remain. Earlier import inventory is historical hash evidence;
historical cache-byte readback remains UNVERIFIED, as in R2.

All 11 tools, official editor/template archive SHA-512 pins, selected ZIP members
and installed/private template copies rehash correctly. Version stdout is exactly
`4.7.2.stable.official.ed1daf0bf`. Preparation libraries, private XDG/Android/Mesa
paths, LP2, original caps, controller/fixture/scene and selectors remain exact.

All 33 original `.log` streams were independently scanned, including 30 separate
command stdout/stderr files and empty streams. Import/export stderr each retain
the same 48-byte unprefixed Android build-tools diagnostic. Exactly two logs,
the client and its private Godot log, each contain the V-Sync warning and argument
error. Standalone orphan StringName and positive unclaimed-string-name scanner
controls reject, while zero/clean controls pass. No profile block is emitted.
Strict failure remains independent of wrapper exit and readiness failure.

## Actual runtime ownership and observation limits

The first OFF uses the exact sealed payload, original full argv, CPUs 0,1,
display `:99127`, LP2 and fresh empty per-condition cache roots. The observer
corroborates actual process/thread affinity, selected environment and full argv
for the client and actual Xvfb. Client log identifies Compatibility, Mesa 25.0.7
and llvmpipe LLVM 19.1.7. Readiness-dependent runtime driver-library, quota/
throttling, thread/settings, fingerprints, work counters and frame-clock records
are absent. Those comparability gates stay unverified, not inferred from startup
text or project defaults. All fixed sample/formula/drift thresholds remain exact
and unexecuted; there is no H1, profiler-cost or gameplay-cause conclusion.

All 15 wrapper command roots exit naturally and reaped, with no wrapper signals,
no forced outer cleanup and empty recorded original groups/sessions/observed
identities under five seconds. The first fixture exits naturally with code 2
and `forced:false`. The intentionally still-live owned Xvfb is terminated by the
controller and records `forced:true`; this is preserved rather than described
as natural exit. No forced descendant cleanup after a naturally exited client
root is recorded. Exact signal escalation/individual Xvfb teardown duration is
not separately retained.

[Independent live-boundary replay](live-boundaries-readback.json) passes 23
predicates. Its seven Xvfb socket samples join the original owned kernel socket
inode to an FD of the exact live Xvfb and the fixed display publication. Terminal
listeners match the pre-acquisition baseline; display socket/lock are absent.
All nine observed exact identities, observed original groups/sessions and the
supervisor's original PGID/SID 168505 membership are absent at the ten-second
terminal row, 11:51:09.952576 UTC. Later independent `/proc` reads also find all
15 wrapper roots, client, Xvfb and original supervisor group/session absent.

All nine short Git roots escape live polling. The short version root is observed
by identity but its detail read races exit; no successful independent live
version argv/affinity/environment readback exists. Other detail reads can also
race exits. The 477 nominal 100 ms polls over 72.298128 seconds establish finite
observations of nine identities, not an arbitrary escaped/reparented-descendant
guarantee. Observer exit 0 is observation completion only.

## Complete retained originals and next boundary

[The complete raw registry](raw-registry.json) binds all 370 original files,
276,747,038 bytes, and the three external wrapper/outer records. All 203
first-validated identities and the early 370-file registry remain unchanged.
Zero ready/metrics/condition/proof files exist. The initial failure packet is
retained at `05881df9`/`587b0c74`; original inspection and ignored-log packaging
mistakes are documented in [the setup note](AUDITOR-SETUP-NOTE.md).

[The complete original archive](retained-actual.tar.gz) is 58,661,240 bytes,
SHA-256 `b3868bc6659e22cdf03ef2111c60e9e5d2c290552bc51ecddda57dcda19d0025`.
All [377 unique regular members](archive-members.json) were reopened and rehashed,
then every original raw/outer file was rehashed again. It includes actual
ELF/PCK, all available staged/cache/UID/native-state/log/receipt bytes, outer
records and seven frozen source files. Only three separately verified official
private template copies are excluded, with exact archive/member bindings.
No actual artifact, state cache or proof file is silently omitted.

Separate post-R3 [R1 preservation](r1-preservation-after-r3.json) passes 940
predicates across all 224 raw files and 231 archive members. [R2 preservation](r2-preservation-after-r3.json)
passes 1,032 predicates across all 247 raw files and 254 archive members. Both
reopen all outer records, official archives/members, exclusions and frozen source
members, then rehash originals again. [Original source readback](original-sources-after-r3.json)
passes 2,585 predicates for both 430-file source/UID/mode inventories and clean
exact HEADs. Old archive hashes remain unchanged. Original failures, overwritten
historical cache versions and missed live-process limits remain preserved.

The next component is a separately preregistered source correction using these
actual argument/readiness and strict-warning bytes plus pinned engine evidence.
It requires fresh source review and a separate actual release before any native
work. This report accepts no physical FPS, stock shipping performance, complete
profiling cost, optimization, gameplay result or whole release gate.
