# Human and device testing plan

**Status: a plan, not results.** Nothing in this file has been run. No participant exists, no device has been used, and no number here is a finding. It lists the questions the repository cannot answer, with success criteria fixed *before* anyone looks at data, so the results cannot be bent to fit afterwards.

References: findings in [`EVIDENCE_LEDGER.md`](EVIDENCE_LEDGER.md), conflicts in [`REVIEW_CONFLICTS.md`](REVIEW_CONFLICTS.md), backlog items (`B-…`) in [`IMPLEMENTATION_BACKLOG.md`](IMPLEMENTATION_BACKLOG.md).

## Ground rules

1. **Report what happened, verbatim.** Record quotes as spoken. Do not summarise a participant into agreement.
2. **Sample sizes are small and say so.** Five to eight participants per usability task finds most large problems; it does not estimate rates. Report counts ("4 of 6"), never percentages, and never call a result "significant" without a design that supports it.
3. **No AI agent counts as a participant, a rater or a facilitator-substitute** for any test below. Agents may prepare materials and tally results.
4. **Pre-register the pass criterion** (below) in the session notes before the first participant. Changing it afterwards must be recorded as a change, with the reason.
5. **Unprimed first.** Ask what the person sees before telling them what it is supposed to be. Show no scores.
6. **Consent and privacy.** Tell participants what is recorded; record nothing beyond screen, voice and notes needed; fictional accounts and fictional Credits only; no real payment instrument ever appears.
7. **No real-money payments.** The economy tasks use fictional balances on a local or test backend.
8. **Write down the build.** Every session records the commit SHA, device model, OS version, display settings (brightness, text size, reduced motion), and whether the build is a debug or a release export.

## Equipment and participants

| Need | Minimum |
| --- | --- |
| Devices | One small phone (about 5.5–6.1"), one typical modern phone (about 6.5–6.8"), one low-end Android phone. An iPhone if iOS is in scope. Names to be fixed by the owner (D-2) |
| Measurement | A millimetre ruler or calipers; a phone-mounted screen recorder; a lux meter app or a known window/sun condition for the daylight test |
| Participants | Five to eight for usability tasks; at least two with substantial mobile-shooter experience and two with little; at least one with colour-vision difference; at least one who uses larger text or reduced motion in their OS. Recruit with the owner's consent; do not recruit minors without guardian consent |
| Raters (artwork) | At least three humans who are not the author, one of them an outside artist (D-6) |
| Builds | The debug build with the commit SHA shown on the menu (the build line already does this) |

## Tests

Each test has: the question, method, measures, **pass criterion fixed in advance**, and what a failure triggers.

### T-01 Physical size of controls and text (device; B-01, AC-01, C-03)

- **Question.** Are targets and text at least roughly the usual physical size on real phones?
- **Method.** On each device, at 100 % text scale, capture a screenshot; measure with the ruler the on-glass height/diameter of the FIRE, FRAG, SMOKE, USE and SWAP controls, the ammunition numeral, and one 14 px caption and one 16 px body line in the armory. Repeat at 130 % text scale. Compute mm per canvas px per device.
- **Measures.** mm per canvas px; target size in mm; x-height or cap height of text in mm.
- **Pass.** Primary touch targets ≥ 7 mm; essential text cap height ≥ 2.2 mm at 100 % on the typical device. (These are the common guidance figures cited in the synthesis; the owner may set stricter ones.)
- **Failure triggers.** A decision to rescale `TOUCH_COMFORT`, `TEXT_FLOOR` and the safe margins as a function of physical size (B-01), then re-run the layout suites.

### T-02 Daylight and OLED legibility (device; B-07, UI-06, WP-05)

- **Question.** Can menu text, HUD numerals and the viewmodel's darkest areas be read outdoors and at low brightness?
- **Method.** At a fixed brightness (100 % and 30 %), indoors and in shade/sun, read aloud a fixed list of 12 strings (menu, HUD, armory) and point to the magazine, the left glove and the sleeve in three viewmodel frames.
- **Measures.** Strings read correctly, time, which targets were identified.
- **Pass.** Every string read correctly by every participant at 100 % brightness in shade; the magazine, glove and sleeve identified by at least 5 of 6 in each lighting condition.
- **Failure triggers.** Value and contrast corrections; palette separation work (B-07).

### T-03 Thumb reach and occlusion (device; B-11, UI-09, AC-06)

- **Question.** Do the on-screen controls reach under the thumbs without hiding what the player needs, and does the default layout suit different hand sizes?
- **Method.** Two-thumb landscape hold; a scripted set of actions (move, look, fire, reload, swap, FRAG, SMOKE, USE) on a practice map; record where thumbs rest and what is covered. Ask which control was hardest and why. Test the default layout and one customised layout.
- **Measures.** Missed taps per action; actions the participant could not reach; areas covered by thumbs; quotes.
- **Pass.** No control is unreachable for any participant without shifting grip; no more than 1 in 10 taps misses for any control after a one-minute warm-up.
- **Failure triggers.** Move or resize controls; offer layout presets for hand size.

### T-04 First-use comprehension of the armory loop (people; B-13)

- **Question.** Can a new player find their cases, open one, equip the result and see it in the first-person view without help?
- **Method.** Moderated, think-aloud, fictional account with one case and one key. Task: "Get a new look for your rifle and show me it in the game." No hints; the facilitator intervenes only after two minutes of no progress and records the intervention.
- **Measures.** Completed unaided (yes/no), time, wrong taps, interventions, comprehension questions after ("what did the percentages mean?", "what would happen if you pressed OPEN CASE again?", "how did you earn these Credits?").
- **Pass.** At least 5 of 6 complete unaided; at least 5 of 6 correctly say that odds describe the chance of each outcome; at least 5 of 6 say Credits are earned in play.
- **Failure triggers.** Rework the flow and its wording; do not add features until the loop is understood.

### T-05 Failure and recovery comprehension (people; EC-01, EC-02)

- **Question.** After a failed or lost purchase, does a person know whether they were charged and what to do?
- **Method.** Simulate (on the test backend): server unreachable; server rejects; answer lost after the request. For each, ask "What happened? Were you charged? What would you do now?"
- **Measures.** Correct answers per state; verbatim reasons.
- **Pass.** For all three states at least 5 of 6 give an answer consistent with the true state (not sent / refused / unknown) and say what they would do.
- **Failure triggers.** Rewrite the failure copy; if people avoid the retry for fear of double charges, make the safety of the retry explicit (the idempotency key is already in place).

### T-06 Trade confirmation reading (people; B-20, EC-08, C-10)

- **Question.** Does the confirmation sheet lead people to notice what they give and what they receive, including a bad deal?
- **Method.** Within-subject, counterbalanced. Present trades of 5 and 20 items per side on the shipped sheet; one trade in each pair contains one clearly unfavourable item in the give list. Ask the participant to confirm or go back. Then show the item-card variant (if built) with a different trade of the same kind.
- **Measures.** Catch rate of the unfavourable item; time on sheet; whether the participant scrolled the terms; confirmation of the true summary line in their own words.
- **Pass.** At least 5 of 6 catch the unfavourable item on the variant that ships. If the shipped text block scores worse than the card variant by 2 or more participants, ship the cards (B-20).
- **Failure triggers.** B-20 becomes P1.

### T-07 Colour-vision and low-vision review (people and simulation; B-14, AC-02)

- **Question.** Are rarity, squad and odds distinguishable without colour alone?
- **Method.** (a) Simulated protan, deutan and tritan renderings of the rarity chips, squad markers and odds table. (b) A short session with at least one participant with a colour-vision difference: sort six items by rarity and name each squad marker. (c) With a low-vision participant or at 130–140 % text, repeat T-04's first four steps.
- **Pass.** Every state is distinguishable by text or shape in simulation; the participant sorts and names correctly; no step becomes impossible at the largest text size.
- **Failure triggers.** Add labels, patterns or shapes.

### T-08 Reload legibility (people; B-08, B-02, RL-01…RL-07)

- **Question.** Does an unprimed viewer understand what the hands are doing in a reload, including that a different magazine arrives?
- **Method.** Show the clip on a phone at full screen, no sound, then with sound. After each viewing, ask: "What is the left hand doing right now?" at five paused frames (reach, grasp, remove, insert, release), "Is the magazine that goes in the same one that came out?", "Does the hand look like a hand?", and "Rate how convincing this reload is on a scale you define for me".
- **Measures.** Count of correct descriptions per frame; the answer to the same/different question; verbatim comments; ratings reported with their reader's own scale.
- **Pass.** At least 5 of 6 describe the hand's action correctly at four of five frames; at least 5 of 6 say the inserted magazine is a different one (if the two-magazine work ships); at most 1 of 6 says the hands do not look like hands for B-06 to close.
- **Failure triggers.** Retime phases, change key poses, rebuild hands (B-06).

### T-09 Performance, thermals and battery (device; B-15, WP-10)

- **Question.** Does the game hold a playable frame rate on target devices for ten minutes?
- **Method.** Scripted ten-minute session on each device with the viewmodel and effects at default; record frame times (median, 95th and 99th percentile, hitches over 50 ms), device temperature or thermal state if exposed, and battery drop; repeat with the viewmodel disabled.
- **Pass.** Median ≤ 16.7 ms and 95th percentile ≤ 25 ms on the typical device; 95th percentile ≤ 33 ms on the low-end device; no sustained throttle collapse in ten minutes. (Targets are the owner's to set; these are a suggested starting point.)
- **Failure triggers.** Reduce the viewmodel's cost or add a quality tier.

### T-10 Safe area and interruptions (device; B-12, EC-02)

- **Question.** Does the game respect cutouts and survive being backgrounded, called, rotated or going offline?
- **Method.** On devices with different cutouts, check every screen for controls in an inset; trigger: incoming call, notification, home button mid-match, airplane mode mid-purchase, rotation, split-screen where available.
- **Pass.** No control or essential text in an inset on any device; the game never double-charges, never loses an in-flight purchase silently, and returns to a sensible state after each interruption.
- **Failure triggers.** Fix insets; persist pending receipts (B-21).

### T-11 Muzzle flash and photosensitivity (people and analysis; B-10, FX-01, C-12)

- **Question.** Is the flash readable as a flash, and does it avoid photosensitive risk?
- **Method.** Short clip on a phone for two or more observers: describe it; compare with a reference sequence they choose; separately, analyse the clip's flash frequency and area against accepted photosensitivity guidance.
- **Pass.** Observers describe it as a flash without prompting; the analysis finds no sequence that exceeds the guidance thresholds.
- **Failure triggers.** Adjust shape, duration, brightness; add a reduced-flash setting.

### T-12 Fairness of pacing (people; EC-05)

- **Question.** Does the pace of earning Credits feel fair?
- **Method.** After three matches on a fictional account, ask about the first opening: "How did that feel, and what would you change?" Record how many matches a participant says they would play for one case.
- **Measures.** Verbatim comments; stated willingness.
- **Pass.** No fixed pass; this is exploratory. Report the distribution and the quotes.
- **Failure triggers.** Revisit the provisional economy with the owner.

### T-13 Screen reader (device; B-26, AC-05)

- **Question.** What, if anything, does TalkBack or VoiceOver say on the menu and armory, and is it usable?
- **Method.** Turn on the platform screen reader; try to start a match and open a case with eyes closed. Record the announcements.
- **Pass.** Exploratory first: document what the engine exposes. A pass criterion is set after that, by the owner.

## Order and effort (rough)

| Block | Tests | Needs | Effort |
| --- | --- | --- | --- |
| A. One device afternoon | T-01, T-02 (own eyes), T-10, parts of T-03, T-09 | Devices, ruler, owner | About one day |
| B. First people session | T-04, T-05, T-06, T-12 together | 6 participants, fictional backend | 2–3 days including setup |
| C. Art review | T-08, T-11, plus an outside artist's critique (D-6) | Raters, clips, a phone | 1–2 days |
| D. Access review | T-07, T-13 | Specialist participants | 1–2 days |

## Reporting format

For each test: build SHA, device, date; method as run (deviations from this plan listed); raw counts; verbatim quotes; whether the pre-registered pass criterion was met; what changed as a result; what remains unknown. Put the report in `docs/research/sessions/<date>-T-xx.md`. Do not edit the ledger's classes without a session report to cite; evidence from these tests enters the ledger as **M** (measured) or **R** (human reviewer judgment), and human reviewers are labelled as such, separately from AI reviewers.
