#!/usr/bin/env python3
"""Join opt-in read-only observations to this process's verbose leak ObjectIDs."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from native_log import failed

PREFIX = 'AUDIO_LIFECYCLE '
ENGINE = 'Godot Engine v4.7.2.stable.official.ed1daf0bf'
ROLES = {'actor_shot', 'actor_hurt', 'reload_voice', 'utility', 'match_device', 'network_shot', 'unknown'}
FORCED_STAGES = {'before_hud_leave', 'after_hud_leave', 'before_final_leave', 'after_final_leave', 'final_pre_quit'}


def object_id(value, optional=False):
    if optional and value == '':
        return ''
    if not isinstance(value, str) or not re.fullmatch(r'-?[0-9]+', value):
        raise ValueError('ObjectID must be a decimal string')
    number = int(value)
    if not -(1 << 63) <= number < (1 << 64) or number == 0:
        raise ValueError('ObjectID is outside the nonzero 64-bit domain')
    return str(number % (1 << 64))


def engine_context(text):
    lines = text.splitlines()
    mentions = [(index, line) for index, line in enumerate(lines) if 'Godot Engine' in line]
    banner = ENGINE + ' - https://godotengine.org'
    if len(mentions) != 1 or mentions[0][1] != banner:
        raise ValueError('Exactly one complete pinned engine banner is required')
    index = mentions[0][0]
    preamble = lines[:index]
    if preamble:
        worker = re.fullmatch(r'WorkerThreadPool: ([1-9][0-9]*) threads, ([0-9]+) max low-priority\.', preamble[0])
        if len(preamble) != 1 or worker is None or int(worker[2]) > int(worker[1]):
            raise ValueError('Engine banner has an unsupported or buried preamble')
    return {'banner_line': index + 1, 'verbose_preamble': preamble}


def analyze(text):
    context = engine_context(text)
    objects, players, weak, checkpoints, headers = {}, [], {}, [], []
    rows = []
    pending_weak, snapshots, final_weak = [], [], {}
    sealed = False
    for line in text.splitlines():
        if line.startswith(PREFIX):
            if sealed:
                raise ValueError('Probe record appears after the sealed final checkpoint')
            row = json.loads(line[len(PREFIX):])
            if (not isinstance(row, dict) or type(row.get('schema')) is not int or row['schema'] != 1
                    or type(row.get('sequence')) is not int or row['sequence'] != len(rows)):
                raise ValueError('Probe schema or contiguous sequence is invalid')
            if (not isinstance(row.get('stage'), str) or any(type(row.get(key)) is not int or row[key] < 0
                    for key in ('process_frame', 'physics_frame', 'usec'))):
                raise ValueError('Probe stage/frame/time fields are invalid')
            if rows and any(row[key] < rows[-1][key] for key in ('process_frame', 'physics_frame', 'usec')):
                raise ValueError('Probe frame/time chronology moves backward')
            rows.append(row)
            kind = row.get('kind')
            if pending_weak and kind not in ('weak', 'checkpoint'):
                raise ValueError('Non-weak record interleaves the weak snapshot loop')
            if kind == 'header':
                if (row['sequence'] != 0 or not isinstance(row.get('driver'), str) or not row['driver']
                        or type(row.get('mix_rate')) is not int or row['mix_rate'] <= 0
                        or row.get('scope') != 'read_only_latest_playback_not_server_drain'):
                    raise ValueError('Probe header is invalid')
                headers.append(row)
            elif kind == 'object':
                identity = object_id(row.get('id'))
                if identity in objects or not isinstance(row.get('class'), str):
                    raise ValueError('Object registration is duplicate or untyped')
                if row['class'] == 'AudioStreamWAV':
                    wav = row.get('wav', {})
                    if (not re.fullmatch('[0-9a-f]{64}', str(wav.get('sha256', '')))
                            or any(type(wav.get(key)) is not int or wav[key] < 0 for key in ('format', 'mix_rate', 'bytes'))
                            or type(wav.get('stereo')) is not bool):
                        raise ValueError('WAV descriptor is invalid')
                objects[identity] = row
            elif kind == 'player':
                identity = object_id(row.get('id'))
                state = row.get('state', {})
                if objects.get(identity, {}).get('class') != 'AudioStreamPlayer3D':
                    raise ValueError('Player observation lacks typed registration')
                if not isinstance(state, dict) or any(type(state.get(key)) is not bool for key in
                        ('inside_tree', 'queued_for_deletion', 'playing', 'stream_paused', 'has_stream_playback')):
                    raise ValueError('Player state is invalid')
                owner = state.get('owner', {})
                if (not isinstance(owner, dict) or owner.get('role') not in ROLES
                        or any(not isinstance(owner.get(key), str) for key in ('id', 'path', 'script'))):
                    raise ValueError('Player owner descriptor is invalid')
                object_id(owner['id'], optional=True)
                for key in ('stream_id', 'latest_playback_id'):
                    state[key] = object_id(state.get(key), optional=True)
                    if state[key] and state[key] not in objects:
                        raise ValueError('Player refers to an unregistered object')
                if bool(state['latest_playback_id']) != state['has_stream_playback']:
                    raise ValueError('Latest playback presence disagrees with public state')
                if state['latest_playback_id']:
                    if (not objects[state['latest_playback_id']]['class'].startswith('AudioStreamPlayback')
                            or type(state.get('latest_playing')) is not bool):
                        raise ValueError('Latest playback type/state is invalid')
                elif state.get('latest_playing') is not None:
                    raise ValueError('Absent playback has a playing state')
                players.append({**row, 'id': identity})
            elif kind == 'weak':
                identity = object_id(row.get('id'))
                if identity not in objects or type(row.get('alive')) is not bool:
                    raise ValueError('Weak observation is invalid')
                weak.setdefault(identity, []).append(row)
                pending_weak.append((identity, row))
            elif kind == 'checkpoint':
                if any(type(row.get(key)) not in (int, float) for key in ('time_since_last_mix', 'time_to_next_mix')):
                    raise ValueError('Public mix timing fields are invalid')
                stage = row['stage']
                if stage not in FORCED_STAGES | {'existing_process_frame'}:
                    raise ValueError('Unknown snapshot checkpoint stage')
                identities = [identity for identity, _ in pending_weak]
                if any(observation['stage'] != stage for _, observation in pending_weak):
                    raise ValueError('Weak row lies outside its matching checkpoint window')
                if len(set(identities)) != len(identities):
                    raise ValueError('Weak object is duplicated within one checkpoint window')
                if stage in FORCED_STAGES:
                    if set(identities) != set(objects):
                        raise ValueError('Forced checkpoint window lacks complete weak object coverage')
                    snapshots.append({'stage': stage, 'checkpoint_sequence': row['sequence'],
                                      'registered_object_count': len(objects), 'weak_count': len(identities)})
                if stage == 'final_pre_quit':
                    final_weak = {identity: observation for identity, observation in pending_weak}
                    sealed = True
                pending_weak = []
                checkpoints.append(row)
            else:
                raise ValueError('Unknown probe record kind')
    if len(headers) != 1:
        raise ValueError('Sole probe header is absent')
    if not players:
        raise ValueError('Player ownership observations are absent')
    stages = [row['stage'] for row in checkpoints]
    expected = {'before_hud_leave': 6, 'after_hud_leave': 6, 'before_final_leave': 1,
                'after_final_leave': 1, 'final_pre_quit': 1}
    expected_order = ['before_hud_leave', 'after_hud_leave'] * 6 + ['before_final_leave', 'after_final_leave', 'final_pre_quit']
    if ([stage for stage in stages if stage in expected] != expected_order
            or stages[-1:] != ['final_pre_quit']):
        raise ValueError('Original leave/final checkpoint coverage is incomplete')
    if pending_weak or not sealed:
        raise ValueError('Probe ends with an incomplete or unsealed weak snapshot')
    footers = re.findall(r'^INPUT_MODE_TEST checks=(\d+) failures=(\d+) graphical_pointer=(\w+) .* baseline=(\w+)$', text, re.M)
    if footers != [('462', '0', 'false', 'false')]:
        raise ValueError('Exact headless base input_mode assertion result is absent')

    leaks = []
    for class_name, identity, references in re.findall(r'^Leaked instance: (\w+):(\d+) - Reference count: (\d+)$', text, re.M):
        identity = object_id(identity)
        registration = objects.get(identity)
        if registration is not None and registration['class'] != class_name:
            raise ValueError('Verbose leak class disagrees with observed ObjectID')
        associations = []
        for row in players:
            state = row['state']
            if identity in (state['stream_id'], state['latest_playback_id']):
                associations.append({'sequence': row['sequence'], 'stage': row['stage'],
                                     'player_id': row['id'], 'state': state})
        leaks.append({'class': class_name, 'id': identity, 'references_at_engine_exit': int(references),
                      'observed': registration is not None, 'descriptor': registration,
                      'player_observations': associations, 'weak_observations': weak.get(identity, [])})
    roles = {role: set() for role in ROLES}
    for row in players:
        roles[row['state']['owner']['role']].add(row['id'])
    expected_roles = {'match_device': 7, 'actor_shot': 70, 'actor_hurt': 70, 'reload_voice': 280}
    coverage = {role: len(ids) for role, ids in sorted(roles.items())}
    classified = set().union(*(ids for role, ids in roles.items() if role != 'unknown'))
    unclassified = sorted({row['id'] for row in players} - classified)
    final_alive_players = [identity for identity, descriptor in objects.items()
                           if descriptor['class'] == 'AudioStreamPlayer3D'
                           and final_weak[identity]['alive']]
    return {'schema': 1, 'scope': 'read-only ownership evidence; no fix or drain qualification',
            'driver': headers[0]['driver'], 'records': len(rows), 'objects': len(objects),
            'engine_context': context,
            'audio_scope': 'ownership and strict exit only; no audible or physical qualification',
            'driver_provenance': 'probe-reported; exact argv and engine binding required separately',
            'player_role_counts': coverage, 'expected_input_mode_role_counts': expected_roles,
            'unclassified_player_ids': unclassified,
            'fixture_owner_coverage_complete': (all(coverage[role] == count for role, count in expected_roles.items())
                                                and len(classified) == 427 and not unclassified),
            'final_alive_player_ids': final_alive_players,
            'final_checkpoint_sequence': checkpoints[-1]['sequence'], 'forced_weak_snapshots': snapshots,
            'strict_raw_log_failed': failed(text), 'leaks': leaks,
            'sample_status': ('leak_observed' if leaks else
                              'untyped_strict_failure' if failed(text) else 'no_typed_leak_in_this_sample'),
            'unobserved_leaks': [row['id'] for row in leaks if not row['observed']],
            'server_drain': 'unknown; no public acknowledgment',
            'polyphonic_coverage': 'latest public playback only; earlier voices unknown',
            'cause': 'unproven; observing a player association does not identify the retaining reference'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    args = parser.parse_args()
    try:
        raw = args.log.read_bytes()
        report = analyze(raw.decode('utf-8', errors='replace'))
        report.update(raw_log_sha256=hashlib.sha256(raw).hexdigest(), raw_log_bytes=len(raw))
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        parser.exit(2, 'Audio lifecycle evidence rejected: ' + str(error) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
