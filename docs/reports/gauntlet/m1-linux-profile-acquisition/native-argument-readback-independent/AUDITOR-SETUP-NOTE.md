# Retained reviewer setup failures

The first owned acquisition discovery ran before the sparse checkout included
the existing correction/sealing/remap fixture reports. Its original
`own-acquisition.stderr` records 30 discovered methods and 11 setup errors.
Exact tracked fixtures were restored with `git sparse-checkout add backend
server tools docs/reports/gauntlet/m1-linux-profile-acquisition`; the separate
`own-acquisition-restored` invocation passes all 38 methods. The original failed
invocation remains a setup failure.

The first independent source/originals audit rehashed the 370 original files,
then incorrectly treated the actual critic registry's relative outer aliases as
absolute file paths. `source-and-originals-initial.stderr` retains the failed
assertion. Its faulty statement was `path = Path(name)` followed by
`check(path.is_absolute() and not path.is_symlink(), 'Outer identity path')`.
The corrected auditor explicitly maps the three aliases to the original `.local`
paths recorded in the actual outer receipt. The next independent invocation
passes 2,740 predicates; the later expanded audit also protects all 8,649 prior
document paths and passes 11,389 predicates. Every output is retained separately.

The first nine independent methods passed in both checkouts. A subsequent,
additional method exposed four numeric fingerprint substitutions accepted by
the candidate. Both final ten-method invocations exit 1 with the same four
failed rejection assertions. Those are candidate validation failures, separate
from setup failures. No candidate source was edited to make them pass.

The complete staged whitespace check reports three trailing spaces emitted by
unittest immediately before failed subcase output. Its original output is
retained as `raw-output-whitespace-check.stdout`; the raw test streams remain
byte-for-byte unchanged. A separate check limited to authored Markdown, Python
and JSON files passes.
