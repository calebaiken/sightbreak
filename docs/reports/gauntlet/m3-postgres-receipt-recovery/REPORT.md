# Production PostgreSQL market receipt recovery

The bounded market boundary passed on native-tested source
`882931dd7024c2b200a72b2a52017dd98b95ee6a`. One actual production API/PostgreSQL
campaign recovered two lost responses through fresh native EconomyUI/API
processes without a duplicate debit, grant or item transfer. This closes a
qualification gap in the accepted B-21 implementation; it does not identify a
new production defect or change production code.

The fresh critic independently observed both live SQL checkpoints, recomputed
the full raw campaign, captured clean unchanged source afterward and confirmed
resource cleanup. Its source-only review is `66760d65`; final runtime review
`5aa3992d` retains `independent-critic/RUNTIME_REVIEW.md`, both live SQL receipts,
independent recomputation and cleanup. Root receives this separate review commit.
The builder's result receipt is `runtime-r1/report.json` inside the archive.

| Observation | Actual result |
| --- | --- |
| Backend | Unchanged production API, four production migrations, PostgreSQL 17.11, pinned cached PostgreSQL 17 digest |
| Native | Pinned Godot 4.7.2; six fresh login processes using actual EconomyUI/API |
| Original/recovery dispatch | Three POSTs with identical route, raw bytes, UUID key and integer expected_price 400 |
| Lost responses | Actual original 200 and replay 200 held after fresh committed SQL; both still-live processes killed with return -9 before any purchase response headers |
| Journal | Original and second-kill captures are byte-identical, 303 bytes; final recovery removes it |
| Settlement | Buyer 600, seller 488, outsider 0; buyer debit 400, seller credit 388, fee 12; one original item transferred, seller loadout removed |
| SQL | Nine distinct timestamped driver queries plus two independent live read-only SQL witnesses |
| Controls | Wrong account and second owned origin retain original journal with zero non-auth mutation attempts; post-clear restart sends none; outsider and changed-price API calls return 409 without business changes |
| Authentication/privacy | Six fresh logins; actual old-session 401 checks; no persisted plaintext password/token and zero redaction events |
| Native diagnostics | No warnings, errors or resource leaks in retained native logs |
| Cleanup | Driver/API/native process groups absent, exact owned container and volume absent, all five ports closed including journal port 64049 |

The fixture consists of three production-registered synthetic accounts. Only
trusted setup in the verified owned test database seeds buyer 1,000, seller 100
and one seller skin using existing helpers and `fictional_test_fixture` ledger
reasons. The purchase adds exactly the two declared ledger entries and one
operation/audit; XP, rewards and game tickets stay unchanged. These are fictional
test balances, with no claim that they were earned by gameplay.

The independent SQL joins validate the original response against the exact
operation/hash and every returned item's database metadata, including random
seed, wear, acquisition time and eligibility. Fresh final account/inventory
reads match the native observations. Both actual SQL clocks and retained wall /
monotonic event order establish commit before kill and a new query after final
response plus refresh. Equal snapshots remain separate files.

Driver PID 149153 was observed starting at 08:48:20 UTC on 2026-10-22; the final
report was written at 08:49:29.394495 UTC, about 69.4 seconds later (start
observation has one-second precision). The exact recorded timeline spans
59.294250391 seconds. Exec session 52864 closed with exit 0. No retry or deadline
extension occurred. The driver used its declared checked 240-second work
deadline and separate cleanup allowance. Resource absence was then read back
independently by the builder and critic.

All 62 owned runtime files and four clean frozen pure-check files are retained
in `market-receipt-evidence.tar.gz`, with no exclusions. The archive has 66 members,
135,813 raw bytes and 19,069 compressed bytes; SHA-256 is
`9e3eb7d7a2cb4ebdad8c94b0e0f59b25cc40b6d252074926311213630960d793`.
`runtime-manifest.json` records original paths, sizes and hashes. Every archived
member was rehashed against its original. Originals remain under
`/workspace/sightbreak-postgres-receipt-market-r1` and
`/workspace/sightbreak-postgres-receipt-freeze-r2`.

The source-only f5bea861 freeze was rejected before runtime. The independent
falsifiers exposed omitted wrong-route mutation observations and an incomplete
response-to-SQL metadata join. Corrections also added early volume/mount checks,
initial postmaster binding, deadline checks before new work and explicit journal
listener ownership/cleanup. The prelaunch record retains the rejected source
identity, earlier failed controls, one correction-edit SyntaxError and its exact
source, corrected pure outputs and the authorized private editor-import receipt.
The final maintained pure suite passes nine oracle and seventeen guard groups;
the fresh critic additionally passed its eleven independent groups.

Production game/backend/server trees equal accepted base 89393f3. The game tree
`d41b8d07985ff63a221e41dfabb6f90dc2eb13c6` adds only the native test probe; its
bytes are unchanged since the separately authorized pinned private import at
38d78ff. Original B-21 attribution remains in history. No backend balance rule,
strict armory assertion, protocol, prediction, rewind, state privacy or
offline/online boundary changed.

Store and case lost-response settlement remain separate unqualified components.
Rendered player recovery/consent, postmatch UX, remote hosts and power-loss
persistence are also outside this result. The market campaign does not close
whole G3/G7/G16 or the v1 mission. No additional broad aggregate or service run
was performed for this boundary.
