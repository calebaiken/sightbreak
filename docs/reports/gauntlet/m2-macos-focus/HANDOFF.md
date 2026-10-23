# Mac foreground observer and independent capture

Candidate worktree `/workspace/sightbreak-macos-focus`, branch
`codex/m2-macos-focus-observer`, starts at `609913e`. [Criteria](CRITERIA.md)
were declared before implementation. Canonical mission/progress/resume/worklog
files are untouched. No engine, OCR, event or CI workload ran locally.

The actual first menu run at `3b97a00` failed before any event or capture. Its
unchanged Swift helper compiled successfully. Game PID 3996 never appeared as
the exact NSWorkspace foreground PID during the five-second polling window;
the final observation was PID 3721. The selected game's window ID/bounds and
activation return were missing. The earlier preflight PID 3571/window 35 must
not be relabeled as game PID 3996. Original raw evidence remains independently
owned at `docs/reports/gauntlet/m2-macos-menu-input/native-run-39729489971` on the
native outcome critic's branch.

Inspected [public API source contracts](public-api-contracts.json) describe
NSRunningApplication's time-varying properties as persisting until the next
main-run-loop turn. That exposes a real risk in sleep/poll observation; it does
not establish the cause of the observed failure. This candidate introduces no
new activation path and keeps the same single public request/options. It records
the API return, selected current window, target application properties, and each
raw before/public-run-loop/after sample. Snapshots include the controller's own
PID, so a foreground observation can be compared with that caller without
guessing what an unrelated PID represented. Public CoreFoundation default mode
is processed only on the controller main run loop. Foreground guard reads also
process it. Exact foreground PID and the five-second deadline stay mandatory;
request success, active flags and window order never substitute for focus.

One separate read-only background capture now precedes activation. It uses the
same helper's own permission and original exact-window geometry/PNG gates.
Its receipt is explicitly capture-only, with no foreground or menu qualification.
A failed capture is retained while focus diagnostics still run; it prevents all
input afterward. Successful background capture cannot pass failed focus.
Foreground menu, Settings and returned-menu captures and all existing
neutral/profile/source/export/down/up/cleanup gates remain unchanged.

Nine new pure focus/capture-boundary controls and eleven original menu controls
pass. They use invented identities and fake clocks/APIs. They cover stale-to-
refreshed sample recording, false request/active/window proxies, the unchanged
five-second boundary, newer focus loss, main-thread refusal, refreshed guard
ordering and independent failed capture/focus. They establish observer readiness
only. Actual CoreFoundation/AppKit timing, helper permission/capture/geometry,
event delivery and navigation remain unverified.

The [fresh source review](independent-review/REVIEW.md) accepts exact
implementation `1260217` for one bounded ARM retry. It retains the 20 packaged
control outputs from `eab9882`, the metadata-only extension and eight independent
controls at final `1260217`. This does not accept native behavior or establish
the old failure's cause. Root must review/integrate and dispatch its own exact
clean source, followed by a fresh native output critic.

The first source critic identified that background success logging called fresh
diagnostics and could process an unrecorded run-loop turn before the main
contrast. That was an evidence limitation, not a bypass. The correction records
a raw pre-background snapshot and retains raw background state, reserving the
first explicit refresh for the recorded focus-loop experiment. Foreground
capture/guard diagnostics remain fresh.

Before root dispatch, require a fresh source critic. The next actual ARM review
must inspect selected game window identity, activation return/options, complete
before/after sample sequence with run-loop results, independent capture helper
permission/geometry/PNG evidence, event attempts and all cleanup/source/profile
receipts. A successful first compilation or preflight does not close these gaps.

Pure controls:

```sh
python scripts/test_macos_menu.py -v
python scripts/test_macos_focus.py -v
```

Largest remaining gap is actual native evidence separating observer freshness
from an activation that the OS never fulfills. No source-level control proves
that cause. Existing platform gates and runtime/gameplay/art remain unchanged.
