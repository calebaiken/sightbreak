# POST-FREEZE first-round source binding and qualification

This addendum was created **after** the independent neutral verdict's local freeze at `2026-10-19T19:46:36.4321805Z`. It is separate from, and supersedes none of, the original artifacts. The original verdict SHA-256 is `f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa`; the freeze SHA-256 is `cfeaa74dce6172fb222e6a7cbbefadb7383fd9169332dd51fd94865294908e8a`.

## Released identity binding

The user authorized the first key's release after verdicts. Its exact published bytes have SHA-256 `04a96c5d995e755924435b6f48225191f66e6fe0c5832fcc8014db70aecedaf0`. That key, the original measurement records, and the first neutral packet consistently identify:

| Label | Reported role / commit | Reported backend tree |
| --- | --- | --- |
| K | Candidate `4a8e9ea73aa8b286d9f1751b0a6b485479737294` | `4ef756639c2e90037bce79a30e2867aebcc798a7` |
| R | V2 baseline `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | `67027b4fa17674ef067c84401af76eb1524419ac` |

Both original measurement Git blobs are available at `4a7ba36216bf354d266b508222aea4cfea30bfea`, match the key's SHA-256 values, and match their original manifest entries. The entire original headers match the key's withheld headers. Neutral rows preserve every original numeric/string value and JSON token apart from insignificant whitespace; no row/sample was rewritten for publication. The exact packet manifest remains `d9a6ea8e0721d573bea5437e84fcc25b899d7b8172f092c4ae7d1415b3c56c36`.

Candidate Git blobs also match both reported common fingerprints: harness `6e4aac58ad913144e2c41455124afd6756e500c5d795636e15ba52b1aa5a3b19`, fixture `7106ccbbf657058087ed4b717143cdcea760513d8a513432b3445a2131a69eb1`. This binds **reported fingerprints**, not independently observed module execution; the source review's conditional fixture-import provenance gap remains applicable.

## Retained failure: K measured app bytes are not fully bound

The exact reviewed K app blob is `16f33c94da490c77a8ab930b88d8fc0662f3fa4c`, raw SHA-256:

`703c20b298d734395f292d4a8c5e415e55e6f35109e9a51dcb36fbcb62647441`

The measurement/key instead record the app-file SHA-256:

`9f94a55f1b19858eec3ac54036601b5c26a330749454a6cb89650d51e298f020`

Those values differ. The initial raw/uniform-CRLF check **failed**; the separate line-ending receipt's five named constructions produced **no matching construction**. No original measured app byte snapshot is claimed retained here. The cause is not established, and neither clean-worktree flags nor matching commit/tree labels repairs this byte-binding gap. Do not infer identical code from this record alone. This does not itself demonstrate a semantic code difference or invalidate the retained arithmetic; it limits attribution to a fully verified executed source artifact.

For R, raw Git SHA-256 `478440d35840f2a60dad08793b73ec1aa983ce5b5cc2414445cf78f79ea19549` differs from recorded `78816607ee70fe47ae1f1c97f48d4d2a360eebe7c0e64ac73c296dfd53fb8121`, but an explicit LF→CRLF expansion matches the latter. That is qualified transformation evidence, not raw byte equality or execution authentication. Other recorded backend-file worktree fingerprints have not all been individually rebound.

The later qualified receipt leaves the original failed check and every original artifact intact. A future supplied source-preservation receipt could add evidence separately; none was opened or inferred here.

## Permitted conclusion: retained SQL statement count only

All ten samples in each row retain these counts:

| Workload `(trades, items/side)` | K | R |
| --- | ---: | ---: |
| `(0,0)` | 3 | 3 |
| `(1,0)` | 4 | 4 |
| `(1,2)` | 5 | 8 |
| `(10,1)` | 5 | 33 |
| `(40,1)` | 5 | 123 |
| `(40,20)` | 8 | 1643 |
| `(501,0)` | 5 | 504 |

The frozen anonymous preference therefore maps, through the released key and reported headers, to the **reported candidate K's historical statement-count win**: five wins, two ties, no recorded count regression. This is a binding of the original narrow verdict, not a new independent performance verdict, execution reproduction, or broad acceptance.

**Not established:** causal/general/population latency; actual-response body or digest equivalence; authoritative before/after state equality independently recomputed from retained snapshots; source execution authenticity; current shipping runtime/test safety; concurrent-load, unbounded-history, or production acceptance. First-round `response_sha256` values fingerprint expected fixtures, and state hashes are explicitly null/not retained. Reported successful assertions do not fill those missing retained observations.

The completed source critic remains **inspection-only** with controls **UNEXECUTED**. Its two assurance findings and memory/concurrency/dangling-reference limits remain attached. The second-round packet/key and its separate blind review were not inspected. Nothing here claims that later evidence passes, fails, or supersedes this first round.

The freeze is a local UTC/hash record, not a trusted timestamp or signature. The stated post-verdict key-release chronology is user-authorized context, not independently timestamp-authenticated history.
