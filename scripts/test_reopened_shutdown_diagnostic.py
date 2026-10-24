#!/usr/bin/env python3
"""Pure controls for actual controller AST; no native process or input is run."""
import argparse
import ast
import contextlib
import io
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / 'scripts/verify_offline_export.py').read_text()
TREE = ast.parse(SOURCE)
MAIN = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
WORKFLOW = (ROOT / '.github/workflows/desktop-alpha.yml').read_text()
ADAPTER = "${{ runner.os == 'Windows' && inputs.verbose_reopened_shutdown && '--reopened-verbose' || '' }}"


def arguments(extra):
    # Execute the production parser statements, stopping before platform/runtime setup.
    statements = []
    for node in MAIN.body:
        statements.append(node)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'args' for t in node.targets):
            break
    namespace = dict(argparse=argparse, Path=Path, os=os, shutil=shutil)
    parser_code = ast.Module(body=statements, type_ignores=[])
    # Inject argv into the real parse_args call without changing parser registration.
    parser_code.body[-1] = ast.Assign(targets=[ast.Name(id='args', ctx=ast.Store())],
                                     value=ast.Call(func=ast.Attribute(value=ast.Name(id='parser', ctx=ast.Load()),
                                                                      attr='parse_args', ctx=ast.Load()),
                                                    args=[ast.Constant(value=None)], keywords=[]))
    import sys
    previous = sys.argv
    try:
        sys.argv = ['verify_offline_export.py', '--output', '/declared/output', *extra]
        exec(compile(ast.fix_missing_locations(parser_code), '<production-parser>', 'exec'), namespace)
    finally:
        sys.argv = previous
    return namespace['args']


def commands(enabled, flags, quit_after=0):
    calls = []
    namespace = dict(str=str, executable='/declared/SIGHTBREAK.exe', flags=flags,
                     args=SimpleNamespace(reopened_verbose=enabled, quit_after=quit_after),
                     initial_trace=Path('/declared/initial'), loaded_trace=Path('/declared/reopened'),
                     env={'DECLARED': 'same'}, launch=lambda *args: calls.append(args))
    # Execute exact production initial construction/launch statements and reopened call.
    all_nodes = list(ast.walk(MAIN))
    initial = next(n for n in all_nodes if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'client_command' for t in n.targets))
    parent = next(n for n in all_nodes if isinstance(n, ast.Try) and initial in n.body)
    start = parent.body.index(initial)
    for node in parent.body[start:]:
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<production-command>', 'exec'), namespace)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'client' for t in node.targets):
            break
    reopened = next(n for n in all_nodes if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'reopened' for t in n.targets))
    exec(compile(ast.Module(body=[reopened], type_ignores=[]), '<production-reopened>', 'exec'), namespace)
    return calls


class ReopenedDiagnosticTests(unittest.TestCase):
    def test_real_parser_defaults_to_disabled_and_accepts_opt_in(self):
        for target in ('windows', 'linux'):
            with self.subTest(target=target):
                default = arguments(['--target', target])
                enabled = arguments(['--target', target, '--reopened-verbose'])
                self.assertIs(default.reopened_verbose, False)
                self.assertIs(enabled.reopened_verbose, True)
                self.assertEqual(default.timeout, 300)
                self.assertEqual(enabled.timeout, 300)
                self.assertEqual(default.quit_after, enabled.quit_after)
                self.assertEqual(default.hosted_render_priority, enabled.hosted_render_priority)

    def test_real_parser_rejects_a_value_instead_of_silently_enabling(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            arguments(['--reopened-verbose=false'])
        self.assertEqual(error.exception.code, 2)

    def test_only_reopened_engine_argv_changes_and_original_commands_are_preserved(self):
        for flags in (['--position', '0,0', '--resolution', '976x549'],
                      ['--accessibility', 'disabled', '--accessibility-driver', 'dummy']):
            for quit_after in (0, 17):
                with self.subTest(flags=flags, quit_after=quit_after):
                    disabled = commands(False, flags, quit_after)
                    enabled = commands(True, flags, quit_after)
                    base = ['/declared/SIGHTBREAK.exe', '--audio-driver', 'Dummy', *flags]
                    initial = base + (['--quit-after', '17'] if quit_after else [])
                    self.assertEqual(disabled[0], ('client', initial + ['--', '--offline-validation',
                                                       '--offline-trace-dir=/declared/initial'], {'DECLARED': 'same'}))
                    original = base + ['--', '--offline-validation', '--offline-trace-dir=/declared/reopened']
                    self.assertEqual(disabled[1], ('reopened', original, {'DECLARED': 'same'}))
                    self.assertEqual(enabled[0], disabled[0])
                    self.assertEqual(enabled[1], ('reopened', base + ['--verbose'] + original[len(base):],
                                                  {'DECLARED': 'same'}))
                    self.assertEqual(enabled[1][1].count('--verbose'), 1)
                    self.assertLess(enabled[1][1].index('--verbose'), enabled[1][1].index('--'))
                    self.assertEqual(flags, base[3:])

    def test_workflow_default_is_false_and_adapter_occurs_only_on_existing_step(self):
        self.assertEqual(WORKFLOW.count('      verbose_reopened_shutdown:\n'), 1)
        block = WORKFLOW.split('      verbose_reopened_shutdown:\n', 1)[1].split('permissions:', 1)[0]
        self.assertEqual([line.strip() for line in block.splitlines() if line.strip().startswith(('type:', 'required:', 'default:'))],
                         ['type: boolean', 'required: false', 'default: false'])
        self.assertEqual(WORKFLOW.count(ADAPTER), 1)
        line = next(line for line in WORKFLOW.splitlines() if ADAPTER in line)
        self.assertIn('python scripts/verify_offline_export.py --target ${{ matrix.target }}', line)
        self.assertIn('--display :102 --timeout 300 --output builds/desktop-playability/offline-input ', line)
        # Evaluate this restricted production Boolean expression for every host/input context.
        expression = ADAPTER[4:-3].replace('runner.os', 'runner_os').replace('inputs.verbose_reopened_shutdown', 'selected')
        expression = expression.replace('&&', ' and ').replace('||', ' or ')
        for host in ('Windows', 'Linux', 'macOS'):
            for selected in (None, False, True):
                with self.subTest(host=host, selected=selected):
                    actual = eval(expression, {'__builtins__': {}}, dict(runner_os=host, selected=selected))
                    self.assertEqual(actual, '--reopened-verbose' if host == 'Windows' and selected else '')


if __name__ == '__main__':
    unittest.main()
