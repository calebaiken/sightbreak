# Independent correction review

Reviewed 2026-10-23 at exact freeze
`3fd9718bc066bedf879f241760c106ee96923060`, controller SHA-256
`3d495f74c7799e58616288a8812c29829c45b426ae737fcc73a5712c63782561`.
**Verdict: ACCEPT source readiness for one separately released diagnostic
setup and OFF/ON/ON/OFF block, subject to the preparation below.** This is a
source verdict. No engine compilation, export or native result is accepted here.
Root retains the runtime-lane release decision; this review starts no run.

The rejection at `51add37` remains valid for its original `1290172` source. All
four rejection files are preserved byte for byte. The correction closes its
three demonstrated failures without changing the fixture, registration, shipping
game tree, original offline controller or canonical mission documents.

## Independent checks

Run from `/workspace/reviews/linux-profile-fixture`:

```sh
python3 docs/reports/gauntlet/m1-linux-opaque-cost-plan/independent-correction-r1-review/audit.py
```

[Audit](audit.py), [recomputed results](recomputed.json),
[original counterexample replay](original-counterexample-replay.json) and
[22-method pure output](pure-controls.txt) retain the evidence. The audit verifies
all 16 correction-ledger file identities and the four original critic files.
It executes the retained unchanged-function replay and independently reproduces
the saved before/after results: the old source accepts all three counterexamples;
the correction rejects the dead Xvfb, stops after its first late client and
rejects the nonfinite cold endpoint. The 22 maintained methods pass with no skips.

My additional pure controls exercise the production deadline code at 24 success
boundaries, including already-published ready/metrics files, argv/host/payload
observations, both acknowledgements, completed wait, final cgroup/PNG/log reads,
owned cleanup, source recheck, validation, publication, reread, receipt hashing
and the final alarm-context exit. Every late case fails after one fake client.
A complete four-condition virtual block at **179.999 seconds per condition**
passes. Each earlier immutable `condition.json` is written once and its actual
bytes match the later block's SHA-256 receipt.

I also exercised the actual POSIX timer with a blocked Python `os.read` on an
empty anonymous pipe. A 40 ms alarm raised the production `TimeoutError` after
about 40 ms; the prior handler returned and the timer was disarmed. A preexisting
active alarm rejects without replacing its handler or timer. A body exception
also restores the handler and disarms. Virtual boundary tests mock timer arming;
the blocked-read test uses the real timer and starts no process or service.

The display success path now checks live owned PID/start identity before and
after observation, a regular lock naming that PID, a Unix-socket path, and a
matching named kernel socket inode held in the owned process's FD table. Stable
filesystem socket/lock identities must survive observation. My twelve ownership
cases include the valid join and rejection of final liveness/start changes,
socket/lock inode changes, lock-PID changes, wrong file types, kernel-path or held
inode mismatch, and dangling socket/lock symlinks. The unchanged dead-child
falsifier rejects before an ownership claim can be made. These controls establish
the declared owned launch protocol, not protection against arbitrary host tampering.

The 180-second acceptance cap remains unchanged and strict: exactly 180 rejects.
The remaining time arms `ITIMER_REAL`; later phases do not restart the budget.
Cleanup remains separately bounded after failure and cannot repair acceptance.
Monotonic postchecks reject delayed signal handling or a late completed child.
Python/POSIX signals cannot promise immediate termination of an uninterruptible
kernel operation; the handoff states that limit accurately. Finite, nonnegative
pre-anchor clocks and finite positive cold/readback durations now reject directly.
Strict JSON parsing also rejects nonfinite constants and floating-point overflow.

## Preparation required before the first released run

1. Stage from the exact clean frozen candidate into a new isolated project.
   Retain the base/overlay inventory and ledger. Run any approved import and
   export only against that stage with private editor/export state. Preserve
   full commands, source identities and failures. Unexpected staged source or
   UID changes must stop preparation; only the explicitly excluded fixture UID
   and import cache are outside the sealed inventory.
2. Verify the pinned Godot 4.7.2 editor/template archive identities and retain
   actual compilation/import/export logs. Independently inspect the ELF and
   embedded PCK, diagnostic scene/fixture/ledger and resource identities before
   sealing. `seal` checks headers and hashes; it does not prove the pack contains
   the expected source. GDScript syntax, imported resource paths, fingerprint
   stability and equal pixels remain unverified until these later stages.
3. Root must release an exclusive native lane with a concrete bounded outer
   wrapper, owned process-group cleanup and retained final receipts. Resolve
   exact executable/Xvfb paths, an unused numbered display, two sorted allowed
   CPUs, fresh output/state directories, tool hashes and OS/kernel/priority
   evidence. Keep the controller in the main thread with no existing real-time
   alarm. The outer wrapper must also bound setup and whole-command/finalization
   work outside individual condition timers; it must preserve the 180-second
   condition cap and the original gameplay controller/deadlines.
4. Run only the fixed fresh-process OFF/ON/ON/OFF sequence. Any setup, compile,
   capability, timing, source/work/pixel/driver/host/throttle or cleanup failure
   remains retained and stops the attempt. This verdict authorizes no adaptive
   warm-up, automatic retry, cap change or self-approved repeat. A fresh critic
   must inspect the resulting exact-source artifacts and raw block independently.

The unchanged estimator measures median post-draw wall cadence at the declared
pacing. Sparse stdout stalls, total profiler overhead, uncapped render cost,
CPU-function attribution, physical FPS, gameplay failure causes and optimization
remain outside this contrast. The four processes supply no confidence or
repeatability estimate. No Godot/import/UID/compile/export/native fixture/Xvfb,
OCR, CI or service ran in this review. Original Linux gameplay failures and all
product/release acceptance gates remain unchanged.
