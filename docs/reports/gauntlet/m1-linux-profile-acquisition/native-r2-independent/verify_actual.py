#!/usr/bin/env python3
"""Read-only independent audit of the failed, sole corrected-source R2 acquisition.

Only Git reads, /proc observations, binary hashing and archive I/O occur. No
builder module is imported and no engine is invoked. A zero auditor exit means
the retained FAILURE was verified, never that the acquisition passed.
"""
import ast
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import struct
import tarfile
import time
import zipfile

SOURCE = Path('/workspace/sightbreak-linux-profile-fixture-native-types')
RAW = SOURCE / 'builds/linux-profile-acquisition-r2'
REPORT = Path(__file__).resolve().parent
FROZEN = '216d39ada8f9d11e2d8544d01fde42da49607b14'
GAME_TREE = '55691684d31d44f1680141954bbe530443de9d1f'
BASE = '3fd9718bc066bedf879f241760c106ee96923060'
CAPS = {'preflight': 60, 'stage': 45, 'version': 15, 'import': 120, 'import-inventory': 30, 'export': 120, 'artifact': 60}
checks, observations = [], {}


def check(value, name, detail=None):
    checks.append({'name': name, 'passed': bool(value), 'detail': detail})
    if not value:
        raise AssertionError(name + ': ' + repr(detail))


def read_json(path):
    def unique(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('Duplicate key: ' + k)
            result[k] = v
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def identity(path):
    path = Path(path)
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
            size += len(block)
    return {'bytes': size, 'sha256': h.hexdigest()}


def bytes_identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args])


def strict_lines(raw):
    found = []
    base = re.compile(r'\b(?:SCRIPT ERROR|Parse Error|ERROR|WARNING)\s*:|\bwarning\b|'
                      r'ObjectDB.*leaked|Leaked instance|resources? still in use|'
                      r'orphan(?:ed)? (?:node|object)', re.I)
    orphan = re.compile(r'\borphan(?:ed)?\s+StringName\b', re.I)
    before = re.compile(r'\b(\d+)\s+unclaimed\s+string\s+names?\b', re.I)
    after = re.compile(r'\bunclaimed\s+string\s+names?\s*[:=]\s*(\d+)\b', re.I)
    for number, line in enumerate(raw.decode('utf-8', errors='replace').splitlines(), 1):
        reasons = []
        if base.search(line):
            reasons.append('original_strict_forms')
        if orphan.search(line):
            reasons.append('standalone_orphan_stringname')
        if any(int(m[1]) > 0 for rx in (before, after) for m in rx.finditer(line)):
            reasons.append('positive_unclaimed_string_names')
        if reasons:
            found.append({'line': number, 'text': line, 'reasons': reasons})
    return found


def proc_snapshot():
    result = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            text = (path / 'stat').read_text()
            tail = text[text.rfind(')') + 2:].split()
            result[int(path.name)] = {'pid': int(path.name), 'start_ticks': int(tail[19]),
                                     'pgid': int(tail[2]), 'sid': int(tail[3]),
                                     'comm': text[text.find('(') + 1:text.rfind(')')]}
        except (OSError, ValueError, IndexError):
            pass
    return result


def emit(name, value):
    (REPORT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    started = time.monotonic()
    raw_paths = sorted(path for path in RAW.rglob('*') if path.is_file())
    check(not any(path.is_symlink() for path in RAW.rglob('*')), 'raw_has_no_symlinks')
    registry = {path.relative_to(RAW).as_posix(): identity(path) for path in raw_paths}
    check(len(registry) == 247, 'exact_actual_raw_file_count', len(registry))
    overall = read_json(RAW / 'overall.json')
    check(overall['source_commit'] == FROZEN and overall['passed'] is False,
          'actual_receipt_records_frozen_failure')
    check(overall['error'] == 'Extra data: line 4 column 1 (char 26)' and
          overall['error_type'] == 'JSONDecodeError', 'actual_failure_boundary')
    check((RAW / 'attempt.claim').read_bytes() == (FROZEN + '\n').encode(), 'one_shot_claim')
    outer_paths = {name: SOURCE / '.local' / ('linux-profile-acquisition-r2-' + name)
                   for name in ('wrapper.stdout', 'wrapper.stderr', 'outer-tool-receipt.json')}
    outer_registry = {name: identity(path) for name, path in outer_paths.items()}
    outer = read_json(outer_paths['outer-tool-receipt.json'])
    check(outer['source'] == FROZEN and outer['release'] == '90a9cab61a554672306d5a630e15e25ea93c8dd0' and
          outer['actual_supervisor_invocation']['initial_tool_response']['session_id'] == 95035 and
          outer['terminal_tool_response']['exit_code'] == 1, 'root_outer_actual_exit_1')
    setup = outer['shell_setup_failure']['actual_tool_response']
    check(setup['exit_code'] == 1 and setup['output'] ==
          '/bin/bash: line 1: .local/linux-profile-acquisition-r2-wrapper.stdout: No such file or directory\n',
          'separate_pre_supervisor_shell_redirection_failure_preserved')
    check(read_json(outer_paths['wrapper.stdout']) == {'passed': False, 'output': str(RAW),
          'error': 'Extra data: line 4 column 1 (char 26)'}, 'wrapper_stdout_agrees_with_failure')
    check(outer_paths['wrapper.stderr'].read_bytes() == b'', 'wrapper_stderr_empty')
    observations['outer_receipt_scope'] = {'terminal_exit': 1, 'session_id': 95035,
        'terminal_observed_clock': outer['terminal_observed_clock'],
        'shell_setup_failure': outer['shell_setup_failure'],
        'scope': 'Original root tool results distinguish shell setup failure from one actual supervisor. Poll duration is not whole runtime.'}

    # Current finite observation is independent of the wrapper's unreached final gate.
    source_start = time.monotonic()
    check(git('rev-parse', 'HEAD').decode().strip() == FROZEN, 'current_source_exact_head')
    check(git('status', '--porcelain', '--untracked-files=all') == b'', 'current_source_clean')
    check(git('rev-parse', FROZEN + ':game').decode().strip() == GAME_TREE, 'frozen_game_tree')
    before = read_json(RAW / 'original-before.json')
    before_map = {row['path']: row for row in before}
    check(len(before_map) == len(before) == 430, 'original_before_430_unique_paths')
    tracked = git('ls-tree', '-rz', FROZEN, '--', 'game', 'scripts')
    parsed = {}
    for entry in tracked.split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, kind, blob = meta.decode().split()
            parsed[path.decode()] = (mode, kind, blob)
    check(set(parsed) == set(before_map), 'preflight_source_inventory_matches_frozen_closed_set')
    lsfile_rows = {}
    for entry in (RAW / '03-git.stdout.log').read_bytes().split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, blob, stage = meta.decode().split()
            lsfile_rows[path.decode()] = (mode, blob, stage)
    check(set(lsfile_rows) == set(parsed), 'actual_index_read_matches_frozen_closed_set')
    for name, (mode, kind, blob) in parsed.items():
        row = before_map[name]
        path = SOURCE / name
        raw = path.read_bytes()
        check(kind == 'blob' and mode in ('100644', '100755') and
              row['git_blob'] == blob and row['mode'] == mode and
              lsfile_rows[name] == (mode, blob, '0'), 'source_git_identity:' + name)
        check(not path.is_symlink() and bytes_identity(raw) ==
              {'bytes': row['bytes'], 'sha256': row['sha256']} and
              hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == blob,
              'source_current_bytes:' + name)
    for name in ('scripts/linux_profile_overhead.py', 'scripts/diagnostics/linux_profile_overhead.tscn',
                 'scripts/test_linux_profile_overhead.py'):
        check(git('show', FROZEN + ':' + name) == git('show', BASE + ':' + name), 'accepted_component_unchanged:' + name)
    fixture = 'scripts/diagnostics/linux_profile_overhead.gd'
    check(git('show', FROZEN + ':' + fixture) == git('show', BASE + ':' + fixture).replace(
          b'var keys := value.keys()', b'var keys: Array = value.keys()'), 'only_reviewed_fixture_type_change')
    for log in ('09-git.stdout.log', '13-git.stdout.log'):
        check((RAW / log).read_bytes() == (RAW / '03-git.stdout.log').read_bytes(), 'later_actual_source_index_equal:' + log)
    observations['source_observation'] = {'started_monotonic': source_start,
        'ended_monotonic': time.monotonic(), 'source_files': len(parsed),
        'source_uids': sum(name.endswith('.uid') for name in parsed),
        'scope': 'Independent finite post-failure read; wrapper final source gate was never reached.'}

    # Reconstruct both staged overlays from frozen stock bytes, without the builder.
    original = read_json(RAW / 'project-stage.json')
    amended = read_json(RAW / 'diagnostic-stage.json')
    amendment = read_json(RAW / 'diagnostic-packaging-amendment.json')
    check(original['source']['commit'] == FROZEN and original['source']['game_tree'] == GAME_TREE,
          'actual_stage_source')
    base_files = {name[5:]: row['sha256'] for name, row in before_map.items()
                  if name.startswith('game/') and 'tests' not in Path(name[5:]).parts}
    check(original['base_files'] == base_files == amended['base_files'], 'actual_stage_base_closed_set')
    project_stock = (SOURCE / 'game/project.godot').read_text()
    preset_stock = (SOURCE / 'game/export_presets.cfg').read_text()
    overlay_project = project_stock.replace('run/main_scene="res://main.tscn"',
                    'run/main_scene="res://diagnostics/linux_profile_overhead.tscn"').replace(
                    '[rendering]\n', '[rendering]\ndriver/threads/thread_model=1\n') + '\n[debug]\nsettings/stdout/print_gpu_profile=false\n'
    overlay_preset = preset_stock.replace('include_filter=""', 'include_filter="diagnostics/*.json"', 1)
    check(amendment['before'] == {'project.godot': overlay_project, 'export_presets.cfg': overlay_preset},
          'original_diagnostic_overlay_exact')
    amended_text = {'project.godot': overlay_project + '\n[editor]\nexport/convert_text_resources_to_binary=false\n',
                    'export_presets.cfg': overlay_preset.replace('script_export_mode=2', 'script_export_mode=0', 1)}
    check(amendment['after'] == amended_text, 'only_registered_text_packaging_amendment')
    check(amendment['original_stage_record_sha256'] == registry['project-stage.json']['sha256'], 'amendment_original_binding')
    check(amended['diagnostic_packaging'] == {'script_export_mode': 0,
          'convert_text_resources_to_binary': False}, 'actual_packaging_receipt')
    check(len(amended['files']) == len(original['files']) == 131 and
          set(amended['files']) == set(base_files) | {'diagnostics/linux_profile_overhead.gd',
              'diagnostics/linux_profile_overhead.tscn', 'diagnostics/source_ledger.json'}, 'stage_131_expected_paths')
    for name, wanted in amended['files'].items():
        check(registry['project/' + name] == wanted, 'staged_source_unchanged:' + name)
        if name in amended_text:
            check((RAW / 'project' / name).read_bytes() == amended_text[name].encode(), 'actual_overlay_bytes:' + name)
        else:
            check(original['files'][name] == wanted, 'unchanged_original_stage_entry:' + name)
    for name, text in amendment['before'].items():
        check(original['files'][name] == bytes_identity(text.encode()), 'original_overlay_identity:' + name)
    for basename in ('linux_profile_overhead.gd', 'linux_profile_overhead.tscn'):
        check((RAW / 'project/diagnostics' / basename).read_bytes() ==
              (SOURCE / 'scripts/diagnostics' / basename).read_bytes(), 'actual_frozen_fixture:' + basename)
    ledger = read_json(RAW / 'project/diagnostics/source_ledger.json')
    check(ledger['content'] == base_files and ledger['source'] == amended['source'] and
          registry['project/diagnostics/source_ledger.json']['sha256'] == amended['source_ledger_sha256'], 'staged_ledger')
    failed_stage = read_json(RAW / 'failed-preparation-complete-stage.json')
    actual_stage = {name[8:]: value for name, value in registry.items() if name.startswith('project/')}
    check(actual_stage == failed_stage and len(actual_stage) == 194, 'failure_stage_inventory_exact_readback')
    generated = set(actual_stage) - set(amended['files'])
    check(len(generated) == 63 and len([name for name in generated if name.startswith('.godot/')]) == 62 and
          generated - {name for name in generated if name.startswith('.godot/')} == {'diagnostics/linux_profile_overhead.gd.uid'},
          'only_root_cache_and_fixture_uid_generated')
    uid = (RAW / 'project/diagnostics/linux_profile_overhead.gd.uid').read_bytes()
    check(re.fullmatch(rb'uid://[a-z0-9]+\n', uid) is not None and
          (RAW / 'failed-preparation-generated-uids/diagnostics/linux_profile_overhead.gd.uid').read_bytes() == uid,
          'generated_uid_original_and_failure_copy_equal')
    observations['stage'] = {'base_files': len(base_files), 'sealed_source_files': 131,
        'current_stage_files': 194, 'generated_cache_files': 62, 'generated_fixture_uid': uid.decode().strip(),
        'qualification': 'Import and export inventories were actually reached; failed artifact inventory and current readback preserve the same 194 files.'}

    # Actual raw logs: retain all streams, including empty files and nonfatal diagnostics.
    log_results = {}
    for name in sorted(n for n in registry if n.endswith('.log')):
        log_results[name] = strict_lines((RAW / name).read_bytes())
    check(len(log_results) == 26, 'all_thirteen_complete_stdout_stderr_pairs_scanned')
    check(not any(log_results.values()), 'all_actual_raw_streams_strict_clean_including_StringName_forms')
    error_text = (RAW / '06-import.stderr.log').read_text()
    check(error_text == "Unable to open Android 'build-tools' directory.\n", 'android_directory_diagnostic_retained_verbatim')
    check((RAW / '10-export.stderr.log').read_text() == error_text, 'same_export_android_diagnostic')
    check((RAW / 'project/diagnostics/linux_profile_overhead.gd').read_text().splitlines()[106].strip() ==
          'var keys: Array = value.keys()', 'actual_imported_fixture_has_reviewed_type_declaration')
    scanner_controls = {'orphan': ('Orphan StringName: Master', True),
        'positive_prefix': ('StringName: 1 unclaimed string names at exit.', True),
        'positive_suffix': ('unclaimed string names: 2', True),
        'zero': ('StringName: 0 unclaimed string names at exit.', False),
        'clean': ('Godot Engine v4.7.2.stable.official.ed1daf0bf', False)}
    for name, (text, expected) in scanner_controls.items():
        check(bool(strict_lines(text.encode())) == expected, 'independent_StringName_scanner_control:' + name)
    check(not any(re.search(r'GPU PROFILE', (RAW / name).read_text(errors='replace')) for name in log_results), 'no_profiler_blocks_emitted')
    observations['strict_log_findings'] = log_results

    phases = overall['phases']
    check([p['name'] for p in phases] == list(CAPS), 'exact_reached_phase_sequence')
    check([p['passed'] for p in phases] == [True, True, True, True, True, True, False], 'six_successful_phases_then_artifact_failure')
    check(overall['whole_cap_seconds'] == 1320 and overall['whole_deadline_monotonic'] ==
          overall['start_monotonic'] + 1320, 'original_whole_deadline_preserved')
    for index, phase in enumerate(phases):
        name = phase['name']
        check(phase['cap_seconds'] == CAPS[name] and phase['deadline_monotonic'] ==
              min(phase['started_monotonic'] + CAPS[name], overall['whole_deadline_monotonic']), 'phase_original_deadline:' + name)
        check(all(type(phase[k]) in (int, float) and math.isfinite(phase[k]) for k in
                  ('started_monotonic', 'ended_monotonic', 'elapsed_seconds')) and
              0 <= phase['elapsed_seconds'] < CAPS[name] and
              phase['ended_monotonic'] - phase['started_monotonic'] == phase['elapsed_seconds'] and
              phase['ended_monotonic'] < phase['deadline_monotonic'], 'phase_observed_before_cap:' + name)
        if index:
            check(phase['started_monotonic'] >= phases[index-1]['ended_monotonic'], 'phase_serial_order:' + name)
        if phase['passed']:
            phase_file = RAW / (name + '.phase.json')
            snapshot = read_json(phase_file)
            check(identity(phase_file)['sha256'] == phase['publication_sha256'] and
                  all(snapshot[k] == phase[k] for k in ('name', 'cap_seconds', 'started_monotonic', 'deadline_monotonic', 'value')) and
                  snapshot['passed'] is False, 'pre_return_phase_publication:' + name)
    check(overall['last_observation'] == 'source inventory' and
          overall['elapsed_seconds'] == overall['end_monotonic'] - overall['start_monotonic'] and
          overall['end_monotonic'] < overall['whole_deadline_monotonic'], 'last_budget_observation_scope')
    observations['timings'] = {'phases': [{k:p[k] for k in ('name', 'cap_seconds', 'elapsed_seconds', 'passed')} for p in phases],
        'last_budget_elapsed_seconds': overall['elapsed_seconds'],
        'limitation': 'Last budget observation precedes failure inventory/publication. Exact failure-publication and whole-return elapsed times were not retained.'}

    commands = overall['commands']
    check([c['label'] for c in commands] == ['git', 'git', 'git', 'stage', 'version', 'import', 'git', 'git', 'git', 'export', 'git', 'git', 'git'], 'only_thirteen_actual_commands')
    check(all(c['exit_code'] == 0 and c['timeout'] is False for c in commands), 'all_child_exits_zero_no_timeout')
    expected_engine = '/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64'
    check(commands[4]['argv'] == ['/usr/bin/taskset', '-c', '0,1', expected_engine, '--headless', '--version'] and
          commands[5]['argv'] == ['/usr/bin/taskset', '-c', '0,1', expected_engine, '--headless', '--editor',
               '--path', str(RAW / 'project'), '--import', '--quit'], 'exact_registered_engine_commands')
    check((RAW / '05-version.stdout.log').read_bytes() == b'4.7.2.stable.official.ed1daf0bf\n', 'actual_engine_version')
    check(all(commands[i]['cwd'] == str(RAW / 'project') for i in (4, 5, 9)), 'private_stage_engine_cwd')
    check(commands[9]['argv'] == ['/usr/bin/taskset', '-c', '0,1', expected_engine, '--headless', '--path', str(RAW / 'project'), '--export-debug', 'Linux', str(RAW / 'export/linux-profile-diagnostic.x86_64')], 'single_exact_registered_export')
    snap = proc_snapshot()
    for index, command in enumerate(commands, 1):
        label = command['label']
        phase = next(p for p in phases if p['deadline_monotonic'] == command['phase_deadline_monotonic'])
        check(phase['started_monotonic'] <= command['started_monotonic'] < command['ended_monotonic'] < phase['ended_monotonic'] and
              command['phase_deadline_monotonic'] == phase['deadline_monotonic'] and
              command['whole_deadline_monotonic'] == overall['whole_deadline_monotonic'], 'command_inside_original_phase:' + str(index))
        for stream in ('stdout', 'stderr'):
            row = command[stream]
            name = f'{index:02d}-{label}.{stream}.log'
            check(row['path'] == str(RAW / name) and
                  registry[name] == {k:row[k] for k in ('bytes', 'sha256')} == row['failure_observation'],
                  'raw_command_log_identity:' + name)
        check(command['log_failures'] == [h['text'] for stream in ('stdout', 'stderr')
                  for h in log_results[f'{index:02d}-{label}.{stream}.log']], 'raw_log_matches_receipt:' + str(index))
        root = command['root_identity']
        check(root['pid'] == command['pid'] and root['pgid'] == root['sid'] == command['pid'] and
              command['signals'] == [] and command['cleanup']['complete'] is True and
              command['cleanup']['forced'] is False and command['cleanup']['root_reaped'] is True and
              command['cleanup']['terminal_original_group'] == command['cleanup']['terminal_original_session'] ==
              command['cleanup']['terminal_observed_identities'] == [] and
              0 <= command['cleanup']['seconds'] < 5, 'recorded_natural_owned_cleanup:' + str(index))
        check(all(not (row['pid'] in snap and snap[row['pid']]['start_ticks'] == row['start_ticks'])
                  for row in command['identity_observations']) and
              not any(row['pgid'] == root['pgid'] or row['sid'] == root['sid'] for row in snap.values()),
              'independent_current_owned_absence:' + str(index))
    supervisor = overall['host_before']
    check(not (supervisor['pid'] in snap and snap[supervisor['pid']]['start_ticks'] == supervisor['start_ticks']), 'supervisor_current_identity_absent')
    native_now = [row for row in snap.values() if re.search(r'godot|xvfb|sightbreak', row['comm'], re.I)]
    check(native_now == [], 'independent_current_recognized_native_names_absent', native_now)
    check(not Path('/tmp/.X11-unix/X99127').exists() and not Path('/tmp/.X99127-lock').exists(), 'fixed_display_currently_absent')
    observations['cleanup'] = {'commands': [{'label': c['label'], 'root_identity': c['root_identity'],
        'observed_identity_count': len(c['identity_observations']), 'cleanup': c['cleanup']} for c in commands],
        'independent_snapshot_monotonic': time.monotonic(), 'recognized_names_now': native_now,
        'scope': 'Recorded observed exact PID/start identities and original group/session, plus later independent absence. No unobserved escaped-descendant guarantee.'}

    env = overall['selected_environment']
    expected_env = {'LP_NUM_THREADS': '2', 'LIBGL_ALWAYS_SOFTWARE': '1', 'GODOT_SILENCE_ROOT_WARNING': '1',
        'SIGHTBREAK_STATE_DIR': str(RAW / 'private-export-state'), 'SIGHTBREAK_BUILDS_DIR': str(RAW / 'export'),
        'ANDROID_USER_HOME': str(RAW / 'private-export-state/android'), 'TMPDIR': str(RAW / 'tmp'),
        'MESA_SHADER_CACHE_DIR': str(RAW / 'private-export-state/mesa'),
        'XDG_DATA_HOME': str(RAW / 'private-export-state/data'), 'XDG_CONFIG_HOME': str(RAW / 'private-export-state/config'),
        'XDG_CACHE_HOME': str(RAW / 'private-export-state/cache')}
    check(all(env[k] == v for k, v in expected_env.items()) and 'DISPLAY' not in env, 'registered_private_preparation_environment')
    pins = read_json(SOURCE / 'docs/reports/gauntlet/m1-linux-profile-acquisition/pins.json')
    check(pins['cpus'] == [0, 1] and pins['display'] == ':99127' and {0, 1} <= set(supervisor['affinity']) and
          supervisor['nice'] == supervisor['scheduler'] == 0 and overall['recognized_native_before'] == [], 'host_admission_and_fixed_cpu_display_selection')
    check(supervisor['quota']['quota'] == '400000 100000' and supervisor['quota']['cgroup_path'] == '/sys/fs/cgroup', 'retained_host_quota')
    for family, libraries in [('supervisor', supervisor['supervisor_libraries']),
                              ('import', commands[5]['actual_tool_libraries']),
                              ('export', commands[9]['actual_tool_libraries'])]:
        for path, wanted in libraries.items():
            check(identity(path)['sha256'] == wanted, 'observed_library_still_equal:' + family + ':' + path)
    observations['host_scope'] = {'affinity_before': supervisor['affinity'], 'nice': supervisor['nice'],
        'scheduler': supervisor['scheduler'], 'quota_before': supervisor['quota'], 'uname': supervisor['uname'],
        'preparation_environment': env, 'import_libraries': len(commands[5]['actual_tool_libraries']),
        'limitation': 'Independent observer corroborates the three engine processes; no native display, runtime Mesa renderer, end-host/quota or comparable conditions exist.'}

    # Rehash official archives and compare selected ZIP members and private copies.
    constants = {}
    for node in ast.parse((SOURCE / 'scripts/toolchain.py').read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('EDITORS', 'TEMPLATES_SHA512'):
                    constants[target.id] = ast.literal_eval(node.value)
    archives = {}
    for tool in pins['tools']:
        check(identity(tool['path']) == {k:tool[k] for k in ('bytes', 'sha256')}, 'pinned_tool_current_identity:' + tool['path'])
    for name, expected in [('godot.zip', constants['EDITORS']['linux'][2]),
                            ('templates.tpz', constants['TEMPLATES_SHA512'])]:
        path = Path('/workspace/tools/godot-4.7.2') / name
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha512').hexdigest()
        check(actual == expected, 'official_archive_sha512:' + name)
        archives[name] = {'sha512': actual, **identity(path)}
    official = []
    for archive_name in ('godot.zip', 'templates.tpz'):
        with zipfile.ZipFile(Path('/workspace/tools/godot-4.7.2') / archive_name) as bundle:
            check(len(bundle.namelist()) == len(set(bundle.namelist())), 'archive_unique_members:' + archive_name)
            for member in [row for row in overall['official_members'] if Path(row['archive']).name == archive_name]:
                info = bundle.getinfo(member['member'])
                with bundle.open(info) as stream:
                    actual = {'bytes': info.file_size, 'sha256': hashlib.file_digest(stream, 'sha256').hexdigest()}
                check(actual == {k:member[k] for k in ('bytes', 'sha256')} and
                      member['official_sha512'] == archives[archive_name]['sha512'], 'official_member_identity:' + member['member'])
                if archive_name == 'templates.tpz':
                    basename = Path(member['member']).name
                    installed = Path('/workspace/sightbreak/.local/data/godot/export_templates/4.7.2.stable') / basename
                    private = RAW / 'private-export-state/data/godot/export_templates/4.7.2.stable' / basename
                    check(identity(installed) == identity(private) == actual, 'installed_private_official_member_equal:' + basename)
                else:
                    check(identity(expected_engine) == actual, 'editor_installed_official_member_equal')
                official.append(member)
    observations['official_archives'] = archives
    observations['official_selected_members'] = official

    # Full original accepted registry is a finite gate record; failure-only new
    # files are intentionally outside it, so build a separate complete registry.
    for name, wanted in overall['validated_evidence'].items():
        check(registry[name] == wanted, 'first_validated_identity_retained:' + name)
    check(len(overall['validated_evidence']) == 171, 'original_registry_171_entries')
    later = ['seal', 'block', 'finalize']
    absent = ['artifact.phase.json', 'seal.phase.json', 'block.phase.json', 'finalize.phase.json',
              'native-block', 'seal.json', 'independent-payload.json', 'embedded-diagnostic.pck', 'outputs.json']
    for name in absent:
        check(not (RAW / name).exists(), 'unreached_output_absent:' + name)
    check(not any(k in overall for k in ('block', 'independent_payload', 'publication_source_observation',
              'host_after', 'recognized_native_after', 'output_manifest_sha256')), 'unreached_final_fields_absent')
    observations['unreached'] = {'phases': later, 'artifact_phase': 'FAILED at packed remap metadata JSON terminal NUL',
        'condition_order_registered': ['OFF', 'ON', 'ON', 'OFF'], 'actual_conditions': 0, 'sample_count': 0,
        'condition_cap_seconds_unchanged': 180,
        'not_qualified': ['complete ELF/PCK/ECFG/remap/UID artifact gate', 'payload seal', 'Xvfb',
            'runtime renderer/CPU/library readbacks', 'same-payload comparison', 'scene pixels/fingerprints',
            'frame clocks/counters', 'profiler OFF/ON capability', 'cadence metrics/H1',
            'final source/host observation', 'normal output-manifest/overall sealing',
            'physical FPS', 'gameplay diagnosis', 'original Linux gameplay acceptance']}
    observations['stage']['between_inventory_cache_changes'] = {}
    for inventory in ('import-complete-stage.json', 'export-complete-stage.json'):
        recorded = read_json(RAW / inventory)
        check(set(recorded) == set(actual_stage), 'actual_reached_inventory_same_closed_paths:' + inventory)
        for name, wanted in amended['files'].items():
            check(recorded[name] == wanted, 'reached_inventory_frozen_source:' + inventory + ':' + name)
        check(recorded['diagnostics/linux_profile_overhead.gd.uid'] == actual_stage['diagnostics/linux_profile_overhead.gd.uid'],
              'reached_inventory_generated_uid_stable:' + inventory)
        differences = {name: {'then': wanted, 'terminal': actual_stage[name]}
                       for name, wanted in recorded.items() if wanted != actual_stage[name]}
        check(all(name.startswith('.godot/') for name in differences), 'only_declared_cache_changes_between_inventories:' + inventory)
        observations['stage']['between_inventory_cache_changes'][inventory] = differences
    observer = [json.loads(line) for line in (REPORT / 'live-observer.jsonl').read_text().splitlines()]
    check(not any(row['event'] == 'failure' for row in observer), 'observer_has_no_failure')
    check(observer[0]['release_reference'] == outer['release'], 'observer_exact_root_release')
    discovered = next(row for row in observer if row['event'] == 'supervisor_discovered')
    check(discovered['identity']['pid'] == supervisor['pid'] and discovered['identity']['start_ticks'] == supervisor['start_ticks']
          and discovered['monotonic'] - observer[0]['monotonic'] < 60, 'independent_supervisor_identity_discovery')
    observations['unobserved_live_native_commands'] = []
    for index in (4, 5, 9):
        native = commands[index]
        seen = [item for row in observer for item in row.get('observed', [])
                if item['pid'] == native['pid'] and item['start_ticks'] == native['root_identity']['start_ticks']
                and item.get('argv', [''])[0] == expected_engine and item.get('identity_revalidated') is True]
        if not seen:
            observations['unobserved_live_native_commands'].append({'label': native['label'],
                'root_identity': native['root_identity'], 'recorded_elapsed_seconds': native['elapsed_seconds'],
                'scope': 'Recorded command/log/cleanup and later absence are checkable; no independent live argv/affinity/environment readback.'})
            check(native['label'] == 'version', 'only_short_version_engine_missed_live')
            continue
        check(True, 'native_engine_independently_observed:' + native['label'])
        check(any(item['affinity'] == [0, 1] and item['selected_environment'].get('LP_NUM_THREADS') == '2'
                  and item['selected_environment'].get('LIBGL_ALWAYS_SOFTWARE') == '1' for item in seen),
              'native_actual_affinity_environment:' + native['label'])
    absent_event = next(row for row in observer if row['event'] == 'supervisor_absent')
    terminal = next(row for row in observer if row['event'] == 'terminal')
    check(terminal['all_observed_absent'] and not terminal['original_groups'] and not terminal['original_sessions'],
          'observer_terminal_owned_scope_clear')
    check(absent_event['monotonic'] < overall['whole_deadline_monotonic'], 'independent_return_bracket_before_whole_cap')
    check(0 <= absent_event['monotonic'] - phases[-1]['ended_monotonic'] < 10,
          'failure_to_supervisor_absence_bracket_under_failure_publication_cap')
    observations['independent_live_scope'] = {'discovered': discovered, 'supervisor_absent': absent_event,
        'terminal': terminal, 'return_upper_elapsed_seconds': absent_event['monotonic'] - overall['start_monotonic'],
        'failure_end_to_absence_upper_seconds': absent_event['monotonic'] - phases[-1]['ended_monotonic'],
        'limitation': 'Observed exact identities only; short-lived between-poll or escaping descendants can be missed. Publication duration is bounded above by this bracket, not measured exactly.'}
    failure = read_json(REPORT / 'payload-failure-readback.json')
    check(failure['acquisition_verdict'] == 'FAILED' and failure['failure']['reproduction']['error'] == overall['error'],
          'independent_exact_packed_input_failure_matches_actual')
    check(identity(RAW / 'export/linux-profile-diagnostic.x86_64') == failure['ELF_identity'], 'failure_proof_exact_ELF_identity')
    observations['payload_failure'] = failure
    # Independently bind the actual ELF prefix and structural pack evidence.
    # This does not turn the inspector's failed semantic artifact gate into PASS.
    executable_bytes = (RAW / 'export/linux-profile-diagnostic.x86_64').read_bytes()
    template_bytes = Path('/workspace/sightbreak/.local/data/godot/export_templates/4.7.2.stable/linux_debug.x86_64').read_bytes()
    def elf_sections(data):
        check(data[:7] == b'\x7fELF\x02\x01\x01', 'actual_ELF_little_endian_64_bit')
        check(struct.unpack_from('<HHI', data, 16) == (2, 62, 1), 'actual_ELF_x86_64_version')
        phoff, shoff = struct.unpack_from('<QQ', data, 32)
        ehsize, phsize, phcount, shsize, shcount, string_index = struct.unpack_from('<6H', data, 52)
        check(ehsize == 64 and phsize == 56 and shsize == 64 and 0 < string_index < shcount < 10000,
              'actual_ELF_table_dimensions')
        check(phoff + phsize * phcount <= len(data) and shoff + shsize * shcount <= len(data), 'actual_ELF_table_bounds')
        for index in range(phcount):
            segment = struct.unpack_from('<II6Q', data, phoff + index * phsize)
            check(segment[2] + segment[5] <= len(data), 'actual_ELF_segment_bound:' + str(index))
        name_offset, name_size = struct.unpack_from('<QQ', data, shoff + string_index * shsize + 24)
        names, sections = data[name_offset:name_offset + name_size], {}
        for index in range(shcount):
            at = shoff + index * shsize
            name, kind, _flags, _address, offset, size, *_ = struct.unpack_from('<II4Q2I2Q', data, at)
            check(name < len(names) and names.find(b'\0', name) >= 0, 'actual_ELF_section_name_bound:' + str(index))
            label = names[name:names.find(b'\0', name)].decode()
            check(label not in sections and (kind == 8 or offset + size <= len(data)), 'actual_ELF_section_closed_identity:' + label)
            sections[label] = (at, offset, size)
        return sections
    sections_now, sections_template = elf_sections(executable_bytes), elf_sections(template_bytes)
    at, start, size = sections_now['pck']
    check(at == sections_template['pck'][0] and start == len(template_bytes) == failure['PCK_start']
          and size == failure['PCK_identity']['bytes'] + 12, 'actual_ELF_single_registered_pack_fixup')
    prefix = bytearray(executable_bytes[:start])
    prefix[at + 24:at + 40] = template_bytes[at + 24:at + 40]
    check(prefix == template_bytes, 'actual_ELF_template_prefix_exact_outside_pack_fixup')
    resources = failure['resources']
    check(len(resources) == len({row['path'] for row in resources}) == 94, 'actual_PCK_resource_closed_count')
    intervals = []
    for row in resources:
        name = row['path']
        check(not name.startswith('/') and '\\' not in name and '\0' not in name and
              all(part not in ('', '.', '..', 'tests') for part in name.split('/')), 'actual_PCK_safe_path:' + name)
        intervals.append((row['pack_offset'], row['pack_offset'] + row['bytes']))
        if Path(name).suffix in ('.gd', '.tscn', '.tres') or name == 'diagnostics/source_ledger.json' or name.startswith('.godot/imported/'):
            check(identity(RAW / 'project' / name) == {k: row[k] for k in ('bytes', 'sha256')}, 'actual_PCK_staged_text_or_cache_equality:' + name)
    check(all(left[1] <= right[0] for left, right in zip(sorted(intervals), sorted(intervals)[1:])), 'actual_PCK_resource_ranges_nonoverlap')
    check(not any(row['path'].endswith(('.gdc', '.remap')) for row in resources), 'actual_PCK_no_bytecode_or_remap_substitutes')

    # Retain every original attempt file except independently verified official
    # template copies. Retain the three external root streams/receipt as well.
    excluded_prefix = 'private-export-state/data/godot/export_templates/4.7.2.stable/'
    excluded = {name: row for name, row in registry.items() if name.startswith(excluded_prefix)}
    check(len(excluded) == 3, 'only_three_official_template_copies_excluded_from_archive')
    archive_path = REPORT / 'retained-actual.tar.gz'
    member_registry = {}
    with tarfile.open(archive_path, 'w:gz', compresslevel=6) as bundle:
        for name, row in registry.items():
            if name in excluded:
                continue
            member = 'attempt/' + name
            bundle.add(RAW / name, arcname=member, recursive=False)
            member_registry[member] = row
        for name, path in outer_paths.items():
            member = 'outer/' + name
            bundle.add(path, arcname=member, recursive=False)
            member_registry[member] = outer_registry[name]
        for name in ('scripts/linux_profile_acquire.py', 'scripts/linux_profile_payload.py',
                     'scripts/linux_profile_overhead.py', 'scripts/diagnostics/linux_profile_overhead.gd',
                     'scripts/diagnostics/linux_profile_overhead.tscn', 'scripts/native_log.py', 'scripts/toolchain.py'):
            raw = git('show', FROZEN + ':' + name)
            member = 'frozen-source/' + name
            info = tarfile.TarInfo(member)
            info.size, info.mtime, info.mode = len(raw), 0, 0o644
            bundle.addfile(info, io.BytesIO(raw))
            member_registry[member] = bytes_identity(raw)
    with tarfile.open(archive_path, 'r:gz') as bundle:
        members = bundle.getmembers()
        check(len(members) == len(member_registry) == len(set(m.name for m in members)), 'archive_complete_unique_closed_set')
        for member in members:
            raw = bundle.extractfile(member).read()
            check(member.isfile() and bytes_identity(raw) == member_registry[member.name], 'archive_original_bytes:' + member.name)
    check({path.relative_to(RAW).as_posix(): identity(path) for path in raw_paths} == registry and
          {path.relative_to(RAW).as_posix() for path in RAW.rglob('*') if path.is_file()} == set(registry), 'raw_unchanged_through_audit_archive')
    check({name: identity(path) for name, path in outer_paths.items()} == outer_registry, 'outer_unchanged_through_audit_archive')
    emit('raw-registry.json', {'scope': 'All original actual attempt bytes at independent post-failure observation',
         'source': str(RAW), 'files': registry, 'file_count': len(registry), 'bytes': sum(v['bytes'] for v in registry.values()),
         'outer': outer_registry, 'archive_exclusions': excluded})
    emit('archive-members.json', {'archive': archive_path.name, 'identity': identity(archive_path), 'members': member_registry})
    emit('audit-results.json', {'schema': 1, 'acquisition_verdict': 'FAILED', 'audit_predicates_passed': True,
        'source_commit': FROZEN, 'preregistration_commit': '2082e964',
        'checks': checks, 'observations': observations,
        'audit_started_monotonic': started, 'audit_ended_monotonic': time.monotonic()})
    print(json.dumps({'acquisition_verdict': 'FAILED', 'audit_predicates': len(checks),
        'raw_files': len(registry), 'archive_files': len(member_registry), 'archive': identity(archive_path)}, indent=2))


if __name__ == '__main__':
    main()
