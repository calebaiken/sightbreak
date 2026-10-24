#!/usr/bin/env python3
"""Validate debug stage observations without inferring an unobserved cause."""
import argparse
import hashlib
import json
import math
from pathlib import Path

PREFIX = 'SIGHTBREAK_INPUT_OBSERVATION '
SCOPE = 'debug_guest_loopback_input_observation'
STAGES = set('ready authority_tick client_tick client_attempt client_connected client_connection_failed client_disconnected welcome_received peer_connected peer_bound peer_expired peer_disconnected input_gate_rejected input_decode_rejected input_received input_stream_rejected input_accepted input_consumed input_send_called snapshot_schema_rejected snapshot_order_rejected snapshot_applied'.split())
COMMON = set('schema scope role reason index wall_unix_msec wall_msec process_frames physics_frames drawn_frames connection_state transport_status transport_id local_id local_attempt peer bound_actor last_bound_actor peer_bound generation joined input_age_msec deadline_remaining_msec simulation_tick authority_epoch stream_ack queue_count stream_rejected stream_skipped prediction_epoch prediction_sequence pending_count pending_oldest_sequence pending_newest_sequence snapshot snapshot_age_msec local_input physical counters latest actor'.split())
INTEGER_FIELDS = COMMON - set('scope role reason connection_state peer_bound joined snapshot local_input physical counters latest actor'.split())
PACKET_KEYS = set('epoch count first last fire reload moving wall_msec'.split())
CONTROL_KEYS = set('sequence fire reload move'.split())
SNAPSHOT_KEYS = set('tick epoch own_ack wall_msec'.split())
REQUIRED = {
    'client': set('ready client_attempt client_connected welcome_received snapshot_applied input_send_called client_tick'.split()),
    'authority': set('ready peer_connected peer_bound input_received input_accepted input_consumed authority_tick'.split()),
}
ROLE_STAGES = {
    'client': set('ready client_tick client_attempt client_connected client_connection_failed client_disconnected welcome_received input_send_called snapshot_schema_rejected snapshot_order_rejected snapshot_applied'.split()),
    'authority': set('ready authority_tick peer_connected peer_bound peer_expired peer_disconnected input_gate_rejected input_decode_rejected input_received input_stream_rejected input_accepted input_consumed'.split()),
}
LIFECYCLE_STAGES = set('ready client_attempt client_connected client_connection_failed client_disconnected welcome_received peer_connected peer_bound peer_expired peer_disconnected'.split())
LATEST_STAGES = set('input_send_called input_received input_accepted input_stream_rejected input_consumed snapshot_applied snapshot_schema_rejected snapshot_order_rejected welcome_received'.split())


def need(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value):
    return type(value) is int


def controls(value, extra=()):
    need(type(value) is dict and set(value) == CONTROL_KEYS | set(extra), 'invalid control projection')
    need(integer(value['sequence']) and type(value['fire']) is bool and type(value['reload']) is bool, 'invalid control values')
    move = value['move']
    need(type(move) is list and len(move) == 2 and all(type(v) in (int, float) and math.isfinite(v) and -1 <= v <= 1 for v in move), 'invalid movement projection')
    need(all(integer(value[k]) for k in extra), 'invalid control identity')


def record_valid(row):
    need(type(row) is dict and set(row) == COMMON, 'unexpected observation fields; privacy projection violated')
    need(row['schema'] == 1 and type(row['schema']) is int and row['scope'] == SCOPE, 'invalid schema or scope')
    need(row['role'] in REQUIRED and row['reason'] in STAGES | {'observation_limit'}, 'invalid role or stage')
    need(row['reason'] in ROLE_STAGES[row['role']] | {'observation_limit'}, 'stage does not belong to observed role')
    need(all(integer(row[k]) for k in INTEGER_FIELDS), 'observation integer field has wrong type')
    need(1 <= row['index'] <= 1024 and row['pending_count'] in range(121), 'invalid bounded observation/history count')
    need(row['role'] != 'authority' or row['queue_count'] in range(121), 'authority queue exceeds bounded input window')
    need(all(row[k] >= 0 for k in ('wall_msec', 'wall_unix_msec', 'process_frames', 'physics_frames', 'drawn_frames', 'transport_id', 'local_attempt', 'local_id', 'peer', 'bound_actor', 'last_bound_actor', 'queue_count', 'stream_rejected', 'stream_skipped', 'simulation_tick')), 'negative observation counter')
    need(type(row['peer_bound']) is bool and type(row['joined']) is bool, 'invalid binding flags')
    need(row['peer_bound'] == (row['bound_actor'] > 0), 'binding flag disagrees with current actor')
    need(row['transport_status'] in {-1, 0, 1, 2} and all(row[k] in range(11) for k in ('local_id', 'bound_actor', 'last_bound_actor')), 'invalid transport/actor identity')
    need(row['connection_state'] in {'offline', 'hosting', 'connecting', 'authenticating', 'joining', 'connected', 'reconnecting', 'failed'}, 'invalid connection state')
    need((row['pending_count'] == 0 and row['pending_oldest_sequence'] == row['pending_newest_sequence'] == -1) or (row['pending_count'] > 0 and 1 <= row['pending_oldest_sequence'] <= row['pending_newest_sequence'] <= row['prediction_sequence']), 'pending history counters disagree')
    controls(row['local_input'])
    physical = row['physical']
    allowed = {'r', 'lmb', 'physical_mouse_fire', 'application_focused', 'paused', 'waiting_for_input_release'}
    need(type(physical) is dict and {'r', 'lmb'} <= set(physical) <= allowed and all(type(v) is bool for v in physical.values()), 'invalid physical/UI projection')
    if row['role'] == 'client':
        need(set(physical) == allowed, 'client UI context missing')
    counters = row['counters']
    need(type(counters) is dict and set(counters) <= STAGES and all(integer(v) and v > 0 for v in counters.values()), 'invalid stage counters')
    need(set(counters) <= ROLE_STAGES[row['role']], 'counter does not belong to observed role')
    if row['reason'] != 'observation_limit':
        need(counters.get(row['reason'], 0) > 0, 'event missing its stage counter')
    snapshot = row['snapshot']
    need(type(snapshot) is dict and (not snapshot or set(snapshot) == SNAPSHOT_KEYS), 'invalid own snapshot projection')
    need(all(integer(v) for v in snapshot.values()), 'invalid own snapshot values')
    need((not snapshot and row['snapshot_age_msec'] == -1) or (snapshot and row['snapshot_age_msec'] == row['wall_msec'] - snapshot['wall_msec'] >= 0), 'snapshot freshness disagrees with capture time')
    latest = row['latest']
    need(type(latest) is dict and set(latest) <= {'input_send_called', 'input_received', 'input_accepted', 'input_stream_rejected', 'input_consumed', 'snapshot_applied', 'snapshot_schema_rejected', 'snapshot_order_rejected', 'welcome_received'}, 'invalid latest-stage projection')
    need(set(latest) <= ROLE_STAGES[row['role']], 'latest metadata does not belong to observed role')
    for stage, value in latest.items():
        need(type(value) is dict, 'stage value is not an object')
        if stage == 'input_consumed':
            controls(value, ('peer', 'actor', 'generation', 'wall_msec'))
        elif stage.startswith('input_'):
            need(set(value) == PACKET_KEYS and all(integer(v) for v in value.values()), 'invalid packet projection')
            need(value['count'] >= 0 and all(0 <= value[k] <= min(value['count'], 12) for k in ('fire', 'reload', 'moving')), 'invalid bounded packet action counts')
            need(value['count'] != 1 or value['first'] == value['last'], 'single-command packet has unequal sequence endpoints')
            need(value['count'] != 0 or value['first'] == value['last'] == -1, 'empty packet has nonempty sequence endpoints')
        else:
            need(set(value) == SNAPSHOT_KEYS and all(integer(v) for v in value.values()), 'invalid snapshot header')
        need(0 <= value['wall_msec'] <= row['wall_msec'], 'future latest-stage observation')
    actor = row['actor']
    need(type(actor) is dict and (not actor or set(actor) == {'id', 'alive', 'ammo', 'reserve', 'reload', 'input'}), 'invalid own actor projection')
    if actor:
        need(integer(actor['id']) and actor['id'] > 0 and type(actor['alive']) is bool and integer(actor['ammo']) and integer(actor['reserve']) and actor['ammo'] >= 0 and actor['reserve'] >= 0, 'invalid own actor values')
        need(type(actor['reload']) in (int, float) and math.isfinite(actor['reload']) and actor['reload'] >= 0, 'invalid own reload observation')
        controls(actor['input'])
        need(actor['id'] == (row['local_id'] if row['role'] == 'client' else row['last_bound_actor']), 'actor projection is not the local/last bound guest')


def parse_log(text):
    need(len(text.encode()) <= 32 * 1024 * 1024, 'observation log exceeds bounded reader')
    rows = []
    for line in text.splitlines():
        if PREFIX not in line:
            continue
        need(line.startswith(PREFIX) and len(line) <= 32768, 'corrupt observation line')
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                need(key not in result, 'duplicate JSON observation key')
                result[key] = value
            return result
        rows.append(json.loads(line[len(PREFIX):], object_pairs_hook=unique_object))
        need(len(rows) <= 1024, 'too many observation records')
    return rows


def analyze_role(rows, role):
    need(bool(rows), 'no observation records for ' + role)
    for row in rows:
        record_valid(row)
    coverage = set(rows[-1]['counters'])
    need(REQUIRED[role] <= coverage, 'missing pipeline stages: ' + ','.join(sorted(REQUIRED[role] - coverage)))
    observed_events = {row['reason'] for row in rows}
    need(REQUIRED[role] - {'snapshot_applied'} <= observed_events, 'missing direct pipeline event records')
    prior, bindings, ended, consumed_sequences = None, {}, set(), {}
    live_peers, binding_accept_counts, lifecycle_counts = {}, {}, {}
    live_bindings = set()
    connected = set()
    observed_attempts = 0
    current_welcome = None
    received = []
    highest_generation = 0
    consumed, accepted, expiries, disconnects, saturations, welcomes, binding_events = [], [], [], [], [], [], []
    max_gap = 0
    for row in rows:
        need(row['role'] == role, 'mixed role evidence')
        need(row['index'] == (prior['index'] + 1 if prior else 1), 'missing or reordered observation index')
        need(row['reason'] != 'observation_limit', 'observer reached its hard cap; evidence truncated')
        reason, counters, latest = row['reason'], row['counters'], row['latest']
        previous_counters = prior['counters'] if prior else {}
        need(counters.get(reason, 0) > previous_counters.get(reason, 0), 'emitted reason did not increment its stage counter')
        if reason in LIFECYCLE_STAGES:
            lifecycle_counts[reason] = lifecycle_counts.get(reason, 0) + 1
        need(all(counters.get(stage, 0) == lifecycle_counts.get(stage, 0) for stage in LIFECYCLE_STAGES),
             'lifecycle counter has no matching observed event')
        need(set(latest) == set(counters) & LATEST_STAGES, 'latest metadata missing from persistent stage history')
        if role == 'authority':
            # RPC processing has no await. Only its receive observation is
            # captured before the synchronous accept/reject outcome.
            need(counters.get('input_received', 0) == counters.get('input_accepted', 0) + counters.get('input_stream_rejected', 0) + int(reason == 'input_received'),
                 'receive/accept/rejection counters disagree with synchronous pipeline')
            rejections = counters.get('input_stream_rejected', 0)
            need(row['stream_rejected'] <= rejections, 'stream rejection state exceeds observed rejection calls')
            if prior:
                expected = prior['stream_rejected'] + rejections - previous_counters.get('input_stream_rejected', 0)
                # A lobby reset advances the epoch and needs zero bound peers.
                # Its replacement stream resets state but retains observer history.
                reset_possible = row['authority_epoch'] > prior['authority_epoch'] and not live_bindings
                need(row['stream_rejected'] <= expected if reset_possible else row['stream_rejected'] == expected,
                     'stream rejection state disagrees within observed stream lifetime')
        if prior:
            for key in ('wall_msec', 'wall_unix_msec', 'process_frames', 'physics_frames', 'drawn_frames'):
                need(row[key] >= prior[key], 'regressed observation ' + key)
            need(all(row['counters'].get(k, 0) >= v for k, v in prior['counters'].items()), 'regressed stage counter')
            need(set(prior['latest']) <= set(latest), 'latest metadata disappeared from persistent stage history')
            need(all(latest[stage] == value for stage, value in prior['latest'].items()
                     if counters.get(stage, 0) == previous_counters.get(stage, 0)),
                 'latest metadata changed without a stage counter increment')
            need(all(value['wall_msec'] >= prior['wall_msec'] for stage, value in latest.items()
                     if counters[stage] > previous_counters.get(stage, 0)),
                 'latest stage call predates the preceding observation')
            max_gap = max(max_gap, row['wall_msec'] - prior['wall_msec'])
        identity = (row['peer'], row['generation'])
        if role == 'client':
            if row['reason'] == 'client_attempt':
                observed_attempts += 1
            need(row['local_attempt'] == observed_attempts and row['counters'].get('client_attempt', 0) == observed_attempts,
                 'client attempt has no matching observed attempt event')
        if role == 'client' and row['reason'] in {'client_attempt', 'client_connection_failed', 'client_disconnected'}:
            current_welcome = None
        if row['reason'] == 'peer_connected':
            need(role == 'authority' and row['generation'] > highest_generation, 'connection generation reused or regressed')
            need(row['peer'] not in live_peers, 'peer gained a second live generation without disconnect')
            highest_generation = row['generation']
            live_peers[row['peer']] = row['generation']
            connected.add(identity)
        if row['reason'] == 'peer_bound':
            need(role == 'authority' and row['peer_bound'] and row['joined'] and row['generation'] > 0 and identity not in ended, 'invalid/reused retired peer generation')
            need(identity in connected, 'binding has no preceding matching connected peer generation')
            need(identity not in bindings, 'peer generation already has an observed binding')
            need(not any(actor == row['bound_actor'] and key != identity and key not in ended for key, actor in bindings.items()), 'actor bound to two live peer generations')
            bindings[identity] = row['bound_actor']
            live_bindings.add(identity)
            binding_accept_counts[identity] = counters.get('input_accepted', 0)
            binding_events.append({k: row[k] for k in ('peer', 'generation', 'bound_actor', 'wall_unix_msec')})
        if row['reason'] == 'welcome_received':
            need(role == 'client' and row['transport_id'] > 0 and row['local_attempt'] > 0 and row['local_id'] > 0, 'welcome has no client transport/attempt identity')
            current_welcome = tuple(row[k] for k in ('transport_id', 'local_attempt', 'local_id'))
            welcomes.append({k: row[k] for k in ('transport_id', 'local_attempt', 'local_id', 'wall_unix_msec')})
        if row['reason'] in {'peer_expired', 'peer_disconnected'}:
            ended.add(identity)
            if row['reason'] == 'peer_disconnected' and live_peers.get(row['peer']) == row['generation']:
                del live_peers[row['peer']]
            if row['reason'] == 'peer_disconnected':
                live_bindings.discard(identity)
            (expiries if row['reason'] == 'peer_expired' else disconnects).append({'index': row['index'], 'peer': row['peer'], 'generation': row['generation'], 'wall_msec': row['wall_msec'], 'wall_unix_msec': row['wall_unix_msec'], 'input_age_msec': row['input_age_msec']})
        if row['reason'] == 'input_send_called':
            value = row['latest'].get('input_send_called')
            need(role == 'client' and row['connection_state'] == 'connected' and value is not None and value['wall_msec'] == row['wall_msec'], 'send call refers to stale/missing client metadata')
            need(value['epoch'] == row['prediction_epoch'] and 1 <= value['count'] <= min(12, row['pending_count']) and 1 <= value['first'] <= value['last'] <= row['prediction_sequence'], 'send-call sequence/history projection disagrees')
            need(current_welcome == tuple(row[k] for k in ('transport_id', 'local_attempt', 'local_id')), 'welcome cannot bind send call to its current client identity')
            need(row['pending_oldest_sequence'] <= value['first'] <= value['last'] <= row['pending_newest_sequence'], 'send-call sequence is outside pending history')
        if row['reason'] in {'input_received', 'input_accepted', 'input_consumed'}:
            need(role == 'authority' and row['peer_bound'] and row['joined'] and bindings.get(identity) == row['bound_actor'] and identity not in ended, 'input stage has no current observed peer-generation binding')
            value = row['latest'].get(row['reason'])
            need(value is not None and value['wall_msec'] == row['wall_msec'], 'input stage refers to stale metadata')
            if row['reason'] == 'input_consumed':
                need(received and accepted, 'direct pipeline consumption precedes observed receive and acceptance')
                need((value['peer'], value['generation'], value['actor']) == (*identity, row['bound_actor']), 'consumed identity differs from current binding')
                need(counters.get('input_accepted', 0) > binding_accept_counts[identity], 'consumption has no acceptance counter progress since binding')
                need(row['stream_ack'] == value['sequence'], 'consumed command differs from immediate stream ACK')
                need(row['actor'] and row['actor']['id'] == value['actor'] and row['actor']['input'] == {key: value[key] for key in CONTROL_KEYS},
                     'consumed command differs from immediate actor input')
                key = (*identity, row['authority_epoch'])
                need(value['sequence'] > consumed_sequences.get(key, 0), 'consumption sequence replayed or regressed')
                consumed_sequences[key] = value['sequence']
                consumed.append({'index': row['index'], **value})
            elif row['reason'] == 'input_accepted':
                need(received, 'direct pipeline acceptance precedes observed receive')
                incoming = latest.get('input_received', {})
                need({key: incoming.get(key) for key in PACKET_KEYS - {'wall_msec'}} == {key: value[key] for key in PACKET_KEYS - {'wall_msec'}},
                     'accepted packet differs from synchronous latest receive')
                need(row['queue_count'] > 0, 'accepted input left an empty queue')
                need(value['epoch'] == row['authority_epoch'] and value['count'] in range(1, 13), 'accepted packet has wrong epoch or count')
                # These are incoming array endpoints, not sorted extrema.
                need(value['first'] >= 1 and value['last'] >= 1 and (value['count'] > 1 or value['first'] == value['last']),
                     'accepted packet has invalid sequence endpoints')
                ack = max(row['stream_ack'], 0)
                need(max(value['first'], value['last']) <= ack + 120, 'accepted endpoint exceeds input sequence window')
                # Only batches of one or two expose every command. Larger
                # batches may hide a fresh middle command behind stale endpoints.
                need(value['count'] > 2 or max(value['first'], value['last']) > ack,
                     'fully exposed accepted batch contains no fresh command')
                accepted.append({'index': row['index'], **value})
            else:
                # Receive is after the identity gate but before packet validation.
                # Its malformed payload fields can describe real rejected input.
                received.append({'index': row['index'], **value})
        if row['pending_count'] == 120:
            saturations.append(row['index'])
        prior = row
    if role == 'authority':
        need(bool(consumed) and bool(accepted), 'acceptance and actual consumption need distinct observed events')
    return {'records': len(rows), 'coverage': sorted(coverage), 'counters': prior['counters'], 'max_observation_gap_msec': max_gap,
            'max_snapshot_age_msec': max(r['snapshot_age_msec'] for r in rows), 'pending_saturation_indices': saturations,
            'accepted_events': accepted, 'consumed_events': consumed, 'expiry_events': expiries, 'disconnect_events': disconnects,
            'welcome_events': welcomes, 'binding_events': binding_events,
            'local_attempts': prior['local_attempt']}


def analyze(client_text, authority_text):
    report = {'scope': 'Debug read-only stage observations; no qualification, physical latency or unobserved cause claim',
              'diagnostic_complete': False, 'cause_status': 'UNRESOLVED; observations identify executed stages and gaps only', 'roles': {}, 'errors': []}
    for role, raw in [('client', client_text), ('authority', authority_text)]:
        try:
            report['roles'][role] = analyze_role(parse_log(raw), role)
        except (ValueError, KeyError, TypeError) as error:
            report['errors'].append(role + ': ' + str(error))
    if not report['errors']:
        links = []
        authority = report['roles']['authority']
        for welcome in report['roles']['client']['welcome_events']:
            candidates = [binding for binding in authority['binding_events']
                          if binding['peer'] == welcome['transport_id'] and binding['bound_actor'] == welcome['local_id']
                          and binding['wall_unix_msec'] <= welcome['wall_unix_msec']
                          and not any(event['peer'] == binding['peer'] and event['generation'] == binding['generation'] and event['wall_unix_msec'] < welcome['wall_unix_msec'] for event in authority['disconnect_events'] + authority['expiry_events'])]
            if len(candidates) != 1:
                report['errors'].append('welcome cannot bind uniquely to an observed live authority peer generation')
            else:
                links.append({'client_local_attempt': welcome['local_attempt'], **candidates[0]})
        report['attempt_generation_links'] = links
    report['diagnostic_complete'] = not report['errors']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--authority', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Preserve prior analysis; use a fresh output path')
    client, authority = args.client.read_bytes(), args.authority.read_bytes()
    report = analyze(client.decode('utf-8', errors='strict'), authority.decode('utf-8', errors='strict'))
    report['inputs'] = [{'role': role, 'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                        for role, path, raw in [('client', args.client, client), ('authority', args.authority, authority)]]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['diagnostic_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
