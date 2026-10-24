# Independent PostgreSQL recovery source binding

The independent critic's post-freeze verdict is **PASS for the bounded source and
artifact binding**. Its earlier blind outcome remains unchanged at
SHA256 `750bfb02e65f3f348567b8bf453b4387f931c70549d7c50469d377fc63bec2ee`.
[Outcome freeze](https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6355013968)
preceded controller/source access;
[source-binding verdict](https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6382123531)
records the subsequent acceptance. This README is a parent summary; the critic's
own completion record and audit files are copied byte-for-byte alongside it.

| Neutral label | Verified shipping source | Outcome |
|---|---|---|
| Set-673EECBC | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | 0/3 exact recoveries |
| Set-8F5F7604 | `7b6f379a3f8c809d0985a64e883cbadfdd78d135` | 3/3 exact recoveries |

The exact existing `controller/mapping.json` retains committed pin
`70a6936e0ebca5b38559fe013d18b0174cf1689bd6fb85788b059b613c70b2bd`.
The controller's frozen-source copies, packaging program, ancillary records and
pins are retained without modification. The original neutral packet and all 237
raw-evidence publication hashes remain unchanged.

## What the independent audit established

- All 114 observation bindings: 84 unchanged and 30 path-neutralized; all 132
  replacements replay exactly. All 30 SQL-stage files are byte-identical.
- Complete 299/307-entry measured source archives and frozen `31438cbc`
  harness/probe agree with their recorded digests. Archive-versus-Git differences
  in 278/286 files are entirely LF-to-CRLF conversion.
- Recovery supplies no fixture payload to the production UI. Startup loads the
  journal; ownership claim rereads it; dispatch uses that pending receipt's path,
  payload, method and message. The inspected real HTTP, PostgreSQL, authentication
  and withheld-response paths agree with the retained observations.
- The original probe's unconditional fixture-price normalization is a redundant
  driver dependency. A minimal-config experiment must move it into send mode;
  failing at that normalization would not disprove production recovery.

The critic found no remaining source-dataflow or transformation blocker. The
already-requested minimal-input control is additional empirical corroboration,
not a prerequisite for acceptance of these three observed postcommit cases.

## Limits and records

The 62-entry cache manifests are bound, but historical cache payloads were not
retained. Historical machine execution, source-cleanliness observations and the
launcher-to-worker process lineage are not independently attested. No new native,
application or database test was run by this source audit. Its scope does not add
power-loss, arbitrary-instruction-window or manual-UI qualification.

`provenance-audit.json` preserves the earlier direct-Git-byte mismatches;
`source-binding-completion.json` resolves them using the measured archives and
newline accounting. The audit scripts retain their captured local paths and are
inspection artifacts, not a portable one-command test suite. `sha256.json` covers
the 21 copied audit/controller files, and scoped `-text` preserves their bytes.
