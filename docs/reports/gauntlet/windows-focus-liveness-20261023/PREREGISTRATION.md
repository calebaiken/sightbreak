# Windows focus recovery liveness fence

Source-only component, registered before implementation on 2026-10-23.
Base `b2e0293a546961230afbd73e5cd2a1a307d69e94`; own branch
`codex/windows-focus-liveness-fence-20261023`. Builder approval is prohibited.

## Inspected bar and failure

The engineering bar is the actual Windows run 39907358390, job 120262263075,
at the base above: original `offline-input/actions.json`, `results.json`,
`restart-profile-trace/events.jsonl`, `status.json`, PNGs and receipt archives
retained by the independent critic in
`windows-combined-recovered-20261023`. The existing native menu-focus suite,
offline capture-fence controls and current controller were read. No shipped-game
or physical input-latency comparison applies.

The last living held-input sample is tick 1140, health 24.1382732200623. The
11b raw screenshot visibly shows 005 HEALTH. A later original alive event at
tick 1166 records health zero; release acknowledgment at tick 1192 is already
dead with `waiting_for_input_release=false`. The controller then presses W
and reaches its original ten-second movement timeout. That trial cannot
qualify a living actor's response to fresh input. Exact capture spans and raw
before/after states will be recomputed without assigning causality to capture
cost, bot code, diagnostics or another source delta.

## Declared change and gates

1. Add a controller-only fence for a living, positive finite-health local actor
   in the original live round, actor identity, standard scenario, schema/scope,
   simulation speed and required UI context. Enforce it before the fresh W-down
   boundary and for each fresh observation considered by the focus stage.
2. Record `FOCUS_PRECONDITION_LOST`, reason, stage, the original baseline,
   previous valid state and rejected raw state separately from a response wait.
   Partial focus receipts must survive failure. A dead or replacement actor,
   later round or phase cannot be accepted because it moved.
3. Keep the original ten-second response wait, whole-flow deadline, other stage
   budgets, all named captures, held-control release `finally` blocks and held
   neutrality checks. Add no retry, life selection or compensating deadline.
   Source/game bytes, health, bots, economy, protocol and export stay unchanged.
4. Pure counterexamples must dispatch no W-down for death before key, fail
   immediately for death during wait (including a simultaneously moved dead
   actor), actor/round/phase changes and invalid health; valid living movement
   must pass. Retain raw before/after values and test timeout/release handling.
5. Run only appropriate Python controls and source/diff checks. No engine,
   import, UID, native input, OCR, export, CI or service execution is authorized.
   An independent critic must judge the frozen source before any later run.

## Retry proposal boundary

Propose, but do not implement or run, the smallest ordinary-input schedule
change supported by the measured timeline. It must preserve stock rules,
bots, health, all captures, held-input contracts and original deadlines, with
no selected seed or automatic hunt for a surviving trial. An inconclusive
precondition loss remains a failed qualification attempt. Plant/guidance and
all-defender elimination are a separate trace; device resolution, next buy
and its restart remain unqualified and its gameplay rule is outside this work.
