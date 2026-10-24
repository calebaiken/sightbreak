# Bounded V2 clock/helper pre-edit adjudication

Existing sole critic reused, independent of the builder. Target proposal commit
`7686aac41440ece6bf84369663c27dc1790008fc`, report prefix
`docs/reports/gauntlet/windows-shutdown-evidence-completeness-r2-20261024/`:
`CONSTRUCTION_V2_MODEL_BEFORE_COMPILER.md`, `CLOCK_SEAM_V2_PROPOSAL.py`, and
`CLOCK_HELPER_V2_PROPOSAL.patch`. Draft SHA256 must equal
`9bcd688d6ed1fa774ec3e9006e7eda9b31d78321d2dd303aa60ec40a4efbac61`.
Read immutable blobs only; do not inspect an unsealed production validator.

Scope is the proposed pure clock architecture and five precise helper clock
sites. Original 0f/67a/7f/63021 and rejected compiler remain immutable. The prior
2904 permits do not approve a compiler or a complete source-positive history.
Keep original old28 methods/assertions/Owner, fault injection, identity reads and
their ordering exact except a separately justified minimal clock seam. No broad
normalization, expectation changes or synthetic advance may conceal a failure.

Require one shared integer-nanosecond monotonic clock with explicit supported
advances and pure reads. Assess wall-clock units and source ordering, finite
typed boundaries, source/global clock patch lifetime and restoration, nested
helpers/callbacks/old-suite schedules, failure/partial paths and fresh trial
independence. Inputs/outputs for future source operations must be staged so a
launch/capture failure cannot have preexisting success captures or final traces.
Conditional route/settle actions and persistent held keys still need the source
requirements from 2904; no clock design can stand in for missing compiler data.

Begin with static inspection. If controlled draft execution is needed, first
commit the concrete cases/oracles/effect guards; execute Python/static only on
CPU4, retain every result, and never call a driver/helper/native process, API,
proc/signal, CI, SDK or capability probe. Do not claim a model score from a seam
test. Return a bounded PERMIT or specific REVISE with remaining limitations.
