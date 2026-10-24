# Final target amendment before implementation inspection or tests

Frozen final source is642dd0e0543698cae5d90b9046d5875beabed111, over
base342c3641ab2fccd1fc875c84188a8395a9b93a96. Builder handoff is
 d139124e8c663c3951eb6c7aaff99d49f2ce9712, with report
/workspace/sightbreak-windows-input-consumption-r4/docs/reports/gauntlet/windows-input-consumption-r4-20261024/HANDOFF.md.
Historical3e688c8c freeze remains in history. Builder/root disclosed that its
new test helper inserted client_tick without advancing snapshot_age_msec, which
could confound current-counter rejection with pre-existing freshness rejection.
Final642dd0e0 changes that helper only according to metadata; verify actual diff.
All earlier preregistration gates remain. Existing-thread reuse stays explicit.

This amendment is committed before R4 implementation or handoff inspection and
before any test execution. The new target is merged into the own review branch
without rewriting preregistration history. Pure/static checks may now begin.
All falsifiers must pair a valid baseline with current snapshot age and alter only
the target source invariant, with old reader/candidate outcomes attributed to
exact bytes. Do not count a stale-snapshot rejection as a counter-state success.
No process/mock-process or Mac suites will run, even if present in builder runner;
select the relevant pure reader/fixture controls and disclose omitted groups.
