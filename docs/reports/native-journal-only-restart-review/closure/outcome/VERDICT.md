# Frozen blind outcome verdict

**WIN: `Set-829261D1`.** It supports the declared receipt-recovery outcome in its one supplied price-400 case. `Set-DB921BCA` fails that outcome in its one supplied case. There is sufficient observation evidence to decide this narrow comparison; source-execution attribution remains independently unverified.

| Neutral arm | Status | Exact recovery cases | Correct initial settlements | Purchase requests: send / recovery / second restart |
|---|---|---:|---:|---:|
| `Set-829261D1` | **supported** | **1/1** | 1 | 1 / 1 / 0 |
| `Set-DB921BCA` | **failed** | **0/1** | 1 | 1 / 0 / 0 |

The question judged is a stable native-client termination after a server commit and withheld response, followed by fresh same-owner authentication using the six-key supplied restart configuration. PostgreSQL remains available. This verdict concerns the recorded causal-input control, not a database-server crash or a reliability-rate estimate.

This document and its companion independent JSON audit were prepared before any controller or implementation-identity access. Evidence access was confined to the nominated ZIP and its contents. Review operations were offline extraction, parsing, hashing and comparisons. No native/application/database/network tests, worktree inspection, source edits or other agents were used.

For compact citations below:

- `A/` means packet path `Set-829261D1/case-01/`.
- `B/` means packet path `Set-DB921BCA/case-01/`.
- These aliases identify neutral labels only. They imply no implementation mapping.

## 1. Packet integrity and independent reconstruction

Both supplied pins match:

```text
ZIP SHA256      7a12ec5de2b8344794c60eab1b83cc116f40de5b0cf0360e6cc0a6e84032625f
MANIFEST SHA256 26ff68587ab032c55d27cbfc56adcb8d45aa5b377d7aac947516b94a7e4fc2b4
```

All **54 manifest-listed payloads** match both SHA-256 and byte length, with no missing or extra payloads. Including `MANIFEST.json`, the extracted ZIP contains 55 files. All ten economic-stage JSON files are present and match their pinned bytes. Both sets contain all three native stdout/stderr pairs; all six stderr files are zero bytes, and the stdout files contain no `ERROR:`, `SCRIPT ERROR:` or `WARNING:` lines. The original killed processes have no native `completed` event; the two restart processes per arm complete and exit with code 0. (`MANIFEST.json`; both arms' `*.stdout.txt`, `*.stderr.txt`, and `timeline.jsonl`.)

I independently parsed the observations, rejected duplicate JSON object keys, compared all economic rows, reconstructed changes by row ID, checked raw HTTP JSON against its parsed counterpart, and joined config, PID, session, journal and receipt records. Producer `result.json` booleans did not determine the outcome. The row counts/deltas, persisted operations, purchase lists and recovered-result comparisons in the semantic aids agree with the independently computed facts.

The ten timeline `state_sha256` values are independently reproducible as SHA-256 of UTF-8 `json.dumps(economic_state, sort_keys=True)` using default separators and no trailing newline. They are economic-object hashes, distinct from the manifest's complete-file hashes. A compact-separator encoding produces different hashes; using the matching default-separator encoding resolves that serialization difference for all ten records.

These checks establish integrity of the supplied packet. They do not independently establish its external publication history, recorder authenticity or the claim that these were unchanged from an earlier publication; those originals are outside the permitted evidence boundary.

## 2. Supplied restart inputs and actual native reads

**All four restart configs contain exactly** `{url,journal,mode,username,password,owner}`. Each uses `mode: "retry"`. The published config values carry the same owner, username, server and journal location as the initial send, with no listing/item/seller UUID, original purchase path, idempotency key, payload, expected price or expected result. Owner is deliberately retained because it is an allowed authentication/binding field. (`A/` and `B/recovery.fixture.redacted.json`, `second-restart.fixture.redacted.json`.)

For every launch, the prelaunch record matches the timeline's `native_inputs_prepared` record. Its private-file SHA-256, length and key list match the native `fixture_read` event. Every native event has the corresponding launched/finished PID. Native `fixture_read` precedes `construct_ui`, `add_ui` and `ui_ready` in the native log.

| Arm | Phase | Native PID | Actually read bytes | Actually read fixture SHA-256 |
|---|---|---:|---:|---|
| A | send | 20004 | 670 | `0e86dec47b7f98ce4ac373eb14b167d9dc9a97fff4468358dce253ecf89d61af` |
| A | recovery | 1700 | 337 | `b579890c1d7cbf7ddf30fe9485b32d70372583c68d1424ba73ef0ed8c4e78c33` |
| A | second restart | 22640 | 337 | `b579890c1d7cbf7ddf30fe9485b32d70372583c68d1424ba73ef0ed8c4e78c33` |
| B | send | 23852 | 670 | `6c88e6d480005952c917e3fd7dee0cdaeaa7bcaf8c3cfc215d09c4aa9f6b3ecb` |
| B | recovery | 28396 | 337 | `baf7f9d638e37be2fe5581a9f3c98afc8aad8c8e874570be3f857d287e1bd1b2` |
| B | second restart | 13500 | 337 | `baf7f9d638e37be2fe5581a9f3c98afc8aad8c8e874570be3f857d287e1bd1b2` |

Sources: each arm's `send.launch-inputs.json`, `recovery.launch-inputs.json`, `second-restart.launch-inputs.json`, and each corresponding stdout `fixture_read` event (displayed line 16). Native read times for A are `1792831262.821`, `1792831264.167`, `1792831265.791`; for B, `1792831246.814`, `1792831248.201`, `1792831249.478` Unix seconds.

Preparation precedes launch at timeline lines 2/3 and 28/29 in both arms, then 62/63 in A and 47/48 in B. The replacement uses the same displayed fixture path as the initial send. The different digest, 670-to-337-byte reduction and native six-key reads support that the restarted process parsed the replacement configuration rather than the retained initial evidence copy. No other native PID is reported at the three launches in either arm.

The supplied argv is the headless/verbose native executable invocation with `--path [PROJECT_ROOT] --script [EXTERNAL_PROBE]/driver.gd`. The 16 supplied environment keys are `APPDATA`, `COMSPEC`, `HOMEDRIVE`, `HOMEPATH`, `LOCALAPPDATA`, `NUMBER_OF_PROCESSORS`, `OS`, `PATH`, `PATHEXT`, `PROCESSOR_ARCHITECTURE`, `SIGHTBREAK_RECEIPT_FIXTURE`, `SYSTEMROOT`, `TEMP`, `TMP`, `USERPROFILE`, `WINDIR`. The sole application-specific environment value is the fixture locator. No purchase values occur in the visible restart config/environment/argv/cwd records.

**Input-absence limit:** each published restart config is 232 bytes, whereas the original private file reported by both recorder and native reader is 337 bytes. Credentials and paths were transformed. The published file hash therefore cannot reproduce the original private-file hash or the pre-neutralization redacted-file hash; the transformed environment likewise cannot reproduce its original digest. Matching original hashes across recorder/native events is a useful cross-process binding, not independent possession or rehashing of the original secret-bearing bytes. Absence from neutralized OS-path values and redacted credentials is not independently inspectable here. This is disclosed in `README.md:88-107`, and is retained as a provenance limit rather than mislabeled as a packet hash failure.

## 3. Real commit, held response, death and recovery order

Both initial purchase requests are `POST` to their original `/market/<listing>/buy` path with strict JSON integer `expected_price: 400` and the original UUID idempotency key. Native `perform_entered` follows authentication and agrees with the proxy's raw body. Each upstream purchase returns HTTP 200 and a full receipt before the response barrier. (`A/timeline.jsonl:19-20`; `B/timeline.jsonl:19-20`; both `killed-client.stdout.txt`, PID 20004 or 23852.)

The following ordering is recorded within each harness clock domain:

| Event | A monotonic_ns | B monotonic_ns |
|---|---:|---:|
| Upstream 200 / hold before client headers | 112333156000000 | 112317218000000 |
| Committed SQL snapshot recorded | 112333234000000 | 112317296000000 |
| Kill requested | 112333234000000 | 112317296000000 |
| Native finished, exit code 1 | 112333265000000 | 112317328000000 |
| Kill acknowledged | 112333281000000 | 112317328000000 |
| Post-kill SQL snapshot / held response discarded | 112333343000000 | 112317406000000 |
| Minimal recovery inputs prepared | 112333375000000 | 112317437000000 |
| Recovery process started | 112333484000000 | 112317546000000 |

Sources: `A/timeline.jsonl:20-29` and `B/timeline.jsonl:20-29`. Where the coarse monotonic values tie, record sequence and recorded wall timestamps supply the event order; I do not infer distinct nanosecond timing from tied values. Database clocks, native Unix seconds and harness monotonic clocks are kept distinct.

The hold, kill request and discard report **zero client response bytes**, and there is no original purchase `proxy_response_delivered` event anywhere in either timeline. The killed PID is consistently 20004 in A and 23852 in B. The original stdout ends at `perform_entered`, without a completed purchase result. Recovery launches only after the acknowledged exit and discard.

The committed state is independently visible through a separate recorded PostgreSQL connection, not merely the proxy's success assertion:

- A: `02-committed-before-kill.json`, database `sightbreak_receipt_85b3fcb05611aa0a_test`, backend PID **8636**, snapshot `2498:2498:`, database clock `2026-10-24 04:41:03.373358-04:00`.
- B: `02-committed-before-kill.json`, database `sightbreak_receipt_e1b13d8620281b05_test`, backend PID **8216**, snapshot `2481:2481:`, database clock `2026-10-24 04:40:47.428245-04:00`.

All ten snapshots report PostgreSQL 17.11 on port 55439. Each arm has five distinct snapshot connection PIDs, correctly joined to its timeline events and database name. Native logs identify Godot 4.7.2. These are recorded native/PostgreSQL observations, not an independently witnessed live execution by this reviewer.

## 4. Exactly one settlement and complete economic stability

Both cases have the following independently derived initial-to-commit changes:

| Economic table | Before | Committed | Actual change |
|---|---:|---:|---|
| players | 2 | 2 | Buyer 2000 -> 1600; seller 2000 -> 2388; other fields unchanged |
| items | 1 | 1 | Owner seller -> buyer; market reservation -> null; other fields unchanged |
| listings | 1 | 1 | active -> sold; buyer null -> original owner; other fields unchanged |
| operations | 0 | 1 | One owner/listing/key-specific Operation with request hash and full receipt |
| ledger | 2 | 4 | Exactly -400 purchase and +388 sale; old rows unchanged |
| audit | 2 | 3 | Exactly one `market_settled`; old rows unchanged |
| loadouts / rewards / trades | 0 / 0 / 0 | 0 / 0 / 0 | No change |

The combined player balance falls from 4000 to 3988, matching the **12 fee** in the receipt and settlement audit. No additional row is removed or added beyond the Operation, two Ledger rows and one Audit row. Sources are each arm's actual `01-before.json` and `02-committed-before-kill.json`.

Concrete row bindings:

| Identity | A | B |
|---|---|---|
| Buyer/owner | `03cb151e-511a-451b-93ca-2543276833c7` | `69106eca-e517-4e7c-8ea9-e011d813edd6` |
| Seller | `8c98b9bd-2cd4-4e17-9d97-d80419172ad2` | `c1bf9ae6-de8e-44ef-bf4b-1f5e470e2f2b` |
| Item | `f6f87dbd-2e0c-491a-a829-9e36c6d93979` | `94831ba4-33ac-410f-b5d8-d37a66145da7` |
| Listing | `e056813c-4926-4000-8daa-eac8d6f2d48f` | `bcd963c4-9bba-434d-9731-998a2f9e53d1` |
| Idempotency key | `5738ac06-1b84-446c-9f72-77215c6e5809` | `7fe3e901-a046-4f33-b048-6a353e36b910` |
| Purchase Ledger row | `f18cb6e5-c6d8-44df-9021-eb9dcac9c371` | `44fb0f23-ea27-41d6-b5e4-6ce65fee3fc5` |
| Sale Ledger row | `d9c4c26f-8154-498a-8453-116c404a2793` | `57838988-c951-4842-a351-f7e063aeb610` |
| Settlement Audit row | `35704f1b-2205-452d-9e11-d65d68631596` | `0d61ce85-04fa-4910-bd1a-9bc8e31e3aa2` |

Each Operation ID is exactly `<buyer>:buy:<listing>:<idempotency-key>`. Its persisted `request_hash` equals independently computed SHA-256 of the actual original UTF-8 body:

- A: `9f5ead2d6a450eff27899d6118ce0ee972bbe29137ef8e5c4ea6090c50458908`.
- B: `b1f1399e9931cd12aa72f9ff43558550cb68bfffeda7ac7f9fc5b86928e43df1`.

**Every field of every row in all nine economic tables is equal to the committed state in `03-after-kill.json`, `04-after-recovery.json` and `05-after-second-restart.json` for both arms.** This includes all retained initial rows; equality was not limited to counts or the purchased item. There is no ancillary seeded population in this packet, so empty tables are only evidence about their observed emptiness.

The reproduced committed economic hashes, unchanged through all later stages, are A `c45eaf85963a37d8731d2ec8e3a0b8229b0b8707b2d7639e66e65059055fe13a` and B `1f48ec829fa1adac731438bcd33d0bfe7012a71b277ed7e2706cb03ab91228f9`.

## 5. Fresh authentication, journal and exact receipt outcome

### Authentication in both arms

Each native phase issues one real `/auth/login`; there is no registration request. The native authentication owner, HTTP login owner and new PostgreSQL Session row all match the original buyer. The three native token digests per arm are distinct, are used on that phase's authenticated proxy requests, and appear as precisely the new Session row at the appropriate stage. Login expiration timestamps also match the database rows after timezone normalization. Existing sessions remain unchanged; counts are **2 -> 3 -> 3 -> 4 -> 5**. Those additions are authentication effects, not economic mutations.

| Arm/phase | Native token SHA-256, also the Session token_hash |
|---|---|
| A/send, PID 20004 | `df3e37dc1e68f21d8c3fcd2bd214d774681efbe87b56ea708a49e71fbc9c1ca9` |
| A/recovery, PID 1700 | `6a8d8fe25e57a4c0379a295d3bd888412054d5dfd469d024dca0586d8edf62cc` |
| A/second restart, PID 22640 | `b3f87b03bc21f14ed73b3ee8006529a46d9246dafc350661f90182987afd29f6` |
| B/send, PID 23852 | `c24de32edd2b2225df3870db6cdb4eb538f8b26f26baa67b89cf8c682e2a9c56` |
| B/recovery, PID 28396 | `e896e1da3ae6866978273b4cc109e6f8857204d2eba3346d4aeae01f9832b6d1` |
| B/second restart, PID 13500 | `ab881d3ad6744c3b9d2acf1b9acc8e8ae2cf525798a02e987f68c3b7dca5076b` |

Sources: `authenticated` events in the three stdout files per arm; login/authenticated-request events in each `timeline.jsonl`; `sessions` in stages 01-05. Tokens are redacted, so their digests are cross-record bindings rather than recomputed hashes of published plaintext tokens.

### Set-829261D1: supported, 1/1

`A/journal-before-kill.raw.json` and `A/journal-after-kill.raw.json` are byte-identical **303-byte** records with SHA-256 `4b860b00769605d69b5710e9d7ef6db162b131ada98c886195f2cee99b3d024c`. Their wrapper length/hash/parsed-record fields match the actual files. The schema-1 transaction contains the original owner, server, method 2, purchase path and payload. It contains no password, username, bearer token or authorization field. Its staged `message: "Transaction confirmed."` is a replay message, not itself proof of a server acknowledgement.

Recovery PID **1700** reports the complete captured transaction in `ui_ready.pending` at Unix `1792831264.292`, before its `authenticated` event at `1792831264.635`. Its completed `pending_on_start` matches the captured record exactly. The authenticated recovery purchase at `A/timeline.jsonl:45` has the same path, key and **byte-identical body** as the original at line 19:

```json
{"expected_price":400,"idempotency_key":"5738ac06-1b84-446c-9f72-77215c6e5809"}
```

The retry receives HTTP 200 and is delivered at lines 46-47. The original upstream receipt, persisted Operation response, retry upstream receipt and native completed result agree on the complete result:

```json
{
  "credits": 1600,
  "fee": 12,
  "item": {
    "acquired_at": "2026-10-24T04:40:59.556679-04:00",
    "collection": "Obsidian",
    "definition_id": "obsidian_rare",
    "id": "f6f87dbd-2e0c-491a-a829-9e36c6d93979",
    "kind": "weapon_skin",
    "marketplace_eligible": true,
    "name": "Obsidian / Carbon",
    "pattern_seed": 684732845,
    "rarity": "Rare",
    "reserved": false,
    "trade_eligible": true,
    "variant": "standard",
    "wear": 0.9322
  }
}
```

Sources: `A/02-committed-before-kill.json:102-125`, `A/timeline.jsonl:20,46`, `A/recovery.stdout.txt` completed event at Unix `1792831264.945`. Full object keys and values were retained. Native `1600.0`, `12.0` and `684732845.0` equal the corresponding whole numbers; booleans were compared as booleans, not numbers. The two raw response strings differ in JSON object key order, so this is exact complete receipt semantics, not byte-identical response serialization. The request bytes are identical and retain an integer price.

After recovery, `pending_after` is `{}` and the journal is absent. Second-restart PID **22640** starts with empty pending, authenticates afresh, returns no new receipt, makes zero purchase requests, and exits 0. Its only POST is login; its other requests are reads. The journal remains absent and all economic rows remain equal to the original committed state. (`A/journal-after-recovery.json`, `journal-after-second-restart.json`, `second-restart.stdout.txt`; `A/timeline.jsonl:63-80`; stages 04-05.)

### Set-DB921BCA: failed, 0/1

There is **no journal before or after termination**: `exists: false`, `record: null`, zero bytes, empty-byte SHA-256. The same absence remains after both restarts. The empty-byte digest in these wrappers does not represent a surviving journal file. (`B/journal-before-kill.json`, `journal-after-kill.json`, `journal-after-recovery.json`, `journal-after-second-restart.json`.)

Recovery PID **28396** has `ui_ready.pending: {}` and completes at Unix `1792831248.675` with `pending_on_start: {}`, `pending_after: {}`, **`result: {}`**. There is no recovery purchase in `B/timeline.jsonl:30-45`. Account credits 1600 and the purchased inventory item are refreshed successfully, but the fee-bearing original receipt is not recovered. The original Operation still persists the complete item receipt, including item `94831ba4-33ac-410f-b5d8-d37a66145da7`, pattern seed 1866701475, wear 0.4024, credits 1600 and fee 12. (`B/recovery.stdout.txt`; `B/02-committed-before-kill.json:102-125`.)

Second-restart PID **13500** also has empty pending/result and no purchase, with unchanged economic rows. That satisfies quiescence and prevents duplicate settlement, but does not repair the missing first recovery.

**Producer-label finding retained:** `B/result.json` says `authoritative_pass: true`, `checks.complete_result: true` and `checks.stable_journal_at_kill: true`, while also correctly reporting `recovered: false` and four false recovery checks. The generic positive flags do not establish the declared recovery outcome. Here stable journal state is stable absence, and a complete original server result is not a recovered native result. Treating those positive flags as recovery acceptance would be a false pass. The underlying observations themselves are consistent about failure.

## 6. Strongest remaining concrete gap and bounded conclusion

**The strongest remaining gap is source-execution provenance.** The actual source hashes for driver/probe/economy UI/API/journal have been replaced by role placeholders, and the sources, original paths and immutable implementation bindings are withheld. Equal placeholder strings cannot establish equal original hashes, identify the executed implementation, or demonstrate that the probe and application derived purchase inputs exclusively from the journal. Native logging of fixture hashes and keys establishes an observed input-read binding; it does not attest the semantics of all loaded code. (`README.md:90-104`; both arms' launch-input `source_file_sha256` maps and native stdout `fixture_read` maps.)

A later controller/source review could inspect those immutable originals, transformation records and loaded-source bindings to address that specific attribution gap. This frozen verdict does not assume such a review has happened. It also preserves the related limits:

1. Redacted private config and neutralized environment/path values cannot be independently rehashed or completely inspected for concealed purchase inputs from this packet. The visible six-key records and matching native read receipts support supplied-input absence within the disclosed transformations.
2. No OS sandbox or independent file-access trace is supplied. Config/environment/argv absence does not prove absence from all host files or from loaded code. The retained initial fixture in the evidence packet is not shown to be the config supplied on restart, but exhaustive non-access to every other host file is not established.
3. Journal survival is established at the measured stable termination boundary. The packet contains no interrupted journal-write/rename/flush or power-loss evidence; none is required to decide this stated case.
4. Both arms use native headless direct-method observations. The packet supplies no broader production/mobile/manual-UI acceptance, statistical reliability or ancillary-regression evidence, and this verdict makes no such claim.

These limits do not make the neutral-label outcome a tie. A supplies a surviving transaction, the matching original retry, the full original receipt and subsequent quiescence; B supplies a genuine absence control and a demonstrable receipt-recovery failure. **Final bounded decision: `Set-829261D1` wins this one stable-termination causal-input control case; `Set-DB921BCA` fails recovery.** No additional crash-window variation is required solely to measure a different scope.

## Frozen audit artifact

The companion `independent-audit.json` was generated from direct observations by the scratch-only `audit_packet.py`. Its 9,645-byte SHA-256 is:

```text
873b727b69b44eb2dd6d9116eb13d34b86e20b268c50783cb291f617ed957f39
```

Scratch directory:

```text
C:\Users\blith\AppData\Local\Temp\opencode\independent-journal-critic-7fbb839fd97341e1aa44aa5f82d59883
```

This exact Markdown and the JSON audit are the pre-identity record. Their final file hashes are reported with the delivery. Any later identity-based analysis must be a separate supplement and preserve these findings.
