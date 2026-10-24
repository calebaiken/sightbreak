# R7 projected lifecycle expiry model

New root-owned branch codex/windows-input-consumption-r7-20261024 at
/workspace/sightbreak-windows-input-consumption-r7, baseabd5/c882. R6 source,
old reader fixtures, reports, final critic and actual replay prereg remain untouched.
Existing independent R6 critic will receive a new target after its R6 rejection;
no new/fresh thread, native run or actual replay is authorized by this plan.
Register before edits/tests. R6 latest supported false complete: joined expiry,
age0, deadline_remaining20000; both source predicate branches are false.

Bar is exact PeerLifecycle constants JOIN20000/IDLE30000/REJECT500 and functions
connected/admitted/active/reject/expired, plus synchronous Match pre-forget expiry
hook and observed wall/age/deadline projection. Reject flag is absent, so do not
assume every joined expiry requires idle30000. Preserve UNKNOWN for hidden rejected
versus unrejected alternatives. No packet identity, delay cause or native pass.

Model the feasible projected states at the expiry row: now=t, last_input=t-age,
deadline=t+remaining. An unrejected state has connect=deadline-JOIN, which cannot
be negative or later than last_input; unjoined also requires last_input=connect.
A rejected state has reject=deadline-REJECT between last_input and now, since
active cannot advance last_input after rejection. All require observed lifecycle
age>=0 and last_input>=0. Evaluate original expiry predicate for every feasible
hidden rejection state. No feasible/eligible state => INVALID; both eligible and
ineligible possible => UNKNOWN; all feasible states eligible => CONSISTENT for
this projected guard. This does not reconstruct all hidden callback history.

Generate independent concrete source-state histories with connected/admitted/
active/rejected events and selected boundary clocks; project only observed fields,
group feasible rejection alternatives, compare classification without deriving
expected outcomes from candidate. Explicit adversarial age/deadline/flag/generation/
ordering mutations, rejection500 and idle30000 equality, negative/missing age,
retired/reused identities and deferredUNKNOWN/laterINVALID precedence must run.
Retain current critic negative unchanged. Fixed old native logs remain unexecuted
until independent whole-source acceptance; no source score can substitute it.

Independent critic also confirms old maintained unbound peer_connected helper
age=-1/deadline=-1 is source-inconsistent: actual connected initializes age>=0 and
remaining=20000-age. Preserve original helper byte-exact in this component; new
positives use separately declared source-state construction. Do not impose all-row
lifecycle timing checks or relabel old schema controls as emitter-faithful. Broader
fixture/lifecycle consistency remains a separate registered obligation.

Change only reader expiry validation and new pure model/behavior tests initially.
Preserve existing55 method/100 assertion ASTs, packet model and all original game/
collector/CI/runtime/privacy/economy source; bind full union. Freeze only after
meaningful pure tests/old failure comparisons, then independent review/iteration.
