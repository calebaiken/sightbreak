# Independent improvement review — branch `claude/independent-audit-visual-v04`

Author: Claude. Base: `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d` (`main` had not moved when this branch was last fetched).
Companion to [CLAUDE_AUDIT_0.3.md](CLAUDE_AUDIT_0.3.md), which records the read-only baseline audit and every finding ID used below.

**This is not an independent acceptance.** I wrote these changes, so my scores for my own work are self-assessments. The separate reviewer pass in §7 ran as a second agent of the same model family; it is a useful adversarial check, not independent human or cross-vendor review. Codex and a human reviewer should treat every number here as a claim to re-run.

**No release candidate is declared.** Physical-device performance, human gameplay feel, and production security gates remain unverified.

## 1. What changed

| Commit | Area | Audit findings addressed |
| --- | --- | --- |
| `285672b` | Read-only audit, probes, baseline evidence | — |
| `81d16b2` | Authoritative weapon timing, hit volumes, spread seed, smoke rest height, halftime loadout | H-1, H-2, M-1, M-2 (halftime only), M-3, M-5, L-5 |
| `06a5666` | Backend: market filtering and limits, rate limiter, login timing, server-key encoding, history order, trade names | M-7, M-8, L-1, L-2, L-6 |
| `92b1c37` | Rendering: batching, shadow participation, shared meshes and shader, render scale, signage | H-3, H-4, M-12, L-9 |
| `d906c17` | Design tokens, HUD, requisition, settings, offline pause, armory transaction clarity | M-10, M-11, L-3, U-1–U-6 |
| `fa65b15` | Transfer hall header in front of its columns | L-9 (remaining part) |
| `fd5776b` | Smoke cloud presentation; concealment shrinks with dissipation | Visual review's "spherical smoke" defect |
| `82ce83f` | Contact occlusion and distance haze | Floating-cargo look on Low; depth separation |
| `2237780`, `b477fa7`, `f8ca47f` | Design-system document, documentation corrections, post-fix probes, this report and evidence | — |
| `9c04d59` | Fixes for the separate reviewer's findings (§7): one-way smoke, client smoke fade, display-name injection, saved touch layouts, interrupted-fire carry, `/history` offsets | R-1, R-2, R-4, R-6, R-9, R-10 |

37 files changed across the branch before this report. No new runtime dependencies, assets with external licenses, or fonts. The economy remains earned-currency only; reward generation is unchanged and still server-committed before any client reveal.

### Not changed (left for Codex or a design decision)

- **M-4** Snapshots broadcast every actor's position and the device carrier to every client (`snapshot_exposes_enemy_positions_and_carrier = true`, 735 B deflated). Fixing it needs per-client visibility culling in the protocol; Codex owns `match.gd` networking. The new radar deliberately never displays opponents, and `ux_contract_test.gd` enforces that, but a modified client can still read the data.
- **M-6** No interpolation buffer or client prediction. `docs/network.md` now describes the actual behavior instead of claiming interpolation.
- **M-9** Rejected or idle ENet peers are not disconnected.
- **M-2 (death)** Weapons still survive death into the next round. Whether dead players drop weapons is a game-design decision, not a defect I should decide; halftime now resets loadouts.
- **L-4** Input gate still drops a newer packet within 12 ms. **L-7** One inactive participant still voids rewards for everyone. **L-8** Crouch still squashes the whole model (hit volumes now follow the squash). **L-10** Bot navigation cost unchanged (110 µs/call).
- **R-3 (reviewer)** Since Codex's review (blocker 2), the body hit volume is exactly the 0.3 movement capsule below the drawn torso top, so body hits never exceed 0.3.0's. It still does not follow the drawn legs and arms: it adds empty air around the legs and misses the outer upper arms. Per-limb volumes would change time-to-kill, so they are a balance decision. See [CODEX_REVIEW_RESPONSE](CODEX_REVIEW_RESPONSE.md).
- **R-5 (reviewer)** Halftime funds (1,200) still afford an SMG (1,100), so bots rebuy at once after the loadout reset. Whether the second half should open with pistols only is an economy decision.
- **R-7 (reviewer)** Resolved in Codex review blocker 3. A protocol version handshake runs before any gameplay RPC; mismatched builds are refused with a reason or dropped at a 5 s timeout. Unmodified 0.3.0 clients still run their own reconnect loop after the drop.
- Operator and weapon models, materials and animation were not reworked; they remain the largest visual gap.

## 2. Verification

All on the same host as the audit (4 vCPU cloud container, Godot 4.7.2 official, Xvfb + Mesa llvmpipe 25.2.8, PostgreSQL 16.15 instead of the pinned 17). The full matrix passed on `82ce83f`, then again on the tree with the reviewer fixes (§7):

| Suite | Baseline `e67f2c8` | Branch | Result |
| --- | --- | --- | --- |
| `scripts/validate.sh` native assertions | 443 | **1,915** (+28 weapon integrity, +40 hit volume, +21 render budget, +26 smoke presentation, +30 UX contract, +1,327 HUD overflow) | exit 0, no script errors |
| Natural bot match (`validate.sh`) | 12 rounds, 5–7 | 10 rounds, 3–7, 64 kills, halftime, plant, one report | pass |
| Backend PostgreSQL tests | 39 | **48** (+9) | 48 passed |
| `test_native_economy.py` (real HTTP) | 14/14 | 14/14 | pass |
| `test_render.sh` (native lifecycle + cosmetic lifecycle) | 11 + 19 | 11 + 19, texture bytes flat | pass |
| `test_account_network.py` | pass | pass | pass |
| `test_bridge_transport.py` | pass | pass | pass |
| `test_reward_bridge.py` | pass | pass (10 wallets, 10 grants, replay minted nothing) | pass |
| Migrations on a fresh database, applied twice | 1–3 | 1–4, idempotent; planner uses `ix_listings_active_price` | pass |

### Audit probe, before → after

`docs/audits/probes/audit_probe.gd` and `backend_probe.py` re-run unchanged against the branch. `verification_probe.gd` is new: the original probe hard-codes the 0.3 headshot rule, so it cannot measure the new path.

| Measurement | Baseline | Branch |
| --- | --- | --- |
| SMG / rifle effective fire rate vs data | −15.0 % / −10.0 % | −0.1 % / −0.1 % |
| Marksman second shot after quick-switch | 0.367 s (designed 0.82 s) | 0.833 s (same as without switching) |
| Spread sequence identical after round reset | true (seed = id·7919+103) | false (crypto-random seed) |
| Recoil pattern after full recovery | continued mid-pattern | restarts (identical bursts) |
| Head cells counted / drawn, standing | 1398 / 599 (2.33×), 799 outside silhouette | 577 / 599 (0.96×), **0 outside** |
| Head cells counted / drawn, crouched | 1774 / 863 (2.06×) | 852 / 863 (0.99×), **0 outside** |
| Smoke thrown onto a container | cloud centre inside the container | rests 1.6 m above the roof surface |
| Loadout after halftime | rifle retained | sidearm only, 1200 funds |
| `_begin_round()` with nine bot purchases | 228.9 ms | 0.9 ms |
| First-person rifle build | 27.09 ms, meshes not shared | 0.06 ms, shared |
| Actor construction | 45.14 ms | 0.68 ms |
| Cosmetic shader per finish | new program each call | one shared program |
| Arena batches / shadow-casting batches | 75 / 75 | 9 / 4 (793 of 1472 instances cast) |
| `/market?rarity=Mythic` behind 500 cheaper listings | 0 results, 247.3 ms | 1 result, 29.9 ms |
| Non-ASCII server key | HTTP 500 | HTTP 403 |
| Login median, wrong password vs unknown user | 83.9 vs 12.0 ms | 154.3 vs 150.0 ms |
| Snapshot size; opponents exposed | 732 B; yes | 735 B; **yes (M-4 open)** |
| Input gate drops newer bunched packet | true | **true (L-4 open)** |

The login timings are both higher because unknown users now pay a full Argon2 verification and the probe shared the host with other work; the point is the gap, not the absolute value.

### Rendering benchmark (fixed cameras, three runs each, `scripts/profile_render.sh`)

Software rendering on two pinned CPU cores. Draw calls and primitives are exact and device-independent; frame times are **llvmpipe CPU rasterization, not phone FPS**.

| View | Standard draws | Standard primitives | Standard median frame | Low draws | Low median frame |
| --- | --- | --- | --- | --- | --- |
| approach | 444 → 152 (−66 %) | 136,954 → 78,274 (−43 %) | 488.1 → 398.1 ms (−18.4 %) | 170 → 106 (−38 %) | 92.4 → 91.1 ms (−1.4 %) |
| site | 239 → 45 (−81 %) | 63,966 → 40,522 (−37 %) | 427.6 → 351.1 ms (−17.9 %) | 90 → 37 (−59 %) | 75.4 → 80.3 ms (+6.5 %) |
| overview | 451 → 166 (−63 %) | 120,622 → 75,674 (−37 %) | 417.4 → 344.1 ms (−17.6 %) | 185 → 120 (−35 %) | 89.2 → 91.1 ms (+2.1 %) |
| operators | 383 → 138 (−64 %) | 113,648 → 75,024 (−34 %) | 464.5 → 389.4 ms (−16.2 %) | 156 → 92 (−41 %) | 85.3 → 84.8 ms (−0.6 %) |

- **Standard** gets cheaper because thin and ground-level geometry stopped rendering into two shadow cascades.
- **Low** has no sun shadows, so that saving does not apply. Its frame times are unchanged within run-to-run spread (individual run medians vary by 5–10 ms). Low primitives rose by 1–8 % from the contact-occlusion mesh. Fewer draw calls should help a mobile driver more than llvmpipe, but that is **unverified**.
- 3D render scale 0.75 cut Standard llvmpipe medians by 25–35 % with the HUD at native resolution. Device benefit is unverified.
- **Smoke probably costs more per frame.** The smoke cost probe, run three times per side, gave median added frame time of +22.0 ms (Standard) / +37.6 ms (Low) for the new cloud vs +8.0 / +0.6 ms for the old one. Run-to-run ranges overlap (old −25 to +108 ms, new +22 to +74 ms), so the size is uncertain; every new-cloud run added time. Low does not help because both presets share the core. An opaque Low core variant was tried, measured no saving, and was dropped. The `fd5776b` commit message's "~17 vs ~6 ms" came from single runs and overstates the certainty. Measure on a device. Details: the [evidence README](../reports/media/claude-v04/README.md).

Raw summaries: `docs/reports/media/claude-v04/benchmarks/`.

## 3. Visual and UX evidence

Before/after captures were rendered by the **same scripts** against the archived baseline and the branch in the same session. See [`docs/reports/media/claude-v04/README.md`](../reports/media/claude-v04/README.md) for the file list, commands, hashes and what each pair shows.

- **Smoke:** the 0.3 core read as one opaque sphere. The branch draws a lobed cloud with a soft, noisy rim and textured edge puffs. An operator standing behind the cloud leaks **0** changed pixels in both versions (concealment unchanged), and the view from inside stays an even fog (luminance standard deviation 0.052 → 0.053). Concealment now shrinks with the visible cloud during the final 1.5 s.
- **Signage:** container "FREIGHT" and hall "TRANSFER" lettering no longer clip into ribs and columns; a test asserts no box face lies in front of the header.
- **Grounding and haze:** grounded solids get a soft contact shadow even on Low; distance haze starts at 34 m, beyond in-yard sightlines.
- **HUD:** radar (self, teammates, sites, known device; never opponents), alive pips, squad marker, kill feed, health bar, utility counts, spread-accurate reticle.
- **Known blemish:** at 960×720 the HUD utility line ("FRAG ×1  SMOKE ×1  FUNDS") sits partly over the sidearm viewmodel's grip. It stays legible in the capture; phone readability is unverified.
- **Armory:** visible selected tab; trade confirmation lists exactly what each side gives and receives, with wear and pattern, the partner's name, the revision, and a gift warning when one side gives nothing; market confirmation identifies the exact instance.

The design system and review checklist are in [`docs/design/DESIGN_SYSTEM.md`](../design/DESIGN_SYSTEM.md).

## 4. Scores after this branch

Same rubric as the audit: **5** = happy path works with significant verified defects; **7** = coherent, several Medium defects, mostly happy-path tests; **8.5** = no open High defects, Mediums tracked, adversarial tests for the main failure modes, runtime evidence; **10** = exceptional. **UNVERIFIED** = no runtime evidence for that dimension.

| Category | Baseline | Branch | Basis | Not established |
| --- | ---: | ---: | --- | --- |
| Architecture & maintainability | 6.5 | 6.5 | Shared tokens, radar extracted, procedural meshes cached. But `main.gd` is still ~1,100 lines and `match.gd` is unchanged. | — |
| Gameplay correctness | 6.0 | 7.5 | No open High. Fire rate, switching, head volume, body volume (never wider than 0.3.0's), spread, recoil, smoke placement and halftime are measured and regression-tested. | Human gunplay feel and balance **UNVERIFIED**; the H-2 headshot-area change and the crouched helmet need a design decision; body volume vs drawn limbs (R-3) and death-drop rule open |
| UI/UX | 6.5 | 7.5 | U-1–U-6, M-10, M-11, L-3 closed with contract tests and native captures at four ratios. | Phone readability, touch feel, accessibility audit **UNVERIFIED** |
| Visual quality | 6.6 | 6.9 | geometry 7.0, materials 6.5, lighting 7.0, models 6.0, effects 7.0, identity 7.5, readability 7.5 | Device rendering **UNVERIFIED**; operator/weapon art unchanged |
| Animation | 6.0 | 6.0 | Not worked on. Stills only. | Motion review **UNVERIFIED** |
| Performance | 5.5 | 6.5 (desktop diagnostic) | Round-start hitch gone; Standard draws −63–81 %, frame −16–18 % on llvmpipe; render-scale option. Low unchanged in frame time. | **Device FPS, thermals, battery UNVERIFIED** |
| Security | 7.5 | 8.0 | M-5, M-7, M-8, L-1, L-2 closed with tests. | M-4 info exposure and M-9 open; production controls absent |
| Networking | 6.0 | 6.5 | Version handshake before any RPC, with a real-process mixed-version matrix; terminal failures and bounded join time. Kill feed RPC added. | M-4, M-6, M-9 (admitted idle peers), L-4 open |
| Economy integrity | 8.5 | 8.5 | Read path fixed; no value-creation path found before or after. | Production load **UNVERIFIED** |
| Stability | 8.0 | 8.0 | Every suite green; texture lifecycle flat. | Device lifecycle and soak **UNVERIFIED** |

No category reaches 8.5 except economy integrity, which already did. The scores rise only where a measured defect was removed and is now covered by a test.

## 5. Risks for integration

1. **`main.gd` was substantially rewritten** (UI construction only; the input pipeline is unchanged). Any concurrent Codex change to `main.gd` will conflict. Merge this branch first or rebase Codex's UI work onto it; do not resolve by taking either side wholesale.
2. **Arena batching changes how surface materials are shared.** Boxes in one family now share one vertex-color material with albedo as an instance color. Code that mutates a single box's material at runtime would now affect its whole family. No current code does this (`world_test`, `render_budget_test` and the cosmetic suites pass), but new effects must use instance colors or a separate material.
3. **Packed body/weapon scenes are cached in static variables** for the process lifetime. Roles are found by node metadata (`body_role`, `weapon_role`), so new parts that need per-instance animation must carry a role and avoid being merged.
4. **Hit volumes now come from the drawn head.** If Codex changes the head or helmet mesh dimensions, update `SBActor.HEAD_VOLUMES` (the body is built from the same constants); `weapon_integrity_test.gd` will fail otherwise.
5. **Smoke frame cost** is probably higher than before (§2) and the Low preset does not reduce it. Measure on a device; if it matters, simplify the core shader (it samples the noise texture three times per pixel) rather than going back to the sphere.
6. **The kill feed adds one reliable authority RPC per elimination.** It carries only actor IDs and a headshot flag, all public at that moment. Builds with different RPC tables are refused by the protocol handshake (`PROTOCOL_VERSION` 2; bump it with any RPC or snapshot change). 0.3.0 clients and servers cannot join this build. Utility snapshots gain an optional `life` field.
7. **Rate limiting no longer takes the global advisory lock.** The economy write path still does. A new partial index on `listings(price, id) WHERE state='active'` (migration 004) must be applied with `backend/migrate.py` before deploying the new `/market`.

## 6. Instructions for Codex review

Review one commit at a time; each is scoped to one area. The gameplay, backend, rendering and HUD commits each passed `validate.sh` when they were made (six of the HUD commit's suites were also re-run from a clean `git archive` of that commit, to rule out uncommitted files), and the full matrix passed on `82ce83f` and on the branch head.

1. Re-run the matrix on your host: `validate.sh`, backend pytest, `test_native_economy.py`, `test_render.sh`, `test_account_network.py`, `test_bridge_transport.py`, `test_reward_bridge.py` (commands in §8).
2. Re-run `docs/audits/probes/audit_probe.gd`, `verification_probe.gd` and `backend_probe.py`, and compare with §2. Structural numbers (counts, ratios, booleans) should match exactly; timings will vary by host.
3. Check `81d16b2` against your design intent for weapon switching. The existing 0.3 s equip delay is now a separate deploy timer, and each weapon keeps its own cooldown while holstered, so switching can no longer skip a cooldown. To change the deploy time, edit `SBActor.DEPLOY_SECONDS`; `weapon_integrity_test.gd` reads it.
4. Check `d906c17` visually in your native capture flow. If any text, color or layout decision conflicts with your direction, the tokens in `design_tokens.gd` are the single place to change it.
5. Contest any score in §4 or any finding in the audit that your evidence does not support.
6. Decide the open items: M-4 visibility culling, M-6 interpolation/prediction, M-9 peer cleanup, the death-drop rule, L-7 reward voiding.

Do not merge on the strength of this report. Merge only after your own re-run and review.

## 7. Separate reviewer pass

A second agent, the same model family as the author, was given read-only access, the audit and the diff `e67f2c8..f8ca47f`. It was told to look for real, reproducible defects and to mark each claim VERIFIED (run) or INFERRED (read). It reviewed an exact `git archive` of the branch, re-ran every Godot suite and the backend tests, and wrote its probes outside the repository. This adds an adversarial pass, but it is **not** independent review: it shares the author's training and blind spots.

It reported ten findings and listed what it checked and found clean. Every finding was re-checked before acting; the fixes are in `9c04d59`.

| # | Severity (reviewer) | Finding | Status | Evidence after the fix |
| --- | --- | --- | --- | --- |
| R-1 | Medium, VERIFIED | One-way smoke: the shader treated the camera as "inside" only within 2.09 m of the centre, but the lobed mesh reaches about 2.9 m. From inside a side lobe you could see out while others could not see in. **Introduced by this branch.** | **Fixed.** One `CORE_LOBES` table now builds the mesh and generates the shader's inside test (every lobe, widened by the billow amplitude); `core_contains()` mirrors it in GDScript. | `smoke_presentation_test`: every vertex of the billowed core is covered and the test stays within 3.2 m. Native: looking out of the side lobe, 59,339 marker pixels before the fix (equal to the no-smoke control), **0** after; Standard and Low concealment still 0 leaked pixels. |
| R-2 | Medium, VERIFIED | Network clients never fade smoke: replica physics is off, so their lifetime never counts down, while the server's concealment shrinks. **Introduced by this branch** (dissipation was new). | **Fixed.** Snapshots carry each utility's remaining lifetime (`life`, optional); replicas apply it. | `smoke_presentation_test`: a replica at half lifetime has 0.5 opacity, matching the server; snapshots without the field leave it unchanged. |
| R-3 | Medium, VERIFIED | The body hit volume does not match the drawn operator: it adds empty air around the legs, misses the outer upper arms, and is 1.78× larger than the drawn body from the side. | **Open; predates this branch.** The 0.3 capsule had the same 0.31 m radius. After Codex's blocker 2 the body is exactly that capsule below the torso top, never wider than 0.3.0. Per-limb volumes would change time-to-kill and are a balance decision for Codex and design. | Recorded as an open finding. Section 2's "matches what is drawn" applies to the head only. |
| R-4 | Medium, VERIFIED (backend) / INFERRED (UI) | Display names can contain newlines and control characters. The newly exposed `names` let a name inject a fake "YOU RECEIVE" block into the trade confirmation. **Exposure introduced by this branch.** | **Fixed.** The server rejects names containing control, format (bidi) or line/paragraph-separator characters. The client flattens names to one line and quotes them in trade terms. Guest names in matches are cleaned the same way on the server. | Backend test: five forged names get 422 and ordinary Unicode names get 201. UX test: a spoofed name stays one quoted line and the dialog has exactly one "YOU RECEIVE" block. |
| R-5 | Low, VERIFIED | After the halftime reset, bots with 1,200 funds immediately buy an SMG (1,100), so the "pistol round" is not one. | **Open; design decision.** Funds and prices are unchanged. The reset now removes carried weapons as intended; whether the second half should open with pistols only is an economy-tuning call. | — |
| R-6 | Low, INFERRED | Layouts saved under 0.3 keep the old TEAM/BUY positions, which the new radar covers. **Introduced by this branch.** | **Fixed.** Saved positions equal to the retired defaults follow the new defaults. Positions the player chose are kept. | UX test: untouched 0.3 positions move below the radar; custom and moved positions stay. |
| R-7 | Low, INFERRED | Adding `_elimination_rpc` shifts Godot's name-ordered RPC IDs. With no protocol version check, a 0.3 client on this server would misroute RPCs silently. | **Fixed later (Codex blocker 3).** A version handshake in SceneMultiplayer authentication runs before any RPC. | `scripts/test_protocol_compat.sh`: six pairings pass. |
| R-8 | Low | Some new checks were circular. The head test compared the constants with a head built from them, nothing compared the body with the drawing, and the smoke tests missed R-1 and R-2. | **Improved.** The head test now measures the rendered head mesh and the tallest rendered body point (the helmet crown), with 1 cm tolerance: the drawn head is a 12-segment sphere about 4 mm inside the ideal ellipsoid. R-1 and R-2 have regression tests. The body still has no drawn-geometry test (R-3). | `weapon_integrity_test` 28 checks. |
| R-9 | Nit, VERIFIED | Holding the trigger through a reload banked one tick: the first rifle interval after it was 0.100 s instead of 0.105 s. | **Fixed.** A cooldown a whole tick or more overdue carries nothing. | New check fails before the fix (0.100 s) and passes after. Sustained rates are unchanged. |
| R-10 | Nit, INFERRED | `/history` ordered `ended_at` as text, which is only correct while every server reports UTC. | **Fixed.** It orders by the value cast to `timestamptz`. | Backend test with a +05:00 server time fails under text order and passes now. |

The reviewer also confirmed, by running code, that sustained fire matches the weapon data and swaps cannot shorten an interval. It found no null access when an actor dies mid-trace, `_elimination_rpc` cannot be exploited, cached meshes and materials are never mutated per actor, and graphics-quality switching updates all batched materials. On the backend it confirmed SQL filters keep the old semantics, the rate limiter is exact under concurrency (140 reads → 120 × 200 and 20 × 429), and login timing is equal (140.2 vs 142.0 ms). In the UI, every baseline setting is still present and pause edge cases behave.

## 7a. Codex review (REQUEST CHANGES at `e018a65`)

Codex confirmed many improvements and raised three blockers: kill-feed HUD overflow, a body hit-volume regression at foot level, and mixed-version protocol stalls. All three were reproduced, given failing regression tests and fixed in `89a743a`, `6e144a0` and `cf9a630`. Root causes, evidence, the full regression run, the design decisions left to Codex (the crouched helmet and H-2's headshot-area change) and the second review are in [CODEX_REVIEW_RESPONSE.md](CODEX_REVIEW_RESPONSE.md).

## 8. Reproduction

```sh
SIGHTBREAK_TOOLS_DIR=<tools> ./scripts/validate.sh                                   # 1,915 native assertions
DATABASE_URL=postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/<name>_test \
  PYTHONPATH=backend .venv/bin/pytest backend/tests -q                                # 48 tests
.venv/bin/python scripts/test_native_economy.py                                       # 14/14
DISPLAY=:99 ./scripts/test_render.sh                                                  # 11/11 + 19/19
DISPLAY=:99 ./scripts/profile_render.sh <out> standard|low                            # §2 benchmark
./scripts/godot.sh --headless --script "$PWD/docs/audits/probes/audit_probe.gd"       # §2 probe
./scripts/godot.sh --headless --script "$PWD/docs/audits/probes/verification_probe.gd"
DISPLAY=:99 ./scripts/godot.sh --audio-driver Dummy --script res://tests/smoke_visual_capture.gd -- --capture-dir=<out>
DISPLAY=:99 ./scripts/godot.sh --audio-driver Dummy --script res://tests/landscape_ui_test.gd -- --capture-dir=<out>
DISPLAY=:99 ./scripts/godot.sh --audio-driver Dummy --script res://tests/hud_overflow_test.gd -- --capture-dir=<out>
./scripts/test_protocol_compat.sh <out>                                              # six real-process pairings
./scripts/test_handshake_hardening.sh <out>                                          # eight hostile-peer handshake checks
```
