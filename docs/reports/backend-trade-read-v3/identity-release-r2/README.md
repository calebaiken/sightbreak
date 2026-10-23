# Released second-round identity key

**The M/V identity key is released.** This archive completes the disclosure
already authorized in [PR19 comment 6354506652](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354506652),
after both second-round verdicts were frozen and the parent verified their
anchors before key access. It does not change either verdict or the neutral
packet.

`mapping.json` is an **exact-byte copy of the existing key**, not a regenerated
mapping. Its original `controller_only` and withholding instructions are retained
as historical metadata; the release status is documented here and in the linked
handoff. The scoped `.gitattributes` disables text conversion for the three
copied source artifacts.

## Executed source versus shipping runtime

| Label | Executed checkout | Shipping runtime reference | Backend tree at measurement |
| --- | --- | --- | --- |
| **M** | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | `67027b4fa17674ef067c84401af76eb1524419ac` |
| **V** | `8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf` | `4a8e9ea73aa8b286d9f1751b0a6b485479737294` | `4ef756639c2e90037bce79a30e2867aebcc798a7` |

Both used enhanced benchmark harness commit
`8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf`, with benchmark SHA256
`416cc212d3200b9351036b7ec205a5bb488748f19c09d7ea0ef1edc24d683dbd`.
V's executed checkout is therefore **8070436**, with shipping runtime **4a8e9ea**.
The later assurance harness/tests and their evidence are separately identified in
the [assurance report](../../BACKEND_TRADE_READ_ASSURANCE_R3.md).

## Exact key and freeze anchors

| Artifact | SHA256 |
| --- | --- |
| [Existing second key](mapping.json) | `28f0de31229e531e7164ce3905ae88cedcbd07ce89e62f046983000ebdecf93a` |
| [Sol's `FROZEN.json`](sol/FROZEN.json) | `185d7b4cd1dacde52d8d9cc48bc35b43fde9b1453ef98a362d798e9bb9ab0f9e` |
| [Sol's second-round verdict](sol/NEUTRAL_RETENTION_VERDICT.md) | `1248f66b7b80e2acbf69595ef084b164957547497f7c40c2e56c4489847fcf3e` |
| [Main critic's condensed parent record](../critic-r2-parent/verdict.md) | `792386bec81aa0de13cdeb70a95ac89a79bbcfb251b662a704c673a03653c10d` |

The Sol files are **Sol's frozen review artifacts**, copied unchanged. These are
the two selected freeze anchors; `FROZEN.json` also references supporting files
in the original Sol audit directory. The main critic artifact remains explicitly
a parent-recorded condensation, not a full transcript. Archive preparation is
by the PR19 owner and adds no new critic verdict.

- [Main second-round freeze](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6276215829).
- [Sol second-round freeze](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354432171).
  Its saved `frozen_utc` is `2026-10-23T00:26:09.129364+00:00`.
- [Parent's completed verification and release](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354506652),
  published at `2026-10-23T00:35:46Z`.

The source paths, exact copied hashes, raw-to-neutral measurement bindings and
release anchors are in `release-receipt.json`. `SHA256SUMS.txt` covers every other
file in this archive, including these instructions and scoped attributes.

## Acceptance boundary

Both blind reviews accept the narrow retained successful GET slice with
qualifications and prefer V for query work. Identity release does not extend that
result to general latency, monetary contracts, concurrent load, peak memory or
unpaginated-history scalability. The source-assurance controls remain the
separate completed artifacts at `172c900795c04f9b8706c4e80d72f55927f40da1`, available
for read-only independent review. **PR19 stays draft pending Sol integration.**
