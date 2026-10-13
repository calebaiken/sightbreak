# Independent engineering audit — SIGHTBREAK 0.3.0-dev

Auditor: Claude (independent reviewer; did not author the audited code).
Audited commit: `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d` (`main` and `origin/main` were identical when fetched; no later commits existed).
Phase: **A — read-only baseline.** No source file was modified to produce this report. Reproduction probes lived outside the repository and ran against the unmodified tree and an immutable `git archive` of the audited commit.

This document records what I verified, what I could not verify, and what I found. A finding is listed only if it is backed by a reproduction or a specific code path; hypotheses I tested and refuted are listed separately. Severities are my judgment and Codex should challenge them with evidence.

## 1. Environment and method

| Item | Value |
| --- | --- |
| Host | Linux x86_64 cloud container, 4 vCPU, 15 GiB RAM, no GPU, no phone attached |
| Engine | Godot `4.7.2.stable.official.ed1daf0bf`, installed by the repository's own `scripts/setup.sh` (published SHA-512 verified) |
| Rendering | Xvfb + Mesa llvmpipe 25.2.8 (software). **Not a mobile GPU.** |
| Database | PostgreSQL **16.15** (local cluster). The repository pins a PostgreSQL 17 Docker image, but no Docker daemon was available. This is a deviation; every backend result below is on 16.15. |
| Python | 3.13.16, dependencies from `backend/uv.lock` via `uv sync --frozen` |

Method: full read of every production source file (manifest in §3), execution of the maintained regression suites, then targeted probes for each suspected defect. Probes measured behavior on the real authoritative code paths (for example `SBActor.tick_authority` at the 60 Hz physics step), not re-implementations.

## 2. Independent re-verification of Codex's reported 0.3 state

| Codex claim | My result on the audited commit | Status |
| --- | --- | --- |
| 443 native assertions pass | 443 pass: actor 72, world 25, hit feedback 10, match 75, profile 10, touch 34, main 35, landscape 144, economy recovery 12, cosmetic presentation 26. Plus uncounted economy-UI pass, short bot round, two ENet clients. `validate.sh` exit 0. | **Reproduced** |
| Complete bot matches work | Natural full match: 12 rounds, 5–7, 81 kills, halftime, plant observed, exactly one result report, 371.0 simulated s | **Reproduced** |
| 39 PostgreSQL tests pass | 39 passed in 6.5 s (on PG 16.15, see §1) | **Reproduced** |
| 14 real HTTP economy checks pass | `NATIVE_REAL_ECONOMY_QA 14/14 passed` | **Reproduced** |
| Network regression passes | Both ENet clients `NETWORK_CLIENT_PASS` | **Reproduced** |
| 30 renderer cleanup checks pass | Native lifecycle 11/11 and cosmetic lifecycle 19/19 under Xvfb; demo capture emitted; texture plateau 61,141,254 B (Codex: 61,272,326 B on a different host) | **Reproduced** |
| Fixed-camera render counters | Identical draw/primitive counts (e.g. approach 444 draws / 136,954 primitives standard, 170 / 40,070 low) | **Reproduced** |
| Visual quality 8.1/10 | My independent baseline is **6.6/10** (§7). Codex's own final captures still show text defects their review recorded as fixed. | **Disputed** |
| Gameplay state correctness 8.8/10 (QA-0.3) | Contradicted by H-1, H-2 and M-1–M-3 below; the suite tests rules happen, not that hit geometry, fire rates and switching match the weapon data. | **Disputed** |
| Multiplayer integrity 8.5/10 in local scope | Contradicted by H-1 (server accepts the quick-switch), M-4 (full-state broadcast), M-5 (predictable spread) and M-6 (no interpolation). | **Disputed** |
| "Remote actors interpolate snapshot positions" (`docs/network.md:72`) | The client applies a single 90 % snap per snapshot (`actor.gd:697`); there is no per-frame interpolation buffer. | **Inaccurate documentation** |

The passing suites are real and most are well constructed (the PostgreSQL suite in particular exercises concurrency, replay and changed-payload replay). They do not exercise the defects below because they assert that rules *occur*, not that the measured mechanics match the declared data.

## 3. Review coverage manifest

Every tracked file outside `docs/reports/` evidence folders was inspected. "Full" means every line was read.

| Path | Responsibility | Lines | Review | Existing test coverage | Findings |
| --- | --- | ---: | --- | --- | --- |
| `backend/app.py` | FastAPI economy: auth, tickets, store, cases, market, trades, rewards, loadouts | 475 | Full | `backend/tests/test_economy.py` (39) | M-7, M-8, L-1, L-2, L-6 |
| `backend/models.py` | SQLAlchemy schema, constraints | 104 | Full | indirect | — |
| `backend/migrations/001–003.sql` | append-only triggers, partial unique listing index, tickets, loadouts | 32 | Full | fixture applies 001 only; 002/003 come from `create_all` | I-3 |
| `backend/migrate.py`, `dev-api.sh`, `dev-db.sh`, `bridge_fixture.py`, `simulate.py`, `config/*.json`, `pyproject.toml`, `uv.lock` (header) | tooling, config | 210+ | Full (lockfile spot-checked) | — | — |
| `backend/tests/test_economy.py` | adversarial PostgreSQL tests | 359 | Full | — | gaps noted per finding |
| `game/scripts/gameplay/actor.gd` | movement, weapons, hit registration, visuals | 732 | Full | `actor_test.gd` (72) | H-1, H-2, H-3, M-1, M-5, M-6, L-8 |
| `game/scripts/gameplay/match.gd` | rounds, objective, bots, RPC, snapshots, rewards | 968 | Full | `match_test.gd` (75), bot tests, `network_probe.gd` | M-2, M-4, M-9, L-5, L-7 |
| `game/scripts/gameplay/arena.gd` | Relay Yard geometry, materials, batching, navigation | 557 | Full | `world_test.gd` (25), `actor_test.gd` | H-4, L-9, L-10 |
| `game/scripts/gameplay/utility.gd` | grenades, smoke | 168 | Full | `actor_test.gd` | M-3 |
| `game/scripts/gameplay/weapons.gd` | weapon data | 13 | Full | `actor_test.gd` | (data for M-1) |
| `game/scripts/gameplay/weapon_model.gd` | procedural weapon meshes | 319 | Full | cosmetic tests | H-3 |
| `game/scripts/gameplay/combat_effects.gd` | pooled casings/sparks/dust | 97 | Full | `hit_feedback_test.gd` | — |
| `game/scripts/network/input_gate.gd` | untrusted input filter | 38 | Full | `match_test.gd` | L-4 |
| `game/scripts/network/economy_bridge.gd` | privileged server HTTP bridge | 77 | Full | `match_test.gd`, `test_bridge_transport.py` | — |
| `game/scripts/main.gd` | menus, HUD, input routing, settings | 870 | Full | `main_test.gd` (35), `landscape_ui_test.gd` (144) | M-10, M-12, U-1–U-4 |
| `game/scripts/ui/economy_ui.gd` | armory, cases, market, trades | 771 | Full | `economy_ui_test.gd`, `economy_recovery_test.gd`, native economy | M-11, L-3, U-5, U-6 |
| `game/scripts/ui/economy_api.gd` | HTTP client | 65 | Full | `economy_ui_test.gd` | — |
| `game/scripts/ui/touch_controls.gd` | multitouch HUD | 229 | Full | `touch_test.gd` (34) | U-2 |
| `game/scripts/ui/item_inspector.gd`, `case_reveal.gd`, `display_models.gd`, `cosmetic_material.gd`, `safe_area.gd` | 3D inspection, reveal, shader finish, safe area | 448 | Full | cosmetic/lifecycle tests | H-3 (shader) |
| `game/scripts/profile.gd` | offline save | 82 | Full | `profile_test.gd` (10) | — |
| `game/project.godot`, `export_presets.cfg`, `main.tscn`, `assets/**/*.import`, `relay_sky.tres` | engine config, export | 140+ | Full | export verification scripts | M-12 |
| `game/tests/*.gd` (25 files) | harnesses | 2,400 | Assertion inventory for all; full read of `actor_test.gd`, `render_benchmark.gd` | — | coverage gaps noted per finding |
| `scripts/*.sh`, `scripts/*.py` (18 files) | setup, export, validation, manifests | 900+ | Full for setup/export/validate/test_render/profile_render/serve; manifest/verify scripts read for credential handling | `test_build_manifest.py` (10) | I-4 |
| `docs/*.md`, `docs/reports/QA-0.3.md`, `PERFORMANCE-0.3.md`, `WORLD-0.3.md`, media READMEs | claims under audit | — | Full for listed reports | — | §2 |

Not reviewed in depth: the 2,379-line `GODOT-COPYRIGHT.txt` (third-party notices; presence confirmed), binary PNG evidence (sampled visually), and the full `uv.lock` body (hash-pinned; only package set checked). No `.github/workflows` directory exists.

## 4. Findings

Severity scale: **Critical** — exploitable value creation/loss, remote compromise or data loss; **High** — breaks competitive fairness or core playability in normal use; **Medium** — real defect with bounded impact or requiring a modified client; **Low** — minor correctness/UX/hardening; **Informational** — context or positive confirmation.

**No Critical findings.** I found no path for a client to set health, damage, ammunition, objective state, wallet balances or rewards. Godot RPC permissions are correct: every server→client RPC is `@rpc("authority")`, and every `any_peer` RPC is server-gated and validated.

### High

#### H-1 — Weapon switching resets the fire cooldown (marksman fires 2.3× faster)
- Subsystem: gameplay / server authority. `game/scripts/gameplay/actor.gd:517` (`_equip` sets `_cooldown = 0.3`), `:538`, `:466`.
- Description: `_equip` overwrites the single shared `_cooldown` with a 0.3 s deploy time. The longer per-shot interval of the weapon just fired is discarded, so fire → switch → switch back fires again after ~0.3 s. The server accepts this from any client because it is legal input.
- Evidence: authoritative tick probe. Marksman (designed interval 0.82 s): next shot at **0.833 s** normally, **0.367 s** with one sidearm swap in between. Switching also zeroes `recoil` and `_shot_index` (instant recoil reset).
- Reproduction: `SBActor` with marksman + sidearm; tick at 1/60 s: fire; next tick send `weapon: "sidearm"`; then `weapon: "marksman"` and fire; measure ticks between `shot_fired` signals.
- Correction: keep a per-weapon ready time; on equip, ready = max(deploy delay, remaining interval of that weapon). Do not reset recoil on equip to zero beyond normal recovery.
- Regression test: quick-switch cannot shorten any weapon's interval; switching to a different, ready weapon still costs only the deploy delay.
- Confidence: High.

#### H-2 — Headshot region is 2.3× the visible head and includes empty air
- Subsystem: hit registration. `actor.gd:554`.
- Description: a hit is a headshot whenever the ray strikes the 0.31 m-radius movement capsule above `head_height − 0.25`. The visible head/helmet is ~0.35 m wide; the capsule is 0.62 m. Rays passing beside the head (or just over the shoulder) count as headshots (×3.5 for the rifle → one-shot kills on shots that visibly missed). Crouching shifts the threshold to 0.88 m while the body is uniformly squashed, so the head zone again extends below the drawn head.
- Evidence: 81×70 ray grid across the target, 1 cm spacing, real physics. Standing: 1,398 cells counted as head vs 599 cells inside the visible head/helmet silhouette (**ratio 2.33**); 799 counted cells are outside the visible head. Crouched: 1,774 vs 863 (**2.06**).
- Correction: classify hits against an explicit head volume aligned to the rendered head (and a body volume for the torso), and let rays that pass through the capsule's empty corners continue to whatever is behind.
- Regression test: center-head = headshot; 0.25 m lateral at eye height ≠ headshot; chest = body; crouched equivalents; a ray through the gap beside a head hits a target behind.
- Confidence: High.

#### H-3 — Per-equip procedural mesh rebuilds stall the main thread every round
- Subsystem: performance (mobile). `actor.gd:356–368` (`_build_gun`), `weapon_model.gd:15–23, 140–184`, `actor.gd:245–354` (`_build_body`), `cosmetic_material.gd:44–48`.
- Description: every equip rebuilds the first-person weapon from scratch (SurfaceTool + MeshDataTool loops, fresh meshes and materials) for **every** actor — including bots, whose first-person gun is invisible, and the headless server. Each body is rebuilt and re-batched per actor and again whenever the team changes (all 10 at halftime). `CosmeticMaterial.finish()` creates a new `Shader` from source on every call, so each equip also requests a new shader program.
- Evidence (desktop CPU, so phones will be slower): one first-person rifle build **27.1 ms**; one actor construction **45.1 ms**; `_begin_round()` with nine bot purchases **228.9 ms** of main-thread time; consecutive builds share no mesh resources; two `finish()` calls return different `Shader` objects.
- Impact: a visible hitch at every round start in offline play, on every weapon swap during a fight (local player and, on clients, every remote actor's swap via `apply_snapshot`), and a larger hitch at halftime. Runtime shader creation is a known source of mobile stutter.
- Correction: build each weapon/body variant once and share meshes via cheap instantiation; cache the cosmetic `Shader`; avoid building first-person geometry for actors that never show it.
- Regression test: repeated equips share mesh resources; round start with nine purchases below an explicit time budget; `finish()` returns a shared shader.
- Confidence: High (timings are host-dependent; the allocation pattern is not).

#### H-4 — Every decorative box is a shadow caster; shadows dominate the 0.3 cost increase
- Subsystem: rendering. `arena.gd:341–376` (`_batch_static_boxes`), `arena.gd:139–145` (sun), `arena.gd:96–108` (labels).
- Description: all 1,460 boxes are batched into 75 MultiMesh instances by material, and every batch casts shadows from the 4-split directional light. That includes 578 instances thinner than 5 cm (bolts, ribs, latches) and 176 ground-level strips under 3 cm tall (seams, drains, lane paint) that cannot produce a visible shadow. All 40 `Label3D` signs also default to shadow casting.
- Evidence: fixed-camera counters on the audited commit: Standard (shadows + 2× MSAA) **444 draws / 136,954 primitives / 488 ms** llvmpipe median (approach) vs Low (no shadows/MSAA) **170 / 40,070 / 92 ms**. About 71 % of primitives and 62 % of draws in that view come from the shadow/MSAA path. Codex's own report shows the 0.3 art raising primitives 5.5× (24,782 → 136,954).
- Correction: exclude thin and ground-decal detail and labels from shadow casting, split batches by shadow participation, reduce directional splits for the small arena, and add a resolution-scale setting (see M-12). Measure before/after with the existing benchmark.
- Regression test: assert no ground-decal/thin batch casts shadows; benchmark primitives must not regress.
- Confidence: High for the counters; frame-time ratios are software-renderer data and **do not predict phone FPS**.

### Medium

#### M-1 — Fire intervals are quantized up to the 60 Hz tick (SMG −15 %, rifle −10 % rate)
- `actor.gd:466, 481, 538`. The cooldown is clamped at zero each tick and reset to the full interval on fire, so any interval that is not a multiple of 1/60 s rounds **up**.
- Evidence: measured over 1,200 ticks — SMG designed 11.76 rounds/s, actual **10.00/s**; rifle 9.52 → **8.57/s**; sidearm −1.4 %; marksman −1.6 %. The SMG/rifle DPS relationship differs from `weapons.gd`.
- Correction: carry the remainder (accumulate `+= interval` while the trigger is held, clamp only when idle). Test: average interval over many shots equals the data within one tick.
- Confidence: High.

#### M-2 — Bought weapons survive death and the halftime reset
- `match.gd:217–224`, `actor.gd:388–433`. Halftime sets every actor to 1,200 funds (a pistol-round reset) but leaves `inventory` and the equipped weapon untouched; death never clears inventory either.
- Evidence: offline match probe — after buying a rifle: `["sidearm","rifle"]` after death, and still `["sidearm","rifle"]`, weapon `rifle`, funds 1200 after halftime.
- Impact: post-halftime "pistol round" is played with rifles; buying has no lasting stakes. Whether weapons should drop on death is a design decision for Codex and human playtesting; the halftime inconsistency is a defect.
- Correction: reset inventory to the sidearm at halftime (minimum); decide death-drop rules with playtest evidence. Confidence: High (behavior); Medium (intended design).

#### M-3 — Smoke cloud is snapped to absolute y = 1.6 m
- `utility.gd:101`. Wherever the smoke detonates, its center is set to world height 1.6.
- Evidence: a smoke resting on a freight container roof (y≈3.1) detonated with its cloud center at (−7, 1.6, −11), **inside the container volume**. A mid-air detonation likewise drops or lifts the cloud to 1.6 m regardless of terrain.
- Correction: place the cloud relative to the surface below the detonation point; keep the same position for bot concealment (`actor.gd:can_see`) and replicated visuals. Confidence: High.

#### M-4 — Snapshots broadcast all hidden state to every client
- `match.gd:757–765`, `actor.gd:689–690`. Every 50 ms each client receives every actor's position, velocity, health, funds, ammunition and inventory, plus `carrier` (which enemy holds the device) and `interactions` (who is planting/defusing).
- Impact: a modified client gets a complete wallhack/ESP. The measured snapshot is 732 B deflated (6,484 B raw), 14.6 KB/s per client.
- Correction (Codex-owned networking): visibility-based relevance for enemy actors, omit enemy economy/ammo/inventory and the carrier identity. Confidence: High.

#### M-5 — Weapon spread is predictable from the actor ID
- `actor.gd:95` seeds `_rng` with `id * 7919 + 103`; `_fire` is its only consumer and nothing reseeds it.
- Evidence: two independently constructed actors with ID 7 produced **bit-identical** shot directions across a round reset; ID 8 differed. A client knows its actor ID and can count its shots from snapshot ammo, so it can predict and cancel each spread offset ("no-spread").
- Correction: seed authoritative spread from a cryptographic or per-match random source on the server only (clients never simulate shots). Confidence: High.

#### M-6 — No snapshot interpolation; local movement is unpredicted
- `actor.gd:692–697`; `match.gd:595–611`. Remote actors are moved 90 % toward the latest snapshot once per 20 Hz packet and are stationary between packets; the local actor hard-snaps to server position with no prediction.
- Impact: visibly stepped motion for every other player and input-to-motion latency of a full round trip for the local player in online play. `docs/network.md:72` describes this as interpolation.
- Correction (Codex-owned): timestamped snapshot buffer with ~100 ms interpolation delay; client prediction with reconciliation. Confidence: High.

#### M-7 — Market filters are applied after `LIMIT 500`
- `backend/app.py:225–233`. The query takes the 500 cheapest active listings, then filters in Python.
- Evidence: 500 cheap commons + 1 Mythic at 5,000 → `GET /market?rarity=Mythic` returned **0** listings.
- Correction: push filters into SQL before the limit (join `items`), add pagination. Test: the case above returns the Mythic. Confidence: High.

#### M-8 — `/market` is unauthenticated, unthrottled and N+1
- Same route. 501 per-row `db.get` calls; **247 ms** per anonymous request at 501 listings on this host. Every write's rate check also takes the global advisory lock (`app.py:47–55`), so a read flood competes with economy writes for the pool. Correction: single joined query, response cap/pagination, rate limit reads. Confidence: High (measured).

#### M-9 — Rejected or idle peers are never disconnected
- `match.gd:614–679` (no server-side `disconnect_peer`, no join deadline; the only `close()` is client-side in `_rejected_rpc`).
- Impact: a peer rejected in account mode can call `_join_rpc` again immediately; each call is a privileged `/server/tickets/consume` request that also consumes the backend's per-IP `server_ticket` budget (120/min, keyed on the game server's own address), so one LAN peer can starve legitimate joins.
- Evidence: code path; the earlier slot-exhaustion hypothesis was **refuted** (see §5). Correction: disconnect after rejection, per-peer join attempt limit and join deadline, local ticket format check before HTTP. Confidence: Medium (path not executed end-to-end).

#### M-10 — Offline pause does not pause
- `main.gd:767–775` ("The match continues while this menu is open."). Correct for network play; in offline 5v5 the bots keep fighting while the player is in a menu. Correction: suspend the offline match process while the field menu is open. Confidence: High.

#### M-11 — Trade confirmation does not state what each side gives and receives
- `economy_ui.gd:764–770`. The confirmation reads "Confirm revision N exactly as displayed?" with no item list; the partner is identified only by a raw UUID (`:728`). The backend's revision check prevents silent swaps, but the user is never shown the final terms at the moment of confirmation — the directive explicitly requires this. Correction: enumerate *you give* / *you receive* with name, rarity, wear and pattern, flag one-sided gifts, and show the partner's display name. Confidence: High.

#### M-12 — Only two quality tiers and no render-resolution control
- `main.gd:423–432`, `project.godot`. Low disables shadows entirely; Standard enables 4-split shadows and 2× MSAA. No `scaling_3d_scale` option exists, which is the primary fill-rate lever on phones. Correction: add render scale and an intermediate tier; validate on devices. Confidence: High (presence); device impact **UNVERIFIED**.

### Low

| ID | Finding | Location | Evidence | Correction |
| --- | --- | --- | --- | --- |
| L-1 | Login timing reveals whether a username exists | `app.py:170–179` | median 83.9 ms (existing user, wrong password) vs 12.0 ms (unknown user) | verify against a dummy hash when the user is missing |
| L-2 | Non-ASCII `X-Server-Key` raises an unhandled 500 | `app.py:67` | `compare_digest` on non-ASCII `str` → status **500** (expected 403) | compare encoded bytes |
| L-3 | Registration hint says 10 characters; backend requires 12 | `economy_ui.gd:233` vs `app.py:137` | code | correct the copy |
| L-4 | Input gate drops the *newer* of two packets < 12 ms apart | `input_gate.gd:10` | two jittered 30 Hz packets 8 ms apart: second (with `fire`) rejected | rate-limit processing per tick and keep the latest |
| L-5 | Recoil pattern continues across bursts | `actor.gd:507, 566–568` | after full recovery the next 8 shots follow a different horizontal pattern (`_shot_index` only resets on reload/equip) | reset the pattern index when recoil has recovered |
| L-6 | `/history` returns an arbitrary 100 match records | `app.py:401` | no `ORDER BY` | order by time |
| L-7 | One deactivated participant voids all ten players' rewards | `app.py:376–378` | whole-match 400, non-retryable | record ineligibility per participant |
| L-8 | Crouch visual is a uniform Y squash | `actor.gd:449` | code | pose legs/torso instead (art) |
| L-9 | Container and hall signs z-fight/clip with ribs and mullions | `arena.gd:124–125, 303` | Codex's final captures read "FR EIGHT SYSTEMS" and "TRAN FER STATION" | offset labels clear of coplanar geometry |
| L-10 | Bot navigation is O(waypoints × obstacles) per re-plan | `arena.gd:217–241` | 105 µs/call; ~8.8 ms CPU per second for 10 bots on desktop | cache nearest waypoints; acceptable for now |

### UX findings (from code and Codex's native captures)

| ID | Finding | Location |
| --- | --- | --- |
| U-1 | HUD omits alive counts, utility counts, a kill feed (kills overwrite the single status line) and which side the player is on; score is a bare "00 / 00" | `main.gd:486–582`, `match.gd:359` |
| U-2 | 12 identical circular buttons; FRAG/SMOKE/USE cluster over the weapon model; no utility count on FRAG/SMOKE | `touch_controls.gd:29–35` |
| U-3 | Buy menu lists the free, always-owned sidearm; owned/unaffordable weapons are not distinguished and fail with "check your round funds" | `main.gd:805–820`, `match.gd:149–150` |
| U-4 | No shared design tokens: menu and armory build separate themes with different golds/crimsons/panels; disabled and selected states are undefined | `main.gd:78–104`, `economy_ui.gd:110–129` |
| U-5 | Armory tabs have no active/selected state | `economy_ui.gd:86–88`; visible in `v03-cosmetics/economy_market.png` |
| U-6 | Market purchase confirmation omits wear/pattern, so listings of the same finish are indistinguishable at confirm time | `economy_ui.gd:687–688` |

### Informational

- **I-1** No armor system exists; the specification does not require one, so this is not a defect.
- **I-2** The authority boundary is sound: server-only simulation, validated input, authority-only server RPCs, server-scoped single-use hashed tickets, idempotent trusted results. Confirmed by code and existing tests.
- **I-3** The PostgreSQL fixture applies only `001_integrity.sql`; tables from 002/003 exist only because `create_all` builds them from the models. Migration drift would go unnoticed.
- **I-4** No CI workflow exists; validation depends on manual script runs.
- **I-5** Aim input (`look`) is unconstrained by design; aim-assist detection is out of scope.

## 5. Hypotheses tested and refuted

- **ENet slot exhaustion.** `create_server(port, 10)` suggested ten idle connections could block all players. Against a real dedicated server process, 10, 30 and 31+ raw idle ENet connections were accepted and a legitimate client still connected every time. Not a finding; M-9 is the narrower confirmed issue.
- **Economy minting/double-spend.** Concurrent purchase, replay, changed-payload replay, case consumption and trade revision paths all serialize under the advisory lock and are covered by passing tests. I found no value-creation path.
- **Client-authoritative state.** No RPC accepts position, health, ammunition, objective or reward values from a client.

## 6. Five highest-value improvements

1. **Server-side weapon timing** (H-1, M-1, L-5): per-weapon ready times, remainder-carrying intervals, recoil pattern reset. Small, fully testable, restores fairness and weapon data fidelity.
2. **Hit volumes that match the rendered head and body** (H-2): explicit head/body intersection with pass-through of empty capsule space.
3. **Remove invisible rendering work** (H-4, M-12): shadow participation only for geometry that can cast a visible shadow, fewer directional splits, render-scale setting, measured with the existing benchmark.
4. **Eliminate runtime mesh/shader construction hitches** (H-3): shared weapon/body meshes and a single cosmetic shader.
5. **Competitive HUD and transaction clarity** (U-1–U-6, M-10, M-11, L-3): shared design tokens, alive/utility/kill-feed HUD, explicit trade terms, offline pause, accurate buy menu.

Networking items M-4 and M-6 are high-impact but sit in Codex's primary ownership and need protocol changes; I recommend Codex lead them with my review.

## 7. Baseline scorecard (before any change)

Rubric for every category: **5** = works on the happy path with significant verified defects; **7** = coherent, several Medium defects, mostly happy-path tests; **8.5** = no open High defects, Mediums tracked, adversarial tests for the main failure modes, evidence from the actual runtime; **10** = exceptional. A category without runtime evidence is **UNVERIFIED**.

| Category | Baseline | Basis |
| --- | ---: | --- |
| Architecture & maintainability | 6.5 | Clear authority split and good tests; but 900-line mixed-responsibility files (`match.gd`, `main.gd`), duplicated UI themes, procedural art inside gameplay classes |
| Gameplay correctness | 6.0 | H-1, H-2, M-1, M-2, M-3 measured |
| UI/UX | 6.5 | Safe-area aware and layout-tested; U-1–U-6, M-10, M-11 |
| Visual quality | 6.6 | My read of Codex's native captures: geometry 7.0, materials 6.5, lighting 6.5, models 6.0, effects 6.0, identity 7.5, readability 6.5. Visible text clipping (L-9), toy-like operators, spherical smoke |
| Animation | 6.0 (stills only) | Procedural transforms; no sequence review; human feel **UNVERIFIED** |
| Performance | 5.5 desktop-diagnostic; **device UNVERIFIED** | H-3 hitches, H-4 shadow cost; no phone data |
| Security | 7.5 | Sound auth/ticket/transaction design; M-7, M-8, M-9, L-1, L-2; production controls absent (documented) |
| Networking | 6.0 | Authority correct; M-4, M-5, M-6, M-9 |
| Economy integrity | 8.5 | No value-creation path found; strong adversarial tests; M-7 is a read-path bug |
| Stability | 8.0 | All suites green; lifecycle plateaus; device lifecycle **UNVERIFIED** |

These are my independent judgments, not an average of Codex's, and Codex should contest any score it believes the evidence does not support.

## 8. Reproduction

Fixes that land later get their own regression tests. The commands used for this report were:

```sh
SIGHTBREAK_TOOLS_DIR=<tools> ./scripts/setup.sh
SIGHTBREAK_TOOLS_DIR=<tools> ./scripts/validate.sh                     # 443 assertions
DATABASE_URL=postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/<name>_test \
  PYTHONPATH=backend .venv/bin/pytest backend/tests -q                  # 39 tests
.venv/bin/python scripts/test_native_economy.py                         # 14/14
DISPLAY=:99 ./scripts/test_render.sh                                    # 11/11 + 19/19
DISPLAY=:99 ./scripts/profile_render.sh <out> standard|low              # counters in H-4
```

Probe sources and their recorded baseline output are committed in [`probes/`](probes/README.md): fire-rate, quick-switch, spread determinism, hit grid, smoke placement, inventory, snapshot size, build timings, arena statistics, ENet idle connections, market filter, server-key encoding and login timing. Timings are host-dependent; structural results (counts, ratios, booleans) are not.
