# Retained audit attempts

These are Python read-only evidence reconstructions on CPU 4. No game/native run
was repeated or changed.

1. `audit-attempt-1.json` was generated from the official selected receipts.
   Its objective currency block encountered `KeyError: attack_score` /
   `KeyError: defend_score`: notifications and consumed-input events have slim
   schemas. The error is retained in each scenario's facts. Earlier satisfied-row
   totals therefore omitted the currency row and were incomplete. They are not
   qualification results.
2. The auditor was corrected to select full raw snapshots containing both score
   fields before and after the objective transition. It also records the six
   actual OpenGL-to-ANGLE warnings and separates the original error/leak regex
   from the preregistered zero-warning failure. `audit-attempt-2.json` retains the
   corrected currency reconstruction and each warning failure.
3. `audit-final.json` adds explicit source/manifest/hash-receipt agreement,
   controller/raw summary equality, and final original/reopened completion-status
   checks. It reports plant 26 / defuse 25 / full-match 25 satisfied enumerated rows,
   plus one unsatisfied zero-warning row per scenario and no unavailable rows.
4. Twelve original PNGs were inspected directly. Their byte hashes and observations
   are retained in `visual-observations.json`; thirty official selected/full-copy
   comparisons are retained in `official-copy-comparison.json`.

The preparation method reviewer had already ended. A proposed additional actual
cross-check agent could not start because the team thread limit was reached.
No additional independent actual subcritic is claimed. The parent performs its
separate final review and overall qualification.
