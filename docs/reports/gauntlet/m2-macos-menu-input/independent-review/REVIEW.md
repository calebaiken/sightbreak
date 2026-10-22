Independent source review, 2026-10-22

ACCEPT `800d36c848a9882bc76ad8eb917b8fd944d565a3` for its first native ARM
compilation and tightly guarded ordinary menu-input attempt, after root's
integration review and a fresh matching export/preflight. No remaining source
blocker was found. Native input remains UNVERIFIED pending original native
outputs and a fresh independent reviewer. This review did not compile Swift,
load native frameworks, launch an engine, run OCR, post events, or dispatch CI.

REJECT the original `aa309a13c2f7854cdc82820255209be67f18ec1f`. Its actual
button/Escape down methods checked the target but omitted a fresh neutral-state
guard. Three independent injected-state probes failed: dirty state at button
down, dirty state at Escape down, and dirty state introduced after the pointer
move. Those paths posted despite the dirty baseline, violating criterion 3.
The failed run is preserved in [round-1-aa309a1-controls.txt](round-1-aa309a1-controls.txt).
This is a source counterexample to the declared boundary guard, without a claim
that concurrent physical input is safe or qualified.

`0827649` puts `neutral()` immediately after `require_target()` in both down
paths, before ownership or event allocation. The same eight independent probes
then pass. `f3cb69a` also rejects foreground loss seen by the newer diagnostics
sample and includes Fn in its modifier baseline. Ten independent probes pass
there. `800d36c` adds public ordinary termination on failure, with a separate
three-second wait before owned-group fallback. Final results are
[13 independent controls](round-4-800d36c-controls.txt) and
[11 packaged controls](round-4-800d36c-packaged-controls.txt), all passing.
The non-Mac packaged negative control deliberately reports a failed journey
with zero launches/captures; that expected refusal passes its unit test.

The final source and imported guard dependencies are recorded by full commit,
size and SHA-256 in [source-receipt.json](source-receipt.json). Reviewed files
matched those frozen Git objects before and after the final controls. All
implementation changes belong to the builder. This reviewer wrote only this
independent-review directory.

| Declared criterion | Source finding and limit |
| --- | --- |
| 1. Source, export and permission identity | `validate_record` verifies current artifact and payload descriptors against clean exact source. Prior preflight must match source/export identity, artifact hash, permission booleans, cleanup/profile state and an observed window. Current Python posting/capture preflights are required again. The Swift executable checks its own screen preflight before ScreenCaptureKit. No request, TCC mutation or alternate identity path is present. The prior `e7718ee` native acceptance is supplied by root's separate critic, not re-established here; it cannot qualify the new helper. |
| 2. Profile boundary | Canonical profile and `.tmp` entries are checked before launch and each input target guard, using entry-aware absence checks. Existing entries block without reading/deleting them. Source inspection of ordinary `main.gd` confirms menu Settings entry and Escape return do not save; setting widgets connect save callbacks after initial values are set. Native directory snapshots/side effects are retained. |
| 3. PID, window, focus, neutral state | Window enumeration is exact child PID, visible, layer zero; the chosen largest window's ID and full bounds remain pinned. AppKit activation must yield the exact frontmost PID. Every down method now checks permission/profile/window/focus and the fresh neutral diagnostic including modifiers before allocation/posting. Independent changed-window, newer-focus, dirty-state and modifier refusals post nothing and acquire no controls. |
| 4. Genuine capture and geometry | A separate read-only executable selects the exact CoreGraphics and ScreenCaptureKit PID/window. It rejects mismatching frames, content size, scale or returned dimensions, including a post-capture bounds recheck. Shadows are explicitly excluded. Original PNGs and helper receipts are preserved. Actual macOS chrome, ScreenCaptureKit behavior and helper permission identity require the first native outputs. |
| 5. Visible target and outcomes | Vision reads the captured CGImage also written as the original PNG. Exact unique SETTINGS at confidence >= 0.8 supplies a normalized bottom-left box; bounds, scale and box guards establish the full-window global-point transform without a guessed titlebar offset. Initial/returned menu requires TACTICAL OPERATIONS and unique SETTINGS; FIELD SETTINGS is a distinct required intervening outcome. |
| 6. OS input evidence | Only pointer move, one button pair and one Escape pair are posted through public CoreGraphics. Combined-session down/up state and foreground PID must be observed; pointer location must reach the target. Post counts are explicitly attempts. No debug activation, in-process UI call or success-log substitute establishes navigation. Native acknowledgement semantics are still unverified. |
| 7. Bounds and cleanup | The driver has a whole-journey deadline, helper call budgets, bounded focus/state/release waits and finally cleanup. Cancellation/post-failure probes retain ownership for release; failed release retains ownership for retry. Unknown controls are not released. Public ordinary close precedes owned-group fallback on failure; refusal returns immediately and its accepted wait is exactly three seconds. Final source/export, profile and process-group receipts are required. Hard kill/concurrent physical input remain outside the stated claims. |
| 8. Scope and workflow | The workflow delta from `a5bd530` is exactly nine additions. The ARM menu attempt requires successful export, same-run preflight and source controls, with a five-minute outer timeout. Existing Windows/Linux input, Intel, default Mac startup/source and iOS steps are unchanged. Source controls qualify readiness only. |

The 0.4-second wait before each post-input screenshot can conservatively fail a
slow draw. It cannot pass missing navigation because the distinct original-pixel
outcome is mandatory; no event is retried. Initial-menu capture has one bounded
read-only retry and preserves failed images/receipts. This is acceptable for the
declared bounded first attempt.

The largest remaining gap is real ARM compilation and raw OS behavior. A native
review must inspect the Swift compiler log and helper hash, each helper's own
permission receipt, exact PID/window/geometry/focus samples, all down/up and
pointer observations, original menu/settings/returned-menu PNGs, and final
process/profile/source/export receipts. A void post return or a workflow success
badge cannot close that gap. Movement, aim, firing, complete offline play,
physical performance and human play remain outside this acceptance.

Read-only requests for Apple's `contentRect`, `pointPixelScale`,
`ignoreShadowsSingleWindow` and `combinedSessionState` JSON documentation were
denied by the network proxy with `Tunnel connection failed: 403 Forbidden`.
No SDK availability or ABI claim is inferred from those failed fetches.

Reproduce the retained rejected source controls from this worktree:

```sh
python -B docs/reports/gauntlet/m2-macos-menu-input/independent-review/controls-round-1.py --revision aa309a1
```

Expected: eight tests, three failures, exit 1. The harness loads adapter source
directly from that immutable Git object; it does not use the current adapter.

Reproduce final independent controls:

```sh
python -B docs/reports/gauntlet/m2-macos-menu-input/independent-review/controls.py --revision 800d36c
python -B scripts/test_macos_menu.py -v
git diff --check a5bd530 800d36c
```

Expected: 13 independent tests and 11 packaged tests pass, then a clean diff
check. Run the packaged test on the reviewed source tree. The final harness
loads frozen adapter and driver Git objects and uses fake APIs only. Its shared
imported guard files are unchanged between the reviewed revisions; their final
hashes are in the source receipt. No command above performs native validation.
