# ARM Mac ordinary menu input candidate

Worktree `/workspace/sightbreak-macos-menu-input`, branch
`codex/m2-macos-menu-input`, begins at `a5bd530`. [Criteria](CRITERIA.md) were
declared before implementation. Canonical mission/progress/resume/worklog files
are untouched. No CI has been dispatched by this builder and no event, engine
or OCR workload has run locally.

The Python driver owns the exported client and ordinary CoreGraphics input.
Public AppKit activation must produce the exact foreground PID. Native
combined-session state must acknowledge pointer/button/Escape movement and
release. Finally releases only controls recorded as owned. Existing native
player-profile entries block launch/input; native cache changes remain visible
in receipts and are preserved. Catchable cancellation is covered; hard kill and
concurrent physical input are outside this bounded observer's claims.

A separate read-only Swift helper checks its own non-requesting capture
permission, then uses supported macOS 14+ ScreenCaptureKit and Vision. Its posting
permission is diagnostic; Python owns posting and checks its own permission. It never
posts input. Original exact-window OS PNGs, full-window point geometry, filter
content dimensions, backing scale and OCR boxes are retained. Unknown chrome or
DPI relationships refuse pointer mapping. The Settings target must be exact,
unique and at least 0.8 confidence; final screen outcomes must distinguish the
menu from FIELD SETTINGS. No save control is clicked.

The registered workflow adds source controls and the bounded actual ARM journey
only after a fresh successful same-source preflight. All existing platform
gates remain unchanged. The driver also rechecks preflight source/export hash,
cleanup/profile/window receipts before launch; a previous run cannot authorize
an unmatched build. A fresh critic must review source before root dispatch and
actual native PNGs/state/source/cleanup before acceptance.

The [independent source review](independent-review/REVIEW.md) accepts exact
implementation `800d36c` for that first ARM compile and guarded attempt. Eleven
packaged and thirteen independent frozen-source controls pass. The original
`aa309a1` rejection, its three failing guard probes, intermediate logs and exact
source hashes remain in the review archive. This approves no unseen native run.

Eleven Linux observer controls pass. These cover titlebar/Retina coordinate
mapping, unknown geometry, ambiguous/low-confidence OCR targets, outcome
recognition, preflight identity/permissions/cleanup, refusal before a down event,
owned-only release and non-native no-launch behavior. They do not compile Swift
or establish Mac API, capture, focus or input delivery. The source helper's first
native compilation and all OS behavior remain unverified.

The first source review found that transaction-entry neutrality was checked
before pointer movement, rather than at each actual down-event boundary. Initial
`aa309a1` is rejected on that declared criterion. The correction checks native
neutral state again immediately after exact-window/focus validation in both down
paths, before claiming ownership or posting. A dirty state at that boundary now
refuses both pointer and Escape down events. The initial injected-state proof
and fresh re-review are retained in milestone evidence.
The fresh neutral-state observation must also retain the exact foreground PID;
an observed focus loss after the first target check now refuses the event.
Failure cleanup also attempts the public ordinary quit request, with a separate
3-second budget, before falling back to owned process-group termination.

Root reports independently inspected raw preflight at `e7718ee`, run
39727011693, job 119653125533: all four queried permissions true; PID 6968,
window 34, bounds `[40, 32, 960, 568]` points; internal viewport 960 × 540 PNG;
normal exit 0, no owned group, absent profile entries unchanged, 86 native files
and 32 directories unchanged. That result supports preparing this attempt. It
does not establish this helper's permission identity, OS screenshot, focus or
event delivery. Root is retaining that separate native critic evidence.

Actual reviewed run commands, on clean native ARM source with matching export:

```sh
python scripts/test_macos_menu.py -v
python scripts/verify_macos_menu.py --preflight builds/desktop-playability/macos-input-preflight/results.json --output builds/desktop-playability/macos-menu-input
```

Largest remaining gap is actual ARM compilation/capture/focus/control/navigation
evidence. A pass is menu input only; movement, aim, firing, offline matches,
physical performance and human play remain open.
