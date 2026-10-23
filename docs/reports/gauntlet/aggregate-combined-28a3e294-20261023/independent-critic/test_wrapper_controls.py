#!/usr/bin/env python3
"""Independent source-only false-success controls; never launches a process."""
import hashlib
import ast
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

BUILDER = Path('/workspace/sightbreak-aggregate-combined-28a3e294/docs/reports/gauntlet/aggregate-combined-28a3e294-20261023')
sys.path.insert(0,str(BUILDER))

def load(name):
    spec=importlib.util.spec_from_file_location(name,BUILDER/(name+'.py'))
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value

runner=load('run_aggregate');archiver=load('archive_originals')

class IndependentControls(unittest.TestCase):
    def fixture(self,root):
        repo=root/'repo';out=root/'out';logs=repo/'.local/validation/run-fixed';smoke=root/'smoke'
        for path in (out,logs,smoke):path.mkdir(parents=True)
        specification=runner.contract(Path('/workspace/sightbreak-aggregate-frozen-28a3e294'))
        for row in specification['mandatory_godot']:(logs/(row['label']+'.log')).write_text('Godot Engine v4.7.2.stable.official.ed1daf0bf\nchecks=1 failures=0\n')
        (logs/'reload-contact.log').write_text('RELOAD_CONTACT_TEST checks=24 failures=0\n')
        life=logs/'connection-lifecycle';life.mkdir()
        for scenario in ('silent','idle','reject'):
            for role in ('server','client'):(life/(scenario+'-'+role+'.log')).write_text('LIFECYCLE {"ok":true}\n')
        for name in ('server.log','cleanup.log','client-a.log','client-b.log'):(smoke/name).write_text('NETWORK_CLIENT_PASS\n')
        (out/'aggregate.log').write_text('NETWORK_LOG_DIR='+str(smoke)+'\nbackend_world.json matches the backend (29 definitions)\nValidation completed. Logs: '+str(logs)+'\n')
        return repo,out,logs,smoke,specification

    def audit(self,paths):
        repo,out,logs,smoke,specification=paths
        return runner.required_logs(repo,out,[logs],specification)

    def test_terminal_original_budget_boundary_uses_exact_committed_predicate(self):
        tree=ast.parse((BUILDER/'run_aggregate.py').read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        terminal=next(n.finalbody for n in ast.walk(main) if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='passed' for t in x.targets) for x in n.finalbody))
        selected=[n for n in terminal if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='passed' or isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='record' and isinstance(t.slice,ast.Constant) and t.slice.value=='whole_budget_met' for t in n.targets)]
        self.assertEqual(2,len(selected))
        executable=compile(ast.Module(body=selected,type_ignores=[]),'exact-terminal-predicate','exec')
        for seconds,want in ((1199.999,True),(1200,False),(1200.001,False),(float('inf'),False),(float('nan'),False)):
            scope=dict(record={'seconds':seconds,'exit_code':0},WHOLE_SECONDS=1200,failure=None,before={'same':True},after={'same':True},terminal={},terminal_ports=[],audit={'failures':[]})
            exec(executable,scope)
            self.assertIs(scope['passed'],want)
        self.assertEqual(1200,runner.WHOLE_SECONDS)
        self.assertEqual(540,runner.PHASE_SECONDS)

    def test_clean_complete_ledger_is_control(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual([],self.audit(self.fixture(Path(temp)))['failures'])

    def test_missing_new_exhausted_suite_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            paths=self.fixture(Path(temp));(paths[2]/'bot-exhausted-primary.log').unlink()
            self.assertTrue(self.audit(paths)['failures'])

    def test_display_log_cannot_substitute_for_maintained_log(self):
        with tempfile.TemporaryDirectory() as temp:
            paths=self.fixture(Path(temp));(paths[2]/'viewmodel-light.log').write_text('checks=1 failures=0')
            self.assertTrue(self.audit(paths)['failures'])

    def test_all_original_orphans_reject_in_complete_ledger(self):
        corpus=Path('/workspace/sightbreak-aggregate-frozen-28a3e294/scripts/fixtures/native_log/input-mode.log').read_text()
        orphans=[line for line in corpus.splitlines() if line.startswith('Orphan StringName: ')]
        self.assertEqual(353,len(orphans))
        for line in orphans:
            for ending in ('','\n','\r\n'):
                with self.subTest(line=line,ending=repr(ending)):
                    self.assertIsNotNone(runner.STRICT.search('Godot startup\n'+line+ending))
        with tempfile.TemporaryDirectory() as temp:
            paths=self.fixture(Path(temp));(paths[2]/'bot-exhausted-primary.log').write_text(orphans[0]+'\n')
            self.assertTrue(self.audit(paths)['failures'])

    def test_summary_only_private_userdata_leak_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            paths=self.fixture(Path(temp));private=paths[0]/'.local/aggregate-state-r1/data/godot/app_userdata/SIGHTBREAK/logs/godot.log';private.parent.mkdir(parents=True)
            private.write_text('StringName: 1 unclaimed string names at exit.\n')
            self.assertTrue(self.audit(paths)['failures'])

    def test_missing_lifecycle_or_catalog_skip_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            paths=self.fixture(Path(temp));(paths[2]/'connection-lifecycle/idle-client.log').unlink()
            self.assertTrue(self.audit(paths)['failures'])
        with tempfile.TemporaryDirectory() as temp:
            paths=self.fixture(Path(temp));raw=(paths[1]/'aggregate.log').read_text();(paths[1]/'aggregate.log').write_text(raw.replace('backend_world.json matches the backend (29 definitions)','SKIPPED catalog fixture drift check'))
            self.assertTrue(self.audit(paths)['failures'])

    def test_archive_rejects_late_same_length_log_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);paths=self.fixture(root);audit=self.audit(paths);(paths[1]/'log-audit.json').write_text(json.dumps(audit))
            path=paths[2]/'actor.log';raw=path.read_bytes();path.write_bytes(b'X'+raw[1:])
            with self.assertRaisesRegex(RuntimeError,'Late log mutation'):
                archiver.archive(paths[1],paths[0],root/'archive')
            self.assertEqual(b'X',path.read_bytes()[:1])

    def test_new_private_log_after_terminal_scan_is_archived_and_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);paths=self.fixture(root);(paths[1]/'log-audit.json').write_text(json.dumps(self.audit(paths)))
            late=paths[0]/'.local/aggregate-state-r1/data/late.log';late.parent.mkdir(parents=True);late.write_text('Orphan StringName: late (static: 0, total: 1)\n')
            receipt=archiver.archive(paths[1],paths[0],root/'archive')
            self.assertTrue(receipt['verified']);self.assertFalse(receipt['strict_clean']);self.assertTrue(late.exists())
            self.assertTrue(any(row['original_path']==str(late) for row in json.loads((root/'archive/MANIFEST.json').read_text())))

if __name__=='__main__':
    unittest.main(verbosity=2)
