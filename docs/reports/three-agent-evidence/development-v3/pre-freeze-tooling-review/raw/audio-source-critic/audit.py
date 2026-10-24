"""Read-only audio critic driver. Runs only serial Python/mock tests, never a native tool."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

EVIDENCE = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
EXACT_PYTHON = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe")


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def run_receipted(label, command, *, env=None):
    started = time.monotonic()
    with (EVIDENCE / (label + ".stdout.txt")).open("xb") as stdout:
        with (EVIDENCE / (label + ".stderr.txt")).open("xb") as stderr:
            completed = subprocess.run(command, cwd=REPO, env=env, stdout=stdout, stderr=stderr,
                                       timeout=180, check=False)
    write_json(EVIDENCE / (label + ".command.json"), {
        "command": list(map(str, command)), "cwd": str(REPO),
        "utc": datetime.now(timezone.utc).isoformat(), "exit": completed.returncode,
        "seconds": round(time.monotonic() - started, 3),
        "environment_overrides": {key: env[key] for key in (
            "NEGATIVE_AUDIO_TEST_OUT", "PYTHONDONTWRITEBYTECODE", "TEMP", "TMP") if env and key in env},
        "stdout_sha256": hashlib.sha256((EVIDENCE / (label + ".stdout.txt")).read_bytes()).hexdigest(),
        "stderr_sha256": hashlib.sha256((EVIDENCE / (label + ".stderr.txt")).read_bytes()).hexdigest(),
    })
    print(label, "exit", completed.returncode, flush=True)
    return completed.returncode


def ast_inventory():
    old_text = (EVIDENCE / "git-head-controls.stdout.txt").read_text(encoding="utf-8-sig")
    now_text = (EVIDENCE / "reviewed-source/scripts__reload_negative_controls.py").read_text(encoding="utf-8-sig")
    def assignments(text):
        return {target.id: node.value for node in ast.parse(text).body if isinstance(node, ast.Assign)
                for target in node.targets if isinstance(target, ast.Name)}
    old, now = assignments(old_text), assignments(now_text)
    names = ("SEQ", "ART", "AUD", "CAP", "CAP_CANCEL", "VIS", "VIS_REDUCED", "DISC", "LIGHT")
    constants = {name: ast.dump(old[name]) == ast.dump(now[name]) for name in names}
    def audio_entries(tree):
        return {node.elts[0].value: node for node in tree["SOURCE"].elts
                if node.elts[0].value in ("A5", "A6", "A7")}
    old_audio, now_audio = audio_entries(old), audio_entries(now)
    entries = {cid: {"identical_ast": ast.dump(old_audio[cid]) == ast.dump(now_audio[cid]),
                     "original": ast.get_source_segment(old_text, old_audio[cid]),
                     "reviewed": ast.get_source_segment(now_text, now_audio[cid])} for cid in old_audio}
    old_capture = (EVIDENCE / "git-head-capture.stdout.txt").read_text(encoding="utf-8-sig")
    now_capture = (EVIDENCE / "reviewed-source/game__tests__reload_audio_capture.gd").read_text(encoding="utf-8-sig")
    import re
    thresholds = {}
    for name in ("ONSET_LEVEL", "TOLERANCE_MS", "SILENT", "CANCEL_AT", "MAX_LATENCY"):
        pattern = r"^const " + name + r" := ([0-9.]+)"
        first, second = re.search(pattern, old_capture, re.M).group(1), re.search(pattern, now_capture, re.M).group(1)
        thresholds[name] = {"original": first, "reviewed": second, "identical": first == second}
    baseline = [node.id for node in now["BASELINE_TESTS"].elts]
    write_json(EVIDENCE / "original-contract-comparison.json", {
        "original_reference": "git HEAD (local pre-working-tree implementation)",
        "baseline_command_constants_identical": constants, "baseline_groups": baseline,
        "audio_control_tuples": entries, "capture_thresholds": thresholds,
        "original_inline_bounds_preserved": {
            fragment: fragment in old_capture and fragment in now_capture for fragment in (
                "int(0.06 * rate)", "int(0.40 * rate)", "maxf(0.10 * peak, 0.004)",
                "f.peak > 0.02", "typical > -45.0", "int(0.080 * rate)",
                "int(0.060 * rate)", "early < SILENT", "loud_after < SILENT")},
    })
    assert all(constants.values()) and all(row["identical_ast"] for row in entries.values())
    assert baseline == list(names)
    assert all(row["identical"] for row in thresholds.values())


def independent_probes():
    sys.path.insert(0, str(REPO / "scripts"))
    import reload_negative_controls as controls
    import test_reload_negative_controls as maintained

    class IndependentHarness(maintained.HarnessTests):
        """Uses the guarded disposable fixture; no actual repository mutation/process."""

        def id(self):
            return type(self).__name__ + "." + self._testMethodName

        def test_missing_receipt_beside_complete_failure_cannot_be_caught(self):
            self.inject = lambda role, cid, command: {"receipt": None} if cid == "A5" else {}
            self.assertEqual(self.call_main(), 1)
            self.assertEqual(self.result()["controls"], [["A5", "crashed"], ["A6", "caught"], ["A7", "caught"]])
            self.assertEqual(len(self.events), 13)
            self.assert_restored()

        def test_actual_cancel_summary_and_unrelated_native_error_are_broken(self):
            self.inject = lambda role, cid, command: {
                "output": "ERROR: Cannot open file res://missing.wav\n   at: open (core/io/file_access.cpp:100)\n"
                    + maintained.summary(checks=11, failures=1, scenario="cancel")
            } if cid == "A6" else {}
            self.assertEqual(self.call_main(), 1)
            self.assertEqual(self.result()["controls"][1], ["A6", "crashed"])
            self.assert_restored()

        def test_each_zero_length_capture_artifact_is_rejected(self):
            for filename in ("mix_reload.wav", "voices_reload.csv", "report_reload.txt"):
                original_process = self.fake_process
                def zero_one(command, *, result_path, **kwargs):
                    code = original_process(command, result_path=result_path, **kwargs)
                    if "-A7-" in result_path.parent.name:
                        (result_path.parent / "capture" / filename).write_bytes(b"")
                    return code
                self.process.side_effect = zero_one
                self.assertEqual(self.call_main(baseline=False), 1)
                self.assertEqual(self.result()["controls"][2], ["A7", "crashed"])
                self.assert_restored()

        def test_partial_multi_file_write_exception_restores_every_original_byte(self):
            actor, audio = Path(controls.ACTOR), Path(controls.AUDIO)
            actor_edit = next(row for row in controls.SOURCE if row[0] == "A6")[2][0]
            audio_edit = next(row for row in controls.SOURCE if row[0] == "A5")[2][0]
            self.patched("SOURCE", [("A6", "synthetic two-file write fault", [actor_edit, audio_edit], None, [controls.CAP_CANCEL])])
            original_write = Path.write_bytes
            seen_mutated_actor = []
            def write_or_fail(path, data):
                if path == audio and data != self.originals[audio]:
                    seen_mutated_actor.append(actor.read_bytes() != self.originals[actor])
                    raise OSError("isolated fixture: second source write denied")
                return original_write(path, data)
            with patch.object(Path, "write_bytes", write_or_fail):
                self.assertEqual(self.call_main(["--only", "A6"], baseline=False), 2)
            self.assertEqual(seen_mutated_actor, [True])
            self.process.assert_not_called()
            self.assertEqual(self.result()["exit"], 2)
            self.assert_restored()

        def test_system_exit_after_mutation_retains_attempt_and_restores_bytes(self):
            self.inject = lambda role, cid, command: {"raise": SystemExit(17)} if cid == "A7" else {}
            with self.assertRaises(SystemExit) as caught:
                self.call_main(baseline=False)
            self.assertEqual(caught.exception.code, 17)
            self.assertEqual(self.result()["exit"], 2)
            self.assertTrue(next(self.out.glob("*-A7-*/attempt.json")).is_file())
            self.assert_restored()

        def prepare_mock_clip(self):
            self.patched("SOURCE", [])
            self.patched("CLIPS", [("N16", "synthetic clip, no Blender", {}, [controls.VIS])])
            def build_fixture(env, output, runner, control):
                (Path(output) / "relay_ar_arms.glb").write_bytes(b"synthetic mutant GLB\x00\xff")
                return True
            self.patched("build", side_effect=build_fixture)

        def test_failed_mock_import_is_not_caught_and_restores_glb_bytes(self):
            self.prepare_mock_clip()
            importer = self.patched("import_assets", return_value=False)
            self.assertEqual(self.call_main(["--only", "N16"], baseline=False), 1)
            self.assertEqual(self.result()["controls"], [["N16", "crashed"]])
            self.assertEqual([call.kwargs["role"] for call in importer.call_args_list], ["mutant", "restore"])
            self.process.assert_not_called()
            self.assert_restored()

        def test_interrupted_mock_import_restores_source_and_glb_bytes(self):
            self.prepare_mock_clip()
            self.patched("import_assets", side_effect=KeyboardInterrupt("fixture import interrupted; no engine"))
            with self.assertRaises(KeyboardInterrupt):
                self.call_main(["--only", "N16"], baseline=False)
            self.assertEqual(self.result()["exit"], 2)
            self.process.assert_not_called()
            self.assert_restored()

    class IndependentClassifications(maintained.PureCase):
        def id(self):
            return type(self).__name__ + "." + self._testMethodName

        def test_actual_capture_failure_report_contract(self):
            message = "nothing is audible on any reload voice before the first event (peak 0.03000)"
            text = "ERROR: " + message + "\n   at: push_error (core/variant/variant_utility.cpp:1024)\n"
            text += "FAIL " + message + "\n" + maintained.summary(checks=14, failures=1)
            self.judged(text, 1, "FAILED", fields={"scenario": "reload", "reduced": "false"})

        def test_missing_native_completion_or_shutdown_fault_cannot_be_caught(self):
            complete = maintained.summary(checks=11, failures=1, scenario="cancel")
            for text, code, errors in (
                ("FAIL intended detector\n", 1, ()),
                (complete, 3221225477, ()),
                (complete + "WARNING: ObjectDB instances leaked at exit\n", 1, ()),
                (complete + "ERROR: 2 resources still in use at exit\n", 1, ()),
                (complete, 1, ("descendants survived command exit",)),
            ):
                state, details, parsed = controls.classify(text, code, "RELOAD_AUDIO_CAPTURE",
                    {"scenario": "cancel", "reduced": "false"}, errors)
                self.judgments.append({"output": text, "exit": code, "process_errors": errors,
                                       "state": state, "errors": details, "summary": parsed})
                self.assertNotEqual(state, "FAILED")
                self.assertNotEqual(controls.control_state([("audio capture (cancel)", state, details)]), "caught")

    suite = unittest.TestSuite()
    for cls in (IndependentHarness, IndependentClassifications):
        for name in sorted(cls.__dict__):
            if name.startswith("test_"):
                suite.addTest(cls(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    write_json(EVIDENCE / (os.environ.get("AUDIO_CRITIC_PROBE_LABEL", "independent-probes") + ".result.json"), {
        "tests": result.testsRun, "errors": len(result.errors), "failures": len(result.failures),
        "successful": result.wasSuccessful(), "native_executed": False,
        "limitation": "Synthetic fixtures, mocked process/import/build functions; no native behavior acceptance.",
    })
    return 0 if result.wasSuccessful() else 1


def main():
    assert Path(sys.executable).samefile(EXACT_PYTHON), sys.executable
    if sys.argv[1:] == ["--probes"]:
        return independent_probes()
    scratch = EVIDENCE / "scratch"
    scratch.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=str(scratch), TMP=str(scratch))
    run_receipted("git-head", ["git", "--no-optional-locks", "rev-parse", "HEAD"])
    run_receipted("git-scoped-status", ["git", "--no-optional-locks", "status", "--short", "--",
        "scripts/reload_negative_controls.py", "scripts/test_reload_negative_controls.py", ".github/workflows/v3-development.yml"])
    run_receipted("git-head-controls", ["git", "--no-optional-locks", "show", "HEAD:scripts/reload_negative_controls.py"])
    run_receipted("git-head-capture", ["git", "--no-optional-locks", "show", "HEAD:game/tests/reload_audio_capture.gd"])
    ast_inventory()
    env["NEGATIVE_AUDIO_TEST_OUT"] = str(EVIDENCE / "maintained-unit-fixtures")
    maintained_exit = run_receipted("maintained-unit-tests", [str(EXACT_PYTHON), "-B", "-m", "unittest", "discover",
        "-s", "scripts", "-p", "test_reload_negative_controls.py", "-v"], env=env)
    env["NEGATIVE_AUDIO_TEST_OUT"] = str(EVIDENCE / "independent-probe-fixtures")
    probe_exit = run_receipted("independent-probes", [str(EXACT_PYTHON), "-B", str(Path(__file__).resolve()), "--probes"], env=env)
    before = json.loads((EVIDENCE / "source-hashes-before.json").read_text(encoding="utf-8"))
    after = [{"path": row["path"], "bytes": (REPO / row["path"]).stat().st_size,
              "sha256": hashlib.sha256((REPO / row["path"]).read_bytes()).hexdigest()} for row in before["files"]]
    write_json(EVIDENCE / "source-hashes-after.json", {
        "files": after, "unchanged": after == before["files"],
        "note": "Read-only audit; no native engine/import/network/DB/campaign/export/GitHub actions.",
    })
    write_json(EVIDENCE / "audit.result.json", {
        "executable": sys.executable, "maintained_test_exit": maintained_exit,
        "independent_probe_exit": probe_exit, "reviewed_source_unchanged": after == before["files"],
        "native_executed": False,
    })
    return 0 if maintained_exit == probe_exit == 0 and after == before["files"] else 1


if __name__ == "__main__":
    sys.exit(main())
