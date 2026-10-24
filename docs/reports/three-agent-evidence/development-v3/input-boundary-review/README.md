# Input-boundary review packet

Start with [REPORT.md](REPORT.md) and [POST_FREEZE_ADDENDUM.md](POST_FREEZE_ADDENDUM.md).

- `producer/`: all permitted noncache originals, three attempts and failure snapshots, main neutral freeze.
- `critic-neutral/`: complete unchanged independent component neutral freeze.
- `git-objects/`, `match-rpc-excerpts/`, `SOURCE_BINDING.json`: exact module and restricted source binding.
- `PROBE_ASSERTIONS.json`, `ACTUAL_COMMANDS.json`, `review-audit/`: reproducible offline checks and command/receipt distinctions.
- `ORIGINS.json`, `OMISSIONS.json`: full payload origin index and precise exclusions.
- `SHA256SUMS.txt`, `FROZEN.json`, `FROZEN.sha256`: complete payload ledger and non-self-referential hash chain.

All native receipts are historical and unsigned. No Match/timer/UDP/actor/network victory, PR20 integration or release approval is claimed. Existing neutral verdicts are unmodified. Do not confuse the component key with the separate large-network key.
