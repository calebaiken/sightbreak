# Physical device acceptance checklist

This is a test procedure, not completed evidence. Record results and defects; leave unexecuted rows unverified. Debug APK signature/export and software-rendered screenshots do not establish physical usability or performance.

## Record the test environment

- Artifact SHA256 and `builds/manifest.json` source identity.
- Phone/tablet model, SoC, RAM, OS, refresh rate, notch/navigation configuration.
- Graphics quality, FOV, sensitivity, frame cap, touch scale and customized layout.
- Build type, battery level, charging state, room temperature, network topology.

## Installation and first play

1. Android: `adb install -r builds/android/sightbreak-debug.apk`; open SIGHTBREAK. Preserve `adb logcat` around failures. Do not publish logs containing credentials or session tokens.
2. iOS: follow `builds/ios/BUILD-ON-MAC.md` on macOS; select a real Development Team and device. Record Xcode build/signing errors separately from gameplay defects.
3. Launch offline without an account. Buy, move/aim/fire simultaneously with three and four fingers, reload, swap, jump/crouch, use frag/smoke, plant/defuse, spectate and finish a match. Return to menu and play a second match.
4. Drag joystick/buttons in the editor, enlarge buttons, reset positions, save, restart and verify restoration. Test both landscape orientations, notches and system navigation gestures. Confirm buttons never remain held after an interruption and joystick/aim touches never fire by themselves.
5. Test sensitivity endpoints, gyro if supported, optional controller mapping, sound settings and reduced motion. Record a human responsiveness/comfort assessment; automated input events cannot replace this.
6. Background/resume during a match, open notification/system overlays and interrupt audio. Record reconnection behavior and missed-input recovery. Test low-storage/save failure recovery separately.

## Performance and networking

- Measure a full 30-minute session including smoke and ten-actor fights. Record median/p95/p99 frame time, sustained FPS, app RSS, thermal throttling and battery change with the measurement tools/settings named. No average-only FPS claim.
- Android `adb shell dumpsys gfxinfo` alone may not capture Godot's native rendering accurately; use an appropriate device GPU/frame-timing profiler and describe its limitations.
- Play a private LAN session, then test controlled latency/loss and reconnection. No public Internet exposure is needed for these checks.
- For authenticated rewards, use ten real independent account players for a complete eligible match. Record privacy-safe authority, duration/activity, reward receipts, replay protection and disqualification behavior. Synthetic fixtures do not satisfy this check.

## Economy interaction

Use only earned fictional Credits. Verify exact odds before committing a case/key, reduced-motion/skip reveal, inventory refresh, saved skin ownership, marketplace listing/buy/cancel and both parties' trade confirmation. Induce response loss and use **RETRY PENDING TRANSACTION**; verify one wallet/item effect. App-process termination still loses the in-memory pending request and remains a known recovery limitation.

## Acceptance

Attach logs and native captures to a dated QA report. Require independent evidence-backed review >=8.5/10 for each applicable category before release acceptance. Missing device evidence stays unverified; failing or lower-scoring categories remain open.
