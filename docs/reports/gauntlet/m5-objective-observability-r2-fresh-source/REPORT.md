# Independent objective observation R2 review: REJECT SOURCE READINESS

Frozen candidate: `dce89495d04c9d3fefece0f8c7929e2e01b8e7df`.
Builder handoff: `f363e31077ad5aec79e901bff8d12bbaf9c27ddf`.
Independent registration: `15e82486`, fresh methods `2e46306b`, unchanged
falsifiers `4e9ef3c3`, recovery registration `fdb23318`.

R2 wins the limited source comparison against rejected candidate `c91d9b98`:
it clears requested observation output, distinguishes early-return statuses,
binds a complete acquisition inventory and rejects all eighteen real original
receipt mutations. It still fails the registered readiness bar. All twelve
new, genuinely changed negative receipts are accepted in each source view.
The reader reports `observable_contract_passed: true` for impossible actor,
perception, destination and authority data.

The largest remaining gap is the decision-to-objective handoff. The reader
checks the objective consumer correctly against the state it is given, but
permits that starting state to change objective, progress, credits and teams
between the last decision and the consumer. A locally consistent consumer
therefore does not establish a source-consistent trace. No native acquisition
release follows from this review.

## Evidence and identity

The original interrupted `own/` and `depth-one/` files are preserved byte for
byte and committed in `1c96187e`. Recovery audit verifies every retained
maintained/source/original command receipt against its stdout/stderr hashes.
Both retained maintained runs passed ten methods. Both source audits passed.
Both unchanged original-rig processes exited 1 for the preserved contradictory
no-op. The correct count is **19 distinct inputs: one baseline and 18 real
mutations**, all eighteen now rejected. The extra named no-op repeats the
positive input with the opposite expectation. This is the adjudication in
`c3a89e53`, not a remaining candidate defect or a twentieth distinct test.

[Recovery audit](recovery-20261024/audit.json) independently verifies all 451
tracked acquisition paths, modes and blobs against the exact Git candidate,
working-file SHA-256 values against its frozen inventory, and absence of
untracked game/scripts source. Both views have identical game and scripts tree
IDs: `d27f5a57cfc1e22d81d4cf584824d363ecc382d1` and
`bf8bab3e5821ea794468f0792c4d9af34443f244`. Reviewer HEADs contain report-only
commits, so the hardcoded candidate label in the fresh script is corroborated by
these independent identities rather than treated as proof itself.

The existing initialized depth-one view remains at the exact candidate with
one reachable commit, no remote, no object alternates and no alternate-object
environment variable. Its parent object is unavailable (`cat-file` exit 128).
The retained creation record identifies an 8,931,186-byte pack with 480 paths,
including component support documents; 451 are the frozen acquisition source
files. This proves the tested history-free local source view. It is not proof
of a new network clone, a different remote transport or an exported artifact.
No new full clone was created.

Independent erasure recovers exact Git `022d60f` AI bytes, SHA-256
`742ae5c96becf4e27071423e0bdd604a13b528c201d38df52f837359fe9214cb`.
The historical reference equals exact Git `0527715` AI bytes. The newer baseline
has thirteen added fallback lines and no removed lines. The reconstruction
cannot establish the historical timeout cause. Manual production-diff inspection
finds observation writes directed to caller-owned output, literal-boolean opt-in
with debug/offline/authority gates, and no inserted selector, RNG draw, movement,
command, economy or protocol change. This is source inspection, not engine proof.

## Reproducible accepted counterexamples

The unchanged [fresh controls](fresh_controls.py) were registered before their
original execution. Recovery reruns them without modifying reader, generator,
mutations or expectations. `recovery-20261024/{own,depth-one}/inputs.json` maps
input indices to exact uncompressed SHA-256 values, compressed-file hashes,
acceptance results, source view, CPU affinity, exit and duration. Input `00` is
the schema-positive baseline; inputs `01` through `12` are the following real
mutations. Every negative accepts in both views and both complete replay
processes exit 1. Original failures remain in their original paths.

| Input | Changed receipt | Why the frozen source cannot emit it |
| --- | --- | --- |
| 01 | Fresh `live_complete` decision identifies actor 7. | The fixed freshness sequence calls actor 6 (`probe:258-262`); the emitted decision uses the actual actor ID (`bot_ai:814`). The CALL reader checks shape without binding that identity (`verifier:391-393`). |
| 02 | Direct perception returns actor 10 with an empty candidate list. | Selection starts null and can change only after an eligible candidate is appended (`bot_ai:359`, `400-405`). The public wrapper serializes that selected actor (`578-583`). The CALL reader checks only list type and ID range (`verifier:394-395`). |
| 03 | Nearest interacting defuser plans and reports destination `[999,0,999]`. | Planted-objective planning selects the device position for that defender (`bot_ai:462-468`), fixed at `[-15,0,10]` by the control (`probe:219-224`). The reader binds interaction eligibility but omits that destination invariant (`verifier:272`, `276-283`). |
| 04 | A decision reports `invented_role_not_in_source`. | The source assigns fixed role values and emits its resulting memory role. The reader admits any nonempty string (`verifier:233`, `271-272`). |
| 05 | An eligible target has fabricated score `-999`, while the decision retains no-target navigation and unchanged target memory. | Score is distance minus specified bonuses (`bot_ai:390-398`); selection writes target memory (`636-643`) and enters combat movement. Navigation belongs to the no-target branch (`719-769`). The reader accepts supplied finite scores and never binds this branch/memory combination (`verifier:259`, `295-303`). Negative scores alone are legal generally; this fixed score and contradictory branch are the defect. |
| 06 | A fixed in-range, in-FOV candidate is marked rejected by FOV. | The mutation asserts the actual pose dot product exceeds the normal FOV threshold, with no recent-damage exception. Source FOV rejection uses precisely that dot predicate (`bot_ai:377-384`). The reader checks range and distance without that predicate (`verifier:290-300`). |
| 07 | Actor 6 gains 100 credits during the final forward action phase without a reward cause. | Kill credit increments kills and awards 300 (`match:495-498`); objective and end-round rewards occur later. No kill, death or other reward transition accompanies this injection. The handoff omits credit binding (`verifier:430-432`). |
| 08 | The final forward objective changes from carried to planted before its consumer, with no planting progress/completion. | Movement/actions and damage precede the objective consumer (`match:297-320`). Planting requires the progress threshold inside that consumer (`414-426`); carrier elimination can drop it (`507-510`), not plant it. The reader accepts a coherent planted consumer applied to this invented starting state. |
| 09 | Actor 6 receives 2.9 progress before that consumer, which correctly clears it as ineligible. | The preceding authoritative state has no progress; action/movement code does not add it. Local clearing succeeds while the unbound cross-phase injection survives (`verifier:430-432`). |
| 10 | Stationary actor 1 teleports to `[999,999,999]` on the final isolated plant tick. | The control moves/actions actor 6 only (`probe:239-243`). The reader binds objective fields and credits across ticks but omits other actors' poses (`verifier:455-470`). |
| 11 | Match RNG becomes `777` on the final plant tick without a bot call. | The selected tick has no thinking call, and subject movement/actions and the objective consumer do not draw match RNG. The control reader lacks that continuity invariant (`verifier:455-470`). |
| 12 | Actor 6 switches to team 1 during the final forward action phase. | That phase contains no team reassignment. Team switching belongs to round initialization, not movement/actions. The handoff binds inputs but omits teams (`verifier:430-432`). |

These are reader falsifiers, not claims about actual engine output. The
maintained positive is explicitly a schema fixture, not an engine model
(`test_bot_objective_observation.py:52-53`). It already gives its defuser
`[15,0,10]` (`42-43`, `103`) despite the device at `[-15,0,10]` (`93-95`).
Its acceptance demonstrates admission and supports the missing-invariant finding;
it does not certify exact source reproduction. The twelve mutated inputs are
distinct within each process and differ from their process's positive input.
Uncompressed hashes can differ across runs because command keys originate in a
Python set; no cross-process byte-identity claim is made.

An additional independent agent inspected the fixed source without executing
checks and corroborated all twelve source violations. Its strongest examples
were empty-list target selection, defuser destination, and spontaneous planting.
It also identified the schema-positive fixture limitation and legal negative
scores; both qualifications are retained above.

## Reproduction and limits

From this reviewer checkout, the complete registered rig reproduces the expected
review failure against either existing source view:

```sh
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/m5-objective-observability-r2-fresh-source/fresh_controls.py "$PWD"
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/m5-objective-observability-r2-fresh-source/fresh_controls.py /workspace/reviews/m5-objective-observability-r2-fresh-depth-one
```

Replay one saved impossible receipt without regenerating it:

```sh
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 - "$PWD" docs/reports/gauntlet/m5-objective-observability-r2-fresh-source/recovery-20261024/own/input-02.log.gz <<'PY'
import gzip
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / 'scripts'))
import verify_bot_objective_observation as reader
print(reader.source_audit(root))
print(reader.verify(gzip.open(sys.argv[2], 'rt').read(), root))
PY
```

The frozen reader prints `observable_contract_passed: true`; a corrected reader
must reject this receipt. Use input `08` for spontaneous planting. The same files
and results are retained for the depth-one view. Keep the original rig unchanged
and preserve its duplicate-no-op exit 1 when validating a correction.

Recovery system Python could not import `gdtoolkit`; this attempted grammar
check is retained as `No module named 'gdtoolkit'` in the audit. The builder's
historical grammar success is not relabeled as a new independent parse. Sparse
working-tree lookups for the handoff and later pure-final records also failed;
the exact handoff was read with `git show f363e310:.../HANDOFF.md`. None of these
lookup failures is counted as a passing check.

Only CPU 4 pure/static checks ran. No Godot, native compilation, import, export,
CI, rendering, process inspection or Mac file-handling review occurred. Godot
4.7.2 types/APIs, native freshness/parity, actual geometry, objective behavior,
strict shutdown, quality, performance and whole release gates remain unverified.
Canonical mission documents and all product source remain unchanged. The builder
must correct supported reader/fixture gaps, freeze a new exact source and obtain
fresh independent source review before separate runtime planning.
