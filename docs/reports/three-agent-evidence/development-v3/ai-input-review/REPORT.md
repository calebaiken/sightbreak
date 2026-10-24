# Exact PR14 AI input review — compact publication evidence

## Decision and scope

**Do not integrate `48eb0586e273f96dc20b346ed444d00ab0f3ac30` wholesale. Retain the V2 bot runtime.** The exact candidate breaks the shipped match/actor interface. Its isolated anchor, hearing-range and damage-facing improvements do not establish a working integrated candidate.

This package publishes a subset of a completed independent native Windows QA review. **No Godot campaign was rerun on the dirty V3 integration checkout for this publication.** No runtime, owner branch, existing V2 evidence, other V3 document, commit or GitHub post was changed by this packaging task. This directory alone was added. The user's separately published PR14 review is not reproduced or independently verified here.

The review is same-model agent QA, **not human acceptance**, graphical playtesting, or multiplayer/platform certification.

## Frozen inputs and engine

| Input | Exact identity |
|---|---|
| V2 / neutral `north` | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| PR14 / neutral `south` | `48eb0586e273f96dc20b346ed444d00ab0f3ac30` |
| Retained probe recovery | `git show d2439ac:docs/reports/three-agent-evidence/stabilization-v2/ai/<file>` |
| Native engine | `Godot_v4.7.2-stable_win64.exe`, verified `4.7.2.stable.official.ed1daf0bf` |
| Engine SHA256 | `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424` |
| Native-run V2 `bot_ai.gd` SHA256 | `f2f8ff5cf1c6f0d1bfa0be0d04b4bc662b1a26f7a4bc38bb9a3cf9da4d749fcd` |
| Native-run candidate `bot_ai.gd` SHA256 | `a685e25b6760078c9162dd15e7a4b66a8bb316dffdbd3c95cebaa7502e09d333` |

The original detached worktrees were `C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-{north,south}-20261019`. Both native editor imports completed before probes. Final HEADs, source-code diffs and indexes were unchanged. **The detached worktrees were not fully clean:** generated tracked `.import` bookkeeping differed in 22 V2 and 10 candidate files. Those differences were preserved, not reset. See [source verification](evidence/source-verification.json), [source hashes](evidence/source-sha256.json), and copied final status logs.

Commit identities, native-worktree byte hashes and `git show` snapshot hashes are distinct. [Source excerpts](provenance/source-excerpts.json) retain commit, repository path, blob SHA1, parent snapshot SHA256 and line ranges without copying the full source snapshots. Exact source recovery commands are included there.

## Ordering: neutral outputs before candidate claims

The unchanged [neutral first assessment](evidence/neutral-first-assessment.md) records the initial unlabelled comparison. Imports finished by **18:55:02 UTC**; retained probes ran from **18:55:48 UTC**. The assessment's original file timestamp is **18:57:36 UTC**, before recorded candidate diff commands at **18:58:01 UTC** and candidate commit-claim retrieval at **18:58:04 UTC**, on 2026-10-19.

One clarification is important: the assessment says the extended baseline sweep was launched and not yet used. Its process receipt shows completion at **18:57:21 UTC**, before the assessment was written. Process completion is not the same as reviewer consumption; the sweep result was not part of that initial assessment. The original wording is preserved, not silently corrected.

These are receipt timestamps plus later-observed file metadata and a reviewer attestation—not signed file-read telemetry or a perfect double-blind experiment. The plaintext label mapping existed earlier; V2 source was read to understand the contracts. See [chronology and its limits](CHRONOLOGY.md) and [derived chronology receipts](provenance/chronology.json).

## Findings

### 1. Blocker: the exact candidate cannot compile its own match

Fixture-free native `--check-only --script res://scripts/gameplay/match.gd` exits **0 for north, 1 for south**. Candidate errors are:

- `game/scripts/gameplay/match.gd:36,94`: missing `RelayYard`; the candidate arena instead declares `SBArena` at `arena.gd:2`.
- `match.gd:454,457`: missing `SBBotAI.nearest_defender()` and `cover_position()`.

Read the [north compile stderr](evidence/logs/north-match-check-only.stderr.log), [south compile stderr](evidence/logs/south-match-check-only.stderr.log), and [exact compile receipts](provenance/compile-receipts.json). Both stdout streams, including the engine banner, are preserved. A separate menu-only smoke exited 0; it did not load the match and does not contradict this failure.

### 2. Strict actor/API and callback failures remain after the first compile error

The strict native probe uses the shipped `SBActor`, **without actor compatibility aliases**:

- Candidate `bot_ai.gd:625` reads nonexistent `actor.id`; the shipped actor exposes `actor_id` (`actor.gd:30`). Compute errors and leaves a sentinel `input_state` untouched.
- The actual actor also lacks the rewrite's `slot`, `hp`, `reloading`, `is_bot`, `planting`, `defusing`, `eye_position()` and `apply_tick()`.
- The actual Node-plus-integer-ID damage callback (`match.gd:379`) does not match candidate `record_damage`'s Node-plus-actor branch (`bot_ai.gd:177–203`). Native `damaged_at` remains `-100`, versus `10` on V2. The dictionary damage overload works; helper success is therefore not production callback success.
- V2's dictionary elimination call errors on nonexistent `actor.is_bot` (`bot_ai.gd:246`); the nearby ally receives no alert. The corresponding V2 control records time `100`.

Strict/API outputs are in `evidence/extra-{north,south}/logs/native_contract_probe-r{1,2}.*`; elimination outputs are `native_elimination_contract-r1.*`. Probe sources and full command ledgers accompany them.

The candidate also changes `compute_bot_input` from writing `actor.input_state` to returning a dictionary (`bot_ai.gd:624,757`). An explicit adapted diagnostic confirms that return alone does not update the actor. Its `tick_bot` calls missing `apply_tick()` at line 270; even the subsequent source path only stores `last_cmd`, whereas the match reads `input_state`. This is the **largest remaining source gap: broken end-to-end bot authority/input contracts**.

### 3. Useful isolated behavior changes are not an integration pass

| Native observation | V2 | Exact candidate |
|---|---|---|
| Five-anchor arrival within 1.8 m, 20 s per slot | 2/5; slots 0, 1, 4 fail | 5/5, in 1.58–3.77 s **with adapters** |
| Easy 18 m hearing, event at 20 m | Memory rejects it but a raw-event destination loop follows it | Adapted helper rejects it and stays on anchor |
| Hidden-source damage yaw, with/without visual memory | Navigation overrides damage facing | Adapted helper preserves expected facing and coherent movement |
| `sound_noise`, 16 events × 3 difficulties × 2 teams | 96/96 exact coordinates | Still 96/96 exact coordinates |

The behavior fixture explicitly supplies otherwise absent actor/match aliases and forwards returned commands to the **real** native `SBActor.tick_authority`, collision and movement engine. It is not a Python simulation, but it **is an adapter**, not the shipped integration. Each tree uses its own frozen arena; this is not a common-arena combat/performance comparison.

Both behavior runs per tree have empty stderr and byte-identical stdout. V2 r1/r2 hash: `53478f356ab3498a858a333c14024867fed98dd71620b0335a1b6a2f015293af`; candidate r1/r2: `24b61c46d30b82ff5642404d2dbc5c6e86b4d4a58a6ebfb10faf4d089440cd08`. Full repeated streams, fixture source and [repeat verification](provenance/repeat-verification.json) are included.

That byte-identity claim is deliberately scoped: north's **strict API** stdout differs between r1/r2 only in its computed aim yaw (`-0.00325` versus `0.016742`); that fixture does not seed the match RNG. Its callback/resource/input-sink observations agree. Both strict streams are preserved, not normalized. Policy and real-equipment repeated stdout is byte-identical on both trees.

`sound_noise` remains a shared source gap: values `2.4 / 1.1 / 0.35` exist, but direct sounds are stored at exact coordinates. Source ranges and measured zero error support this; no sound-precision difficulty improvement is claimed.

### 4. Additional adapted policy regressions

Repeated native policy diagnostics show:

- **Idle human blocks bot defusing:** human 0.4 m from the device, bot 1 m away, human not interacting. V2 designates the bot and requests interaction. Candidate `_choose_designated_defuser` (`bot_ai.gd:594–607`) reserves the idle human and returns bot `interact=false`. The active-human positive control selects the human on both.
- **Easy awareness bounds disappear:** V2 ignores easy team reports and rejects a 40 m normal/hard report. Candidate accepts exact 40 m reports on every difficulty (`bot_ai.gd:493–501`).
- With real corridor LOS and no damage, a sound alert enables candidate rear visual acquisition outside the initial FOV; V2 stays unacquired (`bot_ai.gd:293–307`). This is a policy change, **not evidence of seeing through walls**.

The policy fixture has explicit aliases. Its intentional missing-`apply_tick` error occurs after those observations. See both `native_policy_probe-r{1,2}` streams. **A diagnostic exit 0 containing script errors is not a pass.**

### 5. Real equipment authority passes; selection still regresses

Both trees pass the same five real-actor controls: failed, successful, duplicate and dead-actor purchase preservation, plus round-reset resource ownership. A round-2 rifle purchase charges 2400, equips 30/90 and grants no utility. No unauthorized resource grant was observed; V2 already had the failed-buy repair.

Candidate selection nevertheless returns unsupported `pistol` / `shotgun` IDs (`bot_ai.gd:125–138`; neither exists in `SBWeapons.DATA`), and its strict 2000-credit branch errors on `actor.id`. Actor validation prevents free grants; it does not make the selector correct. Both repeated real-equipment outputs and the broader adapted budget matrix are included.

## What the unchanged retained tests establish

Both labels ran the same recovered V2 probes. Candidate module/integration/objective/extended probes fail to parse; those failed outputs are preserved. V2's extended native sweep completes **9 conditions / 18 rounds**, with **2 plants, 0 defuses**. V2's independent objective controls complete authoritative planting/defusing. There is no valid candidate combat, objective-rate or performance comparison.

Some retained assertions intentionally reproduce old defects, so their `pass=true` is not gameplay acceptance. Historical retained-V2 logs are archived separately under `evidence/retained-v2/`; they are not new PR14 runs.

## Integration recommendation and limits

Keep V2's public helpers, actor names, state shapes, callback overloads and input-only authority boundary. Consider only narrow ports of validated anchor data, one bounded auditory-memory path, and a damage-look guard through navigation. Preserve V2 equipment authority and difficulty/team-report constraints. Validate any future port against V2's actual geometry and full native match runtime; do not import this arena/module rewrite or invent production aliases to make it fit.

This is a docs-only publication of earlier results. No campaign ran on dirty integration; no current packaged-build, multiplayer, mobile, graphical or human acceptance is inferred. The exact candidate was rejected, not silently repaired.

The **complete external bundle** remains at `C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-evidence-20261019`: **341 hashed payload files plus its checksum ledger (342 files total)**. The unchanged [external ledger copy](provenance/external-SHA256SUMS.txt) has SHA256 `726e035f325d2d1f0a1f254ce35314dbdedfbed263385d4d696a4b1150933b68`. Full source snapshots, large diffs/tree listings, generated import payloads and redundant historical data were not copied. Every omission is enumerated with path, byte count and original hash in [omitted files](provenance/omitted-files.json). See [package contents and integrity](PACKAGE.md) and [commands](COMMANDS.md).
