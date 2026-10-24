# Independent r6 review record

Recorded after a separate read-only reviewer returned its verdict, before revealing
the M/Q mapping. This is the parent agent's faithful decision record, not a new run.
The reviewer inspected only the neutral packet, no runtime source or mapping.

**Verdict: M wins, bounded to the supplied process-kill fixture.**

- M recovered27/27; Q0/27. The reviewer cross-checked raw native output, journals,
  timeline request bodies, HTTP status and SQLite contents rather than accepting totals.
- Manifest pin `777bf43a502bcb09992b4fc8ac8b43ff5eb59a9df55b136d3567aa7c3753b909`;
 309/309 listed files match, no extras besides the manifest.
- All54 ledgers pass read-only immutable SQLite integrity checks, with hashes unchanged.
- Three repeats × three routes × three boundaries;27distinct paired receipt IDs,
  matching parsed original bodies, original market price10,000,000 and fee300,000.
- 54 matching original-process kill acknowledgments; 72 recovery processes exited 0;
  wall and monotonic timestamps strictly increase. No captured native/import errors.
- M has27original journals, no declared fixture token/Bearer/auth fields, exact parsed
  receipt/payload replay and matching stored/native results. Each M case has one
  fixture mutation-cost row. Q's before-commit cases lose intent without a mutation;
  its other18 commit once but lose recovery.
- All9M late cases independently prove409rejection < release < original commit.
  The rejected attempt has `_uncertain:false`; `pending:true` preserves the earlier
  unresolved intent. These are different assertions.

## Corrections and strongest remaining challenge

Q's r6 `late_order_verified:true` overstates its exercised chain: no retry or409exists.
It proves only release < original commit. r7 separates these fields and uses null
for the unexercised chain. SQLite `requests` is not all inbound traffic: M has63
timeline requests but45stored request rows; Q27versus18. Rejected/dropped requests
must be audited from timelines/HTTP records.

The strongest falsifier was to **force-kill the recovery process after its observed409,
before normal teardown**, then release the original and recover in a third process.
Every r6 recovery exited normally. r7 implements that falsifier and captures journal
bytes at the second kill and final disk state; its verdict is separately recorded.

## Limits retained

- r6 disk cleanup is a driver summary, supported by native `pending:false`; it lacks
  an independent post-recovery disk snapshot. r7 adds explicit snapshots.
- Exactness is parsed JSON values, identifiers and routes, not raw wire bytes or an
  independent record of human consent.
- Fixture cost rows are not PostgreSQL wallet, seller, inventory or fee-account ledgers.
- Fixed business inputs and item identity are narrow schedule coverage.
- Clean Git fields and hashes are retained provenance assertions, not signed execution
  attestations. Credential checks cover captured journals only.
- Neither this review nor native process kills establish host power-loss durability.

After verdict: M maps to candidate7b6f379, Q to frozen701ce2c. The source critic's
separate PASS concerns the bounded implementation after two correction loops; Sol's
integration and independent QA remains a distinct required handoff.
