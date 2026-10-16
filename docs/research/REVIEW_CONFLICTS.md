# Where reviews, documents and measurements disagree

Each entry gives the two positions, the evidence behind each, my reading, and what would settle it. "My reading" is an opinion (class A/R) from an author who shares a model family with some of the reviewers; it is offered to help the owner decide, not as a ruling. IDs refer to [`EVIDENCE_LEDGER.md`](EVIDENCE_LEDGER.md).

All reviewers to date are AI agents posting under one GitHub account (PR-8). "Claude agent" and "Codex agent" below name the model family only; neither is a human, and neither is an outside professional.

| ID | Subject | Status |
| --- | --- | --- |
| C-01 | Whole-game visual score: 8.1 or 6.6 | **Open**; unresolvable without a shared rubric and human raters |
| C-02 | Weapon-and-arms score: 4.5, 5.5, 4.5, 6.1 | **Open**; the series is not a trend |
| C-03 | UI accessibility 7.0/10 against the derived physical size | **Open**; settled by a phone and a ruler |
| C-04 | "The arms enter neither the rifle nor the magazine" against a 1.33 mm exception | **Resolved** as a documentation imprecision |
| C-05 | Retired score in `KNOWN_LIMITATIONS.md` against later reports | **Resolved** by an edit, not yet made |
| C-06 | Reduced motion: "attenuate staging" against "reload must stay legible" | **Resolved** in code on the uncommitted branch; unverified |
| C-07 | Was the black magazine a lighting problem? | **Resolved**; first diagnosis wrong |
| C-08 | "Layout holds at 16:9, 20:9 and 4:3" | **Resolved**; claim withdrawn |
| C-09 | Aspect policy: bars (`keep`) or wider world (`expand`) | **Open**; a product decision |
| C-10 | Trade confirmation: plain-text terms or item cards | **Open**; design option, to be tested |
| C-11 | "Magazine on screen" against "reload legible" | **Resolved** as a measurement point; the better measure is uncommitted |
| C-12 | Whether the new muzzle flash is an improvement | **Open**; no second observer |

---

## C-01 Whole-game visual score: 8.1 (Codex, `QA-0.3`) against 6.6 (Claude audit, `CLAUDE_AUDIT_0.3`)

**Position A.** `docs/reports/QA-0.3.md`: 8.1/10 for visual presentation. **Position B.** `docs/audits/CLAUDE_AUDIT_0.3.md`: 6.6/10 on the same baseline captures.

**What is known.** Both were applied to the same baseline captures by different agents. I did not find a single shared rubric; from the two documents the categories and the stated reference level appear to differ, which I have not audited line by line (R). `KNOWN_LIMITATIONS.md` still quotes 8.1 as the 0.3 position (PR-7).

**Why it matters.** The 8.5 gate in the mission statement is only meaningful against a defined scale. A 1.5-point spread on identical inputs is larger than most of the improvements the reviews measure afterward.

**My reading.** Both are probably defensible under their own rubrics. 8.1 reads as "complete, consistent, no defects in scope" and 6.6 as "gap to a professional standard". The score is therefore partly a measure of *which question was asked*. I would not cite either as "the" score.

**What would settle it.** (1) Publish one rubric with anchored examples (what a 4, 6, 8 look like), fixed weights and the benchmark level stated. (2) Rate the same frames blind, with at least three human raters including one outside artist, plus the agents, and report the spread. (3) Until then, report scores as `score (rater, rubric id, commit)` and never as a single number.

## C-02 Weapon-and-arms: 4.5, 5.5, 4.5, 6.1

**Series.** 4.5 (Claude agent, `2bba519`) · 4.5 (`5100b3e`) · 5.5 (Codex, `64ec598`) · 4.5 (Claude agent, `b507205`) · 6.1 (Codex, `68251a0`). Gate 8.5; "CS2-class" placed near 9 by the reviewers.

**What is known.** Rubrics, weights and commits differ. The two Claude-agent scores are 4.5 on commits two revisions apart; the two Codex scores are 5.5 and 6.1. The reviewer family explains more of the variance than the commit does. The only anatomy change since `b507205` is a fanned grasp (WP-02), yet the Codex score rose 0.6 and the Claude score is untested on `68251a0`.

**My reading.** I cannot say whether the weapon improved by 1.6 points, by 0.6, or not at all. Measurable improvements are real (bore 10.0° → 3.5°, WP-04; static hands attached, WP-11; magazine un-blackened, WP-06), but each is a defect fix, not evidence the hands read better.

**What would settle it.** Same as C-01, plus: show the same fixed set of stills and a clip to human raters unprimed, and ask the same five questions ("what are the hands doing", "which part is the magazine", "does the weapon look real", "do the hands look like hands", "would you rather hold this or that"), before showing any score.

## C-03 UI accessibility 7.0/10 against the derived physical size

**Position A.** Codex rated accessibility 7.0/10 on the layout evidence (functionality 7.5). **Position B.** AC-01 derives that a 48 px target is about 4.3 mm and 14 px text is 1.3 mm on a 6.1-inch phone.

**What is known.** The reviewer evaluated layout, text scaling, contrast and reduced motion in pixels on a desktop frame. Physical size was not in the review's frame. AC-01 is arithmetic from published phone geometry and the project's stretch mode; it is unmeasured.

**My reading.** The two are not in direct conflict, but the 7.0 should not be read as covering physical legibility. If AC-01 holds, the true score for "usable by a thumb on a phone" is lower than 7.0 whatever the layout tests say. If AC-01 is wrong (for instance the game is expected only on large tablets, or an engine factor offsets it), the concern disappears. I rate the concern credible (D), not confirmed.

**What would settle it.** Install a debug build on two phones (a small and a typical one); measure the rendered height of the HUD buttons and a line of body text with a ruler or a calibrated screenshot; run the 7–9 mm / 2.2–2.5 mm comparison; record in `DEVICE_TESTING.md`.

## C-04 "The arms enter neither the rifle nor the magazine" against a 1.33 mm exception

**Position A.** `DEVELOPMENT_STATUS.md` states the arms enter neither. **Position B.** The contact review (`clip_contact.csv`) records the right arm's trigger finger 1.33 mm inside the rifle; the evidence README states this.

**Resolution.** Documentation imprecision (RL-08). The geometry is as measured; the status line omitted the exception. Fix by editing the status line to include it. No dispute about the data.

## C-05 Retired score in `KNOWN_LIMITATIONS.md`

`KNOWN_LIMITATIONS.md` still states 8.1/10 as the 0.3 position while later documents carry 6.6 and the weapon series (PR-7). This is stale text, not a disagreement of fact. Fix by replacing the number with a pointer to C-01 and the rule "report `score (rater, rubric, commit)`".

## C-06 Reduced motion: attenuate staging, or keep the reload legible

**Position A.** Reduced motion should reduce motion, so staging lift was scaled to 20 % (`reload_tilt *= 0.2`). **Position B.** Codex measured that at 20 % the support hand falls below the frame at 20 % progress and the magazine is 77–92 % on screen (RL-03), i.e. reduced motion made the reload harder to read.

**Resolution.** Reduced motion is a request to remove *vestibular* triggers (large camera motion, sway, tumbling), not to remove the information carried by the reload. The uncommitted work stops scaling the staging and hides the old magazine instead of tumbling it. That is the right reading (my opinion), but unbuilt and unverified. Settled by the hand-in-frame metric on the reduced-motion path, and by someone who uses the setting.

## C-07 Was the black magazine a lighting problem?

**Position A (first diagnosis).** Weak light; confirmed by a coarse measurement. **Position B (correction).** The ambient occlusion had been baked while the magazine sat in the well; per-pixel occlusion found the cause (WP-06, PR-5). **Resolved** in favour of B, and the fix is committed. It stays on this list as a reminder that a confirming coarse measurement is not proof (R2).

## C-08 "The layout holds at 16:9, 20:9 and 4:3"

The author's claim was false; the captures were at 1280 × 720 and 1024 × 576 and were resized (PR-1). Withdrawn in `VISUAL_QA.md`. The aspect behaviour that is now documented comes from `MOBILE_ASPECT_REVIEW.md`, which measures the actual `keep` policy (EV-05). **Resolved.**

## C-09 Aspect policy: `keep` (bars) or `expand` (wider world)

**Position A (shipped).** `keep`: the 16:9 frame, bars on wider or taller screens, 114.19° horizontal world FOV at every size. **Position B (alternative).** `expand`: wider screens see up to 125° horizontally.

**Trade-off.** `keep` gives every player the same competitive view and one tested layout; it wastes screen on 19.5:9 and 20:9 phones. `expand` fills the screen but changes the visible world (competitive fairness) and the HUD's anchor geometry. Not a defect either way (EV-05).

**What would settle it.** Product intent (is fairness across devices a requirement?), plus the first look of a real phone in landscape: do bars read as a defect to users? Test with five or more people on a 20:9 phone before deciding.

## C-10 Trade confirmation: scrolling plain text or item cards

**Position A (shipped).** Pinned summary line and buttons, terms as one scrolling wrapped block. **Position B (alternative, open in the evidence README).** A table or card per item, with inspect.

**What is known.** The shipped sheet is bounded and tested at 36 configurations (UI-01). Whether people read a scrolling text block before accepting a 20-item trade is H. A mistake in a trade is costly; item-level visuals reduce the chance of confusing similar finishes (finish names lead cards for the same reason).

**What would settle it.** A task-based session: give participants a trade with one deliberately unfavourable item among twenty and see whether each variant leads them to catch it. That is the success criterion in the testing plan (T-06).

## C-11 "Magazine on screen" against "reload legible"

`art-v6` reports the magazine at least 94 % on screen and at most 1 % covered from the grasp to the let-go (RL-07). Codex re-measured and agreed on the numbers but noted the hand was not measured. The author conceded that "in frame" is not "legible". The hand-in-frame metric exists only in the uncommitted probe, whose "apart" expression I last saw still giving a nonsensical result (unfixed at the time of the pause). **Resolved as a point of method.** The perceptual question remains (testing plan T-08).

## C-12 Whether the new muzzle flash is an improvement

The flash was rebuilt as a layered additive mesh (FX-01). I read the committed burst as still starry (A). No other observer has judged it. Do not record it as fixed or as not fixed; it is unreviewed. Settle it with a short clip viewed by two or more people, a photosensitivity check (flash frequency and area), and a look at it on a bright phone screen.

---

## Conflicts that are not conflicts

- **Process vs evidence.** Several documents say the work is "accepted in scope". That means a reviewer agreed a specific correction fixed a specific finding (e.g. the HUD in PR #1). It does not accept the whole product, and I have not read any such statement as a general acceptance.
- **"Independent".** The independent reviews cited are independent of the *author's session* only. They are the same account, and one family shares a model with the author. This is the main reason I treat all scores as opinions.
