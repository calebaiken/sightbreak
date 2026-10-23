# Native fixture type correction preregistration

Source and pure Python only, registered before code changes. Own branch
`diagnostic/linux-profile-fixture-native-types`, sparse worktree
`/workspace/sightbreak-linux-profile-fixture-native-types`, exact base
`f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9`. The original worktree
`/workspace/sightbreak-linux-profile-acquisition` and its failed
`builds/linux-profile-acquisition-r1` and `.local` receipts stay untouched.
Independent actual-output critic `/root/linux_profile_native_fresh_critic`
owns preservation and review of that attempt.

## Actual failure and correction

The first actual wrapper attempt exits 1. Its import child exits 0, but
`06-import.stderr.log` reports `Cannot infer the type of "keys" variable because
the value doesn't have a set type` at diagnostic fixture line 107, followed by
the script load parse error. The existing strict log gate stops before export.
There is no diagnostic payload, native block, measurement or cadence result.
The earlier source/pure acceptance did not establish GDScript compilation.

Change only the fixture declaration `var keys := value.keys()` to
`var keys: Array = value.keys()`. `_canonical(value)` accepts a Variant, while
the `TYPE_DICTIONARY` branch supplies the runtime dictionary guard. An explicit
Array declaration avoids inferring a static type from the Variant method call
and keeps the same keys, sort comparator, traversal, serialization and hashes.
Inspection of every fixture `:=` site found no other direct inference from the
untyped `value`: other declarations use literals, typed parameters/variables,
typed engine APIs, or explicit conversions. Do not broaden this correction
without new source evidence and a preregistration amendment before editing.

Update only the corresponding fixture SHA-256 in acquisition `ACCEPTED`; keep
the accepted Python controller and scene hashes exact. Give this candidate one
new fixed output identity, `builds/linux-profile-acquisition-r2`, and therefore
a fresh `attempt.claim` inside that directory. Change only the supervisor's
fixed `OUTPUT` constant for that identity. The failed r1 identity cannot be
reused or removed. The later wrapper stdout/stderr and outer tool receipt use
fresh `.local/linux-profile-acquisition-r2-*` names in this own worktree.

## Preserved design and release boundary

Preserve the complete shipping game tree
`55691684d31d44f1680141954bbe530443de9d1f`, original offline controller, accepted
diagnostic Python controller/evaluator, scene, tests, pins, source references,
all prior reports and raw failures. Keep the same text-script packaging
amendment, pinned 4.7.2 editor/templates, CPUs 0,1, display :99127 and LP2.
Retain one payload, OFF/ON/ON/OFF, separate cold/anchor/readback, 32 warm and
64 measured intervals, all original mathematics, thresholds, comparability
checks and descriptive/limited claims. No gameplay or shipping change.

The original whole bound remains 1320 seconds. Phase caps remain
60/45/15/120/30/120/60/30/750/60 seconds in the original order. Each condition
still has its strict 180-second bound. Cleanup stays five seconds per owned
command; failure publication stays ten seconds. No retry, extra engine query,
export fallback, changed affinity/display or budget extension is introduced.

Run the existing pure acquisition and accepted controller/evaluator suites,
with raw outputs retained in a new `pure-controls/` directory. Inspect the exact
source delta and compare every other tracked path against the frozen base;
bind the source and evidence hashes in the handoff. Read the original failed
import/outer receipt only, retain their identities, and confirm the unchanged
strict-log function still rejects the actual parse/load error bytes. These
checks cannot certify GDScript syntax, imports, export resources, runtime
fingerprints/pixels, cleanup or cadence. Do not add a regex/string test and
describe it as a compiler test.

No Godot, compile/import, generated UID, export, Xvfb, native fixture, profiler,
OCR, CI, service, heavy process or nested agent may run for this source/pure
correction. Commit and push a clean source/evidence freeze. Fresh independent
exact-source review and root's explicit lane release remain required before
any second actual attempt; this registration grants neither.
