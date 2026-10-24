#!/usr/bin/env python3
"""Exercise frozen-source receipts against real isolated Git repositories."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import build_manifest
from godot_process import source_failures, source_snapshot


class RealGitSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='sightbreak-source-identity-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'checkout with spaces'
        self.root.mkdir()
        self.git('init', '--quiet')
        self.git('config', 'user.name', 'Isolated Source Control')
        self.git('config', 'user.email', 'source-control@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.git('config', 'core.preloadIndex', 'false')
        self.git('config', 'index.threads', '1')
        for relative, content in {
            '.gitignore': 'builds/\ngame/.godot/\n',
            'game/main.gd': '# shipping source\n',
            'game/tests/probe.gd': '# validation source\n',
            'scripts/controller.py': '# export controller\n',
            '.github/workflows/validation.yml': 'name: isolated fixture\n',
            'docs/progress.md': '# frozen progress\n',
        }.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
        self.git('add', '.')
        self.git('commit', '--quiet', '-m', 'Isolated baseline')

    def git(self, *arguments):
        return subprocess.check_output(['git', *arguments], cwd=self.root,
                                       text=True, encoding='utf-8', errors='replace').strip()

    def receipt(self):
        with patch.object(build_manifest, 'ROOT', self.root):
            return build_manifest.source()

    def test_clean_receipt_binds_actual_git_commit_tree_and_validation_bytes(self):
        receipt = self.receipt()
        self.assertEqual(receipt['source_commit'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(receipt['source_game_tree'], self.git('rev-parse', 'HEAD:game'))
        self.assertEqual(receipt['source_validation_sha256'], source_snapshot(root=self.root)['content_sha256'])
        self.assertFalse(receipt['source_dirty'])
        build_manifest.require_clean(receipt)

    def test_staged_controller_edit_is_dirty_even_when_worktree_matches_index(self):
        path = self.root / 'scripts/controller.py'
        before = self.receipt()
        path.write_text('# changed controller\n', encoding='utf-8')
        self.git('add', 'scripts/controller.py')
        self.assertEqual(self.git('diff', '--name-only'), '')
        after = self.receipt()
        self.assertNotEqual(before['source_validation_sha256'], after['source_validation_sha256'])
        self.assertTrue(after['source_dirty'])
        self.assertFalse(build_manifest.same_source(before, after))
        with self.assertRaises(SystemExit):
            build_manifest.require_clean(after)

    def test_untracked_probe_is_bound_and_untracked_documentation_is_not_clean(self):
        before = source_snapshot(root=self.root)
        (self.root / 'game/tests/new_probe.gd').write_text('# untracked control\n', encoding='utf-8')
        probe = source_snapshot(root=self.root)
        self.assertNotEqual(before['content_sha256'], probe['content_sha256'])
        self.assertIn('?? game/tests/new_probe.gd', probe['status'])
        (self.root / 'game/tests/new_probe.gd').unlink()
        (self.root / 'docs/untracked.md').write_text('# untracked document\n', encoding='utf-8')
        document = source_snapshot(root=self.root)
        self.assertEqual(before['content_sha256'], document['content_sha256'])
        self.assertTrue(document['dirty'])
        self.assertIn('?? docs/untracked.md', document['status'])
        self.assertTrue(source_failures(before, document))

    def test_second_dirty_edit_changes_receipt_even_with_identical_status(self):
        path = self.root / 'game/tests/probe.gd'
        path.write_text('# first dirty state\n', encoding='utf-8')
        first = source_snapshot(root=self.root)
        path.write_text('# second dirty state\n', encoding='utf-8')
        second = source_snapshot(root=self.root)
        self.assertEqual(first['status'], second['status'])
        self.assertNotEqual(first['content_sha256'], second['content_sha256'])
        self.assertIn('source changed during run', source_failures(first, second))

    def test_ignored_import_and_evidence_files_do_not_taint_source(self):
        before = self.receipt()
        for relative in ('game/.godot/import-cache.bin', 'builds/attempt/raw.log'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'ignored generated data')
        self.assertEqual(self.receipt(), before)

    def test_different_commit_with_identical_game_and_tooling_bytes_is_rejected(self):
        before = self.receipt()
        self.git('commit', '--quiet', '--allow-empty', '-m', 'Different exporter revision')
        after = self.receipt()
        self.assertEqual(before['source_game_tree'], after['source_game_tree'])
        self.assertEqual(before['source_content_sha256'], after['source_content_sha256'])
        self.assertEqual(before['source_validation_sha256'], after['source_validation_sha256'])
        self.assertFalse(build_manifest.same_source(before, after))

    def test_deleted_tracked_file_is_dirty_and_changes_validation_digest(self):
        before = self.receipt()
        (self.root / 'game/tests/probe.gd').unlink()
        after = self.receipt()
        self.assertTrue(after['source_dirty'])
        self.assertNotEqual(before['source_validation_sha256'], after['source_validation_sha256'])


if __name__ == '__main__':
    unittest.main()
