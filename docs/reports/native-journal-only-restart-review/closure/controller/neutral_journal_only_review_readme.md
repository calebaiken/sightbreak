# Neutral journal-only restart observations

## Review boundary and fixed question

Review only this packet. Do not consult repositories, prior verdicts or controller
material to identify the implementations. Random group labels have no ranking.
Use the supplied observations; do not launch clients, applications, services,
database operations or further tests.

The question is whether an existing-account native process can recover the exact
committed market receipt after its original response is withheld and the process
is killed, when each restart's supplied fixture contains only these six keys:

`url`, `journal`, `mode`, `username`, `password`, `owner`.

There is one price-400 case per group. The initial send fixture includes purchase
inputs. The declared method truncates that same private fixture before each
restart and supplies no original path, payload, receipt UUID, item, listing,
seller, expected price or expected result through the replacement fixture,
environment or argv. The surviving journal, when present, is expected to contain
the original transaction. Distinguish journal contents from supplied fixture
contents. A missing journal is an absence control, not a surviving record.

## Files and reconstruction

Each case contains all retained case-level observations:

- Actual SQL snapshots `01-before.json` through
  `05-after-second-restart.json`, containing complete economic and session rows,
  PostgreSQL connection metadata and database clocks. All ten SQL files retain
  their original published bytes.
- `fixture.redacted.json`, the initial purchase/oracle context. This retained
  evidence copy is not the replacement fixture supplied on restart.
- `send.fixture.redacted.json`, `recovery.fixture.redacted.json`, and
  `second-restart.fixture.redacted.json`: the actual per-launch configs after
  credential redaction and disclosed path neutralization.
- The corresponding `*.launch-inputs.json`: prelaunch key lists, original
  private-file hash/length, original redacted-file hash, full argv and supplied
  environment key/value records, cwd and source-file hash fields.
- `timeline.jsonl`: prelaunch input records, native PIDs, HTTP requests/responses,
  hold/discard events, independent committed-state reads and acknowledged exits.
- Complete native stdout/stderr from the initial process and both restarts. The
  native `fixture_read` event reports the hash/length/keys of the config bytes
  actually parsed before UI construction. It also reports source-file hashes.
- Journal captures and original credential-free journal byte files where present.
- `result.json`, the producer's checks and recorded outputs. This is not an
  independent verdict.
- `semantic-comparison.json`, an observation-derived aid with actual row deltas,
  economic equality, persisted/wire/native receipts, login/session matches,
  ordering and per-launch input comparisons. Independently verify these claims.

`OBSERVED_COMPARISON.json` gives observed initial row counts. `MANIFEST.json`
contains every other ZIP payload's SHA-256 and byte length. Use the separately
supplied ZIP and manifest pins. Container timestamps are fixed; timestamps within
the records are original.

## Deterministic quality bar

For every finding, cite a packet path and relevant row ID, phase/PID or timestamp.

1. Confirm completeness and manifest integrity. Reconstruct the result from rows
   and traces before relying on producer booleans.
2. For each restart, require exactly the six permitted config keys. Compare the
   prelaunch key list and private-file hash/length to the native `fixture_read`
   event, bind its PID to the launch/exit events, and check that the input record
   precedes launch. Inspect the supplied environment keys/argv and the disclosed
   transformation limits. A redacted/transformed file cannot independently
   reproduce a private-file hash that includes a secret.
3. Correlate the original strict-integer request, owner and receipt with the real
   upstream success. Require hold, independently visible SQL commit, kill request,
   acknowledged exit and zero-byte discard before recovery. Check for any
   contradictory original-response-delivery event. Keep clock domains separate.
4. Derive the buyer debit, seller credit, fee, ownership/reservation, sold listing,
   persisted Operation/request hash/full response, Ledger and Audit changes from
   actual rows. Require exactly one initial settlement and compare every economic
   table through both restarts, including unrelated rows.
5. Bind all three fresh login digests to real same-owner Session rows. Inspect
   journal bytes or absence, restored pending state, original retry UUID/integer
   body/bytes, and full wire/persisted/native receipt equality. A refreshed account
   or inventory alone is not receipt recovery.
6. Require an empty pending state and no purchase request or economic mutation on
   second restart. Session creation is not an economic mutation.
7. Report each group's exact recovery count and `supported`, `failed` or
   `insufficient`, including contradictions and remaining provenance limits.
   Identify a strongest group only by neutral label if supported. A stable
   missing journal or successful original settlement is not successful recovery.

## Transformations and limits

- Source/version mappings, original paths, original Git bindings, source code,
  source-identity hashes and prior verdicts are held outside the packet. Source
  hash values in observations are replaced by role-labelled placeholders. This
  packet cannot independently attest source-hash equality; exact values and
  immutable originals remain with the controller for source review.
- Exact executable/project/probe/private-state paths and machine-specific OS
  environment path values are replaced by bracketed placeholders. Environment
  key lists, purchase inputs, outcomes, UUIDs, PIDs, clocks and session digests
  remain. Where an OS-path value is replaced, its original absence-of-purchase
  assertion is subject to controller/source verification.
- Every substitution, original immutable commit/path/Git blob/SHA-256, neutral
  file SHA-256 and byte-identical flag is recorded in the separate controller key.
  Transformed copies are not raw-byte-identical files. Embedded fixture and
  environment hashes refer to the original pre-neutralization records; the
  manifest pins the supplied transformed bytes.
- Synthetic plaintext passwords and bearer tokens were redacted by the recorder.
  Original private-file hashes remain as cross-process bindings, not published
  credentials. All actual economic/session rows and journal bytes are retained.
- One case per group is a narrow causal-input check, not a statistical reliability
  or performance study. Original dates/times are preserved. Both invocations omit
  ancillary-regression seeding; no ancillary regression is part of this packet.
- This is a native headless direct-method test of `_authenticate`, `_perform` and
  `_retry_pending`, not mouse/touch confirmation or physical-device qualification.
  It does not test backend failure, interrupted journal write/rename/flush or
  actual power loss. It is not an OS filesystem sandbox: supplied-input absence
  does not prove a hostile process could not search other host files.
- Native whole-number responses may appear as floats and JSONB may reorder object
  keys. Preserve exact JSON integer requests and nanosecond integers, and compare
  complete receipt semantics without discarding fields.
