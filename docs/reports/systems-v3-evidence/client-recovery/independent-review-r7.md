# Independent r7 review record

Parent-recorded decision from the same separate critic's follow-up, using only the
new neutral L/P packet and no source/mapping/outside files. Mapping was revealed
after verdict: P is candidate `e0cd1e4` (runtime `7b6f379`), L is frozen `701ce2c`.

**Verdict: P wins over L. The post-409/pre-teardown force-kill falsifier passes 9/9;
L recovers 0/9. The bounded r6 win remains a separate result.**

- 174/174 manifest files verify against pin
  `701835eba5fd116849bb6eeda48444bd23cfa4f350161fe04cadda45225d6f4b`;
 175files with manifest, no missing/extra entries, unchanged after inspection.
- 18/18 SQLite ledgers pass read-only immutable integrity checks. Each has one
  original receipt and one fixture mutation. Paired bodies, distinct receipt IDs,
  costs and stored responses agree.
- Each arm has 9 original and 9 recovery force-kill acknowledgments. Every case has
  three distinct PIDs; killed processes return1, final process0. P observes9retry409s;
  L observes none and correctly records `late_order_verified:null`.
- For all 9 P cases, both clocks establish 409 → observed pending result → kill request
  → kill acknowledgment → journal capture → original release → original commit
  → third-process replay. The second kill is acknowledged20.33–24.11ms after the
  logged result, inside the probe's declared60second hold without UI teardown.
- P's 9 post-second-kill journals decode byte-identically to first-kill captures and
  raw journal files, with embedded hashes verified. Receipt, route, case/key and
  expected-price consent are unchanged; no fixture credential/Bearer/auth fields.
- All 9 P final native results equal stored results as parsed JSON. Store/case cost 100,
  market10,000,000 with response fee300,000; each arm totals30,000,600fixture cost
  units with no duplicate effect. L's original commits without recovery.
- All 54 timestamped disk-state captures were checked. P's final 9 explicitly record
  absence after the final process completes. No timeouts/native/import errors found.

## Remaining boundary

The proposed falsifier is satisfied. Interruption during initial journal creation,
replacement or successful clearing remains untested: r7 kills at a stable
post-response hold, and the final process completes normally. This is not an
arbitrary-instruction, host-power-loss or PostgreSQL qualification.

Earlier uncertainty is represented by the retained original pending intent;
the rejected request still has `_uncertain:false`. Parsed-JSON request/result
equality and byte-identical journals are distinct claims. Human consent and raw
HTTP bytes are not separately captured. Fixture costs are not audited wallets.
Hashes establish packet consistency, not signed execution provenance; pre-teardown
lifetime relies on the declared probe protocol. Coverage is nine fixed-input schedules.
