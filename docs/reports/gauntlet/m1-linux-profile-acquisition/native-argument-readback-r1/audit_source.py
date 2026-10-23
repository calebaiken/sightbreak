#!/usr/bin/env python3
"""History-free source invariants and source-derived replay, never native proof."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_acquire as acquire
import linux_profile_overhead as diagnostic
from test_linux_profile_thread_readback import old_guard, pinned_parser_model

HERE = Path(__file__).resolve().parent
inventory = json.loads((HERE / 'base-nondoc-inventory.json').read_text())['files']


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(text):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(text).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


old = (HERE / 'retained-r3/linux_profile_overhead.py').read_text()
assert digest(old.encode()) == inventory['scripts/linux_profile_overhead.py']['sha256']
current = (ROOT / 'scripts/linux_profile_overhead.py').read_text()
before, after = functions(old), functions(current)
assert before.keys() == after.keys()
changed = [name for name in before if before[name] != after[name]]
assert changed == ['validate_condition'], changed
expected = old.replace("'thread_mode_argument': 'safe', 'print_profile_setting': False}",
                       "'caller_is_main_thread': True, 'caller_is_render_thread': True, 'print_profile_setting': False}")
needle = "    for key, value in SETTINGS.items():\n"
addition = """    for key in ('caller_is_main_thread', 'caller_is_render_thread'):
        require(report['settings'].get(key) is True, 'Synchronous safe thread readback failed: ' + key)
    require(type(report.get('engine_arguments_filtered')) is list and
            all(type(value) is str for value in report['engine_arguments_filtered']), 'Missing filtered argument readback')
"""
expected = expected.replace(needle, addition + needle)
assert current == expected

old_acquire = (HERE / 'retained-r3/linux_profile_acquire.py').read_text()
assert digest(old_acquire.encode()) == inventory['scripts/linux_profile_acquire.py']['sha256']
current_acquire = (ROOT / 'scripts/linux_profile_acquire.py').read_text()
expected_acquire = old_acquire.replace("'builds/linux-profile-acquisition-r3'", "'builds/linux-profile-acquisition-r4'")
for path, wanted in acquire.ACCEPTED.items():
    tree = ast.parse(old_acquire)
    old_pins = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'ACCEPTED' for target in node.targets))
    assert diagnostic.digest(ROOT / path) == wanted
    expected_acquire = expected_acquire.replace(old_pins[path], wanted)
assert expected_acquire == current_acquire
assert functions(old_acquire) == functions(current_acquire)
assert diagnostic.ORDER == (False, True, True, False)
assert (diagnostic.WARM, diagnostic.SAMPLES, diagnostic.BOUND) == (32, 64, 180)
assert acquire.WHOLE == 1320 and acquire.CLEANUP == 5 and acquire.FAILURE_PUBLICATION == 10
assert acquire.CAPS == {'preflight': 60, 'stage': 45, 'version': 15, 'import': 120, 'import-inventory': 30,
                        'export': 120, 'artifact': 60, 'seal': 30, 'block': 750, 'finalize': 60}

old_fixture = (HERE / 'retained-r3/fixture-ec6b34ce.gd').read_text()
assert digest(old_fixture.encode()) == inventory['scripts/diagnostics/linux_profile_overhead.gd']['sha256']
fixture = diagnostic.FIXTURE.read_text()
expected_fixture = old_fixture.replace(
    '\t\t"thread_mode_argument": "safe", "print_profile_setting":',
    '\t\t"caller_is_main_thread": OS.get_thread_caller_id() == OS.get_main_thread_id(),\n'
    '\t\t"caller_is_render_thread": RenderingServer.is_on_render_thread(),\n'
    '\t\t"print_profile_setting":')
expected_fixture = expected_fixture.replace('''\tvar argv := OS.get_cmdline_args()
\tvar thread_index := argv.find("--render-thread")
\tif thread_index < 0 or thread_index + 1 >= argv.size() or argv[thread_index + 1] != "safe":
\t\t_fail("Pinned synchronous safe render-thread argument required")''', '''\t# Godot consumes --render-thread before exposing its filtered argument list.
\t# The controller verifies exact full argv separately; verify effective state
\t# here on the main thread, including a rejection of a separate render thread.
\tif OS.get_thread_caller_id() != OS.get_main_thread_id() or not RenderingServer.is_on_render_thread():
\t\t_fail("Pinned synchronous safe main/render thread identity required")''')
expected_fixture = expected_fixture.replace(
    '\treport = {"schema": 1, "token": token, "settings": _settings(), "engine": Engine.get_version_info(),\n',
    '\treport = {"schema": 1, "token": token, "settings": _settings(), "engine": Engine.get_version_info(),\n'
    '\t\t"engine_arguments_filtered": OS.get_cmdline_args(),\n')
assert fixture == expected_fixture

changed_nondoc = {'scripts/linux_profile_acquire.py', 'scripts/linux_profile_overhead.py',
                  'scripts/diagnostics/linux_profile_overhead.gd', 'scripts/test_linux_profile_overhead.py',
                  'scripts/test_linux_profile_acquire.py'}
for path, wanted in inventory.items():
    if path in changed_nondoc:
        continue
    assert digest((ROOT / path).read_bytes()) == wanted['sha256'], path

argv = json.loads((HERE / 'retained-r3/native-block/01-/off/launch.json').read_text())['engine_argv']
filtered, user, separate = pinned_parser_model(argv)
assert old_guard(argv) and not old_guard(filtered) and separate is False
warning = (HERE / 'retained-r3/native-block/01-/off/client.log').read_text().splitlines()[1]
assert acquire.strict_log(warning)
print(json.dumps({'passed_source_only': True, 'base_nondoc_files': len(inventory),
                  'unchanged_nondoc_files': len(inventory) - len(changed_nondoc),
                  'controller_changed_functions': changed,
                  'acquisition_functions_unchanged': True, 'fixture_exact_bounded_replacement': True,
                  'old_guard_accepts_recorded_full_argv': old_guard(argv),
                  'model_filtered_args': filtered, 'old_guard_accepts_model_filtered_args': old_guard(filtered),
                  'model_separate_thread': separate, 'actual_R3_thread_state': 'UNRETAINED',
                  'original_VSync_warning_strict_failure': True, 'native_run_authorized': False,
                  'scope': 'Source-derived parser model and pure evidence validation; no runtime argv or thread state observation.'}, indent=2))
