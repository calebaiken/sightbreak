# Independent source review: ACCEPT

Accept exact commit `f3896c60d367466129ba5d2a906234b2dee8174f`, based on
`a3b7070f7739ae854e643f905230ae2b6f1a85cb`, for **one bounded actual ARM macOS
diagnostic attempt**. No blocking source finding remains within the preregistered
criteria. This verdict covers source and pure controls; it does not establish a
native repeat result, leaked object types, a leak cause, or release acceptance.

The original strict native regression gate remains FAILED. A clean verbose repeat
would be diagnostic evidence and would not repair that gate.

## Reviewed evidence and source

Read `AGENTS.md`, `CLAUDE.md`, the vendored gauntlet-loop, sightbreak-gauntlet and
no-ai-slop instructions and evaluation, and the committed first-leak `CRITERIA.md`.
The mission/roadmap files referenced by those repository instructions are absent
from this checkout. The review follows the bounded task and its committed criteria.

Inspected the complete candidate diff, selector, CLI, inherited
`NativeSceneSuites` lifecycle, shared native log gate, source identity helpers,
pinned engine verification, process reaper, workflow and retained fixtures.
`snapshot/` holds 418 exact committed files covering game resources, scripts,
workflow, repository instructions/skills and criteria/fixtures. SHA-256 hashes are
in `snapshot-sha256.json`; Git blob provenance is in `committed-blobs.json`.
`source-freeze-verification.json` confirms that all reviewed implementation,
workflow, game, criteria and fixture paths still equal the reviewed commit. The
builder's uncommitted HANDOFF/readiness files are outside this approval.

Both retained boundaries match their original raw files byte for byte, including
lengths and manifest hashes; see `actual-fixture-verification.json`:

| Original run | Retained strict boundary | Later suites |
| --- | --- | --- |
| 39736389634 at 20464da | actor: exit 0, 73 checks, 0 assertion failures, 6 ObjectDB leaks | 11 unreached |
| 39732825169 at b09cfe1 | input_mode: exit 0, 462 checks, 0 assertion failures, 2 ObjectDB leaks after 6 clean suites | 5 unreached |

The later run's recorded native menu PASS remains distinct from its strict source
failure. The earlier menu failures remain historical failures. The game resource
inventory of the frozen candidate equals the inventory in both original isolation
receipts. Different boundaries and leak counts do not establish a shared cause or
nondeterminism; both remain UNKNOWN. Neither retained suite log has verbose leaked
object type evidence.

## Controls and findings

All **17 independent methods** in `review_controls.py` pass; see
`independent-controls.log`. All **14 maintained methods** pass from the external
snapshot, comprising 8 legacy and 6 new methods; see `maintained-controls.log`.
These counts describe pure controls, not native suite checks.

The independent controls exercise the real inherited constructor, context manager,
configuration, import prerequisite, producer parsing, suite execution, resource
inventories, produced-file hashes, raw logs and cleanup. Engine verification,
platform/source identity and every process/native producer are explicitly fake.
Unexpected subprocess operations fail the control. Both actor and input_mode
complete this mocked lifecycle, and repeated ObjectDB warnings keep the repeat
failed while preserving original evidence.

Additional controls cover:

- 36 adversarial selection variants and 7 malformed receipt shapes with zero
  process launches, including unsupported, absent, foreign, unclean, duplicate,
  unknown, nonterminal and earlier-failure evidence.
- Exact selected suite argv with `--verbose` as the only addition; separate
  bootstrap/import/before/after producers; no alternate suite execution; legacy
  reason-only selection and the default input_mode constructor.
- Changes to original evidence, previously absent evidence, source identity or
  cleanliness, and expiration before construction, all with zero launches.
- The shared 240 second deadline, decreasing process wait limits, timeout
  receipts, owned session/process cleanup and failure when a group remains.
- Import, before-state and after-producer rejection; source/copied-resource
  mutation; namespace deletion failure with honest failed cleanup receipts.
- Bootstrap foreign, absent, warning and nonzero receipts: no import or suite
  launch, no invented cleanup, and preservation of the unvalidated namespace.
- Actual fixture selection against the real frozen resource inventory. Only
  macOS `/var` to `/private/var` resolution is simulated at `Path.resolve`; a
  separate pure filesystem symlink test exercises the public resolution helper.
- The unchanged strict workflow command, diagnostic controls prerequisite,
  6 minute timeout and lack of `continue-on-error` on the diagnostic step.

Representative synthetic lifecycle logs and receipts are retained under
`PURE-MOCKED-*`. They are deliberately fake and provide no native evidence.

The largest remaining gap is the absent actual verbose object type evidence. The
next attempt must retain its strict failure, source identity, original evidence
hashes/absence, raw verbose log, producer/process receipts and honest cleanup
outcomes for a separate native evidence review. This source approval applies only
to the exact implementation reviewed here and one bounded diagnostic attempt.

No Godot, OCR, macOS native API or CI dispatch was run during this review. No
implementation, canonical evidence or game source was edited.
