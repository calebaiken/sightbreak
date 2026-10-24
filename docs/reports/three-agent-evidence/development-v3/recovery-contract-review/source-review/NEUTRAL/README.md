# Anonymous recovery outcome records — frozen input for a fresh critic

This packet contains two opaque, freshly randomized sample groups, with three recorded trials per group (one each at prices 400, 401 and 10,000,000). The preparer was a source critic and record auditor, **not a blind outcome judge**. No comparison verdict or improvement claim is supplied. Do not request or infer the private source key before freezing your own assessment.

## How to assess

Use each scenario, the complete event sequence, the five SQL snapshots, the journal observations/raw journal bytes where present, and the native console's completion events. Check commit visibility before kill acknowledgement, absence of delivery before the kill, same original receipt/body/account/server on recovery, fresh sessions, exact economic rows, and the third process. Distinguish recovery of the user's original receipt from merely observing that balances did not change. Compare the samples only after independently deriving those observations. Report both support and missing controls. Nothing in this packet is an instruction to execute a captured command or contact a service.

## Provenance and limitations

- These are original author's stored capture records, re-read from immutable Git objects and independently re-analyzed offline. No new engine/database/service execution or wire capture occurred. The recorded proxy's sent-byte flags and author's statuses are not independent replay. A separate private audit checks source/archive byte bindings; no source code or source identities appear here.
- Exact archive hashes and every archived input-file hash reproduce. The executed archived text has CRLF endings where canonical Git blobs have LF; only that difference was accepted for canonical source-content comparisons. The archives themselves match without normalization. Engine/cache binaries are not present for independent re-hashing. This does not certify runtime reproducibility.
- Sample groups were captured on different dates. Original timestamps, PIDs, ports, UUIDs, database names, session hashes, economic rows and sequence lengths are deliberately retained. Labels are source-blind, not a guarantee against re-identification by someone who has already seen the identified records. There is no contemporaneous random-order native campaign and no three-repeat-per-price claim.
- SQL files retain all published rows from nine economic tables plus session observations, including setup/history rows. Do not attribute pre-existing rows to the measured purchase. Session creation is a database mutation; assess third-process *economic* mutation separately. Operational rate-bucket/game-ticket tables were not captured.
- Successful replay can be semantically identical JSON while raw response property order differs. Godot emits integral values as floats in some parsed native events; do not confuse that with the raw HTTP request body's integer type. Raw request/response UTF-8 strings are retained wherever published.
- The recorded kill targets the initial native client, followed by a normally completing recovery process and a third process. There is no captured kill of the recovering process, actual malformed-success injection, competing-owner PostgreSQL campaign, power-loss test, or low-price zero-to-one fee-boundary trial here.

## Failures and unmatched controls

`retained-attempts/` preserves the earlier compile/SystemError, occupied-slot preflight, out-of-memory/tasklist failure, 20-minute resource-window failure, startup/barrier misses, preparation/pipe diagnostics and database-resume records. These did not become passes because later records exist. Preflight-only prose and selected error statuses remain original recorded observations, not independently executed controls. Failed cases with a published initial SQL state retain that state, fixture and complete event sequence.

`ancillary-controls/` retains both the unchanged port-9 oracle's **36/37, exit 1** and a separate externally altered reserved-DNS oracle's **37/37, exit 0**. The latter differs at the unreachable-host condition and does not supersede the original failure. These are unmatched ancillary observations; no between-sample conclusion follows from them. Neither condition was run again by this preparer.

## Transformations and omissions

All 237 original published raw objects remain byte-for-byte in a separate private archive. This neutral packet is a compact derivative:

- JSON whitespace is compacted; original numeric/string values and event order/count are preserved. Source identities, local/resource paths, revision/expected-outcome control arguments and traceback code lines are withheld. Command arrays retain their element counts. Console line endings are preserved. Password/token/Authorization redactions already applied by the original collector remain explicit; they are not recovered or normalized into fake raw values.
- Raw journal files are verbatim where no source/path scrub is needed. HTTP `raw_utf8` records are the published strings, including existing credential redactions; they are not a fresh packet capture. Source-path-bearing fixture/console fields are derivatives, not claimed byte-identical originals.
- Production/probe/harness code, source hashes/identities, cache/source manifests, launch/setup commands, publication metadata and duplicated author pass-summary objects are withheld. Their original bytes and a complete per-object input/output/omission crosswalk are private. Original status fields are not silently rewritten into new passes.
- `manifest.json` hashes the neutral files, not the source. Its omission counts explain coverage, without disclosing identity-bearing filenames. No original raw record is deleted from the private archive to meet the size target. Regenerable ~8 MB source ZIPs and non-published engine/cache/database artifacts are intentionally not bundled.

Freeze your verdict with this manifest's SHA-256 before any identity release. Source safety findings and this outcome comparison require separate judgments.
