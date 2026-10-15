# SIGHTBREAK design research synthesis

Evidence classes (M, V, R, A, D, H, U) and the ground rules are in [`README.md`](README.md). Finding IDs (`UI-01`, `WP-02`…) are defined in [`EVIDENCE_LEDGER.md`](EVIDENCE_LEDGER.md). Disagreements are in [`REVIEW_CONFLICTS.md`](REVIEW_CONFLICTS.md); the work that follows from this is in [`IMPLEMENTATION_BACKLOG.md`](IMPLEMENTATION_BACKLOG.md) and [`HUMAN_AND_DEVICE_TESTING_PLAN.md`](HUMAN_AND_DEVICE_TESTING_PLAN.md).

## 1. Summary

1. **This is a record of agent review and software-rendered measurement, not of player research.** No human has played the game on a phone and reported anything that is in the repository. Every score is an AI reviewer's opinion; every frame is a desktop software-rendered capture (Mesa llvmpipe, Xvfb). The conclusions below are about what the *code and captures* show, and about what to test next.
2. **The strongest evidence is for the interface's behaviour.** Defects in the trade confirmation, text scaling, account states, failure messages and menu contrast were found by someone other than the author (UI-01…UI-07), reproduced, fixed, and are guarded by tests that failed on the old code. That is real, but it establishes that the screens do not break, not that they are easy or pleasant to use (UI-10).
3. **The largest unmeasured risk is physical size.** If the derived figures in AC-01 hold, a "48 px" target is about 4.3 mm and "14 px" text is about 1.3 mm tall on a 6.1-inch phone, roughly half the usual guidance. Every layout claim in the repository is expressed in canvas pixels, none in millimetres on a device. One afternoon on a phone could confirm or remove this concern; nothing else on the list has that leverage.
4. **First-person art is the weakest and best-documented area, and the one most in dispute.** Hand anatomy is named as the top weakness by every review (WP-02). Scores for the weapon slice run 4.5 → 5.5 → 4.5 → 6.1 from different reviewers on different rubrics (WP-01, C-02), and the whole-game score is 8.1 or 6.6 on the same captures (EV-03, C-01). I do not treat any of these as the true number.
5. **The reload is the most thoroughly instrumented feature and the least settled.** The shipped reload still re-inserts the same magazine (RL-01). A two-magazine fix exists uncommitted and unbuilt; this synthesis does not count it as progress.
6. **Fidelity is uneven.** One rifle and its arms are authored; three weapons are boxes, operators are primitives, and the environment is box geometry (WP-09, EV-01, EV-02). A viewer's impression of the whole is limited by the weakest of these, and the gap widens as the rifle improves.
7. **The cosmetics economy is designed and checked against a rule list, not against players.** The rules (no urgency, no near-miss, no spend pressure) hold in the reviewed screens (EC-09). Whether the pacing feels fair, whether the odds are understood and whether the trade confirmation is read are all untested (EC-05, EC-08).

## 2. Findings by area

### 2.1 Native mobile UI

**Known (M/V).**
- Text sizing, account states, failure classification and the bounded confirmation are fixed and tested against the real backend's data shapes and, once, against a live local API (UI-01…UI-05, EC-01, EC-10).
- A contrast probe, run on real rendered frames behind each label, found 16 of 48 labels under 4.5:1 and 0 after correction (UI-06). The method (measure what is drawn behind the label, not the intended colour) is reusable; the 4.5:1 threshold is a web proxy (H for game text outdoors).
- The layout survives 5 sizes × 4 text scales × 4 names (UI-10), and a 60 % longer pseudo-translation (UI-12).

**Opinion (R/A).**
- The reviews found the menu and armory *functional*: 7.5/10 functionality, 7.0 accessibility (Codex, on PR #1). The gap review lists a generic wordmark, one typeface and text over a 3D background as identity weaknesses (UI-13, UI-14). These are expert-style judgments by agents.
- In the default HUD layout the FRAG, SMOKE and USE circles sit on the weapon (UI-09). I see it in the captures; whether it matters during play is H.

**Hypotheses and gaps (H/U).**
- Players will find the trade confirmation's scrolling terms sufficient to make an informed decision (EC-08).
- A layout built to a fixed 1280 × 720 canvas is comfortable under a thumb (AC-01, AC-06).
- Safe-area handling works on real notches and rounded corners (UI-04 uses synthetic insets).
- Anything about touch feel, thumb reach, gesture conflicts with OS edges, interruptions (calls, notifications), orientation changes or thermal throttling.

### 2.2 Armory, cosmetics economy, marketplace, trading

**Known.** The server enforces rules (fees, cooldowns, one finish per rarity per collection, idempotency by receipt id); the client displays published odds and states a finish's chance on its card (EC-04). Failures no longer say "retry" when nothing was sent (EC-01). Market, trade and gift paths post exactly the documented payloads (`armory_state_test.gd`).

**Opinion.** The design rules in `docs/design/DESIGN_SYSTEM.md` and `docs/economy.md` are principled and, read against the screens, are followed (EC-09). The independent reviewer accepted the HUD correction and did not dispute the armory's tone.

**Not known.**
- Whether 350-credit cases, 150-credit keys and 100 credits per match feel fair or slow (EC-05). The simulation states fictional assumptions.
- Whether the odds table is read, understood and trusted; whether "chance" language is read as probability (U).
- Whether a first-time player can find YOUR CASES, open a case, equip the result and see the change in the first-person view. This is the end-to-end loop that matters most commercially and it has never been observed.
- Whether rarity is distinguishable for players with colour-vision differences (AC-02).
- Whether the lack of knives, gloves, stickers and charms (EC-06) limits interest. Only the rifle slot is equippable, so the visible reward of an opening is confined to one weapon the player holds at a time.
- Whether the confirmation sheet's plain-text term list is enough, or per-item cards with inspect are needed (EC-08).
- Whether lost pending receipts on app close (EC-02) would be experienced by a real player; the loss is certain, the frequency is U.

**Constraint.** No real-money payments exist and none should be added by this work. Marketplace trust (fraud, scams, third-party selling) is not researched here and needs a separate review before any real-value path exists.

### 2.3 First-person weapons, materials and lighting

**Known (M).** The authored rifle's bore now points 3.5° from the crosshair, down from 10.0° (WP-04). Value separation of gloves and sleeves is about 20 luma in sun and about 5–6 in backlight and shade (WP-05). The viewmodel costs two draw calls and about 34.6k primitives; on a software renderer the median frame rose from 116 to 176 ms (WP-10). The magazine's black-in-hand defect was traced to baked occlusion, after a first diagnosis was wrong (WP-06, PR-5).

**Opinion (R/A).** Hands are the weak point (WP-02): tube fingers, putty gloves, mitten grip. The sleeves read as one tube (WP-03). The pistol grip and receiver read flat, the optic has no reticle (WP-08). I agree with the direction of these judgments when I look at the captures (A), and I note that I am the same model family as two of the reviewers, so my agreement is weak corroboration.

**Not known.**
- Whether the 6.1 or the 4.5 is nearer a human's impression (C-02).
- How the viewmodel reads in motion; captures are stills and contact sheets. Video sequences were not viewed here.
- How it reads on an OLED phone panel in daylight, where the dark interior values (gloves at 15–17 luma) may be invisible and shade separation of 6 may vanish.
- What phone GPUs make of two extra draw calls and 34.6k primitives (WP-10 is software-render only).

### 2.4 Reload animation

**Known.** The reload's phases are timed, sampled, and checked for authoritative-state independence: ammunition, cancellation and completion are not changed by the animation (RL-09). Contact with the rifle is within 1.33 mm for the one finger that touches (RL-08). Online pose updates now follow a presentation clock (RL-11).

**Known defects on the pushed branch.** The same magazine is re-inserted (RL-01); the show step reads as inspection (RL-02); reduced motion over-attenuates the staging (RL-03); casings land at the actor's feet height (RL-04); the seat sound can lead the visible seat by up to 0.1 s (RL-05); two constants disagree (RL-06).

**What the uncommitted work claims to change.** Two magazines, a ballistic drop, clock-driven audio, un-scaled staging under reduced motion, a floor raycast for casings, centralised phase constants. These address RL-01, RL-03, RL-04, RL-05 and RL-06 *in code*. None is built, none is rendered, none is reviewed. **They are neither findings nor evidence of improvement.**

**Opinion.** The reviewers' expectation, which I share but cannot verify, is that a convincing reload shows (a) the old magazine leaving, (b) a different magazine arriving, (c) a visible seat, (d) the hand returning to the grip, each readable at a glance on a phone. Reviewers also asked for a hand-in-frame metric rather than a magazine-in-frame one (RL-07).

**Not known.** Whether any version of the reload reads as a reload to a person who has not seen the contact sheet; whether the 2.25 s duration is acceptable for the game's pacing; whether the audio is satisfying (RL-10 — no listening review).

### 2.5 Effects and presentation

The new muzzle flash is unreviewed and, on my reading of the committed burst, still starry (FX-01). Casings are a few pixels long at 1280 × 720 (FX-02). There is no muzzle smoke, no light from the flash, no draw, inspect or bolt animation (RL-10, FX-02). Smoke is more detailed and probably costlier (FX-03). All of these are A or unverified; none has been judged by a second observer on a device.

### 2.6 Accessibility

Held as design intent and measured as layout: text scale, floor size, 56 px touch target, reduced motion, colour-not-sole-signal (AC-02…AC-04). Not examined: screen readers (AC-05), colour-vision simulation (AC-02), physical size (AC-01), motor accessibility beyond target size (hold-vs-toggle, one-handed play, remapping), audio-only cues, captioning of sound events, flashing/photosensitivity of the muzzle flash and smoke. No accessibility specialist or user with a disability has reviewed anything. The 7.0/10 accessibility score is an agent's opinion on layout evidence.

### 2.7 Overall visual presentation

Environment and operators trail the rifle (EV-01, EV-02). The renderer choice constrains the toolset to baked light, probes, carefully chosen materials and post-tonemapping (EV-04). The aspect policy produces the same world FOV at every size and letterboxes wider phones (EV-05); that is a design choice with a trade-off nobody has tested with players: bars on a 20:9 phone waste screen the user may see as a defect.

## 3. Recurring design problems

These recur across areas. Each links the findings that support it.

| # | Problem | Seen in | Class |
| --- | --- | --- | --- |
| R1 | **Pixel claims stand in for physical claims.** Sizes, margins and tolerances are set in canvas px on a fixed 1280 × 720 frame and never converted to mm on a device | AC-01, UI-08, UI-10 | D, U |
| R2 | **"Present" is accepted as "legible".** A magazine being on screen, a label fitting its box, a rectangle being inside the safe area each stood in for "a person can read it". The measurement improved each time it was challenged (RL-07, PR-2, PR-6) | RL-07, PR-2, PR-6, UI-10 | V |
| R3 | **A metric is optimised, then gamed or found incomplete.** A sleeve across the screen scored "magazine uncovered"; a probe measured the magazine, not the hand | PR-6, RL-07 | V |
| R4 | **Fixtures that look right hide defects** (hand-typed data hid `.0`; resized images hid aspect behaviour) | PR-1, PR-3, UI-05 | V |
| R5 | **Hands and anatomy.** Named by every review, fixed in no revision | WP-02, WP-03 | R, A |
| R6 | **Uneven fidelity.** One authored asset among primitives; the gap widens with each improvement | WP-09, EV-01, EV-02 | A, R |
| R7 | **Scores are not comparable.** Different rubrics, weights, commits and reviewers; all agents; one account | WP-01, EV-03, PR-8, PR-7 | R, M |
| R8 | **Documents drift from evidence.** A status document that omits an exception; a limitations document that still carries a retired score; an evidence log older than its README | RL-08, PR-4, PR-7 | V |
| R9 | **Stateful, unforgiving transactions** are described to the player in the vocabulary of the implementation (retry, receipt, revision), and the safe default (do not charge twice) is invisible to them | EC-01, EC-02, EC-08 | A, H |
| R10 | **Test coverage is behavioural; quality is perceptual.** The suites are large (thousands of checks) and none can fail because a hand looks wrong | UI-10, RL-09 | M |
| R11 | **Nothing in the loop is a person.** No human on a phone, no accessibility reviewer, no outside artist | AC-05, AC-06, PR-8 | U |

## 4. Counter-Strike 2 as a benchmark

**Status of this section.** No Counter-Strike 2 imagery was studied in the project's sessions or for this synthesis; the project's own gap analysis says so. What follows is what I expect a professional shooter's presentation to do, from general knowledge of the genre, marked **expectation (E)**. Someone who owns the game should confirm or correct each line. No CS2 asset, shape, layout, name or palette is to be reproduced, and the identity guardrails in §4.2 apply to everything below.

### 4.1 What the benchmark is useful for

| Benchmark dimension | Expectation (E) | SIGHTBREAK today | Reading |
| --- | --- | --- | --- |
| Silhouette and readability at speed: the weapon, the hands and the world are separable at a glance | A viewmodel whose hand, sleeve and weapon values and hues separate clearly; a clean, uncluttered read | Gloves and sleeves about 20 luma apart in sun, 5–6 in shade (WP-05); tan grip and tan magazine ambiguity (WP-07) | Gap; measurable |
| Hand and arm anatomy that holds up under animation | Fingers with joint structure and plausible grips, with weight and secondary motion on inspect and reload | Tube fingers, putty gloves (WP-02) | Largest gap; reviews unanimous |
| Animation craft: anticipation, weight, follow-through, readable key poses on reload | A reload with legible beats and each hand's job clear | Same magazine back in (RL-01), inspect-like show step (RL-02), no draw/inspect | Gap; the uncommitted work addresses structure, not craft |
| Material response: metal that looks like metal, wear that tells a story, controlled specular | Authored PBR with consistent edge wear, believable speculars under a few well-chosen lights | Authored rifle with baked occlusion; flat pistol grip (WP-08); GL Compatibility constrains lighting (EV-04) | Partial |
| Environment consistent with the weapon's fidelity | Props and surfaces at a comparable level | Box geometry (EV-01) | Large gap |
| Feedback: muzzle, impact, casings, sound | Layered, readable and loud-but-clean effects | Flash unreviewed (FX-01); casings tiny (FX-02); two synthesised clicks (RL-10) | Gap |
| Interface clarity: a HUD that disappears until needed, large readable numerals, consistent iconography | Spare, high-contrast, confident | Contrast measured and corrected (UI-06); HUD collisions at large text fixed (UI-07); circles over the weapon (UI-09) | Partial |
| Inventory and economy presentation: item inspection with good lighting, clear rarity language | A viewer that shows the item well, with legible rarity | Flat glyphs for weapons on the requisition screen (WP-09); card lists (UI-11); no 3D inspect | Gap |

### 4.2 What to take and what to leave

**Take (as principles, not forms):** clear value hierarchy; restraint; a small number of excellent assets before breadth; animation judged in motion on the target device; effects tuned for readability at speed; a viewer for items that shows them well.

**Do not take:** any CS2 name, logo, map layout, weapon shape, colour scheme, sound, UI layout, case or item design, or marketplace presentation. The project's own rule (original IP) already says this. The benchmark is a bar for *craft*, not a source for *content*.

**Identity guardrails** (derived from the project's design documents; confirm with the owner): the operational, desaturated-with-one-accent palette; the "requisition" and "operation" vocabulary; earned-only Credits with no urgency; mobile-first controls and sizes; original weapons and operators. Any backlog item that conflicts with one of these should be rejected or rewritten.

### 4.3 Where mobile-first overrides the benchmark

A shooter benchmarked on a desktop with a mouse and a 27-inch monitor does not transfer directly to a 6-inch touchscreen. The things that must differ on mobile: larger physical targets (AC-01); fewer simultaneous HUD elements; effects tuned to the GPU budget (WP-10); shorter sessions with explicit interruption handling; a viewmodel that frames well in landscape with two thumbs covering the lower corners. "CS2-class" on a phone is a distinct target from "CS2-class" on a PC, and nobody has defined it in measurable terms. That definition is a backlog item (B-22).

## 5. What automated evidence can and cannot show

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Layout sweeps (e.g. 5 sizes × 4 scales × 4 names; 36 sheet configurations) | No overlap, no overflow, minimum sizes met, buttons reachable, in the configurations listed | That text is readable at a real size, that hierarchy is clear, that the screen is pleasant |
| Contrast probe on rendered frames | A measured ratio against the pixels behind each label on a software-rendered frame | Legibility on a phone panel, in sunlight, for low-vision users; whether 4.5:1 is the right bar |
| Backend-derived fixture and drift check | The client displays what the backend's serialisers produce | That the live service matches in all states; one live run exists (EC-10) |
| Payload-parity tests | The client posts the documented fields and nothing on decline | That the UI makes the consequences clear |
| Negative controls | The tests can fail for the listed defects | That the listed defects are all there are |
| Pose sampling, contact CSV, on-screen pixel counts | Where geometry is in a frame, and whether limbs interpenetrate | That a hand looks like a hand, that a reload reads as a reload, that it feels good |
| Luma separation measurements | A numeric gap between values in specific lighting | That the gap is enough on an OLED phone outdoors |
| Authority/lifecycle tests | Animation does not change ammunition, cancel or complete | Nothing about appearance |
| Performance on llvmpipe | Relative cost of features on a software renderer | Phone frame time, thermals, battery |
| AI reviewer scores | One agent's structured opinion under a rubric | An independent acceptance; see C-01…C-04 |

The sentence this table protects: **a passing test does not prove that something looks or feels right.** None of the documents in this folder, and nothing in the backlog, should be closed on test results alone where the item is perceptual.

## 6. Gaps that need a phone or a person

Collected from §2 and detailed in [`HUMAN_AND_DEVICE_TESTING_PLAN.md`](HUMAN_AND_DEVICE_TESTING_PLAN.md):

1. **Physical size** of controls and text on at least two real phones (AC-01).
2. **Frame time, thermals and battery** with the viewmodel and effects on a mid-range and a low-end device (WP-10).
3. **Daylight and OLED legibility** of HUD, menu and the dark viewmodel values (WP-05, UI-06).
4. **Thumb reach and occlusion**; HUD circles over the weapon (UI-09).
5. **Safe area on real devices**, notches, rounded corners, gesture bars (UI-04).
6. **First-use comprehension** of the armory loop: finding, opening, equipping, seeing the result (§2.2).
7. **Trade and market comprehension**: what a person believes they are agreeing to on the confirmation sheet (EC-08).
8. **Reload legibility**: whether a viewer, unprimed, can say what the hands are doing at each beat, with and without sound (RL-01…RL-07).
9. **Colour-vision and low-vision review** of rarity, squads and the odds table (AC-02).
10. **Screen reader** behaviour on both platforms (AC-05).
11. **Interruption handling**: calls, backgrounding, network loss in the middle of a purchase (EC-02).
12. **Perceived fairness of pacing** of Credits and cases (EC-05).
13. **An outside artist's review** of the first-person assets against a professional standard (R7, R11).

## 7. Limits of this synthesis

- It reads documents, comments, a few captures and code descriptions; it did not play, rebuild or re-render anything.
- It does not view video sequences; frame tables and contact sheets stood in.
- It has one author, who is from the same model family as several of the cited reviewers.
- It treats the uncommitted two-magazine work only by its description; it did not build it, per the owner's instruction.
- CS2 comparisons are expectations from general knowledge (E), not observations.
