# Deferred preservation, fresh admission and observer activation

Root cleared CPU 4 read-only replay after the touch final critic `755ee542`
finished its retained failed analyzer/archive work. The [complete original replay](original-preservation-r2.json)
passes 940 predicates in 20.018 seconds, with empty stderr. The saved
[independent replay](recheck_original_preservation.py) launches no native process
and writes only its stdout, redirected into this report directory.

All 224 original files, totaling 178,615,722 bytes, match the original critic's
frozen registry. The retained archive remains SHA-256
`0f3717340bebc35313e89da57c805c016b1a4b7f8a5a45b8eb565f39d7450a6a`.
Its 231 regular, unique, closed-set members were reopened and checked against
the original raw/outer/frozen-source bytes. Both official archives match the
original identities and frozen SHA-512 pins; selected ZIP members and the three
excluded official template copies match. All 224 raw files and three outer
records were rehashed again afterward. Original R1 remains FAILED.

The first [fresh admission](source-admission-reread-1.json), observed at
11:19:59.073612 UTC, again passes 1,798 source/preservation/freshness predicates.
After root provided its actual release reference, the second
[fresh admission](source-admission-reread-2.json) also passes. Both stderr files
are empty. Exact candidate `216d39ada8f9d11e2d8544d01fde42da49607b14` and original
source remain clean; all 430 tracked game/script files in each match frozen
Git bytes. Fresh R2 output/claim and external outer records remain absent at
these finite observations. The source checker does not read release documents;
its hard-coded `root_release_observed:false` describes that checker's scope.

Actual ROOT ONE release is
`90a9cab61a554672306d5a630e15e25ea93c8dd0`. The
[release readback](root-release-readback.md) matches that exact Git blob and
root's materialized release file. The separate [activation admission](activation-admission.json)
binds this release, exact source and unchanged observer SHA-256
`dc3a98af675520e8e6d92f2de2c6de87cd1c177aa30eeb473c0b8980f2e95342`.
Root's release conditions preserve all original bounds and prohibit fallback,
retry, extra probes or source changes.

The unchanged read-only observer started after that release and before R2 output
creation at 11:21:04.888317 UTC, monotonic 26841.660069248. Its retained start row
is in `live-observer.jsonl`: PID 159705, start ticks 2684156, PGID/SID 159705,
actual process/thread affinity `[4]`, identity revalidated, fixed display socket
and lock absent. Initial tool session is 47432. Root was sent that exact row and
must inspect it before launching the sole wrapper within the observer's original
60-second discovery bound. This reviewer has launched no acquisition or native
process. The observer alone is active at this checkpoint; its eventual terminal
receipt and original timeline must be retained before actual cleanup is judged.

This increment verifies original-byte preservation and activation readiness.
Corrected-fixture actual compilation/import, export, all four conditions and H1
remain unobserved here. Original gameplay failures remain FAILED.
