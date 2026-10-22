# Independent archive integrity confirmation

The critic task `/root/authority_order_critic` independently verified the evidence copied by builder commit `640e4852acd92a8143ee528c151757d0d4b61ec2` against the original files in `/workspace/reviews/authority-order-critic`. **All 94 archive members and all 12 surface copies match byte for byte.** There are no missing, extra, changed, nested, duplicate or non-regular archive members. All 93 entries in the original `SHA256SUMS` verify.

The existing [review-raw.tar.gz](review-raw.tar.gz) is 54,407 bytes, SHA256 `eccc4f9375f4c2f14db9cd071a3bc1e53e561555d83c5a9d1b5e8b01288ab926`. It preserves the exact `TASK_BRIEF.txt`, `BRIEF.md`, report/source review, commands in `run_review.py`, receipts, original and revised oracle results, regressions, action/privacy checks, CPU/memory results, rejected fixture iteration, and original hash index. No engine binary, templates, caches, user state or working game tree is in the archive. The surface `.txt` CPU logs are exact copies of the originals' `.log` bytes; original receipt paths retain their original names.

This confirmation is based on root `4ee0d667dd42618011fc7711163c39d9b9c9c132` and adds only evidence documentation. The reviewed product source is `470fad59f5b42742d4e6eb4693b847de06162499` (`470fad5`), with revised oracle/benchmark `d593d7b14b5838d2904a9a35547611e5a08cdf81` (`d593d7b`), compared against `6a0d8d5d85b4fb37943903886982f51b4ed230b0`. Builder and candidate identities were known; this was not blinded.

The [original report](REPORT.md) keeps the distinction between depleted-trigger samples (zero shots in six samples) and the corrected ammo-sufficient, recoil-compensated benchmark. Corrected runs recorded 3,170–3,180 actual shots and matching damage events per active sample. Temporary playback objects released after frame flushes; cleanup was outside the timers. No rendered-latency, speed-up, leak-qualification or whole-network claim follows.

The report also retains the static review of [native suite registration](native-suite-registration.patch): adding `authority_order` to the helper's default SUITES selects the real oracle with its existing exit/log enforcement. This is a static registration check, not native Windows/macOS execution evidence.

Multiattacker attribution, the attacker-first simultaneous full-team wipe policy, and whole networking qualification remain unresolved. This integrity check does not expand the bounded acceptance verdict. No new engine run was performed.

[integrity-verification.json](integrity-verification.json) records the committed archive hash, every original member hash, verified surface copies, source commits and verification operations. To inspect the original index without the working directories:

```sh
git show 640e4852acd92a8143ee528c151757d0d4b61ec2:docs/reports/gauntlet/m3-authority-order/independent/review-raw.tar.gz > /tmp/sightbreak-authority-review-raw.tar.gz
mkdir -p /tmp/sightbreak-authority-review-extracted
tar -xzf /tmp/sightbreak-authority-review-raw.tar.gz -C /tmp/sightbreak-authority-review-extracted
cd /tmp/sightbreak-authority-review-extracted
sha256sum -c SHA256SUMS
```
