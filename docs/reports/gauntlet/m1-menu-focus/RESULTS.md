# Field menu focus result

Builder: `/root`. Independent reviewer: `/root/menu_critic`.
The candidate wins the declared keyboard-focus comparison against 561d0cb.
The [verbatim review](independent-review.md) and [archived evidence](INDEPENDENT_ARCHIVE.md)
limit acceptance to field-menu initial focus, keyboard navigation, explicit
resume and the observed existing pause/input safety. A separate
[archive audit](ARCHIVE_AUDIT.md) checks preservation, hashes and exclusions.

The ordinary FIELD MENU had no initial focus owner. The 8de7331 correction selects
RESUME when it opens and reuses the existing focus style. Labels, settings,
geometry, gameplay timing and ownership rules are unchanged.

The builder and independent reviewer each ran the same actual-scene test against
baseline 561d0cb main: 9 checks, 3 failures, all repeated missing-focus prerequisites.
The candidate passes 30 checks for RESUME focus, SETTINGS order, the forward/reverse
four-action cycle, ui_accept routing, offline pause/resume and released focus over
three opens. The maintained input-mode regression passes 31 checks. These scene
checks use synthetic actions and simulated capabilities.

The independent native control exported exact 561d0cb and confirmed that Escape
opens FIELD MENU without a focus outline and Return leaves it paused. The final
candidate export at 6767e97 shows the existing gold border on RESUME, traverses all
four actions with ordinary OS Tab/Shift-Tab and resumes with Return on three opens.
Offline simulation stays frozen while paused. Native focus loss pauses; restoring
focus waits for explicit Return. W/LMB remain physically held after that resume
while consumed movement/fire stay neutral and ammunition stays 14. The original
screenshots, videos, read-only stock trace, OS actions and receipts are archived.
The successful baseline and both later candidate native runs exit 0. Final r3 took
73.772 seconds under llvmpipe; that duration is a trial record, not a device
performance measurement.

Fresh import exposed a missing `menu_focus_test.gd.uid` in 8de7331. Root retained
it in UID-only aa0b0a4. The reviewer's detached cherry-pick is 6767e97, with shipping
main.gd bytes unchanged from 8de7331. Its source-bound export is clean. The first
wrong-state template failure, redundant setup ETXTBSY failure and native observer
failure during the stock buy phase remain in the archive. The later controller
waits for ordinary live input and completed rendered frames before final captures;
its trial budget changes are disclosed in the original review.

Builder scene commands, each with a fresh `SIGHTBREAK_STATE_DIR`:

```sh
git show 561d0cb:game/scripts/main.gd > builds/mission-m1/menu-focus-baseline-main.gd
./scripts/godot.sh --headless --script res://tests/menu_focus_test.gd -- --baseline-source="$PWD/builds/mission-m1/menu-focus-baseline-main.gd"
./scripts/godot.sh --headless --script res://tests/menu_focus_test.gd
./scripts/godot.sh --headless --script res://tests/input_mode_test.gd
```

The [independent command ledger](independent-commands.md) records its actual paths,
exports and OS proof. Builder outputs remain beside this file; the new test is
registered in the maintained suite and native desktop CI. Latest desktop
[CI 39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860)
has a reported source-suite isolation failure being fixed separately. No overall
CI pass is claimed here.

No physical controller/device behavior, input latency, nested settings journey,
complete offline match, general visual quality or release readiness is certified.
This record does not promote any complete G1–G20 gate. The largest remaining
coverage gap is physical input hardware and human observation.
