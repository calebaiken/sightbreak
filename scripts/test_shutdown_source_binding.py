"""Physical source identity controls using owned temporary Git repositories."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import shutdown_study_retention as retention


class PhysicalSourceControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.git('init','-q')
        self.git('config','core.autocrlf','false')
        self.git('config','core.filemode','true')
        self.files={p:b'fixed source\n' for p in retention.MODEL_PATHS}
        self.files.update({'runtime/unlisted.py':b'original runtime\n',
                           'runtime/source \u03b1.gd':b'original unicode path\n'})
        for name,data in self.files.items():
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(0o644)
        self.git('add','.')
        self.git('-c','user.name=Source Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixed source fixture')
        self.commit=self.git('rev-parse','HEAD').decode().strip()

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,stderr=subprocess.PIPE)

    def test_clean_complete_checkout_binds_every_physical_path(self):
        result=retention.source_binding(self.commit,self.root)
        self.assertEqual(set(result['physical_sources']),set(self.files))
        self.assertEqual(result['non_doc_paths'],len(self.files))
        for name,data in self.files.items():
            record=result['physical_sources'][name]
            self.assertEqual(record['sha256'],retention.sha(data))
            self.assertEqual(record['canonical_sha256'],retention.sha(data))

    def test_hidden_model_and_non_model_changes_never_inherit_git_identity(self):
        for flag in ('--assume-unchanged','--skip-worktree'):
            for name in ('scripts/shutdown_study_retention.py','runtime/unlisted.py'):
                with self.subTest(flag=flag,name=name):
                    path=self.root/name
                    self.git('update-index',flag,name);path.write_bytes(b'changed physical source\n')
                    self.assertEqual(self.git('status','--porcelain','--untracked-files=all'),b'')
                    with self.assertRaisesRegex(ValueError,'physical source bytes differ'):
                        retention.source_binding(self.commit,self.root)
                    path.write_bytes(self.files[name])
                    self.git('update-index','--no-assume-unchanged','--no-skip-worktree',name)

    def test_missing_physical_source_cannot_be_replaced_by_its_git_object(self):
        name='runtime/unlisted.py';self.git('update-index','--skip-worktree',name);(self.root/name).unlink()
        with self.assertRaises(FileNotFoundError):retention.source_binding(self.commit,self.root)

    @unittest.skipIf(os.name=='nt','POSIX executable bit is explicitly unavailable on Windows')
    def test_hidden_executable_mode_change_is_rejected(self):
        name='runtime/unlisted.py';self.git('update-index','--assume-unchanged',name);(self.root/name).chmod(0o744)
        self.assertEqual(self.git('status','--porcelain'),b'')
        with self.assertRaisesRegex(ValueError,'executable mode differs'):retention.source_binding(self.commit,self.root)

    @unittest.skipIf(os.name=='nt','Temporary symlink creation needs separate Windows privileges')
    def test_hidden_symlink_cannot_redirect_source_reads(self):
        name='runtime/unlisted.py';self.git('update-index','--assume-unchanged',name);path=self.root/name
        path.unlink();path.symlink_to(self.root/'scripts/shutdown_study_retention.py')
        with self.assertRaisesRegex(ValueError,'regular physical file'):retention.source_binding(self.commit,self.root)

    def test_only_exact_windows_utf8_lf_to_crlf_conversion_is_recorded(self):
        path=self.root/'runtime/unlisted.py';path.write_bytes(b'line1\r\nline2\r\n')
        record=retention.physical_source_file(path,b'line1\nline2\n','100644',windows=True)
        self.assertEqual(record['checkout_conversion'],'Windows LF to CRLF')
        self.assertIsNone(record['physical_mode'])
        self.assertNotEqual(record['sha256'],record['canonical_sha256'])
        with self.assertRaisesRegex(ValueError,'physical source bytes differ'):
            retention.physical_source_file(path,b'line1\nline2\n','100644',windows=False)

    def test_binary_non_utf8_existing_cr_and_partial_conversion_fail(self):
        path=self.root/'runtime/unlisted.py'
        for expected,actual in [(b'\0\n',b'\0\r\n'),(b'\xff\n',b'\xff\r\n'),
                                (b'line\rvalue\n',b'line\rvalue\r\n'),(b'a\nb\n',b'a\r\nb\n')]:
            with self.subTest(expected=expected):
                path.write_bytes(actual)
                with self.assertRaises((ValueError,UnicodeDecodeError)):
                    retention.physical_source_file(path,expected,'100644',windows=True)

    def test_mutation_during_physical_read_fails_even_if_read_bytes_match(self):
        path=self.root/'runtime/unlisted.py';original=Path.read_bytes
        def racing(target):
            data=original(target)
            if target==path:target.write_bytes(data+b'extra byte')
            return data
        with patch.object(Path,'read_bytes',racing),self.assertRaisesRegex(ValueError,'changed during physical read'):
            retention.physical_source_file(path,self.files['runtime/unlisted.py'],'100644')

    def test_same_length_edit_with_restored_mtime_is_rejected(self):
        path=self.root/'runtime/unlisted.py';before=path.stat();original=Path.read_bytes
        count=0
        def racing(target):
            nonlocal count
            data=original(target)
            if target==path:
                count+=1
                if count==1:
                    target.write_bytes(b'X'*len(data))
                    os.utime(target,ns=(before.st_atime_ns,before.st_mtime_ns))
            return data
        with patch.object(Path,'read_bytes',racing),self.assertRaisesRegex(ValueError,'changed during physical read'):
            retention.physical_source_file(path,self.files['runtime/unlisted.py'],'100644')
        self.assertNotEqual(path.read_bytes(),self.files['runtime/unlisted.py'])

    def test_second_bytes_reject_first_read_mutation_even_with_constant_metadata(self):
        path=self.root/'runtime/unlisted.py';before=path.lstat();original=Path.read_bytes;count=0
        def racing(target):
            nonlocal count
            data=original(target)
            if target==path:
                count+=1
                if count==1:target.write_bytes(b'X'*len(data))
            return data
        with patch.object(Path,'read_bytes',racing),patch.object(Path,'lstat',return_value=before),self.assertRaisesRegex(ValueError,'changed during physical read'):
            retention.physical_source_file(path,self.files['runtime/unlisted.py'],'100644',windows=True)
        self.assertEqual(count,2)

    def test_unchanged_double_read_reports_the_platform_observation_limit(self):
        path=self.root/'runtime/unlisted.py'
        record=retention.physical_source_file(path,self.files['runtime/unlisted.py'],'100644',windows=True)
        self.assertEqual(record['read_observations'],2)
        self.assertEqual(record['change_metadata_scope'],'Windows NTFS ChangeTime unmeasured')


if __name__=='__main__':unittest.main()
