# Retained reviewer setup corrections

R1 used the pure auditors ported from independent a089 review f314385, with
source/run identities and the preregistered strict StringName patterns changed.
The base port and orchestration are recoverable at critic checkpoint `cc790a9`.
All R1 commands, outputs and incomplete JSON are retained in `audit-r1`.

- `audit_phase_captures.py` assumed an `offline_training.json` save existed.
  This earlier route failure never reaches settings persistence. The auditor
  raises `StopIteration` before evaluating even the reached 06c bracket.
- `verify_receipts.py` assumed a success-only `authority` result existed in
  every input schedule. The failed legacy diagnostic omits it. Its per-operation
  guard records `verification_incomplete: KeyError('authority')`, which then
  causes the completeness auditor's list comprehension to raise `TypeError`.
- The old seven-path Windows CRLF expectation omitted four newly tracked
  Linux/Mac fixture files. The native source hash initially disagrees with this
  reviewer expectation, while the source itself reports clean exact e28c8e9.

R2 preserves missing disk state as unavailable and evaluates the reached 06c
bracket independently. The failed diagnostic's absent summary now yields a
false comparison; the complete failed result and later raw summary remain intact.
All three schedules remain enumerated, with two passing and legacy failing.
The eleven-path CRLF set is derived from frozen tracked files and `.gitattributes`:
the four added non-LF-pinned paths are the Linux `.gd` / `.tscn` fixture and Mac
reference JSON / `.swift.txt` fixture. Applying only those declared conversions
reproduces the exact native validation digest. The missing success-only journey
controller digest still yields false, without a fabricated mismatch value.

No candidate or native byte changed. `audit-r2/runtime-completeness.json` remains
false and its command deliberately exits 1. Its seven failed completeness
predicates preserve the failed journey, settings transaction, third input
schedule, absent controller digest, unreached OCR/LEAVE, missing second phase
bracket and missing reopened-process observations. The route and legacy failure
reconstructions independently validate the reasons without promoting either
qualification. `auditor-final-inventory.json` records the final reviewer source
hashes; the original port hashes stay in `auditor-port-provenance.json`.

Two local inspection commands also failed during review: an immediate summary
read attempted the R1 completeness JSON that the TypeError prevented from being
written (`FileNotFoundError`), and `rg .gitattributes` returned 2 because that root
file was omitted from the critic's sparse checkout. Reading the exact frozen Git
blob supplied the attributes without changing the checkout or native evidence.

Reproduce the complete pure audit after safe extraction into fresh directories:

```sh
python3 run_audits.py /absolute/path/to/inner-receipts /absolute/path/to/full-QA \
  --output /absolute/path/to/fresh-audit
python3 audit_legacy_failure.py /absolute/path/to/inner-receipts \
  --output /absolute/path/to/fresh-audit/legacy-failure-recomputed.json
```

The orchestration stores every subcommand exit and does not convert the failed
completeness command into a passing qualification. Original ZIP digests and
traversal/link/duplicate/expansion checks are required before extraction. No
engine, native input or OCR executable is invoked by these review commands.
