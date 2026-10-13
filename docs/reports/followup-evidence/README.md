# Independent follow-up command evidence

These are unedited stdout/stderr captures from independent review on 2026-10-13 UTC. No credential values are present. See [QA review](../QA.md) for commands, scope and measured limitations.

- `aggregate.txt`: intermediate complete validation at `.local/validation/run-87kywe/`.
- `aggregate-final.txt`: final complete validation at `.local/validation/run-sbvU2f/`, after all gameplay/UI/surface changes; 267 counted native checks, PostgreSQL 39, packaging 8.
- `artifact-verification.txt`: independent actual Linux/APK/iOS artifact and source provenance verification; all five delivery checksums were separately recomputed and matched.
- `native-render.txt`: independent real demo and five rendered scene cycles, before the later surface texture pass.
- `native-render-final.txt`: final textured-game native demo and scene-cycle rerun; clean exit and exact texture plateau.
- `landscape-overlap.txt`, `touch-final.txt`, `main-final.txt`: focused final HUD overlap/input reruns.
- `standalone-sky-immediate.txt`: intentionally failing engine diagnostic, expected two texture leaks.
- `standalone-sky-wait.txt`: otherwise identical clean first-frame-retirement control.
- `account-network.txt`, `bridge-transport.txt`: actual account identity/replay/reclaim and exact HTTP fault-injection behavior.
- `native-economy.txt`: independent actual native HTTP/PostgreSQL case, marketplace and trade operations using isolated fictional seed balances; fixture removed afterward.
- `reward-fixture.txt`: actual native HTTP reward settlement for synthetic ten-account duration/activity fixture; not human gameplay.
- `actor-surface.txt`: later 51-check actor/arena rerun after surface work.

A successful process is accepted only with the reported assertions and no unexpected logged script/renderer errors. The intentional standalone failure is diagnostic evidence, not a passing release test.
