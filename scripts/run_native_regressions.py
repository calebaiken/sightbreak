#!/usr/bin/env python3
"""Run source suites with native, per-suite user-data identities.

The private project changes only application/config's custom user-directory
settings. Scripts/assets and the shipping project remain untouched. Godot itself
reports the producing path; Python-only state variables are not treated as proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid

import toolchain
from native_log import failed


SUITES = ('actor', 'match', 'authority_order', 'state_privacy', 'movement_prediction', 'peer_lifecycle',
          'input_mode', 'menu_focus', 'offline_diagnostics', 'hud_objective_hint',
          'activity_provenance', 'bot_squad_symmetry')
PROBE = '''extends SceneTree
func _initialize() -> void:
    var destination := ""
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--receipt="):
            destination = argument.trim_prefix("--receipt=")
    var receipt := {"user_data_dir":OS.get_user_data_dir(), "data_dir":OS.get_data_dir(),
        "project_path":ProjectSettings.globalize_path("res://"), "os":OS.get_name(),
        "custom_user_dir":ProjectSettings.get_setting("application/config/custom_user_dir_name"),
        "uses_custom_user_dir":ProjectSettings.get_setting("application/config/use_custom_user_dir"),
        "profile_exists":FileAccess.file_exists("user://offline_training.json"),
        "diagnostics_exist":DirAccess.dir_exists_absolute(ProjectSettings.globalize_path("user://offline-diagnostics-unit"))}
    var file := FileAccess.open(destination, FileAccess.WRITE)
    if file == null:
        push_error("Cannot write native user-directory receipt")
        quit(2)
        return
    file.store_string(JSON.stringify(receipt, "  "))
    file.close()
    quit(0)
'''


def inventory(directory):
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob('*'))
            if path.is_file() and '.godot' not in path.relative_to(directory).parts}


class NativeSceneSuites:
    def __init__(self, output):
        self.output = Path(output).resolve()
        if self.output.exists() and any(self.output.iterdir()):
            raise RuntimeError('Preserve prior evidence; choose a fresh output directory')
        self.output.mkdir(parents=True, exist_ok=True)
        self.namespace = 'SIGHTBREAK-native-tests-' + uuid.uuid4().hex
        self.source = toolchain.ROOT / 'game'
        self.original = inventory(self.source)
        self.original_config = (self.source / 'project.godot').read_bytes().decode('utf-8')
        self.receipts, self.user_roots = [], set()
        self.probes = 0
        self.temporary = None
        self.report = {'namespace': self.namespace, 'source_resources_sha256': self.original,
                       'suite_timeout_seconds': 120, 'probe_timeout_seconds': 30,
                       'scope': 'Native source suites; not exported or physical-input acceptance'}

    def __enter__(self):
        self.report['engine'] = toolchain.verify_engine()
        self.temporary = tempfile.TemporaryDirectory(prefix='sightbreak-native-tests-')
        self.project = Path(self.temporary.name) / 'project'
        self.driver = Path(self.temporary.name) / 'user_directory_probe.gd'
        try:
            shutil.copytree(self.source, self.project)
            self.driver.write_text(PROBE, encoding='utf-8')
            self.configure('bootstrap')
            self.probe('bootstrap')
            self.execute('private-import', ['--headless', '--editor', '--import', '--quit'], 120)
            return self
        except BaseException as error:
            self.__exit__(type(error), error, error.__traceback__)
            raise

    def configure(self, suite):
        if not re.fullmatch('[a-z][a-z0-9_]*', suite):
            raise ValueError('Use a source-suite identifier')
        headers = list(re.finditer(r'^\[application\](\r?\n)', self.original_config, re.M))
        if len(headers) != 1 or re.search(r'^config/(use_custom_user_dir|custom_user_dir_name)=', self.original_config, re.M):
            raise RuntimeError('Unsupported source application configuration; shipping config was not changed')
        self.custom = self.namespace + '/' + suite
        header = headers[0]
        newline = header.group(1)
        settings = 'config/use_custom_user_dir=true' + newline + 'config/custom_user_dir_name=' + json.dumps(self.custom) + newline
        private = self.original_config[:header.end()] + settings + self.original_config[header.end():]
        (self.project / 'project.godot').write_bytes(private.encode('utf-8'))

    def execute(self, label, arguments, timeout):
        command = [toolchain.binary(), '--path', str(self.project), *arguments]
        started = time.monotonic()
        log_path = self.output / (label + '.log')
        with log_path.open('w', encoding='utf-8') as log:
            result = subprocess.run(command, env=toolchain.environment(), stdout=log,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        text = log_path.read_text(encoding='utf-8', errors='replace')
        receipt = {'command': command, 'exit': result.returncode, 'clean_log': not failed(text),
                   'wall_seconds': time.monotonic() - started, 'log': str(log_path)}
        if label != 'private-import':
            return receipt
        self.report['import'] = receipt
        if result.returncode or failed(text):
            raise RuntimeError(label + ' failed; raw output retained')
        return receipt

    def probe(self, label):
        self.probes += 1
        name = 'producer-%02d-%s' % (self.probes, label)
        destination = self.output / (name + '.json')
        run = self.execute(name, ['--headless', '--script', str(self.driver), '--', '--receipt=' + str(destination)], 30)
        if run['exit'] or not run['clean_log'] or not destination.is_file():
            raise RuntimeError('Native user-directory probe failed; raw output retained')
        receipt = json.loads(destination.read_text(encoding='utf-8'))
        expected = (Path(receipt['data_dir']) / self.custom).resolve()
        actual = Path(receipt['user_data_dir']).resolve()
        if (not receipt['uses_custom_user_dir'] or receipt['custom_user_dir'] != self.custom
                or actual != expected or Path(receipt['project_path']).resolve() != self.project.resolve()
                or expected.parent.name != self.namespace or expected.parent.is_symlink()):
            raise RuntimeError('Engine user-directory identity does not match this owned isolated project')
        self.user_roots.add(expected.parent)
        return {**receipt, 'producer_receipt': str(destination), 'run': run}

    def prepare(self, suite):
        if suite not in SUITES:
            raise ValueError('Unknown maintained source suite: ' + suite)
        self.configure(suite)
        return self.probe('before-' + suite)

    def run(self, suite):
        before = self.prepare(suite)
        if before['profile_exists'] or before['diagnostics_exist']:
            raise RuntimeError('Refusing existing suite state; no save or prior evidence was overwritten')
        receipt = self.execute(suite, ['--headless', '--script', 'res://tests/' + suite + '_test.gd'], 120)
        receipt.update(suite=suite, before=before, after=self.probe('after-' + suite))
        user_dir = Path(receipt['after']['user_data_dir'])
        receipt['produced_files_sha256'] = inventory(user_dir)
        shutil.copytree(user_dir, self.output / (suite + '-userdata'))
        self.receipts.append(receipt)
        (self.output / 'results.json').write_text(json.dumps(self.receipts, indent=2) + '\n', encoding='utf-8')
        if receipt['exit'] or not receipt['clean_log']:
            raise RuntimeError(suite + ' failed; raw output retained')
        return receipt

    def __exit__(self, _type, _value, _traceback):
        errors = []
        self.report.update(passed=False, source_resources_unchanged=False,
                           copied_resources_unchanged=False,
                           temporary_project_removed=self.temporary is None,
                           cleanup=[], finalization_failures=[])

        def record(stage, error):
            failure = {'stage': stage, 'type': type(error).__name__, 'message': str(error)}
            self.report['finalization_failures'].append(failure)
            errors.append(error)
            return failure

        try:
            self.report['source_resources_unchanged'] = inventory(self.source) == self.original
            if not self.report['source_resources_unchanged']:
                raise RuntimeError('Source resource bytes changed during isolated source tests')
        except BaseException as error:
            record('source_resource_inventory', error)
        if self.temporary is not None:
            try:
                current = inventory(self.project) if self.project.exists() else {}
                self.report['copied_resources_unchanged'] = (
                    {name: digest for name, digest in current.items() if name != 'project.godot'}
                    == {name: digest for name, digest in self.original.items() if name != 'project.godot'})
                if not self.report['copied_resources_unchanged']:
                    raise RuntimeError('Copied resource bytes changed during isolated source tests')
            except BaseException as error:
                record('copied_resource_inventory', error)
        for root in sorted(self.user_roots):
            outcome = {'user_namespace': str(root), 'removed': False}
            self.report['cleanup'].append(outcome)
            try:
                if root.name != self.namespace or root.is_symlink():
                    raise RuntimeError('Refusing cleanup outside the unique owned namespace')
                shutil.rmtree(root)
                outcome['removed'] = not root.exists()
                if not outcome['removed']:
                    raise RuntimeError('Owned user-data namespace remained after cleanup')
            except BaseException as error:
                outcome['error'] = record('user_namespace_cleanup', error)
        if self.temporary is not None:
            try:
                private = Path(self.temporary.name)
                self.temporary.cleanup()
                self.report['temporary_project_removed'] = not private.exists()
                if not self.report['temporary_project_removed']:
                    raise RuntimeError('Temporary project remained after cleanup')
            except BaseException as error:
                self.report['temporary_project_cleanup_error'] = record('temporary_project_cleanup', error)
        self.report['failure'] = ({'type': _type.__name__, 'message': str(_value)} if _type is not None
                                  else self.report['finalization_failures'][0] if errors else None)
        self.report['passed'] = (_type is None and not errors and bool(self.receipts) and bool(self.user_roots)
                                and self.report['source_resources_unchanged'] and self.report['copied_resources_unchanged']
                                and self.report['temporary_project_removed']
                                and all(item['exit'] == 0 and item['clean_log'] for item in self.receipts)
                                and len(self.report['cleanup']) == len(self.user_roots)
                                and all(item['removed'] for item in self.report['cleanup']))
        try:
            pending = self.output / 'isolation.json.pending'
            pending.write_text(json.dumps(self.report, indent=2) + '\n', encoding='utf-8')
            pending.replace(self.output / 'isolation.json')
        except BaseException as error:
            # Cleanup has already been attempted. Preserve an existing native
            # exception if writing the receipt also fails.
            failure = record('receipt_write', error)
            self.report['passed'] = False
            if self.report['failure'] is None:
                self.report['failure'] = failure
        if _type is None and errors:
            raise errors[0]
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--suites', nargs='+', choices=SUITES, default=SUITES)
    args = parser.parse_args()
    if len(set(args.suites)) != len(args.suites):
        parser.error('Select each source suite once')
    with NativeSceneSuites(args.output) as runner:
        for suite in args.suites:
            runner.run(suite)
    print(json.dumps({'passed': runner.report['passed'], 'suites': args.suites,
                      'source_resources_unchanged': runner.report['source_resources_unchanged'],
                      'temporary_project_removed': runner.report['temporary_project_removed']}))
    return 0 if runner.report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
