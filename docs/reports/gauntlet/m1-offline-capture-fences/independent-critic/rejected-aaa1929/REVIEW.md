# Independent capture-fence source review

**Verdict: REJECT `aaa1929` for two source acceptance gaps. Native pixel acceptance is pending.**

Reviewed candidate `aaa192903a8e5e333abcf9ada7741e13145a123e`, parent criteria
`3e3b40a3d532fbcb3d5a561a5d81bf84772a1dab`, base
`9d11f1dc4ebc31ad3beea7594b6868ef437bb0d8`, on 2026-10-22. This is a separate
read-only critic's report. Only this external review directory was written.
Product source, canonical mission documents and the candidate branch were not
edited. Installed gauntlet-loop, sightbreak-gauntlet, no-ai-slop and its eval
were read and reused. No skill was reinstalled. No Godot, renderer or OCR ran.

## Blocking findings

1. **Counter regressions inside the two-frame wait are accepted.** In frozen
   `scripts/verify_offline_export.py:155–160`, `rendered` compares each sampled
   counter only with the acknowledgment. It does not retain an intervening
   unready sample. The independent sequence has fresh increasing native wall
   observations and drawn frames `1142 → 1143 → 1142 → 1144 → 1145 → 1146`.
   The function captures and returns success. Physics tick rollback
   `6814 → 6815 → 6814 → 6816` also passes. This contradicts preregistered
   criterion 3's monotonic fence. The committed control tests only rollback
   after `ready` or after capture, so all 13 test groups pass despite this gap.
   Track the last validated fresh counters through every predicate evaluation,
   including samples that do not yet provide two frames. Add the exact
   intermediate rollback controls.

2. **The accepted post-capture state can have been published before capture.**
   Lines 173–188 read `before_capture`, perform a potentially costly source and
   profile binding check, capture, then require only a state newer than
   `before_capture`. The status producer may publish a newer valid state during
   the binding check and stop. That existing publication is sufficient for
   `after_capture`. In the independent declared schedule, the accepted state is
   published at driver time 0.4, capture begins at 0.5 and ends at 0.6, and the
   unchanged state is read at 0.7. The capture callback declares phase/life loss
   during capture, yet the transaction succeeds. Native observer clocks were
   not equated with driver clocks. This is a scheduling counterexample, not an
   assertion that any new native image has this failure. Preregistered criteria
   3–4 require stale observations to remain unready and a fresh post-capture
   observation. Read a post-capture barrier and require a strictly later
   publication before accepting the transaction, within the existing deadline.

`reproduce.py` imports the retained exact candidate observer, implements its own
production-shaped polling callback, and reproduces both counter rollbacks and
the pre-capture publication acceptance. `reproductions.json` retains every
declared polling sample and outcome. It does not import the builder's callback
test harness. The assertions verify that these three gaps remain reproducible;
their successful exit is evidence of rejection.

## Evidence checked

- The original Windows CI39728129445 PNGs were opened directly. `06c` displays
  ROUND 01 / POST and ELIMINATED / SPECTATING; `10` displays the main menu.
  These are the correct regression references. The candidate's reference bytes
  exactly match the full official archive, with SHA-256
  `146e4b8370b021411eb2d2ad2379e8d39f41179a04cf04f38cb9d5ac7031bf46` and
  `c72ca7c9da99aad6641c8c4f1a808d692f27133f68a0196edfd8e02b5d5b2674`.
- Each of the three fixture event objects exactly equals an original raw JSONL
  object: initial trace phase event index 17, initial trace phase event index 19,
  and restart trace initial event index 0. Both event-file hashes match fixture
  provenance. Declared subsequent states are correctly labeled as controls.
- Original actions retain capture intervals 162.906–163.265 seconds (`06c`) and
  208.906–209.093 seconds (`10`). They contain no exact same-process state/frame
  bracket for those named images. Later functional journey success does not
  repair either image.
- The 160-second natural-round log wait and 30-second loaded-profile wait now
  share absolute deadlines with the added helper. The 300-second default whole
  journey and existing input operations remain unchanged. Helper expiry checks
  prevent an over-deadline transaction from being accepted. Native capture
  itself retains the existing synchronous call and can only be judged on the
  original timing receipts during the later native run.
- Reopened tracing switches before new current-state reads. Binding checks pin
  repository source, current native process/PID and trace resolution before
  acknowledgment and around capture. The reopened first loaded event and disk
  profile must equal the initial accepted stock event and saved profile.
  Source/process/trace/profile mutation controls reject sampled mismatches.
- The baseline-to-candidate diff changes no `game`, `backend`, `server`, AGENTS,
  CLAUDE, canonical engineering or roadmap files. The diff passes whitespace
  checks. Modified maintained validation only adds the pure control invocation.

## Replayed controls and limits

The exact frozen builder suite passes 13 groups. Five caption controls pass.
Four native-observation filesystem cases pass and three Windows-only cases skip
on this Linux host. Their original stdout/stderr is retained here. These runs
are pure Python and filesystem checks; they neither invoke OCR nor establish
native renderer behavior. Their pass does not override the counterexamples.

The largest remaining gap is trustworthy new native output at the two named
boundaries. First correct the two acceptance gaps and freeze source again.
Account qualification owns the CPU lane; native work requires its release and
root coordination. Then retain an exact-source native slice, complete raw
captures, state/frame/action brackets, original budgets and any failures. An
independent pixel critic must find the living round-2 buy HUD in `06c` and the
reopened living game HUD in `10`. Source review and declared fixtures cannot
approve those pixels or close the full ordinary journey gate.

Reproduce from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reproduce.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/sightbreak-capture-fences/scripts python3 frozen/scripts/test_offline_capture_fences.py -v
```

The frozen observer depends on the unchanged utility modules in that worktree;
their hashes are retained in `source-provenance.json`. The complete raw reference
archive remains `/workspace/reviews/native-ci-39728129445`.
