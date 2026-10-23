# Evidence ledger

Classes are defined in [`README.md`](README.md): **M** measured, **V** verified defect, **R** reviewer judgment, **A** author observation, **D** derived, **H** hypothesis, **U** unverified. "Status" is as of the heads named in the README; "fixed" means a fix is committed and its own tests pass, not that a reviewer has accepted it.

## UI: menu, HUD, shell

| ID | Finding | Class | Source | Status |
| --- | --- | --- | --- | --- |
| UI-01 | The trade confirmation was a stock dialog with no wrapping or scrolling: 1216 × 1628 px at 20 items a side, 130 % text, its buttons at y 1566, below a 720 px screen | V, M | Codex on PR #1 (comment 6175365176): 4 of 12 checks fail on `148760e` and `2b2731a`, headless and native | Fixed in `7e41de6` (`ConfirmSheet`); 36 configurations through the real button pass. Not yet independently re-reviewed |
| UI-02 | Armory labels ignored the text-size setting (wallet 15 px, headings 28 px at any scale) | V, M | Codex on PR #1; fixed sizes in `economy_ui.gd` | Fixed in `7e41de6` |
| UI-03 | The menu showed a blank `ONLINE` and `0 EARNED CREDITS` for an account that never loaded | V | Codex on PR #1 (F1) | Fixed in `7e41de6` |
| UI-04 | The menu kept its creation-time layout after a resize or safe-area change (header and footer 6 px inside a synthetic inset) | V | Codex on PR #1 (F2) | Fixed in `7e41de6`. Insets are synthetic |
| UI-05 | Whole numbers from the server printed with `.0` (`Pattern 1840233.0`, `XP: 1450.0 · Level: 2.0`, odds `58.0%`) because JSON numbers are floats in Godot. Hand-typed fixtures of integers hid it for all of increment 3 | V | Found by the backend-derived fixture; a negative control reproduces it (PR #12 evidence, `negative-controls.log`) | Fixed in `7e41de6` |
| UI-06 | 16 of 48 menu labels were below 4.5:1 against what is drawn behind them (worst 1.33, the build line; 1.56, the operation heading) at 1280, 960 and 1560 px; 0 of 48 after a stronger scrim and bands (worst 4.98). 4.5:1 is a web guideline used here as a proxy | M | `menu_contrast_probe.gd`, llvmpipe frames | Fixed in `7e41de6`. Whether 4.5:1 is the right bar for game text on a phone in daylight is H |
| UI-07 | At 115–130 % text the status line collided with the FRAG and SMOKE touch buttons, then a custom saved layout made it oscillate between a 346 × 30 line and a 6 × 756 column, hiding health and ammunition | V | Codex on PR #1; `landscape_ui_test` 9,217 checks; native 93/93 against 39/93 failures on the old head | Fixed in `148760e`; Codex accepted the correction in scope |
| UI-08 | At 130 % the ammunition label's box touches SWAP's bounding square by 1.8 px at 1280 × 720 | M | author, PR #1 reply | Open, recorded, not fixed |
| UI-09 | In the default layout the FRAG, SMOKE and USE circles sit over the first-person weapon (the USE circle is on the sidearm's slide in `ui/captures/increment-1/1280x720-100-hud-notice.png`) | A (and earlier R: audit finding U-2) | capture; `CLAUDE_AUDIT_0.3` U-2 | Open. Whether it hurts target acquisition or aiming is H |
| UI-10 | The menu holds its layout across 5 sizes × 4 text scales × 4 names (2,227 checks); this shows the layout does not break, not that the menu is easy to use | M | `ux_contract_test.gd` | Passing; says nothing about usability |
| UI-11 | The inventory is a card list with the inspector below it; choosing an item scrolls the inspector into view but a master-detail layout for wide screens is not built | A | `7e41de6` | Open (design option) |
| UI-12 | There is no localisation system: the menu's string table is replaceable and has been tested with a 60 % longer pseudo-translation only | M | increment-2 README | Open |
| UI-13 | The menu's right-hand column sat directly on the lit yard, which is why UI-06 was low; text over a 3D background rather than on a panel remains the pattern for the build line and operation block | A | menu frames | Mitigated by bands; a panel or an outline is the alternative (H) |
| UI-14 | One font (the engine's bundled face, emboldened for headings) is used for the wordmark, HUD and armory. A generic wordmark was in the gap review's first findings | A, R | `docs/ui/VISUAL_GAP_REVIEW.md` item 7 | Open (identity) |

## Armory, cosmetics economy, marketplace, trading

| ID | Finding | Class | Source | Status |
| --- | --- | --- | --- | --- |
| EC-01 | Failures of every request told the player to "use Retry pending transaction", including reads and requests that never left the device | V | code at `2b2731a`; `economy_api.gd` | Fixed in `7e41de6`: failures are classified (not sent, not reached, rejected, unknown) and only an unknown outcome of a request with a receipt id offers the retry |
| EC-02 | Pending receipts are held in memory only, so closing the app loses the means to recover an unknown purchase; unkeyed requests have no receipt | V (documented) | `KNOWN_LIMITATIONS.md` | Open (Codex-owned backend/client contract) |
| EC-03 | The market buy posts only a receipt id; the price is fixed by the server per listing id. The client does not send the price it displayed | M (code) | `economy_ui.gd`, `backend/app.py` | Open as a request; the risk of a price changing under a listing id is H and looks low |
| EC-04 | The backend has one finish per rarity per collection, so a finish's chance is its rarity's published chance (58 / 26 / 11 / 4 / 0.9 / 0.1 %) | M | `backend/app.py` `definitions()` | The UI now says so on each finish card |
| EC-05 | Provisional economy: a case costs 350, a key 150, a completed match pays 100 (a win +75, the first of a day +150). A new player affords one opening after roughly two matches if one is a win. The simulation is fictional and states its assumptions | M, D | `docs/economy.md` | Pacing and perceived fairness are U |
| EC-06 | Cosmetic breadth is four collections × six rifle finishes plus cases and keys; no knife, glove, sticker or charm items; only the rifle slot is equippable | M | `KNOWN_LIMITATIONS.md` | Whether this sustains interest is H |
| EC-07 | The market has no pagination, no per-weapon or price filtering beyond a text filter, no history and no abandoned-trade expiry | V (documented) | `KNOWN_LIMITATIONS.md` | Open |
| EC-08 | The confirmation sheet shows every item on both sides as plain wrapped text with a pinned count summary; per-item cards with inspect are on the trade screen above it | A | `7e41de6` | Design option. Whether players read the scrolled terms is H and is the first thing to test |
| EC-09 | The design rules forbid near-miss reels, urgency, scarcity badges and spend pressure, and all Credits are earned in play; the rules are checked by review, not by a test that detects a manipulative pattern | M (docs) | `DESIGN_SYSTEM.md` | Holds in the reviewed screens; perceived pressure is U |
| EC-10 | A real local PostgreSQL 16 and the real API ran the armory's account, rejection, replay, 401 and confirmation paths: 37/37, plus the backend's 48 tests. Fictional balances only | M | PR #12 evidence `logs/native-economy.log` | Done once, by the author, on one machine |

## First-person weapons, hands, materials, lighting

| ID | Finding | Class | Source | Status |
| --- | --- | --- | --- | --- |
| WP-01 | Weapon-and-arms scores, by reviewer and commit: 4.5/10 (Claude agent, `2bba519`), 4.5 (`5100b3e`), 5.5 (Codex, `64ec598`), 4.5 (Claude agent, `b507205`), 6.1 (Codex, `68251a0`), against a gate of 8.5 and a "CS2-class" level the reviewers put near 9. Rubrics, weights and commits differ, so the series is not a trend line | R | `VISUAL_QA.md`; PR #2 comments | See `REVIEW_CONFLICTS.md` C-02 |
| WP-02 | Hand anatomy is the weakness every review names: tube fingers, "lumpy putty gloves", a mitten grip hand, support fingertips over the rail. In the committed close-up the support hand shows three round knuckle balls beside the rail and fingers that read as sausages | R (all), A | `VISUAL_QA.md`; `art-v6/support-hand-closeups.png` | Open. The only anatomy change since `b507205` was a fanned grasp |
| WP-03 | Sleeves read as a near-uniform tube; folds exist in the normal map and barely show at 1280 × 720 | R, A | `art-v4/README.md`; Codex 6.1 review | Open |
| WP-04 | The bore's vanishing point was 124 px left of the crosshair (10.0°) and is 38 px left, 21 px above (3.5°) after a re-placement; Codex measured the same | M | probe logs; Codex on PR #2 | Improved; the "held across the body" read is a judgment that has not been re-reviewed on the new frames by a second observer |
| WP-05 | Value separation: in sun the gloves are 89 and the sleeves 110 luma (a gap of about 20); in backlight 33.9 and 38.9, and in shade about 6 apart; gloves in a dark interior measure 15–17 against a self-chosen target of 20 | M | `art-v6` `light-after.log`; `art-v5` | Open for shade and interior |
| WP-06 | The pulled magazine rendered black because its ambient occlusion had been baked while it sat in the well. The first diagnosis (weak lighting) was wrong and was corrected after a finer measurement | V, M | `VISUAL_QA.md` correction; `art-v5` | Fixed. A process lesson: PR-5 |
| WP-07 | In the reload frames the tan pistol grip and the tan magazine sit side by side (frames 0.20–0.32 of `reload-after.jpg`) and are close in colour and value, so which slab is "the magazine" depends on where the hand is. An earlier review reported the same ("the tan grip reads as the magazine") | A, R | `art-v6/reload-after.jpg`; review of `b507205` | Open; the pulled magazine is also the brightest part in sun (143) |
| WP-08 | The pistol grip is a flat block; the receiver and grip read flat in Codex's 6.1 review; the optic has no reticle; the rifle's detail exceeds the box-built environment | R, A | `art-v6` README; Codex 6.1; `VISUAL_QA.md` | Open |
| WP-09 | The other three weapons (sidearm, SMG, marksman) are still procedural boxes; the requisition screen shows flat glyphs for all four. In the HUD capture the procedural sidearm is a blocky slab beside operators built from primitives | A | `increment-1` captures | Open. Fidelity is uneven across the arsenal |
| WP-10 | The authored viewmodel adds 2 draw calls and about 34.6k primitives; on llvmpipe the rigged rifle's median frame is 176 ms against 116 ms with no viewmodel and 128 ms with the procedural one (isolated reruns). Texture residency +5.34 MiB. The arms are 7,828 triangles | M | Codex follow-up on PR #2; `PERFORMANCE_REPORT.md` | Relative software-render cost only. Phone cost is U |
| WP-11 | The static fallback hands used the world projection beside the rifle's 54° one and detached from it | V | Codex on PR #2 | Fixed in `3934110`, confirmed by Codex on `68251a0` |

## Reload and presentation animation

| ID | Finding | Class | Source | Status |
| --- | --- | --- | --- | --- |
| RL-01 | The shipped reload pulls the magazine out, lifts it out to the left and "shows" it, and puts the same magazine back; there is no second magazine and no discard | V (documented) | `ANIMATION_STANDARDS.md`; `art-v6` README | A two-magazine implementation exists **uncommitted** in the graphics worktree. It has not been built, run, tested or reviewed, and nothing here counts it as done |
| RL-02 | In the contact sheet the "show" step (frame 0.47) holds the old magazine up in the middle of the screen. It reads as inspecting a magazine rather than discarding one | A | `reload-after.jpg` | H: removable without loss; U: how players read it |
| RL-03 | With reduced motion on, the reload's staging lift is scaled to 20 % (`reload_tilt *= 0.2`), and the support hand falls below the frame at 20 % progress; the magazine is 77 / 77 / 92 / 77 % on screen at 0.14, 0.20, 0.50, 0.80 | V, M | Codex on PR #2; `actor.gd` at `68251a0` | Open on the pushed branch; addressed in the uncommitted work, unverified |
| RL-04 | Casings take the actor's feet height as the floor; with a real floor at 0 and the actor at 2 they settle at 2.005 | V | Codex on PR #2 | Open on the pushed branch; addressed in the uncommitted work, unverified |
| RL-05 | The seat sound fires from the authoritative reload fraction while the visible animation follows a presentation clock that can lead it by up to 0.1 s (about 4 % of a 2.25 s reload) | V (code reading) | `actor.gd` at `68251a0` | Open on the pushed branch; addressed in the uncommitted work, unverified |
| RL-06 | `RELOAD_REACH` (0.12) and the clip's `P_REACH` (0.14) disagreed; the constant was used only in a test inequality | V (code reading) | `actor.gd`, `arms_build.py` | Open on the pushed branch; the uncommitted work centralises the phases |
| RL-07 | At `68251a0` the magazine is at least 94 % on screen and at most 1 % covered, with at least 9,248 of its pixels visible, from the grasp to the let-go. The probe measured the magazine, not the hand; "in frame" is not "legible" (a reviewer's point, and the author's own correction) | M | `art-v6` README; Codex re-measurement | The hand-in-frame metric exists only in the uncommitted probe |
| RL-08 | Contact review of the clip: the left arm never enters the rifle or the magazine; the right arm's trigger finger is 1.33 mm inside the rifle. `DEVELOPMENT_STATUS.md` says "the arms enter neither" without that exception, which the evidence README does state | M, V | `clip_contact.csv` | A small documentation imprecision |
| RL-09 | Animation never changes authoritative ammunition, cancellation or completion: 183 actor lifecycle checks and 321 authority checks (Codex) pass | V | Codex integration report | Holds; a property of code, independent of how the animation looks |
| RL-10 | Reload sound is two synthesised clicks; no listening review exists; no draw, inspect or bolt animation exists | M (docs) | `KNOWN_LIMITATIONS.md`; status doc | Open |
| RL-11 | Online clients receive the reload timer at 20 Hz; before the presentation clock the pose changed on 39 of 119 ticks and after it on at least 115 | M | Codex finding; author fix and test | Fixed in `7ce8981` |

## Effects

| ID | Finding | Class | Source | Status |
| --- | --- | --- | --- | --- |
| FX-01 | The muzzle flash was replaced by a layered additive mesh (213 triangles, varied per shot, 40 ms). In the committed burst frames the flash is a small bright spike at the muzzle with a faint halo; I read it as still starry. No reviewer has judged the new flash on its own | A | `art-v6/firing-burst.jpg` | Unreviewed. Not "fixed" on the evidence available |
| FX-02 | Brass casings are lathed cases that tumble and bounce; at 1280 × 720 they are a few pixels long. The flash is a mesh with no light; there is no muzzle smoke | A, M | burst frames; status doc | Open |
| FX-03 | Smoke is a lobed, rim-softened cloud that probably costs more than the old core (not measured on a device); no volumetric interaction | M (docs) | `KNOWN_LIMITATIONS.md` | Open |

## Accessibility and physical size

| ID | Finding | Class | Source | Status |
| --- | --- | --- | --- | --- |
| AC-01 | **Derived physical size.** The project renders a fixed 1280 × 720 canvas (`canvas_items`, default "keep" aspect) scaled to the screen height. On a 6.1-inch 19.5:9 phone the screen is about 65 mm tall, so one canvas pixel is about 0.09 mm. Then a 48 px target is about 4.3 mm, a 56 px touch button about 5 mm, 16 px body text about 1.4 mm and the 14 px floor about 1.3 mm tall. Common mobile guidance is 7–9 mm for a target and roughly 2.2–2.5 mm for body text | D | `project.godot`; `touch_controls.gd` (radius 28 px); published phone geometry | **Unmeasured on any device.** If it holds, every "48 px" and "14 px" claim in the repository is about half of the usual physical size on a phone. The largest single reason to test on hardware |
| AC-02 | The design system claims color is never the only signal (chips carry text; squads carry labels). No colour-vision simulation of the rarity colours, squad colours or the odds table has been run | M (docs), U | `DESIGN_SYSTEM.md` | Gap |
| AC-03 | Text scale 85–140 % is honoured in the armory and, per Codex, in the HUD at 85–130 %; the scale control offers 90/100/115/130 in the settings screen | M | `7e41de6`; `DESIGN_SYSTEM.md` | Holds as layout; legibility on a phone is AC-01 |
| AC-04 | Reduced motion is honoured by the case reveal, the loading bar, sway and the old magazine's drop (hidden instead of tumbling) in the uncommitted work; the reload's staging was wrongly attenuated until RL-03 | M, V | code; Codex | See RL-03 |
| AC-05 | No screen-reader (TalkBack, VoiceOver) behaviour has been examined, and what the engine exposes on Android and iOS has not been looked up | U | none | Gap |
| AC-06 | No physical Android or iOS session exists for touch feel, thumb reach, button occlusion, notches, gyro, interruption or thermals; `DEVICE_TESTING.md` is a procedure with no completed rows | U | `DEVICE_TESTING.md`; every report | Gap |

## Environment and overall presentation

| ID | Finding | Class | Source | Status |
| --- | --- | --- | --- | --- |
| EV-01 | The yard is box geometry with flat materials; in the weapon captures the world is a few grey planes and painted lines. The weapon's detail exceeds the world's, and the gap grows as the weapon improves | A, R | captures; `VISUAL_GAP_REVIEW.md` item 9; `VISUAL_QA.md` | Open; a Relay Yard slice is the stated next step |
| EV-02 | Operators are primitive figures (spheres, boxes, articulated limbs); a third-person silhouette and team read exist but the figures read as toys beside the rifle | A, R | HUD capture; `CHARACTER_PRODUCTION.md` | Open |
| EV-03 | Whole-game visual score: 8.1/10 (Codex `QA-0.3`) against 6.6/10 (Claude audit) on the same baseline captures | R | `QA-0.3.md`; `CLAUDE_AUDIT_0.3.md` | See `REVIEW_CONFLICTS.md` C-01 |
| EV-04 | The renderer is GL Compatibility on desktop and mobile, which rules out screen-space reflections, SSAO and the volumetric fog the benchmark is reported to rely on; baked lighting, probes and careful tonemapping remain | M (docs) | `VISUAL_GAP_ANALYSIS.md` | Constraint, not defect |
| EV-05 | The shipped aspect policy is "keep": the 16:9 frame with bars on wider or taller screens, giving 114.19° horizontal world FOV at every size. "Expand" would give wider screens up to 125° horizontally | M | `MOBILE_ASPECT_REVIEW.md` | A product decision; retained pending the owner |

## Process findings (about how the evidence was produced)

| ID | Finding | Class | Source |
| --- | --- | --- | --- |
| PR-1 | The author's claim that the layout "holds at 16:9, 20:9 and 4:3" was false: the captures were at 1280 × 720 and 1024 × 576 and were resized; the claim was withdrawn | V | `VISUAL_QA.md` hands-v2 review |
| PR-2 | A first test of the menu passed while text was truncated and a label had collapsed to 1 px, because it checked rectangles rather than text fitting; native captures exposed both | V | increment-2 README |
| PR-3 | A hand-typed fixture hid float formatting defects for a whole increment; generating the fixture from the backend's serializers found them | V | PR #12 evidence |
| PR-4 | An evidence log was copied before the final run (2,288 checks in the log, 2,292 in the README) | V | independent review of `2b2731a`; errata in increment-3 README |
| PR-5 | A diagnosis (black magazine = weak lighting) was confirmed by a coarse measurement and was wrong; a finer one (per-pixel occlusion) found the cause | V | `VISUAL_QA.md` correction |
| PR-6 | A metric was gamed by an acceptable-looking result (a flat-ended sleeve across the screen scored "magazine uncovered"); an arm-area column was added | V | `art-v6` README |
| PR-7 | The KNOWN_LIMITATIONS document still states a visual score of 8.1/10 as the 0.3 position while later documents carry 6.6 and 5.5–6.1 | V (document inconsistency) | `KNOWN_LIMITATIONS.md` |
| PR-8 | Every comment on the pull requests, from the author, from the Claude reviewers and from the Codex reviewer, appears under one GitHub account (`author_association: OWNER`); only the text identifies who wrote it | M | GitHub API |
