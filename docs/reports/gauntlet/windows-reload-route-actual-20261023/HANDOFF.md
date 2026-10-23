# Windows route controller handoff

Source-only candidate is ea6c330a272f17a8a68ef94af868c70bda95a91e, based on exact
Windows actual 49ae54b0e4f5d880bdf06e4eb783a616b2dff684. Preregistration is
0bd1fe11. Own checkout is /workspace/sightbreak-windows-reload-route-actual,
branch codex/windows-reload-route-actual-20261023. Independent source review is
pending. No engine, export, native process, CI job or qualification dispatch ran.

## Correction and scope

Only native_approach.py changes runtime behavior: `fine` starts true when the
caller explicitly supplies a native pulse callback. That callback now owns the
first displacement from the original stock spawn, instead of waiting for a
continuous coarse walk to reach 2.2 m. The existing short pulse formula, rate
bounds, deadline, all-key cleanup and two distinct neutral stopped readbacks
remain. Callers without the callback keep their previous coarse walk.

The R2 WinUI per-edge owned-window/focus checks remain byte-identical. So do
verify_offline_export.py, native_settings_route.py, export_integration.gd,
verify_integration_export.py and validate.sh. The complete game tree is identical
to 49ae54b0. candidate-bindings.json records their exact hashes. The original
corridor, endpoint, deadlines, three input schedules, stock rules, health, life,
ammunition and AI remain. This is a controller adaptation, not a product input
fix or an actual gameplay pass.

## Evidence and checks

The real bar is run 39940242244, job 120369601915, bound in
original-bindings.json. The independent actual critic retains the complete
original artifacts. PREREGISTRATION.md records the inspected edge/readback
sequence and the separate ordinary network failure. The native fine pulse was
unreached in the original failed route. Historical e28c8e9 corridor and legacy
reload-completion timeouts remain failed.

The added pure plant charges declared diagnostic costs around each traced key
callback and observation. It uses the existing independent 60 Hz ground model,
28 m/s^2 acceleration, 5.1 m/s speed and 13-tick publication. These costs are stress
conditions, not claimed native timing. Its unchanged continuous-walk path still
fails xmin=-8.5 at x=-8.9077778 and releases all requested keys. The opt-in path
reaches the original stopped endpoint in all nine rate/delivery cells, uses no
fallback key-downs and stays inside the corridor. Maximum modeled wall time is
18.151812 s inside the original 35 s cap. declared-model-results.json retains all
nine rows and the original-path counterexample.

Four new methods cover first displacement and stopped arrival, the preserved old
failure, blocked/unreadable observations and post-pulse life/round/focus loss.
Existing controls retain late-callback, per-edge ownership, external controls,
release-error and interrupt failures. prefixed-controls.log preserves the first
pre-fix failure. The final four-method falsifier suite also runs against exact
original controller bytes restored in memory: exit 1, seven failed subtests and
eight errors. That expected failure remains in original-source-final-controls.*;
no tracked source was changed for the restoration.

Both complete-pure/results.json and depth-one-pure/results.json pass all 14
maintained pure groups: 158 methods, 155 passes and the three existing Windows
skips. The two additional approach/Mac-menu groups pass 20 methods. Each full run
therefore has 178 methods, 175 passes and three skips. Shell syntax also passes.
The first focused 130-method run is retained as maintained-pure.log. All work ran
on CPU 4. No whole native aggregate acceptance is claimed.

The fresh initialized depth-one clone is .local/depth-one-source at ea6c330a,
shallow=true and commit_count=1. Its tracked source is clean; 471 available
code/instruction files match byte-for-byte in depth-one-source-bindings.json.
The pure suite uses no report-tree import. run_pure.py records exact commands,
exit codes, method counts and original log hashes, and refuses other CPU affinity.

## Largest remaining deficiency

Actual Windows delivery and the complete living settings/LEAVE/reopen/focus
journey remain unobserved for this candidate. The correction removes the exposed
coarse path; pure dynamics cannot establish how native input is consumed.

The ordinary network input failure is also unresolved. Before firing, the
controller reads an authority sample already 30.435 s old. LMB-down occurs inside
a 38.836 s native authority sample gap, and R-down occurs after a sampled unbound
peer. All retained samples show zero shots, a full rifle magazine and no reload
intent. Actual logs show two disconnects with an intervening reconnect. Production
input sampling, the connected-client send gate, authoritative stream consumption,
silence neutralization and the full-magazine reload guard explain why this trace
cannot identify an R-key defect. They do not establish why either disconnect
occurred or whether client processing stalled. No input/transport timeout or
readiness rule was changed to make it pass.

A fresh independent critic must review ea6c330a and these falsifiers. Root owns
integration, any next read-only consumption/transport diagnostic, and a separately
preregistered native release. No retry is authorized by this handoff.

Reproduce the pure checks in a new output directory:

```sh
taskset -c 4 python docs/reports/gauntlet/windows-reload-route-actual-20261023/run_pure.py --source . --output .local/review-pure
```
