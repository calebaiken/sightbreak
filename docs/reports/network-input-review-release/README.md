# Network input freshness: reviewed identity release

This coordination archive publishes the existing key after the independent
[H-wins outcome was frozen](https://github.com/calebaiken/sightbreak/pull/20#issuecomment-6354437453).
It adds no native run or runtime change. PR20's original source, logs and neutral
packet remain at their published commits.

| Neutral sample | Executed source | Shipping runtime |
|---|---|---|
| H | `77f204083ab5bea4dc9149d3179daf540a994de4` | `f3ceaad98e089aa393c7f5fa650a52695094d979` |
| T | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | same frozen V2 source |

The exact original `mapping.json` is 212,748 bytes; SHA256
`1d5b1cbed67c7fb94c2afe72c64b52b44c1b0915720cd0ddbc21151833709709`.
Its historical parent-only instruction records the pre-verdict access rule.
`release-verification.json` independently checks all **316 original counterpart
blobs** against evidence commit `1627a9a0ca2a954fe8f246c42ff2f205c578b5c5`
and all **11 source artifacts** against their recorded Git objects. The source
counterparts use Git bytes; nine recorded working-file digests instead use CRLF.
Converting only line endings reproduces all nine digests. The first release check
incorrectly expected these two representations to be byte-identical; this
distinction was resolved before publication. No unexplained mismatch remains.

## Recorded review scope

This is a parent-recorded summary of the linked independent verdict, not its full
transcript. The reviewer selected H after auditing 55,743 sampled rows, 32 native
pairs, 64 peer logs and 22 focused gate logs. The result supports the measured
stale-input neutralization and peer-liveness correction. The separate
[source review passed](https://github.com/calebaiken/sightbreak/pull/20#issuecomment-6276000222).

- Input neutralization uses simulation time; peer retirement uses wall time.
- The fixed snapshot-gap window measures horizontal motion, not complete 3D rest.
- Four reported live-peer structures empty after retirement; actor ACK and
  simulation timestamps are not claimed erased.
- Delivered datagrams are not asserted identical across the two native runs.
- The 120-command history-cap stall remains; default prediction and live rewind
  remain off. The optional individual queued-to-ACK trace was interrupted and
  adds no result. Its unpublished work remains isolated.

Original [neutral packet and verification instructions](https://github.com/calebaiken/sightbreak/tree/0cbc3ae7a9a017aa179eaeff61cf902629de1c0d/docs/reports/network-input-freshness-v3/blind)
retain ZIP SHA256 `8fb111324051b4bfc590a216ab09c107ef0c10605f755b7e481757d125172112`
and manifest SHA256 `fe83c4bdcc1ea662f034ff4ebc340a4e115ed27e8a7d404a2aa80175d84146ce`.
See the [source-bound report and reproduction](https://github.com/calebaiken/sightbreak/blob/0cbc3ae7a9a017aa179eaeff61cf902629de1c0d/docs/reports/NETWORK_INPUT_FRESHNESS_V3.md).

A new docs-only worktree checkout ran out of memory before this publication.
Git removed the failed checkout and administrative directory; the unused local
branch still points to `0cbc3ae7`. Contrary to the initial progress comment, an
incomplete checkout is not retained. The existing coordination checkout publishes
this archive. That infrastructure failure supplies no measurement evidence.
