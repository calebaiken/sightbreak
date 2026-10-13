# Response to Codex's PR #1 review (REQUEST CHANGES at `e018a65`)

Three blocking findings, fixed in three focused commits on `claude/independent-audit-visual-v04`, plus five follow-up commits from the second review (see the end of this document). Each defect was reproduced first, and each regression test was confirmed failing on the commit before its fix. The full matrix was then re-run on the final head, `d0278f0`. Evidence is in [`docs/reports/media/claude-v04/codex-review/`](../reports/media/claude-v04/codex-review/README.md). Nothing here is merged and no release readiness is claimed.

| Blocker | Commit | Regression test | On reviewed head | After fix |
| --- | --- | --- | --- | --- |
| 1 · Kill-feed HUD overflow | `89a743a`, `ff41188`, `d0278f0` | `game/tests/hud_overflow_test.gd` | 49 of 436 checks fail | 1,327/1,327 headless, 1,333/1,333 native with captures |
| 2 · Body hit-volume regression | `6e144a0`, `fc52e68`, `5407325` | `game/tests/hit_volume_test.gd` | 8 of 33 fail | 40/40 |
| 3 · Mixed-version protocol stall | `cf9a630`, `a84b208` | `scripts/test_protocol_compat.sh`, `scripts/test_account_network.py`, `scripts/test_handshake_hardening.sh` | mixed pairs stall in "joining" for the full 15 s window | 6/6 pairings and 8/8 hostile-peer checks behave as specified |

## Blocker 1 — kill-feed HUD overflow

**Reproduced.** At 960×720, two 24-character names put the ammunition and utility labels at x = 611 with a 577 px width, off the right edge. The score moved left of centre and the feed ran under the MENU button. At 130 % text, the score also shifted at 1280, 1560 and 1600 px wide.

**Root cause.** Each feed row was a non-wrapping `HBoxContainer` of name labels, so its minimum width was the full text width. Container minimum sizes propagate upward through the side column, the top row and the HUD margin container. Those grew past the viewport and pushed everything anchored to the right. The `.left(16)` character cut did not bound the rendered width; wide glyphs and CJK are much wider per character.

**Fix (`game/scripts/main.gd`):**
- **Frame:** the feed lives in a plain `Control` (`KillFeedFrame`), whose minimum size ignores its children. Its height is measured in the tree for exactly four rows at the current text size, and it clips as a backstop. No feed content can resize the HUD.
- **Name width:** names keep their natural width when they fit; otherwise they share the remaining width. Each name is cut to the longest prefix that fits, measured in the label's own font, with an explicit "…". Godot's built-in overrun was dropped because natively it omitted the ellipsis whenever the cut text exactly filled the width.
- **Cluster safety:** cuts fall only on grapheme boundaries reported by the text server. Combining marks, Indic conjuncts, Thai clusters, flags and keycap sequences stay whole (`ff41188`; the earlier mark-only rule split Devanagari conjuncts).
- **Compact marker:** when space is tight, "HEADSHOT" becomes a gold "HS" before any name is cut. It is still text, so the headshot is not signalled by colour alone.
- **Sanitising:** names pass through `SBDesign.plain_line()`.
- **Unchanged:** text size is not reduced, and touch layouts and accessibility settings behave as before.

**Verified.** The test covers 960×720, 1180×820 (tablet), 1280×720, 1560×720 and 1600×720, at 100 % and 130 % text, with ordinary names, 24-character names (the server's limit) and Unicode/CJK names. Per case it checks:
- the score stays centred and does not move when rows arrive;
- ammo, utility, health, score and radar stay on screen;
- the feed stays on screen and clears the score, radar and MENU button;
- every row is fully visible and every name is drawn whole or as a prefix ending in "…";
- ordinary names are never shortened;
- every cut lands on a grapheme boundary (accents, Devanagari, Thai, flags and keycaps);
- a name built from stacked combining marks keeps every row one line tall (`d0278f0`).

Before and after native captures are in `codex-review/hud/`. Landscape (144), UX contract (30), main (35) and touch (34) suites are unchanged.

## Blocker 2 — body hit-volume regression

**Reproduced with identical rays in three builds.** `docs/audits/probes/hit_grid_probe.gd` was run in an untouched `git archive` of 0.3.0, the reviewed head and this tree, on 1 cm cell centres:
- **Views:** front and side, standing and crouched, plus rays plunging from 2.5 m.
- **0.3.0:** scored by its own rule, a physics ray against the movement capsule with a headshot above `head_height − 0.25`.
- **PR builds:** scored by `trace_shot`.

At 5 cm above the floor, 0.3.0 registers hits across x = ±16 cm and the reviewed head across ±30 cm. In total the reviewed head scored 2,885 cells where 0.3.0 missed, all at foot and shin level.

**Root cause.** 0.3.0's hitbox was the movement capsule: radius 0.31 m, height 1.8 m (1.25 m crouched), with rounded ends. The PR replaced the body with a flat-bottomed 0.31 m cylinder, which fills the corners of the capsule's rounded bottom.

**Fix (`game/scripts/gameplay/actor.gd`).** The body volume is now exactly the movement capsule, read from the live collision shape at the current stance and cut off at the drawn torso top (`BODY_TOP × crouch squash`):
- The ray is intersected analytically (cylinder ∪ caps, overlapped with the half-space). Grazing rays miss, as they do against the physics capsule.
- The head and helmet ellipsoids built from the drawn head are unchanged.
- World-before-actor ordering, nearest-actor selection and pass-through of empty volume space are unchanged.

**Verified (`hit_volume_test.gd`, 40 checks; `compare_hit_grids.py`; the grid probe gives cell-for-cell identical results on the final head):**

| View | 0.3.0 head / body cells | Reviewed head | Now | Hit where 0.3.0 missed (now) |
| --- | --- | --- | --- | ---: |
| Standing, front | 2,256 / 8,084 | 1,190 / 8,556 | 1,190 / 8,146 | **0** |
| Standing, side | 2,256 / 8,084 | 1,217 / 8,556 | 1,217 / 8,146 | **0** |
| Plunging (feet), every view | 0 / 3,484 | 0 / 3,720 | 0 / 3,484 | **0** |
| Crouched, front | 1,884 / 5,046 | 858 / 6,138 | 858 / 5,728 | 146 (all headshots, see decision 1) |
| Crouched, side | 1,884 / 5,046 | 882 / 6,138 | 882 / 5,728 | 155 (all headshots) |

The in-process test scores every ray both ways: physics against the actual layer-2 capsule (0.3.0's hitbox), and `trace_shot`. It asserts:
- no body hit exists where the capsule missed;
- every capsule hit below the drawn torso top still hits;
- the only extra area is the drawn crouched helmet.

It also runs specific foot, shin, torso, edge (±1 cm), head and crouched rays, plus a ray past rounded feet that reaches the operator behind and a wall that blocks the shot. Five analytic rays (`fc52e68`) pin tangent behaviour: a ray exactly on the radius, under the rounded bottom or along the side misses, as it does against the physics capsule. Before that commit, 32-bit rounding let two of them hit. Since `5407325` the spans work in 64-bit floats. 4,000 seeded rays from 40–140 m match an exact line-to-segment distance wherever the surface is more than 0.05 mm away, and an 86° ray just inside the wall hits. The weapon integrity, actor, hit feedback and match suites, and the head-area probe (577/599 standing, 852/863 crouched, 0 cells outside the drawn head), are unchanged.

**Decisions for Codex and design (not chosen silently):**
1. **Crouched helmet vs 0.3.0 capsule.** The drawn crouched helmet reaches 1.29 m, but the 0.3.0 crouched capsule tops out at 1.25 m, and its rounded top reaches only about 0.12 m from the centre line at 1.22 m. So 146–155 cm² of drawn helmet (front/side) is a headshot now and a miss in 0.3.0. This build keeps the drawn helmet hittable, to avoid shoot-through on visible geometry. The alternative, intersecting the head volumes with the capsule, is a two-line change that restores exact 0.3.0 coverage but makes that part of the visible helmet shoot-through.
2. **H-2 changes headshot area; it was not a regression fix.** This was audit finding H-2 and is not new in this response, but it is a real balance change and needs explicit acceptance:
   - Standing headshot area drops from 2,256 to 1,190 cm² (−47 %); 1,004 cm² of air beside the head that 0.3.0 counted as headshots now misses.
   - A 1 cm band at 1.37–1.38 m (62 cm²) changes from headshot to body.
   - Crouched, the shoulder band at 0.88–0.99 m (682 cm²) changes from headshot to body damage.
   - Total hit area falls 9.7 % standing and 5.0 % crouched; the body hit area never exceeds 0.3.0's.
   - Restoring 0.3.0's headshot behaviour means reverting H-2.

## Blocker 3 — mixed-version protocol stall

**Reproduced with real processes.** The dedicated-server and client processes are separate, and 0.3.0 comes from an untouched `git archive`:
- Same-version pairs joined in 0.5–0.8 s.
- Both mixed pairings logged "The rpc node checksum failed" and stayed in "joining" for the whole 15 s observation window. Before this fix nothing ended that state.

**Root cause.** Godot dispatches RPCs by method index in name order. `_elimination_rpc` sorts right after `_buy_rpc`, so it shifts every later index, including `_join_rpc`, `_snapshot_rpc` and `_welcome_rpc`. With no version check, nothing told either side.

**Why not only restore the 0.3.0 RPC table?** Removing `_elimination_rpc` and moving kill events into snapshots would let today's two builds interoperate. But the next RPC change would fail the same silent way, and nothing would detect it. A handshake that runs before, and independently of, the gameplay RPC table prevents the whole class.

**Fix (`game/scripts/gameplay/match.gd`).** A version handshake in SceneMultiplayer's authentication stage. Godot does not admit a peer, and so does not let it exchange RPCs, until both sides complete authentication. It is documented in `docs/network.md`.
- **Hello:** both sides exchange a bounded (≤ 512 B), type-checked JSON hello with `PROTOCOL_VERSION`: 2 now, with 0.3.0 implicitly having none. Only an exact whole-number match is admitted, and a peer's first hello decides (`a84b208`).
- **Mismatch:** a mismatched peer receives the reason, is never admitted, and is dropped about 0.5 s later. `_join_rpc` never runs, so no join ticket is consumed and no slot is allocated.
- **No hello (0.3.0 clients, foreign traffic):** dropped at the 5 s authentication timeout.
- **No answer (0.3.0 servers):** the client gets a specific, terminal message.
- **Bounded waits:** connecting, authenticating and joining are capped at 20 s on the client. Failures are terminal, with no reconnect loop, and a later generic `connection_failed` no longer overwrites the specific reason.
- **Unchanged:** reconnect of an established session works as before (`test_network.sh` reclaims both slots).

**Verified.** `scripts/test_protocol_compat.sh` asserts every pairing, including a protocol-bumped copy of this build standing in for the next incompatible release:

| Client | Server | Expected | Observed | Result | Last message shown to the player |
| --- | --- | --- | --- | --- | --- |
| 0.3.0 (e67f2c8) | 0.3.0 (e67f2c8) | join | joined after 0.50 s | PASS | Round live. Secure Relay Yard. |
| this branch (protocol 2) | this branch (protocol 2) | join | joined after 0.28 s | PASS | Round live. Secure Relay Yard. |
| 0.3.0 (e67f2c8) | this branch (protocol 2) | server drops pre-handshake client | never admitted; dropped 3x by the server, first after 5.1 s; 0.3.0 client retries on its own | PASS | Connecting to Relay Yard… |
| this branch (protocol 2) | 0.3.0 (e67f2c8) | client reports missing handshake | failed after 5.1 s, no retries | PASS | No version handshake from the server within 5 seconds. It is probably running an older SIGHTBREAK release (0.3.0 has no handshake) or is not a SIGHTBREAK server. Join a server running the same version as this client. |
| next build (protocol 3) | this branch (protocol 2) | explicit mismatch | rejected after 0.2 s with the reason shown | PASS | Version mismatch: this client uses SIGHTBREAK network protocol 3. This server uses network protocol 2; this client sent protocol 3. Install the same SIGHTBREAK version as the server to join. |
| this branch (protocol 2) | next build (protocol 3) | explicit mismatch | rejected after 0.2 s with the reason shown | PASS | Version mismatch: this client uses SIGHTBREAK network protocol 2. This server uses network protocol 3; this client sent protocol 2. Install the same SIGHTBREAK version as the server to join. |

`test_account_network.py` adds a protocol-99 client that presents the join ticket first. It is rejected in 0.68 s, and the same ticket then binds the real client to slot 1. That proves the rejected attempt consumed neither the ticket nor a slot. Guest rejection, replay rejection and account reclaim are unchanged.

**Limitation (cannot be fixed retroactively).** An unmodified 0.3.0 client cannot display a message it does not know. The server drops it at 5 s every time; the 0.3.0 client then runs its own reconnect loop, which only a client update can change.

## Full regression run (commit `d0278f0`)

Same host, PostgreSQL 16.15 (the repository pins 17), Xvfb/llvmpipe. Each suite was run once on the committed head; the counts are actual output, not targets (`codex-review/matrix-d0278f0.log`, `validate-d0278f0.log`).

| Suite | Result |
| --- | --- |
| `scripts/validate.sh` | exit 0: **1,915** native assertions (previously 548; +40 hit volume, +1,327 HUD overflow), a natural 10-round bot match, and two ENet clients with reconnect |
| Backend PostgreSQL tests | **48 passed** |
| `scripts/test_native_economy.py` (real HTTP) | 14/14 |
| `scripts/test_render.sh` (renderer lifecycle) | 11/11 + 19/19, texture bytes flat across cycles |
| `scripts/test_account_network.py` | pass, including the new incompatible-protocol case |
| `scripts/test_bridge_transport.py` | pass |
| `scripts/test_reward_bridge.py` | pass — 10 exact wallets, 10 ledger grants, replay minted nothing |
| `scripts/test_protocol_compat.sh` | **PASS**, all six pairings |
| `scripts/test_handshake_hardening.sh` | **PASS**, 8/8 hostile-client and hostile-server checks (7/8 fail on `fc52e68`) |

No existing assertion was removed or loosened. The new tests failed on the reviewed head as described above. Software-render timings and captures are not device evidence: Android/iOS frame rate, thermals and touch feel remain **UNVERIFIED**.

## Second review

## Second review

A second Claude agent reviewed the final blocker fixes adversarially. It wrote its own probes and attack harnesses rather than rereading these tests. It is the same model family as the author, so this is **not independent acceptance**; Codex's review remains the gate.

- **First attempt:** an environment restart interrupted it before its report. Its recovered probes found two defects, both fixed with regression tests:
  - truncation split Devanagari conjuncts, Thai clusters, flags and keycaps (`ff41188`);
  - 32-bit rounding let rays that only touch the capsule register hits (`fc52e68`).
- **Second attempt:** it reviewed `fc52e68` in full and found **no blocking defect**. It confirmed the defects below by reproduction, and all of them are fixed here.

| Finding (reviewer's severity) | Reproduction | Fix | Regression test (fails before → passes after) |
| --- | --- | --- | --- |
| Long-range precision (non-blocking): at 70–100 m the capsule caps used 32-bit `Vector3.dot`, so body hits landed up to 3.7 mm outside the 0.3.0 capsule and hits up to 3.1 mm inside were lost | 20k rays per range against exact geometry | `5407325`: 64-bit closest-approach spans | `hit_volume_test.gd`: 4,000 seeded 40–140 m rays (4 extra and 3 lost → 0) |
| Steep-ray margin (note): the tangent margin scaled with pitch, so an 86° ray 0.3 mm inside the wall missed | crafted rays | `5407325` | `hit_volume_test.gd` steep ray (miss → hit) |
| Hello flood (non-blocking): each hello re-armed the 0.5 s drop, so 14,560 hellos drew 14,520 replies and log lines and held the slot to the 5 s timeout | hostile client | `a84b208`: first hello decides, later ones are ignored | `test_handshake_hardening.sh spam` (14,520 replies, 5.02 s → 1 reply, 0.53 s) |
| Ordering (note): a mismatched hello followed by a good one was admitted; a good one followed by a bad one logged a rejection and an engine error, then was admitted | hostile client | `a84b208` | `bad_then_good` (admitted → dropped at 0.53 s), `good_then_bad` (1 error → 0) |
| Fractional protocol (note): 2.9 was truncated to 2 and admitted; 1e400 logged as INT64_MIN | hostile client | `a84b208`: whole numbers only | `fractional` (admitted → rejected), `huge` |
| Client crash (note): a non-boolean `accepted` threw in the handler, then the client waited 5 s for a misleading message | hostile server | `a84b208`: type-checked | `accepted_text` (script error → explicit mismatch) |
| Hang-up message (non-blocking): a server that disconnects during the handshake (ENet discards the queued reason) produced "probably running an older release" after 0.1 s | hostile server | `a84b208`: an early hang-up says the server closed the connection during the version check | `hang_up`, `reject_then_hang_up` |
| Tall names (note): one letter plus 23 combining marks drew an 84 px row and pushed the two newest kills out of the clipped feed | native capture | `d0278f0`: at most two generic combining marks per character | `hud_overflow_test.gd` stacked-marks set (30 failures → 0) |

Not changed, with reasons:
- **A ray that starts inside a capsule** registers at t = 0, where 0.3.0's physics ray ignores the shape it starts in. Live capsules collide, so a shooter's eye cannot be inside another operator's capsule in play.
- **Display-name sanitising** (`SBDesign.plain_line`, unchanged since 0.3) cuts at 24 code points without an ellipsis and turns zero-width joiners into spaces. This splits family emoji and some Persian and Indic spellings. It is recorded in `docs/KNOWN_LIMITATIONS.md` and is out of scope for this PR.
- **The final `hit_volume_test.gd`** does not parse on `e018a65`, because its tangent and long-range checks call a helper added in `6e144a0`. The failure counts above were measured against the commit before each check was added. The 33-check version fails 8/33 on `e018a65` for the stated reasons.
- **`hud_overflow_test.gd` on `e018a65`** hangs after its script error until `validate.sh`'s 540 s timeout kills it.

The reviewer found these sound:
- **Existing assertions:** none removed or loosened between `e018a65` and `fc52e68`.
- **Malformed hellos:** 200 KB, non-UTF-8, nested and silent peers never crashed the server or reached an RPC, ticket or slot. Godot discards non-auth packets from authenticating peers (`scene_multiplayer.cpp`).
- **Reconnect** of established sessions still works.
- **Truncation cost:** `_fit_text` takes at most 0.43 ms.
- **Unicode layouts:** emoji, Thai, CJK and Arabic feed layouts keep full rows.

It did not test real packet loss or latency, raw crafted ENet packets, Jolt, or Android/ARM.
