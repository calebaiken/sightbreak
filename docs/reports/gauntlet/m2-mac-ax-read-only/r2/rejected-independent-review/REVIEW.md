# Independent source decision: REJECT

Exact rejected source: `cf4de47f5a94e64146dc3f6402da677c41d1b012`.
Handoff inspected: `455686ebda9a94326f112319b63f8e5f43ba8c34`.
Own preregistration: `709264ea`, recorded before implementation/test inspection.
This is a source/pure review; it authorizes no runtime or CI attempt.

The maintained twelve-command replay passes all 110 top-level methods in my
independently fetched exact depth-one checkout. Six additional native-boundary
pure methods run against those same frozen files: one positive control passes,
and five intended safety assertions fail. These failures require correction
before source approval.

## Blocking findings

1. **The declared 0.25-second call cap is not checked.**
   `scripts/probe_macos_ax.py:89` calls the API between two `guard()` calls, but
   each guard compares only with the five-second observation deadline. A fake
   `AXUIElementGetPid` that advances the actual patched monotonic clock from
   10.000 to 10.300 returns success while the whole deadline remains 15.000.
   Setting an AX messaging timeout does not let source accept a successful
   call that exceeds the registered per-call bound. The maintained late-call
   test replaces `guard()` with a function that raises, so it does not expose
   this missing elapsed-time predicate. Retain 0.25 seconds and explicitly
   reject late returns without resetting the five-second deadline.

2. **Post-call rejection loses owned Core Foundation references.**
   At lines 114, 132 and 196, a Create/Copy call can return its owned pointer
   and then encounter a deadline/window exception inside `call()`'s second
   guard. `application()` never reaches `hold()`; `attribute()` and `elements()`
   never reach either their immediate error release or `hold()`. Independent
   replays return pointers 0xA11, 0xA22 and 0xA33, raise on the post-call guard,
   invoke `close()`, and observe an empty release list in all three cases.
   A timely copied attribute is released correctly in the positive control.
   Register or release every Create/Copy result even when a post-call timing,
   ownership or geometry check fails; also keep the existing native-error and
   size-limit cleanup paths covered.

3. **A native embedded NUL can turn a different title into exact Deploy.**
   `scripts/probe_macos_ax.py:152` decodes `buffer.value`, which stops at the
   first NUL rather than preserving the complete CFString conversion. The pure
   CF boundary supplies the bounded valid UTF-8 title
   `DEPLOY · OFFLINE 5V5\x00DIFFERENT TITLE`; the actual reader returns
   `DEPLOY · OFFLINE 5V5`. Feeding that result through the unchanged shared
   traversal and full observation validator produces
   `unique_semantic_candidate=True`. The original title would be rejected by
   `normalized_title()` if preserved, because it contains a control character.
   Read the complete counted string and reject embedded NUL/control characters;
   preserve strict UTF-8 and the existing 512-byte cap and exact word sequence.

These are source counterexamples, not claims that the current Godot tree emits
an embedded NUL or that Apple APIs have already overrun or leaked in execution.

## Retained evidence and passing scope

- [native-boundaries.log](native-boundaries.log) retains all five raw assertion
  failures, the passing boundary control and the complete title acceptance
  counterexample. [replay_native_boundaries.py](replay_native_boundaries.py)
  constructs no native library, engine or executable process. Run it with the
  exact checkout path as its first argument.
- [depth-one-pure.log](depth-one-pure.log) retains all twelve unmodified commands,
  raw output, exit codes and durations. The seven native files match the review
  worktree; the clone is shallow, has exactly one reachable commit and has clean
  status. [source-and-depth-one-identity.json](source-and-depth-one-identity.json)
  records those facts. No historical object is used by the maintained controls.
- The game tree is unchanged at `55691684d31d44f1680141954bbe530443de9d1f`.
  Eight original runtime/helper/log files match the actual b294ef9 Git blobs
  and the preservation fixture. The normal workflow body matches its actual
  baseline except for the new explicit choice and its normal-job exclusion.
  The diagnostic choice routes to the separate macos-15 job.
- Source inspection found no event creation/posting, AX action/attribute setter,
  trust prompt or global AX search. The messaging-timeout configuration is the
  declared read-only-method exception. Geometry-only AXValue decoding is
  distinct from reading the forbidden AXValue attribute. Typed CF/AX guards,
  own-PID/unique-window checks, text-entry subtree pruning, byte/node/depth caps,
  one focus and separate ordinary close are present. The C integer/pointer,
  CGPoint/CGSize and Objective-C signatures have no identified source mismatch;
  their behavior on Apple remains untested.
- The controller imports the original budgets and retains raw native capture,
  failed receipts, strict logs, source/payload/default-userdata checks and
  owned-group cleanup. Its declared public launch option and private default
  profile inventory amendment are diagnostic-only. It sends no Deploy or
  reward action. A broad passing-source or native claim does not follow from
  these passing scoped observations.

The largest remaining gap is the mismatch between the native-boundary contract
and its implementation: late calls, exceptional ownership and complete titles
need faithful handling and meaningful controls. After correction and a fresh
exact source review, actual exported AX exposure, observer TCC trust, coordinate
agreement and fixed-budget completion will still be unobserved until a
separately released diagnostic attempt.

The c838907 / run 39920948579 gameplay failure remains FAILED: raw and fixed 2×
Deploy confidence 0.5 versus the unchanged required 0.8, before any CGEvent.
No game/audio/protocol/economy, original helper or implementation file was edited
by this critic. No native/Apple compile, engine/import, capture/OCR executable,
service, CI or nested agent was run.

## Review setup errors

The preregistration retains the initial incorrect builder-registration filename.
A premature identity read while the local depth-one fetch was finishing also
returned the following raw setup errors; no tests ran in that incomplete checkout:

```text
fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
HEAD
false
fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
ls: cannot access 'scripts/test_macos_ax_read_only.py': No such file or directory
```

After fetch completion, sparse selection and detached checkout completed at the
exact freeze. The retained successful identity and twelve-command replay come
from that completed checkout. The setup error is not a candidate test failure.
