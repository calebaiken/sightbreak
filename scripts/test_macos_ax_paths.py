#!/usr/bin/env python3
"""Replay pure AX controls under a Linux-reproducible macOS-style temp alias."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from macos_ordinary_input import no_symlinks
from probe_macos_input import NativePrerequisiteBlocked


ROOT = Path(__file__).resolve().parents[1]


class AXTemporaryRootControls(unittest.TestCase):
    def test_production_still_rejects_alias_while_test_owned_root_can_be_canonicalized(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary).resolve()
            real=base/'real';real.mkdir()
            alias=base/'alias';alias.symlink_to(real,target_is_directory=True)
            with self.assertRaises(NativePrerequisiteBlocked):no_symlinks(alias/'evidence')
            no_symlinks((alias/'evidence').resolve())

    def test_new_full_pure_suites_pass_with_aliased_tempdir_without_changing_runtime_guards(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary).resolve()
            real=base/'real';real.mkdir()
            alias=base/'alias';alias.symlink_to(real,target_is_directory=True)
            environment=dict(os.environ,TMPDIR=str(alias),TEMP=str(alias),TMP=str(alias))
            for name in ('test_macos_ax_read_only.py','test_macos_ax_controller.py'):
                with self.subTest(name=name):
                    result=subprocess.run([sys.executable,str(ROOT/'scripts'/name),'-v'],
                        cwd=ROOT,env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
                    self.assertEqual(result.returncode,0,result.stdout)


if __name__=='__main__':unittest.main()
