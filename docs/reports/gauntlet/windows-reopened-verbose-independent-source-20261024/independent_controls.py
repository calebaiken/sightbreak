#!/usr/bin/env python3
"""Read production AST only; no controller imports or native execution."""
import argparse
import ast
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(os.environ['REVIEW_SOURCE']).resolve()
CONTROLLER = (ROOT / 'scripts/verify_offline_export.py').read_text()
WORKFLOW = (ROOT / '.github/workflows/desktop-alpha.yml').read_text()
VALIDATE = (ROOT / 'scripts/validate.sh').read_text()
ADAPTER = "${{ runner.os == 'Windows' && inputs.verbose_reopened_shutdown && '--reopened-verbose' || '' }}"
COUNTS = {}


def main_ast(source):
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'main')


def parser(source, argv, host='Linux', native_validation=False):
    nodes = []
    for node in main_ast(source).body:
        if native_validation and isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'display_socket' for t in node.targets):
            break
        nodes.append(node)
        if not native_validation and isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'args' for t in node.targets):
            break
    namespace = dict(argparse=argparse, Path=Path, __doc__='isolated production parser',
                     os=SimpleNamespace(name='nt' if host == 'Windows' else 'posix', environ={}),
                     platform=SimpleNamespace(system=lambda: host),
                     shutil=SimpleNamespace(which=lambda value: '/declared/' + value))
    old = sys.argv
    try:
        sys.argv = ['controller', '--output', '/declared/output', *argv]
        with contextlib.redirect_stderr(io.StringIO()):
            exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-production-parser>', 'exec'), namespace)
    finally:
        sys.argv = old
    return namespace['args']


def commands(source, target, enabled, quit_after, width, height):
    main = main_ast(source)
    flags_nodes = [n for n in ast.walk(main) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'flags' for t in n.targets)]
    assert len(flags_nodes) == 2
    chosen = next(n for n in flags_nodes if ('--position' in ast.unparse(n)) == (target == 'windows'))
    calls = []
    environment = {'DECLARED': 'unchanged'}
    namespace = dict(str=str, executable=Path('/declared/SIGHTBREAK'), ui=SimpleNamespace(width=width, height=height),
                     args=SimpleNamespace(reopened_verbose=enabled, quit_after=quit_after, target=target),
                     initial_trace=Path('/declared/initial'), loaded_trace=Path('/declared/reopened'), env=environment,
                     launch=lambda *values: calls.append(values))
    exec(compile(ast.Module(body=[chosen], type_ignores=[]), '<exact-production-flags>', 'exec'), namespace)
    flag_copy = namespace['flags'][:]
    initial = next(n for n in ast.walk(main) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'client_command' for t in n.targets))
    parent = next(n for n in ast.walk(main) if isinstance(n, ast.Try) and initial in n.body)
    for node in parent.body[parent.body.index(initial):]:
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-production-initial>', 'exec'), namespace)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'client' for t in node.targets):
            break
    reopened = next(n for n in ast.walk(main) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'reopened' for t in n.targets))
    exec(compile(ast.Module(body=[reopened], type_ignores=[]), '<exact-production-reopened>', 'exec'), namespace)
    assert namespace['flags'] == flag_copy
    assert len(calls) == 2
    assert all(call[2] is environment for call in calls)
    return calls, flag_copy


def audit(controller=CONTROLLER, workflow=WORKFLOW, validate=VALIDATE):
    main = main_ast(controller)
    registrations = [n for n in ast.walk(main) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'add_argument' and any(isinstance(a, ast.Constant) and a.value == '--reopened-verbose' for a in n.args)]
    assert len(registrations) == 1
    registration = registrations[0]
    assert len(registration.args) == 1
    keywords = {kw.arg: ast.literal_eval(kw.value) for kw in registration.keywords}
    assert set(keywords) == {'action', 'help'} and keywords['action'] == 'store_true'
    accesses = [n for n in ast.walk(main) if isinstance(n, ast.Attribute) and n.attr == 'reopened_verbose']
    assert len(accesses) == 1 and isinstance(accesses[0].value, ast.Name) and accesses[0].value.id == 'args'
    launch_sites = [n for n in ast.walk(main) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'launch']
    assert sorted(ast.literal_eval(n.args[0]) for n in launch_sites) == ['client', 'reopened', 'xvfb']
    for target in ('linux', 'windows'):
        for quit_after in (0, 1, 17):
            for width, height in ((976, 549), (1280, 720), (1920, 1080)):
                disabled, flags = commands(controller, target, False, quit_after, width, height)
                enabled, _ = commands(controller, target, True, quit_after, width, height)
                base = ['/declared/SIGHTBREAK', '--audio-driver', 'Dummy', *flags]
                user_args = ['--', '--offline-validation', '--offline-trace-dir=/declared/initial']
                assert disabled[0][:2] == ('client', base + (['--quit-after', str(quit_after)] if quit_after else []) + user_args)
                assert enabled[0] == disabled[0]
                reopened = base + ['--', '--offline-validation', '--offline-trace-dir=/declared/reopened']
                assert disabled[1][:2] == ('reopened', reopened)
                assert enabled[1][:2] == ('reopened', base + ['--verbose'] + reopened[len(base):])
                assert enabled[1][1].count('--verbose') == 1
                assert enabled[1][1].index('--verbose') < enabled[1][1].index('--')
    assert workflow.count('      verbose_reopened_shutdown:\n') == 1
    block = workflow.split('      verbose_reopened_shutdown:\n')[1].split('permissions:')[0]
    assert [line.strip() for line in block.splitlines() if line.strip().startswith(('type:', 'required:', 'default:'))] == ['type: boolean', 'required: false', 'default: false']
    assert workflow.count(ADAPTER) == 1
    assert workflow.count('inputs.verbose_reopened_shutdown') == 1
    assert workflow.count('--reopened-verbose') == 1
    line = next(line for line in workflow.splitlines() if ADAPTER in line)
    assert line == "        run: python scripts/verify_offline_export.py --target ${{ matrix.target }} ${{ runner.os == 'Windows' && '--hosted-render-priority below-normal' || '' }} --display :102 --timeout 300 --output builds/desktop-playability/offline-input " + ADAPTER
    prefix = workflow[:workflow.index(line)]
    assert prefix.rstrip().endswith("- name: Living-player offline input and settings restart (Windows/Linux)\n        if: always() && steps.export.outcome == 'success' && runner.os != 'macOS'")
    assert validate.count('python3 scripts/test_reopened_shutdown_diagnostic.py -v\n') == 1


class IndependentSourceTests(unittest.TestCase):
    def test_actual_production_parser_defaults_and_options(self):
        count = 0
        for host in ('Linux', 'Windows'):
            target = host.lower()
            for selected in ([], ['--reopened-verbose'], ['--reopened-verbose', '--reopened-verbose']):
                for priority in (['inherited', 'below-normal'] if target == 'windows' else ['inherited']):
                    for timeout in ('300', '91.5'):
                        args = parser(CONTROLLER, ['--target', target, '--timeout', timeout, '--hosted-render-priority', priority, *selected], host, True)
                        self.assertIs(args.reopened_verbose, bool(selected))
                        self.assertEqual(args.timeout, float(timeout))
                        self.assertEqual(args.quit_after, 0)
                        self.assertEqual(args.hosted_render_priority, priority)
                        count += 1
            self.assertEqual(parser(CONTROLLER, [], host).target, target)
        COUNTS['accepted_parser_contexts'] = count

    def test_actual_production_parser_rejects_values_and_unknown_engine_options(self):
        variants = [['--reopened-verbose=false'], ['--reopened-verbose=true'], ['--reopened-verbose', 'false'], ['--reopened-verbose', 'true'], ['--reopened-verbose=--verbose'], ['--verbose'], ['--reopened-verbose', '--rendering-driver', 'opengl3']]
        for values in variants:
            with self.subTest(values=values), self.assertRaises(SystemExit) as error:
                parser(CONTROLLER, values)
            self.assertEqual(error.exception.code, 2)
        COUNTS['rejected_parser_contexts'] = len(variants)

    def test_existing_native_host_and_budget_rejections_remain(self):
        cases = [('Windows', ['--target', 'linux']), ('Linux', ['--target', 'windows']), ('Darwin', ['--target', 'linux']), ('Linux', ['--hosted-render-priority', 'below-normal']), ('Linux', ['--timeout', '0']), ('Linux', ['--quit-after', '-1'])]
        for host, values in cases:
            with self.subTest(host=host, values=values), self.assertRaises(SystemExit) as error:
                parser(CONTROLLER, values, host, True)
            self.assertEqual(error.exception.code, 2)
        COUNTS['preserved_native_rejections'] = len(cases)

    def test_exact_commands_all_actual_flag_platform_and_size_contexts(self):
        audit()
        COUNTS['paired_command_contexts'] = 2 * 3 * 3

    def test_workflow_all_typed_event_lane_host_input_contexts(self):
        expression = ADAPTER[4:-3].replace('runner.os', 'host').replace('inputs.verbose_reopened_shutdown', 'selected').replace('&&', ' and ').replace('||', ' or ')
        count = 0
        for event in ('push', 'workflow_dispatch'):
            for lane in ('all', 'linux', 'windows', 'arm-macos-ios'):
                for host in ('Linux', 'Windows', 'macOS'):
                    for requested in (None, False, True):
                        selected = requested if event == 'workflow_dispatch' else None
                        actual = eval(expression, {'__builtins__': {}}, dict(host=host, selected=selected))
                        self.assertEqual(actual, '--reopened-verbose' if host == 'Windows' and selected else '')
                        count += 1
        COUNTS['typed_adapter_contexts'] = count

    def test_direct_auditor_rejects_meaningful_mutations(self):
        variants = {
            'parser-default-on': (CONTROLLER.replace("action='store_true',", "action='store_true', default=True,"), WORKFLOW, VALIDATE),
            'parser-string-option': (CONTROLLER.replace("action='store_true',", "action='store',"), WORKFLOW, VALIDATE),
            'always-verbose': (CONTROLLER.replace("if args.reopened_verbose else []", "if True else []"), WORKFLOW, VALIDATE),
            'inverted-selection': (CONTROLLER.replace("if args.reopened_verbose else []", "if not args.reopened_verbose else []"), WORKFLOW, VALIDATE),
            'user-argument-position': (CONTROLLER.replace("*(['--verbose'] if args.reopened_verbose else []), '--',", "'--', *(['--verbose'] if args.reopened_verbose else []),"), WORKFLOW, VALIDATE),
            'initial-client-verbose': (CONTROLLER.replace("client_command = [str(executable), '--audio-driver', 'Dummy', *flags]", "client_command = [str(executable), '--audio-driver', 'Dummy', *flags, '--verbose']"), WORKFLOW, VALIDATE),
            'extra-native-flag': (CONTROLLER.replace("*(['--verbose'] if args.reopened_verbose else []), '--',", "*(['--verbose', '--headless'] if args.reopened_verbose else []), '--',"), WORKFLOW, VALIDATE),
            'linux-only-workflow': (CONTROLLER, WORKFLOW.replace(ADAPTER, ADAPTER.replace("'Windows'", "'Linux'")), VALIDATE),
            'unconditional-host-workflow': (CONTROLLER, WORKFLOW.replace(ADAPTER, "${{ inputs.verbose_reopened_shutdown && '--reopened-verbose' || '' }}"), VALIDATE),
            'workflow-default-on': (CONTROLLER, WORKFLOW.replace('      verbose_reopened_shutdown:\n', '      verbose_reopened_shutdown:\n        default: true\n'), VALIDATE),
            'workflow-extra-flag': (CONTROLLER, WORKFLOW.replace(ADAPTER, ADAPTER.replace("'--reopened-verbose'", "'--reopened-verbose --verbose'")), VALIDATE),
            'workflow-extra-step': (CONTROLLER, WORKFLOW + '\n        run: other ' + ADAPTER, VALIDATE),
            'missing-maintained-invocation': (CONTROLLER, WORKFLOW, VALIDATE.replace('python3 scripts/test_reopened_shutdown_diagnostic.py -v\n', '')),
        }
        for name, values in variants.items():
            self.assertNotEqual(values, (CONTROLLER, WORKFLOW, VALIDATE), name)
            with self.subTest(name=name), self.assertRaises(AssertionError):
                audit(*values)
        COUNTS['meaningful_mutation_rejections'] = len(variants)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IndependentSourceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps(dict(source=str(ROOT), methods=result.testsRun, failures=len(result.failures), errors=len(result.errors), cases=COUNTS), sort_keys=True))
    sys.exit(not result.wasSuccessful())
