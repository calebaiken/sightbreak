# Prioritised implementation backlog

This is a list of recommendations, not a plan of record and not a commitment. **Nothing here has been implemented by this research branch.** IDs `UI-…`, `WP-…` etc. refer to [`EVIDENCE_LEDGER.md`](EVIDENCE_LEDGER.md); `C-…` to [`REVIEW_CONFLICTS.md`](REVIEW_CONFLICTS.md); `T-…` to [`HUMAN_AND_DEVICE_TESTING_PLAN.md`](HUMAN_AND_DEVICE_TESTING_PLAN.md).

## How items are written

- **Basis** is the evidence class that justifies the item (M, V, R, A, D, H, U). An item based on H or U is a hypothesis to test, and its first step is the test.
- **Owner** follows the repository's branch ownership: the graphics branch (`claude/cs2-fidelity-art-production`, PR #2), the UI branch (`claude/native-ui-production-v1`, PR #12), and Codex-owned networking/backend/integration. Items for Codex are *requests*; I do not edit Codex branches.
- **Done when** states the evidence that closes the item. For anything perceptual, a test result alone never closes it (see synthesis §5). "Human review" means a person who is not the author and not an AI agent.
- **Authorization.** Items touching the uncommitted art work are marked **[needs authorization]**. They are not to be started without the owner's renewed approval, including any Blender build.

## Owner decisions that gate the backlog

| ID | Decision | Why it matters | Recommendation (opinion) |
| --- | --- | --- | --- |
| D-1 | Authorize building, testing and reviewing the uncommitted two-magazine reload (and the Blender run it needs) | RL-01, RL-03…RL-06 are open on the pushed branch; the fix exists only as unbuilt code | Authorize one bounded session with a stop rule (below, B-02), or explicitly shelve it |
| D-2 | Target devices (at minimum one small and one typical modern phone, one low-end) | Almost every P0/P1 test needs a device | Name the devices before B-01 |
| D-3 | Aspect policy: `keep` or `expand` (C-09) | Affects every HUD anchor and the world FOV | Keep `keep` until D-2 devices show whether bars read as a defect |
| D-4 | How much of the arsenal must reach authored quality for the next milestone: one rifle, or all four | WP-09; effort scales ~linearly | One authored weapon, with the others visibly deferred and presented honestly, rather than four at half quality |
| D-5 | Scoring convention and raters (C-01, C-02) | Without it no score can be compared | Adopt B-03 and add at least one human or outside rater |
| D-6 | Whether to engage an outside artist for a one-off review of the first-person assets | R7, R11: no review has ever been by a professional | Yes, for a paid single-session critique; cheapest way to calibrate every score so far |
| D-7 | Definition of the mobile quality target ("CS2-class on a phone") (B-22) | §4.3 of the synthesis | Define it in measurable terms before further scoring |
| D-8 | Scope of cosmetic categories after the rifle (knives, gloves, stickers) (EC-06) | Content breadth versus depth | Defer until the open/equip/see loop is shown to work with players (T-04) |

## P0: measure or decide before building more

| ID | Item | Basis | Owner | Done when |
| --- | --- | --- | --- | --- |
| B-01 | **Physical-size check on two or more real phones.** Measure the rendered height of the HUD buttons and body/caption text; compare with 7–9 mm and 2.2–2.5 mm; record in `DEVICE_TESTING.md` | AC-01 (D), C-03 | UI branch + owner's devices | A table of measured mm per element per device, signed by the person who measured, and a decision recorded on whether `DESIGN.TOUCH_COMFORT` / `TEXT_FLOOR` need changing |
| B-02 | **Decide the fate of the uncommitted two-magazine reload.** If authorized (D-1), run one bounded loop: build, run `reload_legibility_probe`, update `weapon_art_test.gd` for `SBReloadPhases`, run the art suites, commit, and request independent review. Stop rule: if after two iterations the hand-in-frame metric and the contact sheet still do not show a different magazine arriving, stop and report | RL-01, RL-03…RL-06 (V) | Graphics branch **[needs authorization]** | Built, tested, committed, pushed; contact sheet shown to a reviewer who reports what they see; RL-01 closed only if an unprimed viewer identifies two magazines |
| B-03 | **A scoring convention.** One rubric with anchored examples; fixed weights; the benchmark stated; scores reported as `score (rater, rubric id, commit)`; no single-number claims | C-01, C-02, PR-7, R7 | Docs (any branch) | Rubric merged; `KNOWN_LIMITATIONS.md` and `DEVELOPMENT_STATUS.md` updated to cite it |
| B-04 | **Correct two documentation imprecisions**: add the 1.33 mm trigger-finger exception to the status line; replace the retired 8.1 in `KNOWN_LIMITATIONS.md` with a pointer to B-03 | C-04, C-05, PR-7 | Docs | The text matches `clip_contact.csv` and the rubric; diff reviewed |
| B-05 | **Independent re-review of PR #12 head `7e41de6`** against the original findings (F1–F4) and the new sheet; the reviewer should repeat the 1216 × 1628 reproduction | UI-01…UI-07 | Reviewer (Codex or human) | A review comment per finding: accepted / not accepted, with the reviewer's own measurement |

## P1: the visible weaknesses and the highest-risk unknowns

| ID | Item | Basis | Owner | Done when |
| --- | --- | --- | --- | --- |
| B-06 | **Rebuild hand anatomy from a reference.** Establish a hand reference sheet (proportions, joint positions, three grips: pistol grip, rail support, magazine), then rebuild fingers with joint structure; replace the mitten grip; keep topology animatable | WP-02, WP-03, R5 | Graphics branch **[needs authorization]** | Stills and a clip reviewed by a human or outside artist (D-6) who answers the five questions in C-02 without the author present; at least two of three say the hands look like hands |
| B-07 | **Separate the grip from the magazine and the sleeve from the glove**, and re-check shade/interior values on a phone panel. Options: change the magazine's hue/value, change the grip's, or add an edge highlight | WP-05, WP-07 | Graphics branch **[needs authorization]** | Measured separation in sun, backlight, shade, interior; on a phone in daylight, a viewer picks out the magazine in one look |
| B-08 | **Reload legibility test**, including a hand-in-frame metric on the reduced-motion path, then a decision on the "show" step. Test: five people, unprimed, ask "what are the hands doing" at five key frames and in motion | RL-02, RL-03, RL-07, C-06, C-11 | Graphics branch + testers | T-08 results recorded; the show step kept or removed on that evidence |
| B-09 | **Make the art tests follow the shared phase constants** (`weapon_art_test.gd` references removed `Actor.RELOAD_*`) | RL-06 (V, in the uncommitted tree) | Graphics branch **[needs authorization]** | Test suite compiles and passes after B-02; negative control: change a phase, test fails |
| B-10 | **Review the muzzle flash** as a short clip on a phone, by two or more observers; check flash area and frequency against photosensitivity guidance; decide, then iterate or leave | FX-01, C-12 | Graphics branch + testers | Reviewer notes recorded; photosensitivity check recorded; the ledger status changed from "unreviewed" |
| B-11 | **HUD placement test**: do the FRAG, SMOKE and USE circles over the weapon impede aiming or reading? Test with five players, thumbs on a real phone, using the customisable layout as the baseline | UI-09 (A/R), AC-06 | UI branch + testers | T-03 results; move the circles only if players say they obstruct |
| B-12 | **Safe area on real devices**: notch, punch-hole, rounded corners, gesture bar; confirm the menu, the sheet and the HUD sit inside | UI-04 (synthetic insets only) | UI branch + devices | Screenshots on at least two real devices with different cutouts; no control inside an inset |
| B-13 | **First-use session of the armory loop**: find YOUR CASES, open a case, equip the result, see it in the first-person view; observe, do not help | Synthesis §2.2 (U) | Testers | T-04 complete: completion rate, time, errors, quotes recorded verbatim |
| B-14 | **Colour-vision simulation** of rarity colours, squad colours and the odds table (protan, deutan, tritan); check each state is also carried by text or shape | AC-02 (U) | UI branch | Simulated screenshots for each; findings logged; any state distinguishable by colour only is fixed |
| B-15 | **Performance on phones**: frame time, thermals and battery over a 10-minute session, mid-range and low-end, with and without the authored viewmodel and effects | WP-10 (software-render only), FX-03 | Graphics branch + devices | Frame-time percentile table per device; a go/no-go for the viewmodel's cost |

## P2: quality improvements once P0/P1 are settled

| ID | Item | Basis | Owner | Done when |
| --- | --- | --- | --- | --- |
| B-16 | **Make sleeve forms readable**: fold shapes and shading that survive at 1280 × 720 and on a phone | WP-03 (R, A) | Graphics branch **[needs authorization]** | Human review confirms the sleeve reads as cloth with form |
| B-17 | **A Relay Yard slice at the rifle's level of finish**: authored surfaces, props, baked lighting, probes | EV-01, EV-04 | Graphics branch | Side-by-side with the weapon reviewed by a human; the weapon no longer outshines the yard by an obvious margin |
| B-18 | **Authored first-person quality for a second weapon**, or an honest presentation that defers the other three (D-4) | WP-09 | Graphics branch | The requisition screen shows each weapon honestly; the second weapon passes the same five-question review |
| B-19 | **Operator figures** that read as people at the HUD's scale | EV-02 | Graphics branch | Human review of a third-person clip |
| B-20 | **Per-item cards with inspect in the trade confirmation**, only if T-06 shows the text block is not enough | EC-08, C-10 (H) | UI branch | T-06 shows an unfavourable item is caught by at least as many participants with the new design, and not fewer |
| B-21 | **Persist pending receipts** across app close so an unknown purchase can be recovered | EC-02 | **Request to Codex** (client/backend contract) | A test that kills the app mid-purchase and recovers the same receipt id |
| B-22 | **Define "CS2-class on a phone"** in measurable terms (value separation, anatomy checklist, readable beats, frame budget, target sizes) | Synthesis §4.3 | Owner + docs | A one-page definition agreed by the owner; scores are then reported against it (B-03) |
| B-23 | **Typography and wordmark identity**: a distinctive wordmark and a second typeface for headings, licensed or original | UI-14, UI-13 | UI branch | Owner approves; the gap review item 7 closed with the owner's sign-off, not a score |
| B-24 | **Item viewer in the armory**: a lit 3D or posed view of the selected finish | Benchmark expectation E (not a finding) | UI + graphics | T-04 participants identify finishes more accurately with the viewer than with swatches |
| B-25 | **Listening review of reload and fire sound** | RL-10 | Audio (unowned) + testers | Notes from three listeners; sound design backlog written |
| B-26 | **Screen-reader investigation**: what the engine exposes on Android and iOS; what the HUD and menu would need | AC-05 (U) | UI branch | A short report with a feasibility call per platform |
| B-27 | **Server-side expected-price check on market buy** | EC-03 | **Request to Codex** | Backend rejects a purchase whose expected price differs from the listing's |
| B-28 | **Market pagination, filters, history, abandoned-trade expiry** | EC-07 | **Request to Codex**; UI follow-up | Added with tests; UI shows pages and filters |
| B-29 | **Close the 1.8 px ammunition/SWAP overlap at 130 % text** | UI-08 | UI branch | `landscape_ui_test` gains a check; no overlap at the 1280 × 720 130 % case |

## P3: later, or only if the evidence calls for it

| ID | Item | Basis |
| --- | --- | --- |
| B-30 | Knives, gloves, stickers and charms | EC-06; gated by D-8 and T-04 |
| B-31 | Localisation system beyond the replaceable string table | UI-12 |
| B-32 | Master-detail inventory for wide screens | UI-11 |
| B-33 | Muzzle smoke and flash light; smoke volumetrics | FX-02, FX-03 |
| B-34 | Casings readable at phone scale | FX-02 |
| B-35 | Draw, inspect and bolt animations | RL-10 |
| B-36 | Aspect-policy change to `expand` | C-09, D-3 |

## Suggested order

1. **This week, no building:** D-1…D-7 decided or consciously deferred; B-03, B-04 (documents only); B-05 (review request).
2. **Next, one device afternoon:** B-01, B-12 and a first look at B-11 and B-15. They cost a day, and they could change every later size and placement decision.
3. **Then, art, if authorized:** B-02 and B-09 together; B-07 in the same pass; B-08 with testers; B-10.
4. **Then, the largest gap:** B-06 with an outside reference or artist (D-6), because it is the one defect every review names.
5. **In parallel, UI/economy:** B-13, B-14, B-20 only if T-06 says so; B-21 and B-27 as Codex requests.
6. **After the above:** B-16…B-19 (fidelity of the rest), B-22 drives the next scoring round.

## What this backlog deliberately omits

- Anything that copies a Counter-Strike 2 asset, layout, name or palette.
- Real-money payments or any real-value path for the marketplace. If one is ever contemplated it needs its own review (fraud, regulation, platform rules) before design work.
- A target score. The 8.5 gate stays the owner's; this backlog does not claim any item raises a score by a given amount.
- Merging any pull request or editing any Codex branch.
