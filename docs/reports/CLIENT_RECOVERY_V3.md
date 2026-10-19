# B-21: durable native client receipt recovery

## Candidate and measured result

Draft [PR #18](https://github.com/calebaiken/sightbreak/pull/18), branch
`astra/systems-v3-recovery`, based on PR #16 `d2439ac`.

- Runtime implementation: **ac48342e9aa9f557a23eb6fa5c67b3549b1d0ee7**.
- Tested source/harness checkpoint: **223ec0cdcb4549503734abe6b156b057b01b577a**.
- Matched frozen reference: **701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd**.
- Host: Windows 11, Python 3.14.6, Godot **4.7.2.stable.official.ed1daf0bf**.
- Both source trees were clean before and after the completed campaign. Exact game
  trees, probe/harness hashes and invocation paths are in [the raw summary](systems-v3-evidence/client-recovery/campaign-r4/summary.json).

The declared failure mode is loss of a keyed store, case-opening or market-purchase
receipt when the app exits around server commit. The quality bar is recovery of
every original intent after restart, with its original receipt and consent price,
one authoritative mutation/debit and no bearer credential in the app journal.

| Same-host workload | Frozen V2 | Candidate |
|---|---:|---:|
| Recovered after restart (3 repeats × 3 transaction kinds × 2 kill boundaries) | 0/18 | **18/18** |
| Original receipt/body reused on recovery | 0/18 | **18/18** |
| Duplicate authoritative mutations | 0 | **0** |
| App journals containing a bearer credential | 0 | **0** |
| Pending journals left after confirmed recovery | 0 (receipt was lost) | **0** |

V2's nine pre-commit cases have no mutation and no recoverable intent. Its nine
post-commit cases have one mutation but no recoverable receipt. The candidate's
18 cases each have one mutation and the original confirmed item. This is a
durable HTTP/SQLite fixture with the real native UI and real process termination,
not a claim of newly reproduced PostgreSQL economy correctness or host power-loss
durability. Retained V2 PostgreSQL evidence remains the server reference.

## Implementation boundaries

`TransactionJournal` writes and flushes a validated temporary receipt, then renames
it into place **before** dispatch. It stores only the original account/server,
endpoint, POST body, method and completion message. Payload fields are allowlisted;
credentials stay in the in-memory API. JSON-loaded consent prices are restored to
integers for the server's strict expected-price contract.

The existing confirmation, case reveal and public `_perform` interface remain.
Sign-out, expired authentication, transport failure and non-conclusive recovery
responses retain the original receipt. A new mutation cannot replace it. Damaged
or unwritable storage blocks dispatch; failure to remove a confirmed receipt keeps
the same replay available. Recovery requires signing in to the original account
and server and pressing the existing retry action.

## Applicable native checks

At `223ec0c`: journal **22/22**, recovery **12/12**, armory **749/749**, menu
**51/51**, and economy-screen/URL-policy/offline-separation suite pass with no
engine errors. [Commands and raw logs](systems-v3-evidence/client-recovery/native-checks/summary.json).
Native PostgreSQL UI regression and the separate harsh reviews are still pending.

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
native probe against both, kills the process at the fixture's pre/post-commit
event, restarts it and checks persisted receipts and authority ledgers. The output
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
  36-case matched campaign passes. SQLite files and native/HTTP logs are retained.
  Fixture credentials are synthetic and scoped to the in-process test server;
  they are not real account sessions. The app journal excludes them.

Raw retained files have a [SHA-256 manifest](systems-v3-evidence/client-recovery/sha256.json).
An independent critic receives only the [unlabelled K/R packet](systems-v3-evidence/client-recovery/blind/comparison.json)
and raw logs/ledgers; the [mapping](systems-v3-evidence/client-recovery/blind/mapping.json)
is withheld until its verdict. A separate source critic reviews failure semantics.
Their findings and Sol's independent checks determine the next iteration.
