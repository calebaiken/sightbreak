"""Read-only, synthetic CPython follow-up. Never invokes a native engine/export.

The original probe is loaded unchanged, then its output root is redirected.
Corrected controller modules are imported first from the captured source.
"""
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import hashlib
import json
import os
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
BEFORE = ROOT.parent / "critic-current-20261019T191820649592Z"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path[:0] = [str(OUT / "source/scripts"), str(ROOT / "scripts")]
import export_flow as flow
import verify_integration_export as integration
import verify_offline_export as offline

spec = spec_from_file_location("unchanged_original_probe", BEFORE / "control_export_boundaries.py")
original = module_from_spec(spec)
spec.loader.exec_module(original)
original.OUT = OUT
sys.path[:0] = [str(OUT / "source/scripts"), str(ROOT / "scripts")]


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def original_hashes():
    paths = ["control_export_boundaries.py", "export-mutation-control/reproduction.json",
             "export-mutation-control/synthetic-controller-output/results.json",
             "offline-watchdog-control/reproduction.json", "offline-watchdog-control/at-watchdog-overrun.json"]
    return [{"path": str(BEFORE / rel), "sha256": hashlib.sha256((BEFORE / rel).read_bytes()).hexdigest()} for rel in paths]


def units():
    temp = OUT / "unit-temp"
    temp.mkdir()
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp),
               PYTHONPATH=os.pathsep.join([str(OUT / "source/scripts"), str(ROOT / "scripts")]))
    with (OUT / "unittests.stdout.txt").open("xb") as stdout, (OUT / "unittests.stderr.txt").open("xb") as stderr:
        result = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_export_flow", "test_export_ui"],
                                cwd=OUT / "source/scripts", env=env, stdout=stdout, stderr=stderr)
    save(OUT / "unittests.exit.json", {"exit": result.returncode})
    print("Scoped unit tests exit:", result.returncode, flush=True)


def integration_replacement():
    caught = None
    with (OUT / "integration-replacement.stdout.txt").open("x") as stdout, \
            (OUT / "integration-replacement.stderr.txt").open("x") as stderr, \
            redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            original.mutate_control()
        except Exception as error:
            caught = type(error).__name__ + ": " + str(error)
    case = OUT / "export-mutation-control"
    result = json.loads((case / "synthetic-controller-output/results.json").read_text())
    observed = {"synthetic_control_not_native_evidence": True, "probe_adjustment": "Unmodified original mutation function; corrected modules preloaded and OUT redirected.",
                "caught": caught, "controller_passed": result["passed"],
                "original_false_pass_reproduced": result["passed"],
                "correctly_rejected": result["passed"] is False and caught is not None}
    save(case / "after-observation.json", observed)
    print(json.dumps(observed), flush=True)


def offline_replacement():
    case = OUT / "offline-replacement-control"
    case.mkdir()
    root, executable = original.create_export(case)
    evidence = case / "synthetic-controller-output"
    fake_pil = ModuleType("PIL")
    fake_pil.Image = SimpleNamespace(open=lambda path: original.FixtureCrop())
    texts = iter(["100 HEALTH", "14/60", "100 HEALTH", "15/59"])
    caught = None
    with (case / "controller.stdout.txt").open("x") as stdout, (case / "controller.stderr.txt").open("x") as stderr, \
            redirect_stdout(stdout), redirect_stderr(stderr), ExitStack() as stack:
        original.fixture_boundaries(stack, offline, case, root, executable, mutate=True)
        stack.enter_context(patch.dict(sys.modules, {"PIL": fake_pil}))
        stack.enter_context(patch.object(offline, "ocr_text", lambda *args, **kwargs: next(texts)))
        stack.enter_context(patch.object(sys, "argv", ["verify_offline_export.py", "--output", str(evidence),
                                                      "--xvfb", "SYNTHETIC-XVFB-NOT-EXECUTED", "--display", ":61973",
                                                      "--tesseract", "SYNTHETIC-OCR-NOT-EXECUTED", "--timeout", "10"]))
        try:
            offline.main()
        except Exception as error:
            caught = type(error).__name__ + ": " + str(error)
    result = json.loads((evidence / "results.json").read_text())
    observed = {"synthetic_control_not_native_evidence": True, "probe_adjustment": "Original fixtures reused for offline main; valid HUD OCR text mocked to reach final byte check.",
                "caught": caught, "controller_passed": result["passed"],
                "correctly_rejected": result["passed"] is False and caught is not None}
    save(case / "after-observation.json", observed)
    print(json.dumps(observed), flush=True)


def direct_ocr():
    case = OUT / "stalled-ocr-control"
    case.mkdir()
    started = time.monotonic()
    caught = None
    try:
        offline.ocr_text([sys.executable, "-B", "-c", "import sys,time; print('partial OCR stdout',flush=True); print('partial OCR stderr',file=sys.stderr,flush=True); time.sleep(30)"],
                         b"SYNTHETIC-NOT-IMAGE", started + .25, case / "ocr")
    except Exception as error:
        caught = type(error).__name__ + ": " + str(error)
    elapsed = time.monotonic() - started
    observed = {"synthetic_control_not_native_evidence": True,
                "probe_adjustment": "Original sleeping CPython OCR child now called through actual ocr_text, not removed check_output boundary.",
                "caught": caught, "seconds": elapsed,
                "stdout": (case / "ocr.stdout.txt").read_text(), "stderr": (case / "ocr.stderr.txt").read_text(),
                "correctly_bounded": caught is not None and caught.startswith("TimeoutError") and elapsed < 4}
    save(case / "after-observation.json", observed)
    print(json.dumps(observed), flush=True)


def supervisor_descendant():
    case = OUT / "supervisor-descendant-control"
    case.mkdir()
    worker = case / "synthetic-worker.py"
    evidence = case / "evidence"
    child_program = (
        "from pathlib import Path; import json,os,time; "
        f"Path({str(case / 'child-started.json')!r}).write_text(json.dumps({{'pid':os.getpid()}})); "
        "time.sleep(1.5); print('ERROR: escaped exported-flow descendant',flush=True); "
        f"Path({str(case / 'child-finished.json')!r}).write_text('finished'); raise SystemExit(7)"
    )
    worker.write_text("from pathlib import Path\nimport json,subprocess,sys,time\n"
                      "out=Path(sys.argv[sys.argv.index('--output')+1])\n"
                      f"child=subprocess.Popen([sys.executable,'-B','-c',{child_program!r}])\n"
                      f"marker=Path({str(case / 'child-started.json')!r})\n"
                      "while not marker.exists(): time.sleep(.005)\n"
                      "print('synthetic worker exiting zero',flush=True)\n"
                      "(out/'results.json').write_text(json.dumps({'passed':True,'synthetic_control_not_native_evidence':True}))\n")
    with (case / "supervisor.stdout.txt").open("x") as stdout, redirect_stdout(stdout):
        code = flow.supervise(worker, ["--output", str(evidence)], evidence, 5)
    early_result = json.loads((evidence / "results.json").read_text())
    early = {"supervisor_exit": code, "result": early_result,
             "child_finished_at_return": (case / "child-finished.json").exists(),
             "log_at_return": (evidence / "watchdog.log").read_text()}
    save(case / "at-return.json", early)
    time.sleep(2)
    late_log = (evidence / "watchdog.log").read_text()
    observed = {"synthetic_control_not_native_evidence": True, **early,
                "child_finished_later": (case / "child-finished.json").exists(),
                "log_after_child": late_log,
                "false_pass_reproduced": code == 0 and early_result.get("passed") is True and "ERROR:" in late_log}
    save(case / "after-observation.json", observed)
    print(json.dumps(observed), flush=True)


if __name__ == "__main__":
    save(OUT / "original-controls-hashes-before.json", original_hashes())
    units()
    integration_replacement()
    offline_replacement()
    direct_ocr()
    supervisor_descendant()
    save(OUT / "original-controls-hashes-after.json", original_hashes())
