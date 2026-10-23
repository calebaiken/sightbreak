# Independent production market lost-response review

Verdict: PASS for the declared local market recovery boundary at frozen source
`882931dd7024c2b200a72b2a52017dd98b95ee6a`. Root released the runtime lane
before launch. The critic was active before the driver started, independently
queried live SQL at both declared checkpoints, retained each query before
releasing its barrier, and recomputed the actual retained campaign afterward.
This is one passing bounded attempt, with no deadline extension or retry.

## Source and actual runtime

Builder session `52864`, driver PID/PGID `149153`, used owned run
`sightbreak-pg-receipt-5f9ae87bdf8e`, container
`98a71b3273263cf7ad395e17915c60b60bf9b73ac1bf204e439e1dcd66faa78a`, database
`sb_receipt_5f9ae87bdf8e_test` and role `sb_receipt`. The critic retained selected
current Docker daemon fields, exact container/run/owner labels, cached image
identity, one loopback port mapping, exact writable named data volume and its
labels. It inspected no process/container environment or credentials.

Actual PostgreSQL is 17.11. The cached pinned image is
`postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3`.
Godot is `4.7.2.stable.official.ed1daf0bf`, SHA-256
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
All four unchanged production migrations ran. Independent source-after captured
the exact clean frozen source, component hashes and trees before the builder was
permitted to archive evidence. The production backend, server and game files
remain equal to accepted `89393f3`; the added game files are only the test/UID.

## Independent live SQL

Both observations used the explicit managed local Docker socket, selected-field
SQL, internal PostgreSQL socket and an enforced read-only session. Actual
`transaction_read_only` returned `on`. Endpoint/context/TLS selectors were
cleared while Docker config/proxy identity was preserved. No password or DSN
appeared in argv, output or retained observer configuration.

| Phase | Query requested UTC | Query completed UTC | Seconds after ready marker |
| --- | --- | --- | --- |
| Pre-original | 08:49:10.638419 | 08:49:10.756913 | 39.799 |
| Post-final response and refresh | 08:49:27.503809 | 08:49:27.598015 | 13.080 |

Both occurred on 2026-10-22 within the existing 60-second checkpoints. Each
receipt retains its own query ID, requested/completed monotonic and wall clocks,
actual SQL clock, raw rows and source/cluster/postmaster identity. The final
independent query starts after the actual final native response and fresh
account/inventory refresh. It is not a reused earlier observation.

The critic independently verified the original fixture and recomputed its
transition to buyer 600, seller 488, outsider 0 and fee 12. Exactly one original
buyer/listing/UUID operation has the exact canonical request hash and full
original business response. Exactly two sale ledger rows debit 400 and credit
388. The original item transfers to the buyer, retains its metadata, clears its
reservation, marks the listing sold and removes the seller's loadout. XP stays
zero; no rewards or game tickets exist. Its own final live rows equal the
campaign's settled business state. All nine campaign SQL snapshots have distinct
query IDs and correct phase/query clock bounds.

## Lost responses and native recovery

The full timeline contains exactly three non-auth mutation attempts, all on the
same original POST path with byte-identical raw bodies, UUID and price 400.
Every attempt was recorded before forwarding. Six distinct native processes
complete actual fresh production login; the proxy retains only auth status and
redaction markers.

For both the original purchase and first retry, the actual production HTTP 200
precedes retained committed SQL, the live native PID/start identity and its
owned journal socket inode, kill request, acknowledged Linux exit `-9`, and
response drop with zero response header bytes sent. Kill acknowledgments occur
62.062 ms and 58.587 ms after the respective upstream 200s. The driver then
revokes each killed session and observes actual 401 with the old session.

The two captured journals are byte-identical, 303 bytes, SHA-256
`f174f1f912e0eefccb825dce66d62dadb70e8303834aa8bea3c0740a29c0954c`.
They bind the original account/server/method/path/payload and contain only the
declared transaction fields. Wrong-account and second-origin native controls
retain the journal, return the actual guard error and issue zero non-auth
mutation attempts. Outsider API replay returns 409 without the buyer's item.

The third correctly authenticated process receives the original stored result,
clears the journal and reports actual post-response `/me` and `/inventory`
reads equal to its native account/inventory. Post-clear restart has no pending
record and sends no mutation. Changed price 401 with the original key receives
409. All control/replay snapshots preserve the single original business effect.
Native logs show no script/parser/resource-leak failure and the proxy has no
failure event. The driver exits zero with `focused_checks_passed`.

## Privacy and cleanup

The frozen driver's in-memory private-value scan covers every persistent owned
output/state byte and reports no credential persistence or redaction event.
The independent audit checks auth evidence shape, transaction raw bodies,
credential-field/value patterns and journal fields without reading or retaining
the private credential values. Backend password/session hashes remain outside
selected SQL. This preserves the distinction between the driver's private-value
test and the critic's independently inspectable evidence.

After completion the critic independently checked the exact CID and volume:
both selected inspections return absence. Every retained driver/API/native/
command/PostgreSQL PID identity is absent. All five recorded loopback ports,
including the deterministic journal listener, reject connection. These direct
observations agree with the builder's successful bounded cleanup receipt.

`runtime-r1/` retains both independent live witnesses and exact selected command
outputs, independent source-after and cleanup, the recomputation verdict,
62 campaign files (127,919 bytes) and their hash manifest. `observe_live.py` and
`audit_runtime.py` retain the actual observer/audit code. Earlier rejected source
and correction failures remain preserved separately.

This result qualifies local production PostgreSQL/API market receipt recovery
under two native process kills. Fictional fixture balances are not earned
progression. Store/case routes, remote-host impairment, host power loss, rendered
player consent, usability and complete G3/G7/G16 remain open.
