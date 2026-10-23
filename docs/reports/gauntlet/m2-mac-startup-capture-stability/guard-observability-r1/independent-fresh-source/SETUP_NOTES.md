# Retained inspection setup notes

Before checks, a read-only Git inspection requested
`617b348b:docs/reports/gauntlet/m2-mac-ax-read-only/r3/independent-actual/REPORT.md`.
Git returned `fatal: path ... does not exist in 617b348b`. Listing that exact
report tree identified `ACTUAL_REVIEW.md`, which I then read successfully.
No candidate or evidence bytes changed.

A batched read-only search also named `scripts/test_macos_startup.py` and `rg`
reported it absent. The maintained file is `scripts/test_macos_ordinary_startup.py`;
the declared runner selected it correctly. This inspection typo was not a
candidate test or a missing-fixture result.

Required old screen-identity and OCR fixture directories were selected before
the first maintained replay. Both own exact shallow checkouts materialized their
indexes and sparse files before clean-status checks. No sparse-fixture failure
or native execution occurred in this review. Raw runner logs retain their
original whitespace; `.gitattributes` excludes those raw logs from whitespace
normalization checks.
