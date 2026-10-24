# First-round backend evidence — bounded publication

This is an **append-only publication**, not a new measurement or implementation approval. The first independent neutral verdict and its freeze are copied byte-for-byte under `verdict/`; the original anonymous input is under `packet/`. The now-released **first** key is under `released-key/`. The second-round packet/key was not inspected.

## Verified ledger

| Evidence | Published location | Status |
| --- | --- | --- |
| First independent verdict | `verdict/NEUTRAL_VERDICT.md` | Exact supplied SHA-256 `f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa` |
| Original freeze | `verdict/FROZEN.json` | Exact SHA-256 `cfeaa74dce6172fb222e6a7cbbefadb7383fd9169332dd51fd94865294908e8a`; local freeze UTC `2026-10-19T19:46:36.4321805Z` |
| First packet manifest | `packet/SHA256SUMS.txt` | Exact SHA-256 `d9a6ea8e0721d573bea5437e84fcc25b899d7b8172f092c4ae7d1415b3c56c36`; all covered files verify |
| Released first key | `released-key/mapping.json` | Exact SHA-256 `04a96c5d995e755924435b6f48225191f66e6fe0c5832fcc8014db70aecedaf0` |
| Original K measurement | `original-measurements/K-measurement.json` | Exact Git blob `2c69520474ffd52c73fff5288cd0ca0baae68180` from evidence commit `4a7ba36216bf354d266b508222aea4cfea30bfea`; SHA-256 `93d25da3b5c74a2c997a038f05556431c353c2cbdd5b675a1bc5a89473761b94` |
| Original R measurement | `original-measurements/R-measurement.json` | Exact Git blob `055d27e4dcdbc94f2630afeea85311ae59b52890` from that evidence commit; SHA-256 `dbe47d0a3d1dd5567344c37283e59570cfed01a3edb68f40b24d411b23ab4f93` |
| Original evidence manifest | `original-measurements/source-SHA256SUMS.txt` | Exact Git blob `c3092586ae4b2966efe348694126457ac5a8b085`; SHA-256 `4d5bd6158360cb2fcaf39c0c9531b795e7f48606dcc6a926855d9b3419944935` |
| Source critic evidence | `../source-review/original/` | All 17 completed evidence files copied exactly; **controls remain UNEXECUTED** |

The released key binds **K → reported candidate `4a8e9ea73aa8b286d9f1751b0a6b485479737294`**, **R → reported V2 baseline `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`**. Original measurement headers match the key, and all seven rows per label preserve the original JSON tokens except insignificant whitespace: **14 workload records / 140 retained timed samples**. Reported backend tree identities and the common harness/fixture Git fingerprints verify. These are file/provenance checks, not authentication of historical execution.

## Important unresolved source-byte binding

`binding/BINDING_VALIDATION.json` retains **165 passing checks and one failed check**. K's recorded measured `backend/app.py` fingerprint (`9f94a55f…`) does **not** equal the pinned Git blob fingerprint (`703c20b2…`). Neither a whole-file line-ending conversion nor the additional explicitly recorded constructions explains it. `binding/LINE_ENDING_QUALIFICATION.json` retains every negative result. **Do not present this as a complete measured-app byte match.**

R's app fingerprint matches an explicit LF→CRLF expansion, not raw Git bytes. The inspection source objects match the completed source review. The full recorded backend worktree fingerprint inventory is retained, not individually revalidated. Current shipping source safety remains **inspection-only**, not runtime/test or production certification.

## Read the qualification, not just the winner

`binding/POST_FREEZE_ADDENDUM.md` formally binds the released identities after the original freeze. It permits only the historical retained **SQL statement-count** preference for K: five wins, two ties, no recorded count regression. It does **not** establish general latency, independently retained response/state equivalence, or production acceptance. The first packet lacks actual response bodies/digests and authoritative before/after snapshots/hashes. A second-round review elsewhere is neither imported nor anticipated here.

No old verdict, freeze, input, review, or failure record is superseded or edited. The later `binding/QUALIFIED_RECEIPT.json` adds qualifications; it does not replace the original artifacts or turn the failed check into success.

## Publication mechanics

- `COPY_LEDGER.json` gives exact-byte copy origins, lengths, and SHA-256 values.
- `OMISSIONS_AND_REFERENCES.json` lists local-only/Git originals, deliberately uninspected owner payloads, and missing first-round evidence.
- `raw/collect-commands.json` records every read-only Git invocation, return code, and stdout/stderr hash and length. Raw files, including empty stderr logs, are retained and unignored. A successful binding requires explicit expected output, never merely empty stdout.
- `publish_evidence.py collect` and `binding/qualify_app_bytes.py` performed file/JSON/hash arithmetic only. After restart, `binding/finalize_qualification.py` rechecks retained bytes before sealing. **No retained verifier, audit, freeze, source collector, or assurance-control script was rerun.**
- `publish_evidence.py seal` checks nested attributes/visibility and creates `PUBLICATION_RECEIPT.json` plus complete manifests. Nested `.gitattributes` disables text/filter/ident/encoding transformations; nested `.gitignore` keeps raw logs visible.
- Each `PUBLISHED_SHA256SUMS.txt` covers every file recursively in its own directory except itself. The returned manifest hashes are the outer anchors; there is no self-hash claim.

The approved CPython 3.13 interpreter was used only for publication validation. The measurements record Python 3.12.14. This does not rerun or upgrade them, nor retroactively change the completed review's historical interpreter limitation. No application/native/DB/service/test/network/export execution, index edit, commit, or GitHub operation was performed.
