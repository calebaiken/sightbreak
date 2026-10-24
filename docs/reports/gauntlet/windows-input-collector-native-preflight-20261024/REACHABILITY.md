# Independent movement count and coverage

Separate read-only critic `/root/collector_native_preflight_critic_20261024/movement_reachability`
derived the expected count from exact source, without executing the engine.

| Contribution | `game/tests/movement_prediction_test.gd` | Count |
| --- | --- | ---: |
| Movement loop | line44 `range(360)`, checks64–65 | 720 |
| Terminal movement checks | lines67–73 | 5 |
| Admission checks | lines82–88: 3 direct, 5 loop, 2 direct | 10 |
| Control projection | lines92–95 | 4 |
| Packet projection | lines100–101 | 2 |
| Disabled observer invariants | line106 | 1 |
| Total | 720 + 5 + 17 | 742 |

Root `11c5773eff6888c5157784c272aca144614338d4` has the same 725 movement
checks. The candidate adds the helper and its unconditional call, with no removed
test lines. `_initialize()` defers `run()` at lines19–20; `run()` calls
`native_input_observation_controls()` at line22 before any await. `check()`
increments even after a false assertion. The twenty-iteration packet creation
loop adds no checks.

The only observer instance is newly constructed at line102, receives no configure
call or scene insertion, and is called directly at line105. Its state starts as
`{}` at `match.gd:110`, so `_native_input_observe()` returns at line1267. Enabled
state changes, physical-input reads, multiplayer access, record construction and
printing at lines1268–1321 do not execute. The seventeen checks therefore cannot
qualify enabled emission, cap/throttle behavior, native event coverage or overhead.
The static count is conditional on parsing and completion; only actual output
can establish `checks=742 failures=0`.

The helper's first orientation shell lacked CPU affinity; every subsequent read
used CPU4. It changed no files and launched no engine, native or observer process.
