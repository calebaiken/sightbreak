# Journal-only restart input follow-up

## Frozen scope

This test/harness-only follow-up addresses the fixture-assisted recovery
falsifier from the completed three-case-per-group neutral review. It runs one
price-400 purchase on each exact source: `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`
and `7b6f379a3f8c809d0985a64e883cbadfdd78d135`. Use `--repetitions 1` and omit
`--native-economy`. Freeze this harness/probe in Git before either capture.

The original harness `31438cbcea6ef08a131ae312c65b94f7e3e882c3`, its six-case
evidence at `49268b8702c44a6a19adfc743727f5aad2a10e8b`, and its neutral packet
remain separate historical measurements. Production UI/API/backend source is
archived from the measured commits without edits. Import metadata comes from
their existing exact-source caches. Native launches are serial. Each invocation
creates and drops only its own `sightbreak_receipt_<hex>_test` database on the
recorded PostgreSQL endpoint `127.0.0.1:55439`.

## Changed input boundary

- Price normalization occurs only in the probe's `mode == "send"` branch.
- Before recovery and second restart, the private fixture is truncated and
  rewritten with exactly `url`, `journal`, `mode`, `username`, `password`, `owner`.
  The original path, receipt UUID, payload, item, listing, seller, expected price
  and expected result are absent. The driver retains its original in-memory
  config for oracle comparisons. Its redacted evidence copy is outside the
  extracted project; its path is never supplied to the native process.
- Native environment construction uses an explicit Windows housekeeping-key
  allowlist plus the single fixture-path variable. The captured full environment
  and argv are checked for original purchase identifiers. The native working
  directory is the isolated archived game. The setup-fixture file is removed
  before native execution.
- Before each launch, retain the actual fixture hash/length/key list, redacted
  fixture and its hash, complete supplied environment/argv/cwd, and exact
  driver/probe/UI/API/journal-file hashes. Environment hashing uses UTF-8 JSON
  with sorted keys, compact separators and ASCII escaping.
- The external probe reports the hash, length and keys of the bytes it actually
  parsed before UI construction, and independently reads the on-disk probe,
  UI/API and journal-source hashes. The driver requires equality to its
  prelaunch record. Retry modes reject any key set other than the six above.
  Source hashes bind files; they are not OS-level execution attestation.

## Fixed outcome checks

Retain the existing actual SQL stages 01–05, PID and clock-domain timelines,
complete captured native outputs, request/response bytes, journal bytes or
absence, same-account fresh-session digests and economic invariants. Require a
held upstream success, independent committed SQL visibility, kill request,
acknowledged exit and zero-byte discard before recovery begins. Require one
initial settlement, exact original receipt/body/result on any successful replay,
and no additional economic effect or purchase request on second restart.

The planned absence control is 0/1 exact recovery; the other source's planned
result is 1/1. Preserve contrary outcomes and failed attempts. A missing journal
is not a surviving journal even when a stable-state flag is true.

This is a one-case causal-input check per source, not a new three-case campaign,
native economy regression, performance comparison or statistical reliability
study. It exercises native methods, not mouse/touch confirmation. It does not
test backend crash, interrupted journal writes/rename/flush or machine power
loss. The process is not an OS filesystem sandbox; the claim concerns supplied
fixture/environment/argv inputs and inspected source, not a malicious process
searching unrelated host files or proof against a dishonest recorder.

## Prior independent review source

PR18 comment: https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6355013968

Frozen file supplied by the controller:
`Temp/opencode/independent-receipt-audit-32dbe88ce35c4da8b2d16d21e7b0dc36/_FROZEN_VERDICT.md`.
SHA-256: `750bfb02e65f3f348567b8bf453b4387f931c70549d7c50469d377fc63bec2ee`.
Summarize its scoped verdict in the new report; any retained full copy must
match these exact frozen bytes. Keep that prior verdict and source mappings
outside the new two-case outcome-critic packet. No new critic is dispatched by
this follow-up.
