# Interrupted aggregate validation: missing sparse fixture

The unmodified `scripts/validate.sh` at clean frozen `a23e349` exited 1. Root's
sparse checkout omitted the tracked reload-contact CSV and adjacent GLB hash
under `docs/reports/media/art-v9/hands/logs`. This is an execution-checkout error;
the missing-fixture failure remains an actual failed attempt.

Before that stop, the new activity, bot squad and authority checks, ordinary game,
server, profile/input/HUD, 9,217 landscape and 2,227 UX checks, economy/UI,
account-output validators, reload sequencing and all three real-time Dummy audio
captures completed without a failing step. The raw logs retain every assertion
summary. Later network, catalog/build/observation checks did not run in this
attempt. No full aggregate pass is claimed.

Before/after source identities agree, including HEAD and shipping/validation
hashes. There was no DISPLAY and no optional backend SQL execution. The separate
UI input-mode correctness run overlapped the tail of this aggregate; no timing
or performance comparison is claimed from this run.

Root restored only the tracked fixture directory through sparse checkout, leaving
HEAD and game/scripts content unchanged. The exact failed reload-contact command
then passed 24 checks. A complete fresh aggregate rerun is queued after the
current independently evaluated touch correction. The committed archive retains
all 57 selected original logs/receipts;
MANIFEST.json is the authoritative count and hash inventory.
