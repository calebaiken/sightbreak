# Preserve R1; correct only extracted route harness dependencies

Original R1 ran all eight controls: two supported assertion failures, one route
harness NameError, zero skips. Its complete 12293538 bytes/source/results remain
unchanged. The extracted relocate_settings_actor needs the frozen source globals
SETTINGS_COVER and SETTINGS_SPAWN; extraction omitted them. No candidate route
operation ran before that NameError, so it is not a consumer failure or pass.

Replay ONLY original test08 against the same saved ordinary baseline and proposal.
Import the frozen control module without invoking its main, set the two constants
from exact source AST literal assignments, and redirect its new output prefix.
Keep all original assertions/test08 source and all producer/source functions exact.
No full draft rerun, new positivity expectation, error skip or old-result rewrite.

Give the extracted source pulse a bounded fake-sleep seam: at most32 sleep calls
per pulse; advance by the requested duration rounded upward to the declared
clock's integer-nanosecond resolution. This declares at most1ns oversleep, which
is permitted by the real source loop and prevents a positive sub-nanosecond float
residual from creating a zero-progress pure-test loop. The actual source method,
clock definition, recorded consumer data and receipt assertions do not change.
This is an explicit fake scheduling cost, not normalization of any raw input.

Use the original effect guards and CPU4; write fresh pure-r2-route-only outputs.
Retain its exact binding, result and raw failure if any. No R2 reader/collector,
native/API/proc/SDK/CI/capability/helper/study execution or score is introduced.
