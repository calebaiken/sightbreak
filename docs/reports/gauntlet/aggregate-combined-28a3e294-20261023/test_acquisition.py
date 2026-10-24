"""Pure false-success controls. These tests launch no engine/helper/service."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


runner = module("run_aggregate")
archiver = module("archive_originals")


class Controls(unittest.TestCase):
    def test_exact_contract(self):
        repo = HERE.parents[3]
        value = runner.contract(repo)
        self.assertEqual(56, len(value["mandatory_godot"]))
        self.assertEqual(5, len(value["display_only_godot"]))
        groups = [r for r in value["python"] if r["source_test_methods"]]
        self.assertEqual([11, 7, 4, 15, 24, 5, 7, 4, 5, 15, 16, 8, 8], [r["source_test_methods"] for r in groups])

    def test_strict_stringnames(self):
        for text in ("Orphan StringName: Master (static: 0, total: 1)",
                     "StringName: 353 unclaimed string names at exit.",
                     "Orphan StringName: spaces and punctuation ! (static: 4, total: 5)\r\n"):
            with self.subTest(text=text):
                self.assertIsNotNone(runner.STRICT.search(text))

    def test_other_strict_failures(self):
        for text in ("SCRIPT ERROR: x", "ERROR: y", "Parse Error", "ObjectDB instances leaked at exit",
                     "Leaked instance: AudioStreamWAV", "Resources still in use at exit", "Traceback (most recent call last)",
                     "FAILED (errors=1)", "FAIL: fixture", "Ran 5 checks failures=1"):
            with self.subTest(text=text):
                self.assertIsNotNone(runner.STRICT.search(text))

    def test_clean_controls(self):
        for text in ("StringName: 0 unclaimed string names at exit.", "checks=590 failures=0", "OK (skipped=3)", "EXPECTED protocol rejection"):
            self.assertIsNone(runner.STRICT.search(text))

    def test_escaped_and_adopted_descendants(self):
        rows = {1: {"pid": 1, "ppid": 9, "pgid": 1, "sid": 1, "start_ticks": 10, "argv": "bash", "comm": "bash"},
                2: {"pid": 2, "ppid": 1, "pgid": 2, "sid": 2, "start_ticks": 20, "argv": "child", "comm": "python"},
                3: {"pid": 3, "ppid": 9, "pgid": 3, "sid": 3, "start_ticks": 30, "argv": "orphan", "comm": "python"},
                4: {"pid": 4, "ppid": 99, "pgid": 4, "sid": 4, "start_ticks": 40, "argv": "unrelated", "comm": "python"}}
        found = runner.identify_owned(rows, Path("/abs/frozen"), 9, 1, {})
        self.assertEqual({1, 2, 3}, set(found))

    def test_pid_reuse_does_not_inherit_ownership(self):
        row = {"pid": 3, "ppid": 99, "pgid": 3, "sid": 3, "start_ticks": 31, "argv": "unrelated", "comm": "python"}
        seen = {(3, 30): dict(row, start_ticks=30)}
        self.assertEqual({}, runner.identify_owned({3: row}, Path("/abs/frozen"), 9, 1, seen))

    def test_archive_preserves_failed_and_late_outer_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = root / "run"; run.mkdir()
            (run / "result.json").write_text('{"passed":false}')
            (run / "outer-exit.json").write_text('{"exit_code":1}')
            receipt = archiver.archive(run, root / "repo", root / "archive")
            self.assertTrue(receipt["verified"])
            self.assertEqual(2, receipt["original_files"])
            self.assertTrue((run / "outer-exit.json").exists())
            with self.assertRaises(FileExistsError):
                archiver.archive(run, root / "repo", root / "archive")

    def test_archive_rejects_postaudit_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); run = root / "run"; run.mkdir()
            log = root / "original.log"; log.write_text("clean")
            (run / "log-audit.json").write_text(json.dumps({"network_dirs": [], "files": [{"path": str(log), "bytes": 5, "sha256": "wrong"}]}))
            with self.assertRaisesRegex(RuntimeError, "Late log mutation"):
                archiver.archive(run, root / "repo", root / "archive")

    def test_archive_scans_new_private_log_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); run = root / "run"; run.mkdir()
            (run / "result.json").write_text('{"passed":true}')
            private = root / "repo/.local/aggregate-state-r1/data"; private.mkdir(parents=True)
            (private / "late.log").write_text("StringName: 353 unclaimed string names at exit.\n")
            receipt = archiver.archive(run, root / "repo", root / "archive")
            self.assertFalse(receipt["strict_clean"])
            self.assertEqual(1, receipt["scanned_logs"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
