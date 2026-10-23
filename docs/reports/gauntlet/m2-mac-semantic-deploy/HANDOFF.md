# Source handoff: explicit ordinary Mac semantic Deploy

Frozen runtime/source commit: `d370774c40f2ad63774519e0c258f06d765b9e0a`.
Own branch: `codex/m2-mac-semantic-deploy-20261023`.
Own worktree: `/workspace/sightbreak-mac-semantic-deploy`.
Preregistration: `05fe6a8a`, before all implementation. Base exact `db9d305f`;
its non-document source equals `ea6c330a`. Later handoff is documentation only.
Builder has approved neither this source nor a native attempt.

Review [IMPLEMENTATION.md](IMPLEMENTATION.md), [source-union.json](source-union.json),
and [PREREGISTRATION.md](PREREGISTRATION.md). Successful semantic prerequisite is
sealed actual `d4e25303`, exact d527/run39946498627/job120390346371, scoped to
read-only ARM exposure. No ordinary-input acceptance transfers from that run.

All150 top-level pure methods pass on CPU4 with no skips (136 Mac,9 preflight,
5 strict log; nested alias suites also pass). [pure-final](pure-final) retains the
final ordinary worktree replay. Exact d370 source was pushed before an independent
local depth-one checkout: shallow=true, one commit, clean before/after;
[depth-one/identity.json](depth-one/identity.json) binds its source and full
non-document delta. [depth-one](depth-one) retains the same150 passing methods.
The filtered clone occupies16MiB of Git objects; its lazy checkout reports the
server-filter warning but obtains only the sparse requested content. It has no
parent history. No test fetches historical objects.

Replay without native execution:

```sh
taskset -c 4 python docs/reports/gauntlet/m2-mac-semantic-deploy/run_pure.py \
  --source-root /workspace/sightbreak-mac-semantic-deploy \
  --output /workspace/sightbreak-mac-semantic-deploy-fresh-review-pure
```

Required sparse paths for the full pure replay: `scripts`, `.github`, `game`,
`.claude`, this report, `docs/reports/gauntlet/m2-macos-screen-identity/fixtures`,
and `docs/reports/gauntlet/m2-mac-derived-ocr/original-native-39912086121/macos-ordinary-input`.
The initial omitted-game setup failure is retained in maintained-first.log;
restoring exact tracked files fixes setup, with no skipped check.

The explicit future command adds `--deploy-target owned-ax` to the existing
ordinary verifier with its exact fresh preflight and fresh output directory.
This is a recipe description only. There is no workflow amendment, native
execution, import/export, CI dispatch, new qualifier, release or actual verdict
for this combined candidate. The default OCR route and Windows/Linux defaults
remain unchanged. Game tree remains `55691684d31d44f1680141954bbe530443de9d1f`.

Retained failed harness iterations and their corrections are described in
IMPLEMENTATION.md. Raw unittest trailing spaces are preserved with a scoped
`.gitattributes` whitespace exception; no raw output is normalized. One source
fixture generator accidentally ran off CPU4 for roughly10–20 seconds; later
pure/source Python and clone commands are pinned. No native work ran locally.

Largest gap: actual ordinary Mac Deploy/input/gameplay on this combined source.
The target expires at the original request start+at most5 seconds, while the
previous read-only AX controller used3.842307584 seconds. Slower collection or
extra guarding may reject before the click; no renewed deadline or second
observation is allowed. Existing gameplay, strict-log, privacy/profile, cleanup,
physical/Intel/iOS and whole-release gates remain intact and unqualified where
unobserved. A fresh independent source verdict and then separate actual
preregistration, admission and root release are still required.
