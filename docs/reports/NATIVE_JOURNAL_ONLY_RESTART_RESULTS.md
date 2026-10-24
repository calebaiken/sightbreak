# B-21 follow-up: recovery with purchase inputs absent from restart fixtures

## Result

**Exact `7b6f379a3f8c809d0985a64e883cbadfdd78d135` recovered 1/1 committed
price-400 receipts. Exact `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` recovered
0/1. Actual purchase-input absence was captured on all four restart launches.**

This is the requested narrow follow-up to the prior critic's fixture-assisted
recovery falsifier. Both invocations used identical driver/probe bytes frozen at
**`7be70f73ec6a065849d902e7075d2b76e78bdd21`**, `--repetitions 1`, and no
`--native-economy` flag. The successful runs occurred on October 24, 2026.

| Measured source | Initial / recovery / second-restart PID | Purchase requests by phase | Exact recovery | Journal at kill |
| --- | --- | --- | --- | --- |
| `701ce2c4` | 23852 / 28396 / 13500 | 1 / 0 / 0 | 0/1 | Absent |
| `7b6f379` | 20004 / 1700 / 22640 | 1 / 1 / 0 | 1/1 | 303 bytes, unchanged across kill |

Both purchases settled exactly once: buyer **2,000 → 1,600**, seller
**2,000 → 2,388**, fee **12**. Each added one Operation, two Ledger rows and one
`market_settled` Audit row. The item changed owner and cleared its reservation;
the listing became sold to the correct buyer. All nine complete economic tables
were identical at commit, after kill, after recovery and after second restart.
Both cases recorded three distinct native-login digests matched to same-owner
real PostgreSQL Session rows. Second restart sent no purchase request.

The candidate's recovery body bytes equal the original strict-integer request;
its full native result equals the held HTTP result and persisted Operation
response. The baseline refreshed account/inventory but had an empty retry result
and no journal or recovery request. Its economic checks do not imply recovery.

## Actual input-absence evidence

The external probe's `config.payload.expected_price` normalization now occurs
only inside `mode == "send"`. Before each restart, the driver truncates the
same private fixture and writes exactly:

```text
{url, journal, mode, username, password, owner}
```

No path, payload, original receipt UUID, item, listing, seller, expected price or
expected result is supplied in that config. The original purchase config remains
in the driver for oracle comparisons; its redacted evidence copy is outside the
native working directory and is not passed to the process. The native environment
uses an explicit Windows housekeeping allowlist plus `SIGHTBREAK_RECEIPT_FIXTURE`;
it excludes the driver's `DATABASE_URL` and arbitrary inherited application
variables. Captured argv contains only executable/headless/verbose/project/probe
arguments. Original purchase identifiers were checked absent from environment
and argv. Native cwd is the isolated archived game.

Each restart's actual private file was **337 bytes**. The driver captured its
hash, length, exact key list and redacted config before launch. Before constructing
the UI, the native probe hashed the text it actually parsed, reported its length
and keys, and rejected nonminimal retry configs. All six launch-read bindings,
including the two initial sends, matched the prelaunch records and native PIDs.

| Source | SHA-256 of actual private retry file, identical on both restarts |
| --- | --- |
| `701ce2c4` | `baf7f9d638e37be2fe5581a9f3c98afc8aad8c8e874570be3f857d287e1bd1b2` |
| `7b6f379` | `b579890c1d7cbf7ddf30fe9485b32d70372583c68d1424ba73ef0ed8c4e78c33` |

Inspect each arm's `run-1/recovery.fixture.redacted.json`,
`second-restart.fixture.redacted.json`, corresponding `*.launch-inputs.json`,
`native_inputs_prepared` timeline entries and native `fixture_read` events.
`verification.json` independently reconstructs the key/hash/length/PID matches,
original redacted-file/environment hashes, source bindings and economic result.
Plaintext credentials are not published, so private-file hashes are cross-process
bindings rather than hashes reproducible from the redacted copies.

## Exact provenance and process boundary

| Component | SHA-256 |
| --- | --- |
| Frozen Python driver | `168b2574f94a660f8fd62bf974136c6e55536e5896ea3ab08fa66e670e61885d` |
| Frozen external probe | `f33f1c7e52206aeb3ca54f4a5dc65e07d7e859b323b3b137367d6fd926d314ff` |
| Both production `economy_api.gd` files | `246a50de1e68137715f2e1430b6c2f5cd42761f0d64acb26032e7f8668e81e7f` |
| `701ce2c4` production `economy_ui.gd` | `4dcf553e08180727f8aed9b5fd2543123f8b23d6dc63433beb33027550d2f236` |
| `7b6f379` production `economy_ui.gd` | `310cb4e7aaf110efd6b6d8eebc221231bdb169665a3062b1bc13437af0f9a84b` |
| `7b6f379` production `transaction_journal.gd` | `72fa6d9779e621f71d11b5686080c1c12f1f46846fe129be5004f4930a320117` |
| Official Godot 4.7.2 executable | `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424` |

Every prelaunch record includes exact driver/probe/UI/API/journal source hashes.
The probe independently reads the on-disk probe/UI/API/journal hashes. All match
the frozen harness and exact measured Git archives; the baseline records the
journal source's absence. Full archived-source and copied-cache manifests remain
available. Both archived production sources remained unchanged, and the shared
backend tree is `67027b4fa17674ef067c84401af76eb1524419ac`.

The existing hold proxy observed upstream HTTP 200 and held all response headers
and bytes. An independent read-only PostgreSQL connection observed the commit
before kill request. Native exit was acknowledged, the held response discarded,
and only then recovery launched. Original purchase responses were not delivered.
Kill acknowledgement occurred at **08:40:47.494774 UTC** and **08:41:03.443281 UTC**;
hold-to-ack intervals were 110 and 125 ms. These establish ordering, not speed.
All native launches recorded an empty competing-native PID list.

Python was **3.12.14**, PostgreSQL **17.11**, endpoint **127.0.0.1:55439**. Both
uniquely created databases were confirmed dropped:

- `sightbreak_receipt_e1b13d8620281b05_test`
- `sightbreak_receipt_85b3fcb05611aa0a_test`

The first invocation timed out connecting to PostgreSQL before database creation;
its `runs` list is empty. Its intended database
`sightbreak_receipt_dc2c4fa65cf1f39b_test` was later confirmed absent. The initial
restore's server log records successful startup, but its controlling shell timed
out before writing a return-code record. After the subsequent session/server
interruption, read-only status found the dedicated server absent again. The
recorded existing cluster/data/options were restored, authenticated health and
data-directory identity were verified, and the two requested cases then ran.
Failed logs and restoration records are retained. There was no completed case to
repeat, no data reinitialization and no other worker database/process removal.

## Prior three-case neutral verdict, retained separately

The independent frozen review in
[PR18 comment 6355013968](https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6355013968)
declared **WIN: Set-8F5F7604**, supported **3/3** versus exact-receipt failure
**0/3** for Set-673EECBC, limited to stable postcommit/withheld-response/native-kill
recovery. Both groups settled every initial purchase once with no subsequent
economic effect. This was a recovery distinction, not duplicate settlement.

That reviewer verified all 122 manifest payloads and reconstructed all six cases,
30 SQL stages, 18 native outputs and the journals/session/order evidence. Its
2,078 observation-consistency checks had no unresolved mismatch. Prices
400/401/10,000,000 burned fees 12/12/300,000; each case added one Operation, two
Ledger rows and one settlement Audit row. Candidate journals of 303/303/308 bytes
survived unchanged, exact requests/results replayed, and second restarts were
empty. The other group had stable journal absence and empty retries. The reviewer
also reconciled the extra ancillary seed rows and six groups of fresh sessions.

The strongest remaining gap was causal/provenance independence: recorder source
was withheld and every restart read a fixture that still carried original
purchase fields. The proposed falsifier was recovery with credentials/original
server/surviving journal and original purchase fixture inputs absent. This new
two-case run tests that stronger supplied-input boundary directly. It does not
retroactively relabel or replace the prior measurements or complete the separate
source critic's review.

The prior verdict explicitly excluded arbitrary crash windows, journal-write or
flush interruption, backend/power failure, manual confirmation, physical devices,
performance/statistical reliability and independent instrumentation/shipping
attestation. It did not verify the outside ancillary 36/37 versus calibrated
37/37 claims; those remain separate and contributed no recovery cases. Neither
that six-case campaign nor the ancillary regression was rerun here.

The exact prior frozen file is retained at
`native-journal-only-restart-evidence/prior-review/_FROZEN_VERDICT.md`, SHA-256
`750bfb02e65f3f348567b8bf453b4387f931c70549d7c50469d377fc63bec2ee`.
It is not included in the new neutral outcome packet.

## Reproduction and limits

Use a clean checkout of harness commit `7be70f73`, the existing exact-source
import caches, and new output directories. Run the following serially with the
existing Python 3.12.14 venv; the retained `r2/*.command.json` files contain the
actual commands and paths:

```powershell
$python = 'C:/Users/blith/AppData/Local/Temp/opencode/sightbreak-backend-trade-env/venv312/Scripts/python.exe'
$godot = 'C:/Users/blith/AppData/Local/Temp/opencode/godot/Godot_v4.7.2-stable_win64.exe'
& $python scripts/validate_native_transaction_restart.py `
  --source <clean-701ce2c4-checkout> --revision 701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd `
  --cache-source <clean-701ce2c4-checkout>/game/.godot --godot $godot `
  --out <new-control-output> --repetitions 1 --expect-recovered 0
& $python scripts/validate_native_transaction_restart.py `
  --source <clean-7b6f379-checkout> --revision 7b6f379a3f8c809d0985a64e883cbadfdd78d135 `
  --cache-source <clean-7b6f379-checkout>/game/.godot --godot $godot `
  --out <new-recovery-output> --repetitions 1 --expect-recovered 1
```

This is one case per source at a stable aftercommit boundary. The native methods
`_authenticate`, `_perform`, `_retry_pending` were exercised, not mouse/touch
confirmation. No backend crash, interrupted journal write/rename/flush or power
failure was tested. The process is not an OS filesystem sandbox; supplied-input
absence does not establish that a hostile process could not search unrelated
host files. On-disk source hashes and consistent recorder traces are not OS-level
execution attestation or proof of an honest recorder. Production API/UI/backend
bytes come from the named commits, without production changes.

[Raw evidence](native-journal-only-restart-evidence/README.md) ·
[Offline verification](native-journal-only-restart-evidence/verification.json) ·
[Git-blob publication proof](NATIVE_JOURNAL_ONLY_RESTART_GIT_PUBLICATION.json) ·
[Frozen protocol](NATIVE_JOURNAL_ONLY_RESTART_PROTOCOL.md).
