"""Local temporary Git/source-only controls. Never construct native/kernel APIs."""
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import acquire_fov_math_reference as a
from test_fov_binary_input import erase_timing_constructor,timing_binding_baseline

OLD_TEST_MODULE_SHA='036b76a9107e3198e312605686fdc5a487d88f0aa686d7021f4e4c4c7475ab89'
OLD_BINDING_SOURCE='def source_binding(expected,*,deadline,clock=time.monotonic):\n    def remaining():\n        value=deadline-clock()\n        require(value>0,"source binding exceeded whole deadline")\n        return value\n    require(len(expected)==40 and all(c in \'0123456789abcdef\' for c in expected),\'full frozen source required\')\n    actual=subprocess.check_output([\'git\',\'rev-parse\',\'HEAD\'],cwd=ROOT,text=True,timeout=remaining()).strip()\n    require(actual==expected,\'source HEAD mismatch\')\n    for staged in (False,True):\n        command=[\'git\',\'diff\',*([\'--cached\'] if staged else []),\'--quiet\',\'--\',\'.\',\':!docs/\']\n        require(subprocess.run(command,cwd=ROOT,timeout=remaining()).returncode==0,\'source has tracked non-doc changes\')\n    extras=subprocess.check_output([\'git\',\'ls-files\',\'--others\',\'--exclude-standard\',\'--\',*COMPONENT],cwd=ROOT,timeout=remaining())\n    require(not extras,\'untracked component source\')\n    files={}\n    for path in COMPONENT:\n        remaining();files[path]=digest(ROOT/path);remaining()\n    return dict(commit=actual,files=files)\n'


def git(root,*args):
    return subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false',*args],cwd=root,stderr=subprocess.PIPE,timeout=10)


def fixture(root):
    git(root,'init','-q');git(root,'config','core.autocrlf','false');git(root,'config','core.filemode','true')
    files={name:('100644',('fixture '+name+'\n').encode()) for name in a.COMPONENT}
    files['scripts/native_log.py']=('100644',b'imported helper\n')
    files['scripts/name with\ttab\nand newline.py']=('100755',b'binary\0payload\n')
    for name,(mode,data) in files.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(0o755 if mode=='100755' else 0o644)
    (root/'docs').mkdir();(root/'docs/excluded.md').write_bytes(b'non-source documentation')
    git(root,'add','--all');git(root,'-c','user.name=BindingFixture','-c','user.email=fixture@invalid','commit','--no-gpg-sign','-qm','fixture')
    return git(root,'rev-parse','HEAD').decode().strip(),files


def bind(root,commit):
    with patch.object(a,'ROOT',root):return a.source_binding(commit,deadline=time.monotonic()+30)


def old_binding(root,commit):
    namespace=dict(time=a.time,subprocess=a.subprocess,ROOT=root,COMPONENT=a.COMPONENT,digest=a.digest,require=a.require)
    exec(compile(OLD_BINDING_SOURCE,'<frozen-old-source-binding>','exec'),namespace)
    return namespace['source_binding'](commit,deadline=time.monotonic()+30)


class PhysicalGitControls(unittest.TestCase):
    def test_exact_canonical_tree_covers_all_components_import_and_nul_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);commit,files=fixture(root);result=bind(root,commit)
            self.assertEqual(result['commit'],commit);self.assertEqual(result['non_doc_paths'],len(files));self.assertEqual(set(result['physical_sources']),set(files))
            self.assertEqual(set(result['files']),set(a.COMPONENT));self.assertIn('scripts/native_log.py',result['physical_sources'])
            self.assertEqual(result['physical_sources']['scripts/name with\ttab\nand newline.py']['physical_mode'],'100755')
            self.assertTrue(all(row['read_observations']==2 and row['change_metadata_scope']=='POSIX st_ctime_ns' for row in result['physical_sources'].values()))
            (root/'docs/excluded.md').write_bytes(b'documentation changed')
            self.assertEqual(bind(root,commit),result)

    def test_f323_hidden_acquire_bytes_executable_and_import_benchmarks_old_accept_new_reject(self):
        for kind in ('acquire-bytes','executable','imported-helper'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);commit,files=fixture(root)
                name='scripts/native_log.py' if kind=='imported-helper' else 'scripts/acquire_fov_math_reference.py'
                git(root,'update-index','--assume-unchanged','--',name)
                if kind=='executable':git(root,'config','core.filemode','false');(root/name).chmod(0o755)
                else:(root/name).write_bytes(files[name][1]+b'physical mutation')
                git(root,'diff','--quiet');self.assertEqual(old_binding(root,commit)['commit'],commit)
                with self.assertRaisesRegex(RuntimeError,'physical source'):bind(root,commit)

    def test_assume_unchanged_and_skip_worktree_cannot_hide_tracked_dependency_mutation(self):
        for flag in ('--assume-unchanged','--skip-worktree'):
            with self.subTest(flag=flag),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);commit,files=fixture(root);name='scripts/native_log.py'
                git(root,'update-index',flag,'--',name);(root/name).write_bytes(b'hidden tracked import mutation')
                git(root,'diff','--quiet')
                with self.assertRaisesRegex(RuntimeError,'physical source bytes'):bind(root,commit)

    def test_missing_directory_and_symlinked_physical_file_reject(self):
        for kind in ('missing','directory','symlink'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);commit,files=fixture(root);path=root/'scripts/native_log.py';path.unlink()
                if kind=='directory':path.mkdir()
                if kind=='symlink':
                    target=root/'same-bytes';target.write_bytes(files['scripts/native_log.py'][1]);path.symlink_to(target)
                with self.assertRaises((RuntimeError,FileNotFoundError)):bind(root,commit)

    def test_hidden_owner_executable_mode_alone_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);commit,files=fixture(root);name='scripts/native_log.py'
            git(root,'config','core.filemode','false');(root/name).chmod(0o755);git(root,'diff','--quiet')
            with self.assertRaisesRegex(RuntimeError,'executable mode'):bind(root,commit)

    def test_final_head_query_rejects_changed_commit_without_new_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);commit,files=fixture(root);real=subprocess.check_output;calls=[]
            def output(command,**options):
                calls.append(command)
                if len(calls)==4:return '0'*40+'\n'
                return real(command,**options)
            with patch.object(a,'ROOT',root),patch.object(a.subprocess,'check_output',side_effect=output):
                with self.assertRaisesRegex(RuntimeError,'HEAD changed'):a.source_binding(commit,deadline=time.monotonic()+30)
            self.assertEqual([c[1] for c in calls],['rev-parse','ls-tree','cat-file','rev-parse'])


class ParserAndObservationControls(unittest.TestCase):
    def tree(self):
        records=[];blobs={}
        for name in [*a.COMPONENT,'scripts/native_log.py','scripts/a\ttab\nnewline.py']:
            data=name.encode()+b'\0';blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();blobs[blob]=data
            records.append(b'100644 blob '+blob.encode()+b'\t'+name.encode()+b'\0')
        raw=b''.join(records);batch=b''.join(blob.encode()+b' blob '+str(len(data)).encode()+b'\n'+data+b'\n' for blob,data in blobs.items())
        return raw,blobs,batch

    def test_nul_tree_and_binary_batch_parse_exactly(self):
        raw,blobs,batch=self.tree();records=a.source_tree(raw)
        self.assertEqual(len(records),len(a.COMPONENT)+2);self.assertEqual(a.source_blobs(batch,list(blobs)),blobs)
        self.assertIn('scripts/a\ttab\nnewline.py',{row['path'] for row in records})

    def test_empty_truncated_duplicate_unsafe_and_wrong_mode_tree_reject(self):
        raw,blobs,batch=self.tree();first=raw.split(b'\0')[0]+b'\0'
        cases=[b'',b'\0',raw[:-1],raw+first,raw.replace(b'100644 blob ',b'120000 blob ',1),
               raw.replace(b'100644 blob ',b'100644 tree ',1),raw.replace(b'\tscripts/',b'\t../scripts/',1)]
        for bad in cases:
            with self.subTest(),self.assertRaises(RuntimeError):a.source_tree(bad)

    def test_missing_corrupt_truncated_extra_and_wrong_object_batch_reject(self):
        raw,blobs,batch=self.tree();first=next(iter(blobs));cases=[b'',batch[:-1],batch+b'junk',batch.replace(b' blob ',b' tree ',1),batch.replace(first.encode(),b'0'*40,1),batch.replace(blobs[first],b'X'*len(blobs[first]),1)]
        for bad in cases:
            with self.subTest(),self.assertRaises(RuntimeError):a.source_blobs(bad,list(blobs))

    def test_restored_mtime_mutation_during_read_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.py';path.write_bytes(b'original');path.chmod(0o644);before=path.stat();real=Path.read_bytes;done=False
            def read(current):
                nonlocal done
                data=real(current)
                if current==path and not done:
                    done=True;current.write_bytes(b'mutated!');os.utime(current,ns=(before.st_atime_ns,before.st_mtime_ns))
                return data
            with patch.object(Path,'read_bytes',read),self.assertRaisesRegex(RuntimeError,'source changed'):
                a.physical_source_file(path,b'original','100644',deadline=time.monotonic()+5,clock=time.monotonic)

    def test_ctime_only_observation_change_and_second_read_change_each_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.py';path.write_bytes(b'original');path.chmod(0o644);real=Path.lstat;calls=0
            def lstat(current):
                nonlocal calls
                value=real(current)
                if current!=path:return value
                calls+=1
                return SimpleNamespace(st_dev=value.st_dev,st_ino=value.st_ino,st_size=value.st_size,st_mtime_ns=value.st_mtime_ns,st_ctime_ns=10 if calls==1 else 11,st_mode=value.st_mode)
            with patch.object(Path,'lstat',lstat),self.assertRaisesRegex(RuntimeError,'source changed'):
                a.physical_source_file(path,b'original','100644',deadline=time.monotonic()+5,clock=time.monotonic)
            actual=Path.read_bytes;reads=0
            def read(current):
                nonlocal reads
                if current!=path:return actual(current)
                reads+=1;return b'original' if reads==1 else b'different'
            with patch.object(Path,'read_bytes',read),self.assertRaisesRegex(RuntimeError,'source changed'):
                a.physical_source_file(path,b'original','100644',deadline=time.monotonic()+5,clock=time.monotonic)

    def test_expired_original_budget_forbids_git_and_midread_budget_rejects(self):
        with patch.object(a.subprocess,'check_output',side_effect=AssertionError('no late Git')):
            with self.assertRaises(RuntimeError):a.source_binding('a'*40,deadline=100,clock=lambda:100)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.py';path.write_bytes(b'original');clock=SimpleNamespace(now=100);real=Path.read_bytes
            def read(current):
                result=real(current);clock.now=101;return result
            with patch.object(Path,'read_bytes',read),self.assertRaises(RuntimeError):a.physical_source_file(path,b'original','100644',deadline=101,clock=lambda:clock.now)


class TimingProtectionControls(unittest.TestCase):
    def source(self):return (Path(__file__).parent/'test_fov_math_reference.py').read_bytes()

    def test_exact_donor_and_complete_old_module_hash_reconstruct(self):
        original=erase_timing_constructor(self.source())
        self.assertEqual(hashlib.sha256(original).hexdigest(),OLD_TEST_MODULE_SHA)
        self.assertEqual(timing_binding_baseline()['sha256'],'8c33308f610f09a3710106eaf0392fdad9fa9918c00d573f8796d305167e1e31')

    def test_assertions_clock_query_cost_and_binding_deadline_mutations_reject(self):
        raw=self.source()
        changes=[(b'self.assertEqual(len(timeouts),4)',b'self.assertEqual(len(timeouts),3)'),
                 (b'all(0<t<=1 for t in timeouts)',b'all(0<=t<=1 for t in timeouts)'),
                 (b'clock.now=101.',b'clock.now=102.'),(b'clock.sleep(.1)\n                return',b'clock.sleep(.01)\n                return'),
                 (b"binding=acquisition.source_binding('a'*40,deadline=101.,clock=clock)",b"binding=acquisition.source_binding('a'*40,deadline=102.,clock=clock)")]
        for old,new in changes:
            self.assertIn(old,raw)
            with self.subTest(old=old),self.assertRaises(ValueError):erase_timing_constructor(raw.replace(old,new,1))

    def test_duplicate_decorated_outside_missing_and_earlyreturn_methods_reject(self):
        raw=self.source();name=b'    def test_source_git_children_receive_only_remaining_whole_deadline(self):'
        cases=[raw.replace(name,b'    @staticmethod\n'+name,1),raw+ b'\ndef test_source_git_children_receive_only_remaining_whole_deadline(self):\n    pass\n',
               raw.replace(name,b'    def missing_timing(self):',1),raw.replace(name,name+b'\n        return',1)]
        for bad in cases:
            with self.subTest(),self.assertRaises((ValueError,SyntaxError)):erase_timing_constructor(bad)

    def test_outside_comment_or_other_method_is_not_hidden_by_normalization(self):
        raw=self.source();mutated=raw.replace(b'class SupervisorControls',b'# outside comment\nclass SupervisorControls',1)
        self.assertNotEqual(hashlib.sha256(erase_timing_constructor(mutated)).hexdigest(),OLD_TEST_MODULE_SHA)
        changed=raw.replace(b'class FakeClock:',b'class ChangedClock:',1)
        self.assertNotEqual(hashlib.sha256(erase_timing_constructor(changed)).hexdigest(),OLD_TEST_MODULE_SHA)


if __name__=='__main__':unittest.main()
