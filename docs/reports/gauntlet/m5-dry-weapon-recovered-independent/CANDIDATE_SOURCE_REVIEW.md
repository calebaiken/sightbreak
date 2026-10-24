# Candidate source review

Verdict: **PASS source boundary and maintained registration** at final freeze
`8e8d13e7dbf427b464519868d38a9c40aa732594`, pending native measurement. Product
source is the same as `bd4ea03f071be4c90db90e3f5ff56e8846af7cf7`. The
production delta is exactly three added lines in the no-target primary-return
loop. No fixture byte, action consumer, profile, fallback, reload, objective,
timer, authority, economy or network code changes.

The existing ownership check remains first. For an owned primary, dictionary
lookup with sentinel `Vector2i(-1, -1)` skips only recorded `Vector2i.ZERO`.
Missing state therefore retains ordinary actor equip defaults. Either positive
clip or positive reserve differs from zero and stays eligible. The literal
rifle, marksman, SMG priority list and first eligible selection remain unchanged.
The active weapon is constrained to sidearm before this lookup, so all queried
primary entries are holstered; stale active ammo-store entries cannot replace
the active fields. The actor's equip/reload authority remains unchanged.

The exact common fixture SHA-256 remains
`059a49bdf1e755a049e0fa4a904d303eb5fc9ce1fd05cbfc993ee9881aa46863`.
The complete actor and match scripts match the reviewed baseline. This is a
named source comparison, not a blind result. The largest remaining gap is
absence of actual candidate output; source inspection is not candidate gameplay
acceptance. The documented finite-priority, injected-perception, unlogged
snapshot and session-only cleanup limits remain.

The separate registration adds one mandatory `run_godot` invocation to
`validate.sh`, one `bot_dry_weapon` entry to the native default suite tuple and
the explicit headless/Dummy command for the same fixture. It removes no suite,
retains previous suite order and argument overrides, and adds no skip or weaker
failure condition. `set -euo pipefail` preserves a nonzero engine exit through
the validation tee pipeline. The native runner already rejects a nonzero suite
exit or error log. AST checks of those registrations and `bash -n` pass; their
exact checks and hashes are retained in `registration-review.json`. No maintained
aggregate or native platform-suite pass is claimed from this registration review.
