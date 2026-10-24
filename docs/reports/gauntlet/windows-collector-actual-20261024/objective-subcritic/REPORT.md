# Actual objective and full-match subcritic

The actual run demonstrates the enumerated player-objective and earned offline
progression behaviors below. It fails the preregistered zero-warning requirement:
all six plant/defuse/full-match client and reopened logs contain the OpenGL 3.3
fallback-to-ANGLE warning at line 2. These behavioral observations do not qualify
the run or override the parent's separate living-journey failure.

This review covers run 40080238905, job 120832097220, exact source
`c32415148db1f110bbc7eadfca3793d4693429ff`. It uses only the parent's official
`.local/windows40080238905/receipts/evidence` and `full` extractions. Thirty selected
scenario files match their official full-QA counterparts byte-for-byte; see
`official-copy-comparison.json`. This comparison supplies no archive-completeness
claim. Job-log lines44115,45038 and46007 retain the original180/180/1800-second
scenario commands. The scenario receipts agree on clean source, game tree
`bca627d5dc8e4482b63e263020a6382f2d36f33c`, and executable SHA256
`35672b0d19dc3cb8bda429f71b0c4512e8184059a0f48176ace23411d1e46e70`.
The native executable was not independently downloaded by this subcritic.

`audit-final.json` contains raw facts, original source anchors and individual
predicate statuses. It has 26 satisfied predicates for plant, 25 for defuse and 25
for full-match. Each scenario also has one unsatisfied zero-warning predicate;
none of the final rows is unavailable. These counts describe the enumerated
reconstruction, not whole-gate acceptance. Original native pass and partial flags
remain reported facts and do not supply predicate results.

| Raw observation | Plant | Defuse |
|---|---:|---:|
| Final native consumed-E start/completion ticks |1371→1551|1402→1702|
| Authoritative hold |180ticks /≈3s|300ticks /≈5s|
| Local contribution |0→1|0→1|
| Match funds |800→1100|800→3800|
| Completion actor |Same local actor, alive100HP|Same local actor, alive100HP|
| Natural resolution |Device defused; attacker dead0HP|Device defused; defender alive100HP|
| Conservative next-buy wall upper bound |4.672s|4.484s|
| Final receipt wall time |67.016s|56.890s|

Both scenarios retain seed 42 declared initial layouts, original rules,
protocol 6/default-off prediction, fresh zero training and ten living 100 HP
actors. Raw actions record out-of-range rejection and an interrupted hold that
progresses then resets to zero without contribution. The final hold begins from
known-zero progress in the eligible live state. Each final hold has exactly one
authoritative held-E edge and one completion notification; elapsed/tick lower
bounds satisfy the original one 60 Hz-tick tolerance. Legitimate authoritative
approach and native role/carrier conditions are reconstructed separately.

The plant's800→1100 is the capped ordinary300 objective award. The defuse's
800→3800 is300 objective plus2700 winning-round award in the same post transition.
Score calculations use full raw snapshots, not slim notification records. Raw
actions/events cover natural device resolution and next-round buy within the
original12s limit. The plant attacker is alive 100 HP at post-plant role observation
and capture, then dies before natural device resolution. The resolved PNG visibly
says ELIMINATED/SPECTATING; no living-through-resolution claim follows.

Neither objective run retains an `offline_training.json` file. Both reopened
commands are ordinary launches without validation/scenario flags. Their original
reopened PNGs display the default local record: level1,150XP to level2, zero
credits/matches/wins/eliminations/deaths. This supports normal default-profile
restart. It does not prove loading an earned disk profile or establish a saved
runtime-profile equality transaction for those incomplete matches.

The full stock match records all natural rounds 1–12 and the halftime team switch.
Its final score is 6:6 DRAW. The complete 5v5 roster has ten unique IDs and exactly
one human, whose0kills/0assists/11deaths/0objectives match the summary and rendered
roster. There is exactly one completed event, no duplicate-completion event and
zero dropped diagnostic events. The retained original status has one completion;
the reopened stock buy status has zero.

The first stock live actor starts sidearm 15/60. Raw action snapshots show
authoritative displacement about 1.254 m and changed aim, actual depletion to 14/60,
nativeR reload countdown, then 15/59. Ammunition totals are conserved. This is
delivered automated native input, not human input-feel evidence.

Earned progression is recomputed from the raw completed summary:

```text
XP = 0 +120 +15×0kills +50×0objectives =120
level =1 +floor(sqrt(120/150)) =1
credits =100base +0win +150first-daily +0level =250
```

The final local training profile has 120 XP, level 1, 250 credits, one match, zero
wins/kills and 11 deaths, with exactly one matching history entry. The daily marker
changes from empty to 2026-10-24. Settings remain unchanged. The actual isolated
AppData save, raw completion `training_after`, controller training receipt and
reopened stock match's raw `initial_profile` are equal. The disk save is 3194 bytes,
SHA256 `9373e73164684f22ab80e48c8096161ece1c45297cb17efe8c14f1b780019e6b`.
The reopened stock match remains in buy with zero completions and the final disk
profile still equals earned training. This establishes the bounded earned
disk/runtime restart transaction. The fresh HUD's800FUNDS are match funds,
separate from the250 training-credit record.

Twelve original 976×549 PNGs were directly inspected with `view_image`.
`visual-observations.json` retains every image SHA256, size and concrete
observation. They visibly corroborate the living plant role, successful living
defuse, default objective menus, DRAW6:6/12rounds result with+120XP/+250credits,
ten-row final roster, earned reopened menu, and fresh stock buy HUD. No OCR,
image transformation, blind comparison or aesthetic score was used.

Both native roots exit 0 for each scenario; retained command exits and cleanup
error arrays agree. The original `native_log.py` error/resource-leak regex finds
no error/leak in these six logs. It does not reject the renderer WARNING. The
preregistration explicitly says warnings/leaks remain failures at line 195, so
all three scoped zero-warning rows are unsatisfied. No local engine/native
execution, input, cleanup, source edit, workflow action, commit or push occurred.

The retained audit attempts and corrections are documented in `ATTEMPTS.md`.
Physical hardware, human play, performance, collector completeness, online
wallet/inventory rewards and whole-release acceptance remain outside this review.
