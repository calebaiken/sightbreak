# Reconstructed Mac ordinary input component

This is a new candidate from published checkpoint
`917b143ba4e4b0d9644a7a0ddeee1dd64c139682`. The interrupted, unpushed Mac
source and raw run were absent from the restored snapshot. Nothing here recovers
or certifies that missing work. Native execution remains UNVERIFIED.

The inspected regression bars are `scripts/verify_macos_menu.py`,
`scripts/macos_native_input.py`, `scripts/macos_window_capture.swift` and
`scripts/verify_offline_export.py` at that checkpoint. Preserve their existing
menu, Windows/Linux, objective, full-match and leak gates. This component can
qualify only stock Deploy, living sidearm fire/reload, FIELD MENU / LEAVE MATCH
and ordinary close on ARM macOS. It cannot qualify objectives, completed matches,
restart persistence, Intel Macs, physical input latency, human play or CS2 parity.

## Isolation decision recorded before implementation

Godot 4.7.2 source is actually fetched; URLs, byte counts and SHA-256 values are
in `upstream-source.json`. `SConstruct` defaults `disable_path_overrides=true` for
export templates. `main/main.cpp:1864` rejects `--main-pack` without that compiled
capability. `core/config/project_settings.cpp:747` separately loads an executable
sibling `override.cfg`, with project overrides enabled by default. Do not assume
that the stock template accepts `--main-pack`, rebuild a template, use the editor
as the artifact or rewrite HOME.

Stage a byte-exact copy of the exported `.app`, preserving executable permissions.
Add only `Contents/MacOS/override.cfg` with
`application/config/use_custom_user_dir=true` and a fresh
`application/config/custom_user_dir_name`. Every pre-existing copied payload file
and the original export must hash identically before and after. Record exact
executable and PCK descriptors, the build manifest, source identity, helper source
and binary hashes, override bytes/hash and the controller command/environment.
No other project setting, graphics mode, rule, spawn, seed or profile value may
change. The native attempt must establish whether this route works in that exact
artifact; source research alone cannot close isolation.

Use the actual account home from the OS account database; refuse a different HOME
and any symlink in the default or selected private path. Do not pre-create the
private directory. Before Deploy, require the exact artifact to create its private
`user://` log there, require a pinned-version engine header, and require the whole
default SIGHTBREAK directory inventory to remain unchanged. Existing default player
profiles remain a blocker. Retain private caches/logs/profiles, including failures;
do not delete or fabricate saves. Initial trace must prove fresh defaults, stock
random spawns/teams/seeds, normal difficulty/rules, protocol 6 and prediction off.

## Preregistered correctness and native budgets

1. Independent source critic must approve the frozen candidate and falsifiers
   before any export, CI dispatch, engine, service or native run. Pure source tests
   may run here. Root owns the single native CPU lane and releases execution.
2. Actual CGEvent input only. Before every down event require current permissions,
   exact foreground PID, the owned layer-zero window, pinned chrome/bounds and
   neutral OS controls. Pointer targets require one exact Vision label at >=0.8
   confidence, a finite in-bounds box and proven full-window/Retina mapping. The
   read-only ScreenCaptureKit/Vision helper never posts events or asks permission.
3. Total native component limit 300 seconds, including 60-second helper compile.
   Keep original bounds: window 30, focus 5, menu 60, Deploy readiness 30, live 60,
   fire acknowledgement plus two drawn frames 5, reload start 5, reload completion
   15, post-reload two frames 5, FIELD MENU pause 10, returned menu 30, ordinary
   close 20 seconds. Each screenshot helper is bounded to 25 seconds within the
   same total limit. No deadline extension, reduced resolution/quality, fixed seed,
   time-scale change or gameplay debug mutation may rescue a failed attempt.
4. One stock menu Deploy click must produce the ordinary fresh match. Fire is
   allowed only in the same first living live round with full sidearm 15/60,
   normal time scale, focused unpaused game. Two one-second LMB holds with 0.35-second
   released intervals match the original schedule. Require acknowledged release,
   depleted ammo 1..14, reserve 60 and two drawn frames within the original 5 seconds.
5. Original native fire and reload screenshots must show positive health and exact
   authoritative sidearm ammo/reserve, with the same living player/round checked
   before and after capture. Require actual R-down OS acknowledgement, observed
   positive reload countdown before any transfer, R-up acknowledgement, full 15
   ammo after the countdown, exact reserve conservation and two further drawn frames.
   Reject death, respawn, stale snapshots, changed weapon/round, paused gameplay,
   unobserved reload, vanished focus and mismatched rendered values.
6. Real Escape must open FIELD MENU, freeze the same living state and show the exact
   FIELD MENU and LEAVE MATCH labels. Select LEAVE MATCH by original screenshot
   coordinates, verify the ordinary home screen, release every owned control and
   use the public AppKit termination request. Success requires exit 0 without
   fallback signals, every owned helper/client process group gone, no held controls,
   unchanged source/export, unchanged default directory and no native error/leak
   signatures. A cleanup failure fails the component. Preserve failed logs/pixels.
7. Add the component to the ARM workflow without changing original host matrices,
   platform journey/objective/full-match commands, stage budgets or strict error/
   leak tests. An independent critic must inspect raw native outputs and screenshots
   before root accepts the result. Unsupported or failed criteria stay open.

The largest current deficiency is that no actual Mac gameplay output has been
observed. Pure tests can reject false receipts; they cannot qualify native input.
