# PR19: direct batch-bound and imported-fixture assurance

This follow-up closes the two assurance findings in
[Sol's frozen-source review](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6275997901):
an upper query-count budget alone did not enforce 500-ID batches, and the
benchmark recorded the harness-root fixture hash rather than the module actually
imported. Sol found no introduced runtime defect in the scoped optimization.
Its synthetic control programs were **not executed** and are not counted here.

## Runtime, tests, harness and evidence are distinct

| Component | Frozen identity |
| --- | --- |
| Shipping runtime reference | `4a8e9ea73aa8b286d9f1751b0a6b485479737294` |
| Test assertion + measurement provenance change | `8dc8e3715dcaeb99fe6e3544243ee591d68c337b` |
| Final control-runner freeze, before completed execution | `3e7ce7409322766d07afe504d97f47c5b3614875` |
| Current backend tree, **including changed test file** | `1dfac444b684ca1a791540e5831fc7d88538abed` |
| Executed `backend/app.py` working-byte SHA256, unchanged | `9f94a55f1b19858eec3ac54036601b5c26a330749454a6cb89650d51e298f020` |
| Test/fixture file SHA256 | `5eb5d4a45484b26514edddf214e8ae81e7ab9186f262857fe64845abe215e595` |
| Benchmark SHA256 | `099457e84deffa2fc0400d9be4bddc0f6b2d519d51559238ece94fd590b64a72` |
| Final control-runner SHA256 | `bd6cc8d62ef5b6c114866583954fa7ba5c8a453020dc13a871385eea454880ce` |

The shipping backend, excluding `backend/tests`, still matches `4a8e9ea` in Git
and its recorded working-file bytes match the preceding retention round. The
only backend change is `backend/tests/test_trade_reads.py`. The complete backend
tree therefore differs from the original runtime/test tree; it is not described
as byte-identical including tests. The original economy test file is unchanged.

`fixture_id`, `seed_workload`, `canonical_trades` and `database_snapshot` have
identical ASTs to the original fixture. The new fixture-file hash reflects test
assertions/recorded properties, not changed workload generation.
[Source preservation](backend-trade-read-v3/assurance-r3/source-preservation.json)
and [executed source/Git-byte bindings](backend-trade-read-v3/assurance-r3/source-files.json)
retain these checks. Exact executed test/harness/control bytes are also archived.

## Finding 1: executed direct-bound negative control

The existing parameterized test now records the number of bound parameters for
each executed SQL statement and asserts every count is at most **500**. The
query-count ceiling and full response assertion remain. Only parameter counts,
not bound values or bearer headers, enter the JUnit properties.

The completed run used Python **3.12.14** and real PostgreSQL **17.11**, executing
only the two existing boundary nodes. A separate scratch copy of the exact
working backend bytes then changed all four constants in `trades`: both item
and participant loop steps and slices, **500 → 5000**. Candidate runtime files
were never mutated. The retained [patch](backend-trade-read-v3/assurance-r3/attempt-2/batch-5000.patch),
[mutant file](backend-trade-read-v3/assurance-r3/attempt-2/batch-5000-app.py.txt),
[mutation identity](backend-trade-read-v3/assurance-r3/attempt-2/mutation.json)
and [materialization receipt](backend-trade-read-v3/assurance-r3/attempt-2/materialization.json)
make the control independently reconstructable.

| Case | Runtime | Queries / old ceiling | Largest bound count | New bound result |
| --- | --- | ---: | ---: | --- |
| 40 trades × 20 items/side | Shipping | 8 / 8 | 500 | PASS |
| 501 trades, empty offers | Shipping | 5 / 5 | 500 | PASS |
| 40 trades × 20 items/side | Isolated 5000 mutant | 5 / 8 | **1,600** | Expected FAIL |
| 501 trades, empty offers | Isolated 5000 mutant | 4 / 5 | **502** | Expected FAIL |

Thus the executed mutant passes the old ceiling while failing the new direct
bound. The two failures occur specifically at `assert all(size <= 500 ...)`,
after payload equality and query-budget assertions have passed.

- [Shipping run](backend-trade-read-v3/assurance-r3/attempt-2/candidate/pytest.log):
  **2 passed**, exit 0, 3.60 s.
- [Mutant run](backend-trade-read-v3/assurance-r3/attempt-2/batch-5000/pytest.log):
  **2 expected failures**, exit 1, 3.85 s.
- [Machine-readable counts](backend-trade-read-v3/assurance-r3/attempt-2/bound-results.json),
  both JUnit XML files and exact command/database receipts are retained.

These two nodes are the new targeted validation. The historical **61/74** suite
results keep their original source/test binding; neither full suite nor the
seven-workload benchmark was rerun for this follow-up.

## Finding 2: actual imported module provenance

The benchmark now inspects the imported `test_trade_reads` module itself and
records `imported_fixture` with its actual `__file__`, resolved path, SHA256 and
expected harness-root SHA256. A byte mismatch raises `Imported fixture byte
mismatch` before fixture setup or measured requests. `final_imported_fixture`
repeats the check after measurement, and identity must remain unchanged.

The runtime-reference check now compares shipping backend files excluding tests,
while still recording the complete backend tree, individual backend file hashes,
test/fixture hash and harness commit/hash. This allows a test-only assurance
change to remain bound to shipping runtime `4a8e9ea`.

Executed import-only controls call the same identity function used by the
measurement path, with the benchmark's source-first import precedence:

- The actual current module is accepted with SHA256 `5eb5d4a4...` and its full
  `__file__` retained.
- A separately copied source fixture with an appended comment shadows the
  harness-root fixture and is **rejected**, exit 1. Its actual hash is
  `a2d93bdeed15293bf2541fdddeed3ccacf6e038994156ac6842112ba5a586206`,
  rather than the expected `5eb5d4a4...`.
- A connection-denial hook records **zero database connect calls** for these
  probes. They do not execute measured requests. This validates the import
  provenance gate without claiming a new benchmark run containing those fields.

[All import commands/results](backend-trade-read-v3/assurance-r3/attempt-2/fixture-probes.json),
stdout identities and stderr are retained.

### Original pinned pairs: explicit post-hoc corroboration

Four fresh-process imports reconstructed the original search paths using the
pinned source and harness commits. Every actual imported fixture byte hash
matches the original reported value:

```text
7106ccbbf657058087ed4b717143cdcea760513d8a513432b3445a2131a69eb1
```

| Original round/source | Source commit | Fixture resolution in replay |
| --- | --- | --- |
| First / V2 | `701ce2c` | No source fixture; fallback to harness `4a8e9ea` |
| First / candidate | `4a8e9ea` | Source fixture |
| Retention / V2 | `701ce2c` | No source fixture; fallback to harness `8070436` |
| Retention / candidate | `8070436` | Source fixture |

The original candidate records already captured their source fixture file hash,
which also matches the reported harness-root hash; the original V2 source tree
contains no `test_trade_reads.py`. The
[historical binding receipt](backend-trade-read-v3/assurance-r3/historical-fixture-binding.json)
binds these observations to the original measurement-file hashes and replayed
`__file__` paths. **This is post-hoc source/import reconstruction, not an original
execution-time module-path capture.** No pinned-pair mismatch is established.

### Retained failed attempt and byte handling

The first control attempt, frozen at `8dc8e37`, completed the two shipping passes,
two expected mutant failures and current positive/mismatch import controls. Its
first historical replay then correctly rejected a hash mismatch and stopped.
The remaining historical probes did not execute in that attempt.

Cause: `git archive` on this Windows host applied CRLF conversion. The exported
fixture hashed to `b8019a17b37e78b9109184bc7b59c844b77598484e402ae38f887c50f270d9e3`,
whereas the original retained fixture and unfiltered Git blob use LF and hash to
`7106ccbb...`. LF-to-CRLF conversion exactly reproduces the rejected hash. This
was a reconstruction error, not a newly observed mismatch in the original runs.

The corrected runner was frozen at `3e7ce74` before the completed narrow run. It
uses exact working bytes for current mutation copies and unfiltered `git cat-file`
blobs for historical replay. Per-file blob IDs and materialized hashes are
retained. Both attempts, including the failed replay/overall exit 1 and later
successful completion, remain in the [raw archive](backend-trade-read-v3/assurance-r3/).
Earlier repeated controls are not counted as additional coverage.

## Evidence, reproduction and key disposition

Archive: `docs/reports/backend-trade-read-v3/assurance-r3/` — **56 files including
the manifest**. SHA256 of its `SHA256SUMS.txt`:

```text
38a72cbab4948e9144040626c3793e6310e74d0d73758ab8c83b6e18867c4f8c
```

Original external completed receipts:

```text
C:\Users\blith\AppData\Local\Temp\opencode\trade-assurance-r3-4e16a7a9422e
```

The earlier failed attempt remains at `trade-assurance-r3-af9b53fc8cb4` under the
same Temp/opencode root. Both attempts' raw files were copied without rewriting
bytes. Existing evidence attributes preserve raw line endings; Windows Git
operations use command-scoped `core.longpaths=true`, and whitespace checks allow
the retained CR-at-EOL bytes.

To reproduce, use an isolated checkout of `3e7ce7409322766d07afe504d97f47c5b3614875`
with the established Python 3.12 environment and `SIGHTBREAK_TEST_ADMIN_URL` for
the existing loopback PostgreSQL service, then run:

```powershell
& 'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-backend-trade-env\venv312\Scripts\python.exe' -B scripts/check_trade_read_assurance.py --out "C:\Users\blith\AppData\Local\Temp\opencode\trade-assurance-repro-$([guid]::NewGuid().ToString('N'))"
```

For exact LF test/harness/control bytes, create that checkout with
`git -c core.autocrlf=false worktree add --detach <new-path> <freeze-commit>`.
Runtime checkout line-ending variants are explicitly recorded in per-file hashes;
the mutation copy always preserves its current source's exact working bytes.
The runner requires committed code, checks the shipping-runtime reference,
creates only unique `*_test` databases and drops each one in `finally`.

All four databases from the two retained attempts were dropped. PG55439 was left
running for the separate receipt worker; no server lifecycle/configuration work
was performed.

At the subsequent post-restart publication check, the read-only command
`pg_isready -h 127.0.0.1 -p 55439 -U sightbreak -d postgres` returned
**no response**. The completed controls predate that restart; their receipts
remain valid. No test was repeated or database/process changed for publication.

The **first K/R key was formally released** on
[PR19](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6276165709) and
[PR17](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6276165701),
after the frozen first-round verdicts:

```text
C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-read-key-4916805315cb\mapping.json
SHA256: 04a96c5d995e755924435b6f48225191f66e6fe0c5832fcc8014db70aecedaf0
```

**K binds to runtime `4a8e9ea`; R binds to V2 `701ce2c`.** Labelled evidence is
commit `4a7ba36216bf354d266b508222aea4cfea30bfea`, and the first neutral archive is
`ebe4646ebc25a2139f05fca035b327360f5371f4`. The
[formal release receipt](backend-trade-read-v3/assurance-r3/first-key-release.json)
includes complete commit and raw/neutral hash bindings.

The main second-round critic's frozen conclusions are now archived as the exact
[parent-recorded verdict](backend-trade-read-v3/critic-r2-parent/verdict.md), tied to
[PR19 comment 6276215829](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6276215829).
This is a **condensed parent record, not the full critic transcript**. Its verified
SHA256 is `792386bec81aa0de13cdeb70a95ac89a79bbcfb251b662a704c673a03653c10d`.
It records **ACCEPT WITH QUALIFICATIONS: V wins query count; captured safety is
PASS/tie**. It does not evaluate source/monetary-contract safety or waive these
separate assurance findings. The exact source bytes, copy receipt and a separate
manifest are retained; this publication did not conduct a new critique.

**The second M/V key is released.** The parent verified
[Sol's second frozen verdict](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354432171)
and the main critic's frozen parent record before the
[release handoff](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354506652).
The [exact existing key and Sol freeze anchors](backend-trade-read-v3/identity-release-r2/)
are now archived byte-for-byte. Key SHA256:
`28f0de31229e531e7164ce3905ae88cedcbd07ce89e62f046983000ebdecf93a`.
**M executed `701ce2c`; V executed checkout `8070436`, with shipping runtime
reference `4a8e9ea`.** Both used enhanced harness `8070436`; the later assurance
test/harness/control commits listed above are a separate follow-up.

The archived Sol anchors are attributed to Sol: `FROZEN.json` SHA256
`185d7b4cd1dacde52d8d9cc48bc35b43fde9b1453ef98a362d798e9bb9ab0f9e` and verdict SHA256
`1248f66b7b80e2acbf69595ef084b164957547497f7c40c2e56c4489847fcf3e`.
Historical withholding fields in the earlier frozen receipts remain unchanged;
this release record supersedes them as current handoff status. Both original neutral
packets and both raw measurement rounds still match their prior manifests; this
follow-up neither rewrites them nor changes their expected-versus-actual response
hash qualifications. No new critic was spawned or polled.

PR19 remains draft. Unpaginated whole-history allocation, large-database plans,
peak memory, concurrency and inherited READ COMMITTED/dangling-reference limits
retain their prior scope; this follow-up adds no API or production performance
claim.
