# Recorded commands and reproduction boundaries

**Historical receipts, not instructions to rerun on dirty integration.** No native commands below were executed during publication. Exact original executable/argument arrays, cwd, timestamps, exit status, timeout and both stream hashes remain unchanged in:

- `evidence/commands.jsonl` and `commands-started.jsonl` — original setup, engine, recovery, source, direct-compile and verification receipts. Some referenced raw outputs are intentionally external-only; consult the omissions manifest.
- `evidence/runtime-{north,south}/commands{,-started}.jsonl` — unchanged retained-probe runs.
- `evidence/extra-{north,south}/commands{,-started}.jsonl` — strict, adapted, equipment, policy, elimination and repeated-control runs.
- `provenance/compile-receipts.json` — direct compile receipts with local stream paths and original root-ledger line numbers.

## Frozen source and native engine

Original repository: `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak`.

```text
north = 701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd
south = 48eb0586e273f96dc20b346ed444d00ab0f3ac30
engine = C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe
engine SHA256 = ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424
```

The earlier setup created distinct detached `sol-ai-north-20261019` and `sol-ai-south-20261019` worktrees. Original `--headless --path <tree>\game --editor --import` commands completed for **both** before probe launch. Import logs are copied. Final import bookkeeping makes the trees not fully clean, despite unchanged code/index and HEADs.

## Minimal fixture-free blocker reproduction

These are the exact original direct-check argument forms; repeat only against separately verified frozen worktrees if a future task authorizes it:

```powershell
& 'C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe' --headless --path 'C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-north-20261019\game' --check-only --script 'res://scripts/gameplay/match.gd'
& 'C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe' --headless --path 'C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-south-20261019\game' --check-only --script 'res://scripts/gameplay/match.gd'
```

Original cwd is the corresponding worktree root. North exits 0; south exits 1. The logs and receipts are included, including empty streams.

## Native probe command schema

Every original control was invoked as the following argument array, with a 60 Hz fixed physics cadence:

```text
<engine> --headless --path <frozen-worktree>\game --fixed-fps 60 --script <absolute-original-probe-path>
```

Original external probe root: `C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-evidence-20261019`. The copied fixture bytes retain their original hashes. A future replay using this publication would substitute its `evidence/` path for the probe path; that would be a new invocation, not the recorded original command.

| Probe | Contract/scope | Captured runs per tree |
|---|---|---|
| `native_contract_probe.gd` | Shipped actors, no actor aliases; lightweight match-shaped container; callback call shapes, input sink, equipment IDs and real match loading | r1, r2 |
| `native_elimination_contract.gd` | Shipped actors, V2 dictionary elimination callback; no aliases | r1 |
| `native_equipment_contract.gd` | Shipped real actor purchase/reset logic, no aliases | r1, r2 |
| `native_behavior_probe.gd` | **Explicit actor/match aliases and manual returned-input bridge**; real actor movement/collision; own source arena | r1, r2 |
| `native_policy_probe.gd` | **Explicit aliases**; callout, idle-human defuse and real-LOS/FOV diagnostics; deliberate missing `apply_tick` test at end | r1, r2 |
| `res://tests/bot_ai_regression_test.gd` | Each input's own test, unmodified | r1 |

Candidate strict/policy/elimination probes deliberately continue after erroring calls. **Their process exit 0 does not mean the contract passed. Read stderr and individual observations.** Behavior and real-equipment controls have empty stderr on both repeated runs.

`provenance/repeat-verification.json` compares captured stdout without changing it. Behavior, policy and real-equipment repeats are byte-identical within each tree; north strict API repeats are not (the only changed line contains a different aim yaw from the fixture's unseeded RNG). Do not describe all strict output as deterministic. Elimination has no repeat claim.

The retained probes were recovered byte-for-byte using:

```text
git show d2439ac:docs/reports/three-agent-evidence/stabilization-v2/ai/module_probe.gd
git show d2439ac:docs/reports/three-agent-evidence/stabilization-v2/ai/authority_contract_probe.gd
git show d2439ac:docs/reports/three-agent-evidence/stabilization-v2/ai/integration_controls.gd
git show d2439ac:docs/reports/three-agent-evidence/stabilization-v2/ai/objective_controls.gd
git show d2439ac:docs/reports/three-agent-evidence/stabilization-v2/ai/native_comparison_extended.gd
```

Their new native outputs are under `evidence/runtime-*`, not the historical `.log` files copied under `evidence/retained-v2/`. Some retained controls assert reproduction of a defect; a printed `pass=true` is not acceptance of that behavior.

## Packaging and checksums only

`Build-PublishSet.ps1` is the newly authored, path-pinned packaging script. It only reads the external bundle, copies verified bytes, derives provenance JSON, and writes this package's checksums. It does **not** invoke Godot, git or any archived runner.

The original `evidence/Run-*.ps1` and `Invoke-Recorded.ps1` are archival command drivers. They are not invoked by the packaging script; do not run them on dirty integration. Engine binaries, game assets and complete source worktrees are not included. Reproducing gameplay requires those separately verified dependencies and new authorization; reviewing this publication requires only the logs, receipts and hashes.
