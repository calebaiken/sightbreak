# B-21: durable native client receipt recovery

## Candidate and measured result

Draft [PR #18](https://github.com/calebaiken/sightbreak/pull/18), branch
`astra/systems-v3-recovery`, based on PR #16 `d2439ac`.

- Current runtime and matched harness: **7b6f379a3f8c809d0985a64e883cbadfdd78d135**.
- Earlier checkpoints: `ac48342` implementation, `223ec0c` first matched run,
  `cda6372` first critic fixes; all earlier evidence remains available.
- Matched frozen reference: **701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd**.
- Host: Windows 11, Python 3.14.6, Godot **4.7.2.stable.official.ed1daf0bf**.
- Both source trees were clean before and after the completed campaign. Exact game
  trees, probe/harness hashes and invocation paths are in [the r6 raw summary](systems-v3-evidence/client-recovery/campaign-r6/summary.json).

The declared failure mode is loss of a keyed store, case-opening or market-purchase
receipt when the app exits around server commit. The quality bar is recovery of
every original intent after restart, with its original receipt and consent price,
one authoritative mutation/debit and no bearer credential in the app journal.

| Same-host workload | Frozen V2 | Candidate |
|---|---:|---:|
| Recovered after restart (3 repeats × 3 kinds × before/after/late commit) | 0/27 | **27/27** |
| Original receipt/body reused on recovery | 0/27 | **27/27** |
| Retained receipt through retry409 before delayed original commit | No saved receipt | **9/9** |
| Duplicate authoritative mutations | 0 | **0** |
| App journals containing a bearer credential | 0 | **0** |
| Pending journals left after confirmed recovery | 0 (receipt was lost) | **0** |

V2's nine pre-commit cases have no mutation and no recoverable intent. Its eighteen
post/late-commit cases have one mutation but no recoverable receipt. The candidate's
27 cases each have one mutation and the original confirmed item. Every late-commit
case records rejection, release and original commit in the required order; every
native termination has a PID and completion acknowledgement. This is a
durable HTTP/SQLite fixture with the real native UI and real process termination,
not a claim of newly reproduced PostgreSQL economy correctness or host power-loss
durability. Retained V2 PostgreSQL evidence remains the server reference.

## Implementation boundaries

`TransactionJournal` acquires a local OS-released exclusive owner, writes and flushes
a validated temporary receipt, reads its closed bytes back, then renames and verifies
the published bytes **before** dispatch. Ownership spans staging, dispatch, retry and
clear. The guard accepts no network peers or data; a hash-port collision fails closed.
The journal stores only the original account/server,
endpoint, POST body, method and completion message. Payload fields are allowlisted;
credentials stay in the in-memory API. JSON-loaded consent prices are restored to
integers for the server's strict expected-price contract. Changing its storage path
while owned is rejected. A stale UI claim releases a newly acquired guard and reloads
the journal, allowing another UI to proceed without a sticky lock.

The existing confirmation, case reveal and public `_perform` interface remain.
Sign-out, expired authentication, transport failure and non-conclusive recovery
responses retain the original receipt. A new mutation cannot replace it. Damaged
or unwritable storage blocks dispatch; failure to remove a confirmed receipt keeps
the same replay available. Recovery requires signing in to the original account
and server and pressing the existing retry action. All failed recoveries retain the
receipt: a refusal now cannot prove an earlier attempt did not commit. Successful
keyed responses must include an item identity and the route's confirmation fields.

## Applicable native checks

At `7b6f379`: journal **41/41**, recovery **12/12**, armory **749/749**, menu
**51/51**, and economy-screen/URL-policy/offline-separation suite pass with no
engine errors. [Commands and raw logs](systems-v3-evidence/client-recovery/native-checks-r6/summary.json).
The journal checks include a separate competing native process, two live stale-UI
owners, account/server mismatch, retry failures, malformed success, corrupt storage,
unwritable paths and actual-file truncation fault injection. Native PostgreSQL recovery
and the updated blind outcome review remain pending; the current source re-review
found no blocking defect in this bounded slice.

## Reproduce

Create separate clean checkouts at the two exact source commits. From the tested
candidate checkout, with the official Godot executable installed:

```powershell
python scripts/validate_transaction_restart.py `
  --godot 'C:\path\Godot_v4.7.2-stable_win64.exe' `
  --baseline 'C:\path\frozen-v2' --candidate . `
  --out 'C:\path\new-evidence-directory' --repetitions 3
```

The harness imports each project, records source identity, runs the same external
native probe against both, kills the process at the fixture's commit boundary,
restarts it and checks persisted receipts and authority ledgers. The late-commit
variant holds the original, returns409 to a retry, then releases the original and
restarts again. Barrier timeouts and incorrect event order fail the trial. The output
directory must not exist and must be outside either checkout.

For each native check above, invoke Godot with
`--headless --path game --script res://tests/<test-name>.gd` after importing.
On Windows, use a waiting/capturing subprocess runner: invoking the GUI executable
directly from PowerShell can return before the process finishes.

## Retained failures and controls

- [UI preflight](systems-v3-evidence/client-recovery/ui-preflight/): frozen V2
  failed four of 746 assertions; candidate's provisional closed-port fixture
  failed the same four of 748. Windows can classify a refused port as generic
  uncertainty. The final test allows that conservative classification and uses
  reserved `.invalid` DNS for the definitely-unsent branch. Runtime transport
  classification was not loosened.
- [Trial r1](systems-v3-evidence/client-recovery/failed-r1/runner.txt): fixture JSON
  parsed the initial market price as a float, unlike the actual UI's integer
  capture. The strict fixture rejected it before the kill boundary. The probe now
  normalizes its initial input; app recovery still must round-trip the real journal.
  Expected killed-socket errors are handled across headers as well as body writes.
- [Trial r2](systems-v3-evidence/client-recovery/failed-r2/runner.txt): all 18 V2
  cases ran, then candidate editor import reported allocation/preload errors.
  The trial is incomplete, not a pass. Subsequent full r4 passed without source changes.
- [Trial r3](systems-v3-evidence/client-recovery/interrupted-r3/): harness-server
  restart cancelled execution during import. No outcome is counted.
- [Completed r4](systems-v3-evidence/client-recovery/campaign-r4/runner.txt): full
  36-case matched campaign passes at `223ec0c`; a blind critic selected that candidate,
  but source review required additional fixes before acceptance.
- [Completed r5](systems-v3-evidence/client-recovery/campaign-r5/summary.json): `cda6372`
  recovered27/27. A critic found its late-commit barrier did not fail on timeout, so
  it cannot establish the new ordering claim. All per-case logs/ledgers remain; the
  temporary wrapper stdout expired before publication. The r5 native-check launcher
  also mistyped `menu_account_test`; that failed invocation and corrected passes remain.
- [Completed r6](systems-v3-evidence/client-recovery/campaign-r6/runner.txt): `7b6f379`
  recovered27/27 with strict late ordering and clean source checks. Raw SQLite ledgers,
  journal captures, native/HTTP logs and timestamped PID events are retained.

Fixture credentials are synthetic and scoped to the in-process test server; they
are not real account sessions. The app journal excludes them. Credential assertions
cover the receipt journal, not a whole-profile forensic scan.

## Critic loop and remaining boundary

The first source review blocked acceptance on four issues: shared-file races,
unchecked writes, premature clearing on failed recovery, and malformed success.
`cda6372` addressed them. A second review found a stale-owner lock/liveness defect
and the permissive late-commit oracle; `7b6f379` corrected both. The independent
source re-review now passes this bounded process-restart slice. A fresh reviewer
receives only the r6 neutral M/Q packet; its mapping is withheld until verdict.

The largest evidence gap from the first blind review was real PostgreSQL market
settlement through a lost response, fresh authentication, recovery and a second
restart. That independent oracle is in progress, with exact-source results to follow.
The original backend does not durably fence terminal rejected receipts, so a
permanently rejected uncertain intent can remain blocked. Forgetting it would be
unsafe while an earlier request may still commit. Port collisions fail closed;
filesystem path aliases beyond the app's canonical journal path are not an identity
guarantee. Read-back and process-kill tests do not establish host-power-loss durability.

## Evidence byte preservation

An audit found Git CRLF normalization changed177 of the initial314 published raw
files relative to their original SHA-256 manifest. Every working raw file still
matched that manifest. The [pre-repair audit](systems-v3-evidence/client-recovery/pre-repair-byte-audit.json)
is retained. A scoped `.gitattributes` now disables text conversion and restores the
original bytes; subsequent publication verifies hashes against committed Git blobs
as well as working files. This repairs evidence transport, not measured outcomes.

Raw retained files have a [SHA-256 manifest](systems-v3-evidence/client-recovery/sha256.json).
The earlier [unlabelled K/R packet](systems-v3-evidence/client-recovery/blind/comparison.json)
and [mapping](systems-v3-evidence/client-recovery/blind/mapping.json) remain alongside
the later campaign. Separate source and blind reviews plus Sol's source-bound
independent checks determine integration readiness. Protocol6, default-off prediction,
disabled live rewind and all existing economy/visual/bot activation gates remain.
