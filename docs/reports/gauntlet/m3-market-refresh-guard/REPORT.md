# Market final refresh guard

Source baseline: `ad6cdc20db2a2f3ac179ba3cf3bed502620b6171`.
Own branch: `codex/m3-market-refresh-guard-20261023-0322`.
Criteria committed before implementation on 2026-10-23.

The comparison bar is the fetched baseline runner, its pure guard suite and the
accepted market runtime at `882931dd`. A sibling store investigation reproduced
a source hole: login reads survive when final replay succeeds and its refresh
fails, so equality against a phase dictionary can accept stale values. The
accepted market timeline has post-response reads at rows 68 and 69 after marker
67. This change must preserve that evidence and its original source identity.

Required behavior:
1. Final success requires successful GET /me and GET /inventory observations on
   the original proxy and final_recovery phase, strictly after the third market
   response was forwarded and before final native completion.
2. Compare the native result to those selected fresh observations before any
   final SQL snapshot, observer handoff, or success status.
3. Reject absent, failed, stale, wrong-phase and wrong-origin observations.
   Capturing request phase and serializing response publication must prevent
   concurrent proxy threads from reclassifying old requests as fresh.
4. A pure full Run.execute regression must reproduce the baseline false
   acceptance with stale login values and a failed post-replay refresh. Every
   real service, subprocess, network and database entrypoint must be forbidden.
5. Pure tests must accept the exact retained market timeline and exercise
   concurrent publication ordering. Original 240-second work deadline, cleanup,
   ownership, privacy, authoritative economy and import behavior remain intact.

Scope is test tooling, pure regressions, this evidence and a narrowly scoped
stdlib-only pull-request CI workflow if the local filesystem remains unavailable.
No game, backend, production service, original raw archive or accepted report
changes. No merge. New native/runtime or whole-gate acceptance is not implied.
Independent criticism is required after the candidate is frozen.

Execution and independent verdict are pending.
