# Actual R3 first rejection

FAILED at source `ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef`, root release
`801e4514ab869ad6869e5631dc303f58ca28772f`. The sole supervisor exits 1;
outer error is `Command exit/timeout: 15-accepted-block`. The block's actual
first OFF client exits 2 before `ready.json`; its error is
`Incomplete condition: Fixture exited before ready.json`.

Original [failure readback](failure-readback.json) binds copied original failure
inputs, full launch/block/overall/outer receipts, frozen fixture, exported ELF
and PCK. [Initial registry](initial-raw-registry.json) freezes all 370 current
raw files before full audit. No attempt byte or claim was changed. Import,
export, artifact and seal are recorded reached; full independent qualification
of those boundaries is still pending at this early packet.

The original 692-byte [client log](failure-input/native-block/01-/off/client.log)
contains both strict failures:

```text
WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.
ERROR: LINUX_PROFILE_OVERHEAD Pinned synchronous safe render-thread argument required
```

The recorded launch argv and independent live process observation include
`--render-thread safe` before `--`. Frozen fixture `_run`, lines 267–270,
searches `OS.get_cmdline_args()` for those tokens and rejects. The returned
engine-argument array was not retained. This packet establishes the rejection
and full process argv, not a cause for the different runtime argument view or
an actual thread/V-Sync setting readback. The client reaches this guard before
ledger read, fixed-world construction, readiness, cold anchor or sampling.

Zero `ready.json`, `metrics.json` or proof PNG files exist. ON2, ON3, OFF4,
comparison, finalization and H1 are unreached. The separate V-Sync warning
would independently fail the unchanged strict gate. A future correction must
preserve these original failures and needs separate source review/preregistration/
root release; no retry, continuation or new native command is authorized here.
