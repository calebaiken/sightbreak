# Source-positive defuser fixture correction

Independent critic acbe3943 REPORT already records the schema-positive defect;
its follow-up independently confirms bot_ai462–468 keeps the actual device
position for the nearest living defender, including outside interaction range.
The old helper always plans[15,0,10] while control_defuse places the device and
actor6 at[-15,0,10]. Old input00..04 and their baseline acceptance remain exact.

Before fixture edits, expand this component to correct only that helper
destination using planted/live-team1/nearest-defender source predicates, for
every generated thinking row. Do not use test name or interaction success as
the predicate. Preserve old helper source here. Regenerate the same independent
four mutations using the unchanged critic script against the corrected helper;
retain both original and regenerated positive/negative results. A new strict
reader rejecting old source-inconsistent positive data is not itself proof that
the four mutations are fixed. The new baseline must pass and independent mutations
must reject for their own supported errors. Remaining eight gaps stay blocking.

Add meaningful maintained regressions for the four violations and the valid
nearest-defuser plan inside/outside2.6m. No production/probe/AI/source changes.
