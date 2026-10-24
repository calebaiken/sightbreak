# Retained ordinary sparse fixture setup failure

Before qualification, attempted:
`git sparse-checkout add --no-sparse-index docs/reports/gauntlet/windows-input-consumption-r7-expiry-builder-tests-20261024`.
This Git version's add subcommand does not accept --no-sparse-index and returned
129 with `error: unknown option no-sparse-index` plus usage. The unsupported
option did not restore that fixture directory. Existing no-sparse-index setting
from init/set remains valid; add does not need it.

The subsequent original own-final run retained257 selected methods with0 assertion
failures,11 missing-file errors and3 inherited skips. All independent model groups,
retained139 and13 shell parses passed. These11 errors are failed setup evidence,
not candidate correctness failures or a passing pure run. The separate bounded
pack explicitly included both required new test report fixture directories, so
depth-final selected257 passed254 with3 skips and no failures/errors.

Correction registered before rerun: add the exact tracked expiry-builder-tests
directory using the supported add syntax, preserve every original raw error, and
rerun only selected pure checks to a new own-pure-fixture-rerun output directory.
Candidate source/expectations remain unchanged. Independent model/corpus groups
already passed and are not rerun for this document-fixture setup correction.
