#!/usr/bin/env python3
"""Independent pure controls of exact committed source; no Godot/native APIs."""
from contextlib import ExitStack, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / 'snapshot'
sys.path.insert(0, str(SNAPSHOT / 'scripts'))
import diagnose_native_input_mode as diagnostic
import run_native_regressions as native

IDENTITY = dict(source_commit='f3896c60d367466129ba5d2a906234b2dee8174f',
                source_game_tree='fb6be859e05812d8707be1ef5c6f747d2588c1e9',
                source_content_sha256='fake-pure-identity', source_validation_sha256='fake-pure-validation',
                source_dirty=False, source_game_dirty=False)
ENGINE = '/pure/fake-pinned-engine'


class Rig:
    """Use the real inherited context manager, file hashes, config and cleanup.

    Only platform/source identity, engine verification, subprocess launch, owned
    process reaping and a controlled monotonic clock are mocked. Producer JSON is
    written by fake processes and parsed/validated by the unmodified implementation.
    """
    def __init__(self, base, suite='actor', mode='clean', at=None):
        self.base, self.suite, self.mode = base, suite, mode
        self.root, self.original, self.output = base/'repo', base/'original', base/'new'
        (self.root/'game/tests').mkdir(parents=True)
        # Exact committed project config and selected script bytes, minimal pure source tree.
        for name in ('project.godot', 'tests/actor_test.gd', 'tests/input_mode_test.gd'):
            shutil.copyfile(SNAPSHOT/'game'/name, self.root/'game'/name)
        self.original.mkdir()
        self.now, self.calls, self.reaped, self.roots, self.projects = 0, [], [], set(), set()
        self.at = at
        namespace = 'SIGHTBREAK-native-tests-' + '0'*32
        project = '/pure/sightbreak-native-tests-original/project'
        producer = dict(project_path=project, data_dir='/pure/native-data',
                        user_data_dir='/pure/native-data/'+namespace+'/'+suite,
                        uses_custom_user_dir=True, custom_user_dir=namespace+'/'+suite,
                        profile_exists=False, diagnostics_exist=False,
                        run={'exit':0, 'clean_log':True})
        self.rows = [dict(suite=suite, exit=0, clean_log=False,
                          command=[ENGINE,'--path',project,'--headless','--script','res://tests/'+suite+'_test.gd'],
                          before=copy.deepcopy(producer), after=copy.deepcopy(producer))]
        self.isolation = dict(passed=False, failure={'message':suite+' failed; raw output retained'},
                              namespace=namespace, engine=diagnostic.toolchain.ENGINE,
                              source_resources_unchanged=True, copied_resources_unchanged=True,
                              temporary_project_removed=True, finalization_failures=[],
                              cleanup=[{'removed':True,'user_namespace':'/pure/native-data/'+namespace}],
                              source_resources_sha256=native.inventory(self.root/'game'))
        self.save()
        (self.original/(suite+'.log')).write_text('WARNING: 6 ObjectDB instances were leaked at exit\n')

    def save(self):
        (self.original/'results.json').write_text(json.dumps(self.rows))
        (self.original/'isolation.json').write_text(json.dumps(self.isolation))

    def popen(self, command, **kwargs):
        project = Path(command[2])
        self.projects.add(project)
        config = (project/'project.godot').read_text()
        custom = json.loads(re.search(r'^config/custom_user_dir_name=(.*)$',config,re.M).group(1))
        label = 'private-import' if '--editor' in command else command[command.index('--script')+1]
        selected = label == 'res://tests/'+self.suite+'_test.gd'
        call = {'command':command, 'kwargs':kwargs, 'label':label, 'custom':custom, 'waits':[]}
        self.calls.append(call)
        if '--receipt='+str(self.output) in command:
            raise AssertionError('Wrong receipt target')
        stage = 'suite' if selected else 'import' if label == 'private-import' else custom.rsplit('/',1)[1]
        if stage == self.at and self.mode == 'advance-deadline':
            self.now = 240.1
        if '--receipt=' in ' '.join(command):
            destination = Path(next(arg.removeprefix('--receipt=') for arg in command if arg.startswith('--receipt=')))
            data = self.base/'data'
            user = data/custom
            user.mkdir(parents=True,exist_ok=True)
            self.roots.add(user.parent)
            receipt = dict(user_data_dir=str(user),data_dir=str(data),project_path=str(project),
                           uses_custom_user_dir=True,custom_user_dir=custom,
                           profile_exists=False,diagnostics_exist=False,os='macOS')
            if self.mode == 'bootstrap-foreign' and custom.endswith('/bootstrap'):
                receipt['project_path'] = str(self.base/'foreign-project')
            if self.mode == 'before-dirty' and len(self.calls)==3:
                receipt['profile_exists'] = True
            if self.mode == 'after-foreign' and len(self.calls)==5:
                receipt['user_data_dir'] = str(self.base/'foreign-user')
            if not (self.mode == 'bootstrap-absent' and custom.endswith('/bootstrap')):
                destination.write_text(json.dumps(receipt))
        if selected:
            user = self.base/'data'/custom
            user.mkdir(parents=True,exist_ok=True)
            (user/'produced.txt').write_bytes(b'pure produced bytes\n')
            if self.mode == 'leak': kwargs['stdout'].write('WARNING: 6 ObjectDB instances were leaked at exit\n')
            if self.mode == 'source-mutated': (self.root/'game/tests/actor_test.gd').write_text('changed')
            if self.mode == 'copy-mutated': (project/'tests/actor_test.gd').write_text('changed')
        if label == 'private-import' and self.mode == 'import-warning':
            kwargs['stdout'].write('ERROR: pure import failure\n')
        if self.mode == 'bootstrap-warning' and custom.endswith('/bootstrap'):
            kwargs['stdout'].write('ERROR: pure bootstrap failure\n')
        class Process:
            pid = 70000+len(self.calls)
            returncode = 0
            def wait(inner,timeout):
                call['waits'].append(timeout)
                if self.mode == 'timeout' and selected:
                    inner.returncode = -15
                    self.now = 241
                    raise subprocess.TimeoutExpired(command, timeout)
        process=Process()
        if self.mode == 'bootstrap-nonzero' and custom.endswith('/bootstrap'): process.returncode=2
        return process

    def reap(self, process):
        self.reaped.append(process.pid)
        return dict(owned_group_gone=self.mode!='unreaped', signals_sent=[], exit_code=process.returncode)

    def run(self, **extra):
        with ExitStack() as stack:
            for target,name,value in ((diagnostic.platform,'system',lambda:'Darwin'),
                                      (diagnostic.platform,'machine',lambda:'arm64'),
                                      (diagnostic.toolchain,'binary',lambda:ENGINE),
                                      (diagnostic.toolchain,'environment',lambda:{}),
                                      (diagnostic.toolchain,'verify_engine',lambda:diagnostic.toolchain.ENGINE),
                                      (diagnostic,'source',lambda:dict(IDENTITY)),
                                      (diagnostic.time,'monotonic',lambda:self.now),
                                      (diagnostic.subprocess,'Popen',self.popen),
                                      (diagnostic,'reap',self.reap)):
                stack.enter_context(patch.object(target,name,value))
            stack.enter_context(patch.object(diagnostic.toolchain,'ROOT',self.root))
            # Any unexpected real subprocess operation is a control failure.
            stack.enter_context(patch.object(diagnostic.subprocess,'run',side_effect=AssertionError('Real subprocess forbidden')))
            stack.enter_context(patch.object(diagnostic.subprocess,'check_output',side_effect=AssertionError('Real subprocess forbidden')))
            for name,value in extra.items(): stack.enter_context(patch.object(diagnostic,name,value))
            with redirect_stdout(io.StringIO()):
                result = diagnostic.run(self.original,self.output)
        return result,json.loads((self.output/'diagnostic.json').read_text())


class IndependentControls(unittest.TestCase):
    def test_committed_snapshot_and_latest_raw_fixture_exact_hashes(self):
        manifest=json.loads((HERE/'snapshot-sha256.json').read_text())
        for name,digest in manifest.items():
            self.assertEqual(hashlib.sha256((SNAPSHOT/name).read_bytes()).hexdigest(),digest,name)
        raw=Path('/workspace/sightbreak-mac-menu-native-review/docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/full-qa/regressions')
        fixture=SNAPSHOT/'docs/reports/gauntlet/m2-macos-first-leak/fixtures/39736389634'
        for name in ('results.json','isolation.json','actor.log'):
            self.assertEqual((raw/name).read_bytes(),(fixture/name).read_bytes())

    def test_actual_fixtures_with_real_resource_inventory_and_only_resolve_alias_simulation(self):
        fixtures=SNAPSHOT/'docs/reports/gauntlet/m2-macos-first-leak/fixtures'
        original_resolve=Path.resolve
        def simulated_resolve(path,*args,**kwargs):
            value=str(path)
            if value.startswith('/var/folders/'): return Path('/private'+value)
            return original_resolve(path,*args,**kwargs)
        for run,suite in (('39736389634','actor'),('39732825169','input_mode')):
            directory=fixtures/run
            before=diagnostic.evidence(directory)
            rows=json.loads((directory/'results.json').read_text())
            selection={}
            with (patch.object(diagnostic.toolchain,'ROOT',SNAPSHOT),
                  patch.object(diagnostic.toolchain,'binary',return_value=rows[-1]['command'][0]),
                  patch.object(Path,'resolve',simulated_resolve),
                  patch.object(diagnostic.subprocess,'Popen') as launch):
                self.assertIsNone(diagnostic.select_failure(directory,selection))
                self.assertIsNone(diagnostic.select_failure(directory))  # Legacy reason-only API.
                launch.assert_not_called()
            self.assertEqual(selection,{'suite':suite})
            self.assertEqual(before,diagnostic.evidence(directory))

    def test_public_resolve_accepts_real_pure_symlink_alias_and_refuses_foreign(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); (base/'private').mkdir(); (base/'alias').symlink_to(base/'private',target_is_directory=True)
            self.assertTrue(diagnostic.same_native_path(str(base/'alias/project'),str(base/'private/project')))
            self.assertFalse(diagnostic.same_native_path(str(base/'alias/project'),str(base/'foreign/project')))
            for bad in (None,123,[],{},'relative/project'):
                self.assertFalse(diagnostic.same_native_path(bad,str(base/'private/project')))

    def test_full_inherited_lifecycle_for_both_suites_and_only_one_verbose_suite(self):
        for suite in ('actor','input_mode'):
            with self.subTest(suite=suite),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp),suite); original=diagnostic.evidence(rig.original)
                result,report=rig.run()
                self.assertEqual(result,0,report)
                self.assertTrue(report['passed']); self.assertFalse(report['strict_gate_repaired'])
                self.assertEqual(report['status'],'DIAGNOSTIC_CLEAN_REPEAT')
                self.assertEqual(report['selected_suite'],suite)
                self.assertTrue(report['original_evidence_unchanged']); self.assertEqual(original,diagnostic.evidence(rig.original))
                self.assertEqual(len(rig.calls),5)
                self.assertEqual(len(rig.reaped),5)
                self.assertTrue(all(c['kwargs']['start_new_session'] is True for c in rig.calls))
                self.assertEqual([c['command'][3:] for c in rig.calls if '--verbose' in c['command']],
                                 [['--headless','--verbose','--script','res://tests/'+suite+'_test.gd']])
                self.assertEqual(rig.calls[1]['command'][3:],['--headless','--editor','--import','--quit'])
                self.assertTrue(rig.calls[0]['custom'].endswith('/bootstrap'))
                self.assertTrue(all(c['custom'].endswith('/'+suite) for c in rig.calls[2:]))
                iso=report['isolation']
                self.assertNotEqual(iso['namespace'],rig.isolation['namespace'])
                self.assertTrue(iso['source_resources_unchanged']);self.assertTrue(iso['copied_resources_unchanged'])
                self.assertTrue(iso['temporary_project_removed']);self.assertTrue(all(c['removed'] for c in iso['cleanup']))
                self.assertTrue(all(not p.exists() for p in rig.projects|rig.roots))
                produced=json.loads((rig.output/'repeat/results.json').read_text())[0]
                digest=hashlib.sha256(b'pure produced bytes\n').hexdigest()
                self.assertEqual(produced['produced_files_sha256'],{'produced.txt':digest})
                self.assertEqual((rig.output/('repeat/'+suite+'-userdata/produced.txt')).read_bytes(),b'pure produced bytes\n')
                self.assertEqual([c['waits'][0] for c in rig.calls],[30,120,30,120,30])
                self.assertTrue((rig.output/'repeat/owned-processes.json').is_file())

    def test_repeated_leak_keeps_original_and_repeat_failed_with_honest_cleanup(self):
        for suite in ('actor','input_mode'):
            with self.subTest(suite=suite),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp),suite,'leak'); before=diagnostic.evidence(rig.original)
                result,report=rig.run()
                self.assertEqual(result,1);self.assertFalse(report['passed']);self.assertFalse(report['strict_gate_repaired'])
                self.assertEqual(report['failure']['message'],suite+' failed; raw output retained')
                self.assertEqual(before,diagnostic.evidence(rig.original))
                self.assertEqual(len(rig.calls),5)
                self.assertTrue(report['isolation']['temporary_project_removed'])
                self.assertTrue(all(c['removed'] for c in report['isolation']['cleanup']))

    def test_import_and_before_probe_failures_prevent_selected_suite(self):
        for mode,expected in (('import-warning',2),('before-dirty',3)):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp),mode=mode)
                result,report=rig.run()
                self.assertEqual(result,1);self.assertFalse(report['passed'])
                self.assertEqual(len(rig.calls),expected)
                self.assertTrue(all('--verbose' not in c['command'] for c in rig.calls))
                self.assertTrue(all(not root.exists() for root in rig.roots))

    def test_unvalidated_bootstrap_namespace_preserved_and_no_import_or_suite(self):
        for mode in ('bootstrap-foreign','bootstrap-absent','bootstrap-warning','bootstrap-nonzero'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp),mode=mode)
                result,report=rig.run()
                self.assertEqual(result,1);self.assertFalse(report['passed'])
                self.assertEqual(len(rig.calls),1)
                self.assertEqual(report['isolation']['cleanup'],[])
                self.assertTrue(all(root.exists() for root in rig.roots))
                self.assertTrue(report['isolation']['temporary_project_removed'])

    def test_after_probe_foreign_does_not_claim_suite_success_and_removes_only_validated_root(self):
        with tempfile.TemporaryDirectory() as temp:
            rig=Rig(Path(temp),mode='after-foreign')
            result,report=rig.run()
            self.assertEqual(result,1);self.assertFalse(report['passed'])
            self.assertEqual(len(rig.calls),5)
            self.assertFalse((rig.output/'repeat/results.json').exists())
            self.assertTrue(all(not root.exists() for root in rig.roots))

    def test_full_lifecycle_timeout_and_unreaped_group_fail(self):
        for mode in ('timeout','unreaped'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp),mode=mode)
                result,report=rig.run()
                self.assertEqual(result,1);self.assertFalse(report['passed'])
                self.assertEqual(len(rig.calls),4 if mode=='timeout' else 1)
                self.assertEqual(len(rig.calls),len(rig.reaped))
                self.assertFalse(report['strict_gate_repaired'])
                if mode=='timeout':
                    self.assertEqual(report['failure']['type'],'TimeoutExpired')
                    self.assertTrue(report['owned_processes'][-1]['timed_out'])
                    self.assertIn('finalization_failure',report)
                else:self.assertFalse(report['owned_processes'][0]['cleanup']['owned_group_gone'])

    def test_resource_mutation_cleanup_is_honest(self):
        for mode,key in (('source-mutated','source_resources_unchanged'),('copy-mutated','copied_resources_unchanged')):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp),mode=mode)
                result,report=rig.run()
                self.assertEqual(result,1);self.assertFalse(report['passed']);self.assertFalse(report['isolation'][key])
                self.assertTrue(report['isolation']['finalization_failures'])
                self.assertTrue(report['isolation']['temporary_project_removed'])

    def test_owned_namespace_cleanup_failure_remains_failed_and_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            rig=Rig(Path(temp)); original_rmtree=shutil.rmtree
            def refuse_owned(path,*args,**kwargs):
                if Path(path).name.startswith('SIGHTBREAK-native-tests-'):
                    raise OSError('Independent pure cleanup failure')
                return original_rmtree(path,*args,**kwargs)
            with patch.object(native.shutil,'rmtree',refuse_owned):
                result,report=rig.run()
            self.assertEqual(result,1);self.assertFalse(report['passed'])
            self.assertFalse(report['isolation']['cleanup'][0]['removed'])
            self.assertTrue(all(root.exists() for root in rig.roots))
            self.assertTrue(report['isolation']['temporary_project_removed'])
            self.assertEqual(report['isolation']['finalization_failures'][0]['stage'],'user_namespace_cleanup')
            self.assertFalse(report['strict_gate_repaired'])

    def test_adversarial_selection_inputs_no_process_launch(self):
        variants=('empty','invalid-json','missing-results','missing-isolation','missing-log','no-leak','unsupported',
                  'earlier-failed','later-clean','duplicate','unknown','bool-exit','float-exit','missing-prior-clean',
                  'foreign-engine','foreign-script','extra-argv','relative-project','foreign-before','foreign-after',
                  'namespace','before-profile','before-diagnostics','before-run-warning','after-run-exit','cleanup-root',
                  'cleanup-multiple','cleanup-failed','copy-unclean','source-unclean','temp-unclean','finalization-failed',
                  'resource-hashes','engine-version','failure-message','no-before')
        for variant in variants:
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp)); row=rig.rows[-1]
                if variant=='empty':rig.rows=[]
                elif variant=='unsupported':row['suite']='match';rig.isolation['failure']['message']='match failed; raw output retained'
                elif variant=='earlier-failed':rig.rows.insert(0,{'suite':'match','exit':0,'clean_log':False})
                elif variant=='later-clean':rig.rows.append({'suite':'input_mode','exit':0,'clean_log':True})
                elif variant=='duplicate':rig.rows.insert(0,copy.deepcopy(row))
                elif variant=='unknown':rig.rows.insert(0,{'suite':'alien','exit':0,'clean_log':True})
                elif variant=='bool-exit':row['exit']=False
                elif variant=='float-exit':row['exit']=0.0
                elif variant=='missing-prior-clean':rig.rows.insert(0,{'suite':'match','exit':0})
                elif variant=='foreign-engine':row['command'][0]='/foreign/engine'
                elif variant=='foreign-script':row['command'][-1]='res://tests/input_mode_test.gd'
                elif variant=='extra-argv':row['command'].append('--verbose')
                elif variant=='relative-project':row['command'][2]='sightbreak-native-tests-foreign/project'
                elif variant=='foreign-before':row['before']['project_path']='/foreign/project'
                elif variant=='foreign-after':row['after']['user_data_dir']='/foreign/actor'
                elif variant=='namespace':rig.isolation['namespace']='SIGHTBREAK-native-tests-foreign'
                elif variant=='before-profile':row['before']['profile_exists']=True
                elif variant=='before-diagnostics':row['before']['diagnostics_exist']=True
                elif variant=='before-run-warning':row['before']['run']['clean_log']=False
                elif variant=='after-run-exit':row['after']['run']['exit']=2
                elif variant=='cleanup-root':rig.isolation['cleanup'][0]['user_namespace']='/foreign'
                elif variant=='cleanup-multiple':rig.isolation['cleanup'].append(copy.deepcopy(rig.isolation['cleanup'][0]))
                elif variant=='cleanup-failed':rig.isolation['cleanup'][0]['removed']=False
                elif variant=='copy-unclean':rig.isolation['copied_resources_unchanged']=False
                elif variant=='source-unclean':rig.isolation['source_resources_unchanged']=False
                elif variant=='temp-unclean':rig.isolation['temporary_project_removed']=False
                elif variant=='finalization-failed':rig.isolation['finalization_failures']=[{}]
                elif variant=='resource-hashes':rig.isolation['source_resources_sha256']={}
                elif variant=='engine-version':rig.isolation['engine']='foreign'
                elif variant=='failure-message':rig.isolation['failure']['message']='input_mode failed; raw output retained'
                elif variant=='no-before':row.pop('before')
                rig.save()
                if variant=='invalid-json':(rig.original/'results.json').write_text('{')
                elif variant=='missing-results':(rig.original/'results.json').unlink()
                elif variant=='missing-isolation':(rig.original/'isolation.json').unlink()
                elif variant=='missing-log':(rig.original/'actor.log').unlink()
                elif variant=='no-leak':(rig.original/'actor.log').write_text('ERROR: unrelated failure\n')
                result,report=rig.run()
                self.assertEqual(rig.calls,[])
                self.assertFalse(report['passed']);self.assertFalse(report['strict_gate_repaired'])
                self.assertEqual(result,0,report)
                self.assertEqual(report['status'],'SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE')

    def test_changed_evidence_source_or_prelaunch_deadline_never_launches(self):
        for kind in ('actor-log','absent-input-log','source-identity','source-dirty','deadline'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp)); current=dict(IDENTITY); real=diagnostic.select_failure
                def select(directory,selection):
                    reason=real(directory,selection)
                    if kind=='actor-log':(directory/'actor.log').write_text('changed\n')
                    elif kind=='absent-input-log':(directory/'input_mode.log').write_text('new evidence\n')
                    elif kind=='source-identity':current['source_validation_sha256']='changed'
                    elif kind=='source-dirty':current['source_dirty']=True
                    else:rig.now=240
                    return reason
                result,report=rig.run(select_failure=select,source=lambda:dict(current))
                self.assertEqual(result,1);self.assertEqual(rig.calls,[]);self.assertFalse(report['passed'])
                self.assertIn('no launch',report['failure']['message'])

    def test_malformed_receipt_shapes_fail_closed_without_process(self):
        for kind in ('result-object','result-element','suite-list','namespace-list','before-list','before-run-list','cleanup-object'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temp:
                rig=Rig(Path(temp))
                if kind=='result-object':rig.rows={}
                elif kind=='result-element':rig.rows=[None]
                elif kind=='suite-list':rig.rows[0]['suite']=[]
                elif kind=='namespace-list':rig.isolation['namespace']=[]
                elif kind=='before-list':rig.rows[0]['before']=[]
                elif kind=='before-run-list':rig.rows[0]['before']['run']=[]
                else:rig.isolation['cleanup']={}
                rig.save()
                _result,report=rig.run()
                self.assertEqual(rig.calls,[]);self.assertFalse(report['passed'])
                self.assertIn(report['status'],('FAILED','SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE'))

    def test_shared_remaining_deadline_bounds_every_process_and_stops_after_expiry(self):
        with tempfile.TemporaryDirectory() as temp:
            rig=Rig(Path(temp)); actual_popen=rig.popen
            def advancing(command,**kwargs):
                process=actual_popen(command,**kwargs)
                rig.now+=45
                return process
            rig.popen=advancing
            result,report=rig.run()
            self.assertEqual(result,0,report)
            self.assertEqual([c['waits'][0] for c in rig.calls],[30,120,30,60,15])
            self.assertTrue(all(0<t<=120 for c in rig.calls for t in c['waits']))
        with tempfile.TemporaryDirectory() as temp:
            rig=Rig(Path(temp),mode='advance-deadline',at='suite')
            result,report=rig.run()
            self.assertEqual(result,1);self.assertEqual(len(rig.calls),4)
            self.assertFalse(report['passed'])

    def test_legacy_constructor_defaults_and_unsupported_suite_no_process(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'game').mkdir();(root/'game/project.godot').write_text('[application]\n')
            with patch.object(diagnostic.toolchain,'ROOT',root),patch.object(diagnostic.subprocess,'Popen') as launch:
                runner=diagnostic.VerboseInputMode(root/'out',240)
                self.assertEqual(runner.suite,'input_mode')
                with self.assertRaises(ValueError):diagnostic.VerboseInputMode(root/'unsupported',240,'match')
                launch.assert_not_called()

    def test_workflow_only_diagnostic_controls_name_and_output_changed(self):
        text=(SNAPSHOT/'.github/workflows/desktop-alpha.yml').read_text()
        self.assertIn('run: python scripts/run_native_regressions.py --output builds/desktop-playability/regressions',text)
        self.assertIn('timeout-minutes: 6\n        run: python scripts/diagnose_native_input_mode.py --failed-output builds/desktop-playability/regressions --output builds/desktop-playability/source-leak-verbose',text)
        diagnostic_step=text.split('- name: ARM Mac retain verbose first failed leak suite after strict failure',1)[1].split('- name:',1)[0]
        self.assertNotIn('continue-on-error',diagnostic_step)
        self.assertIn("steps.native_regressions.outcome == 'failure'",diagnostic_step)
        self.assertIn("steps.macos_leak_diagnostic_controls.outcome == 'success'",diagnostic_step)


if __name__=='__main__':unittest.main(verbosity=2)
