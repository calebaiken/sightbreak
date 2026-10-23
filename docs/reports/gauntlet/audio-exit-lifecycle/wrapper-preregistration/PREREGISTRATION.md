# One-shot acquisition wrapper preregistration

Source/pure work only, after analyzer freeze `73cdfc2`. This is a separately
reviewable Linux-only wrapper; macOS/Windows acquisition remains unsupported.
The source bar is the retained original root controller SHA-256
`43dfdeae51aaa95dbb43aeb33125c772688f50e604cc471c8b4ba0309734c7fe`, copied unchanged
beside this file. Adaptation will be explicit. Its error-line matcher misses the
ObjectDB WARNING; all new strict gates will use unchanged `native_log.failed`.
The old exact-argv verbose repeat tool will not change.

One exclusive fresh output directory reserves one attempt before any process.
Require exact caller-provided full source commit, clean source, complete tracked
game/scripts bytes matching their Git blobs, an explicit expected executable
SHA-256 and exact pinned `--version`. No downloads or installation. Copy only
tracked game files to the owned private project. Change only the two declared
custom-userdir project settings; use fresh private XDG/native userdata. Probe
before/after the suite using Godot's actual project/userdata paths and driver.
Driver must equal the default Dummy selected by the unchanged headless argv.

The suite tail stays exactly `--headless --verbose --script
res://tests/input_mode_test.gd -- --audio-lifecycle-diagnostic`. Import uses
headless editor/import/quit on the private copy only. Capture complete copy maps,
pre/post inventories, newly generated UIDs and raw stdout/stderr combined per
process. Import may add only Godot cache files and valid UID sidecars for copied
scripts previously missing them. No tracked bytes may change. Reject preparation
errors/warnings caught by strict scan and skip suite after any preparation loss.

Budgets: 120 seconds each for import and suite, 30 for version/identity probes,
240 seconds for the whole attempt including cleanup/finalization. Reserve time
inside that whole bound for cleanup and final source/inventory receipts. Poll
Linux `/proc` with bounded intervals; record PID, start ticks, PGID and SID.
Signal only the original validated group or exact observed live identities;
reject PID reuse and never kill by name. Normal exit and failure paths must
record bounded TERM/KILL cleanup, observed survivors and remaining session/group
members. Polling can miss an unseen escaping/reparented descendant; no complete
arbitrary-descendant guarantee will be claimed.

Always retain attempted-phase and overall failure receipts, including timeout,
setup/import/identity/drift/analyzer/cleanup failures. Archive produced userdata
and UIDs before removing owned project/state when no observed survivors remain.
Never remove outside the reserved output. Keep strict sample cleanliness separate
from acquisition integrity; a leak remains a strict failure, and no sample closes
the historical blocker or identifies cause/drain by itself.

Pure controls must prove exact argv/default-driver binding, source/engine/fresh
output refusal, strict import-warning rejection, preparation skip, UID/source
drift rejection, timeout budget/cleanup reservation, PID-reuse signal refusal,
survivor failures and retained overall receipts on errors. Full-flow controls use
mocked engine processes only. No Godot/import/UID/GDScript/native/CI/OCR/service
will run during authoring. Freeze/push source and controls for fresh independent
review of both this wrapper and analyzer before any acquisition.
