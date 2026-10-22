# Independent pure-validator and archive followup

Accept the corrected pure validator at `b38508e` and the final committed archive
at `6a4a955`. This follows the original bounded acceptance `93f6b68`; it adds no
native execution or broader release qualification. The complete game execution
remains source `471fbd8`.

The first post-run helper, `0aae3f8`, tied payload winners, objectives, activity,
bot flags and combat statistics to observations. All 14 standard-Python controls
and the frozen raw replay passed independently. An independent synthetic boundary
then found a false rejection: production exports the minimum of integer terminal
duration and integer activity, while the helper used integer activity alone.
The retained counterexample has terminal duration `519.9999999999999`, activity
`520.0000000000001`, and the valid exported value 519.

Correction `b38508e` reconstructs terminal duration from the emitted summary,
applies the production cap, and confines adjacent-floor ambiguity to 0.1
microseconds around an integer. All 15 maintained controls pass under standard
Python. The independent boundary now passes; swapped winners preserving five
wins, swapped objectives preserving six contributions, a bot flag and a combat
contradiction all reject. Both strengthened validators accept the archived
`471fbd8` completion and earned payload. No product gameplay, backend or result
worker file changed. The `validate.sh` registration parses successfully; a full
suite rerun is not claimed here.

Archive inspection independently verifies:

- All 58 indexed files match `round-1/sha256.txt`; the directory has exactly those
  files plus the manifest, and each byte matches its committed Git blob.
- All 50 archived native build outputs exactly match the original completed run.
- Four driver/preflight logs exactly match their separate original files.
- Four post-run pure-validation receipts are correctly identified as later
  archive-only receipts rather than native run outputs.
- All 56 files from the first archive at `da42281` remain byte-identical; only
  two correction receipts and their manifest entries were added.
- The only omitted original runtime control files are the empty stop marker and
  SQLite lock; no observed result, checkpoint, report or child log is missing.
- The independent complete settlement recomputation passes again using the
  committed archive, with the same payload hash, account identities, activity,
  score progression, SQL settlement and recovery states as the original review.

The native manifest SHA-256 is
`b7e0ffbaead95e82a7c7c2d5d7bd994dee80558ed15af408f2cde1af6fa7d0c8`.
Its engine-check log retains its original trailing blank line; preserving that
raw byte is intentional. Source diffs and shell syntax checks pass.

Receipts and reproducible review scripts are under `followup/`. The original
participation, AFK resistance, headless, loopback traffic, wildcard game binding,
impairment, deployed-launcher and power-loss limits remain unchanged. G3/G16 stay
in progress. This followup launched no Godot, container or backend process.
