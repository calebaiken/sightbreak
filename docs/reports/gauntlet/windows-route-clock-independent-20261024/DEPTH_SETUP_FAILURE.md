# Retained initialized source-view setup failure

The first build_depth_one.py attempt transferred a local object pack containing
only the candidate commit, its trees and selected source/support blobs. It
exited 1 during Git cone sparse configuration because Git attempted to read
omitted documentation blobs. Its original empty stdout and complete stderr are
preserved as depth-one-creation.json and depth-one-creation.stderr. No test ran
in that incomplete view and no new clone/remote/alternate was introduced.

Recovery will preserve that directory and failure history. Record its current
status, configure explicit non-cone paths for exactly the already-transferred
source/support files before applying read-tree -mu HEAD, then record fresh
recovery identity/output. This is the same initialized candidate/object pack,
not a different candidate or a passing first setup. All later test outputs use
new paths. No missing documentation is inferred to be source or test success.

The first non-cone recovery applied the source paths successfully but then
failed its clean-status assertion: five tracked root files remained absent
from the earlier failed materialization. That second failure is preserved in
depth-one-recovered.stderr and depth-setup-second-status.txt. Restoring only
.gitattributes, .gitignore, AGENTS.md, CLAUDE.md and README.md from the exact HEAD
completed setup. depth-one-final.json records the clean final one-commit view.
Only then did depth models and pulse tests run, using fresh output paths.
