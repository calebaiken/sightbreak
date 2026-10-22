"""Use the existing isolated runner for three additional maintained source tests.

The CLI's ten-suite allowlist is extended only in this driver process. Native
namespace protection, 120-second suite timeout, source guards and cleanup are
unchanged. No source file in scripts/ or game/ is modified by the driver.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_native_regressions as native

additional = ("touch", "hud_overflow", "input_lifecycle")
native.SUITES = (*native.SUITES, *additional)
with native.NativeSceneSuites("builds/feed-revision-regressions-r2") as runner:
    for suite in ("touch", "hud_overflow", "hud_objective_hint", "input_lifecycle"):
        runner.run(suite)
print("FOCUSED_HUD_REGRESSIONS passed=" + str(runner.report["passed"]))
