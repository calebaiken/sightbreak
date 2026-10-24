#!/usr/bin/env python3
"""Validate debug stage observations without inferring an unobserved cause."""
import argparse
from bisect import bisect_left
from copy import deepcopy
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


class UnknownTransition(ValueError):
    """The observations do not identify a sound stream context."""


def expiry_projection(row, *, connected_at=None):
    """Feasible hidden rejection states under the fixed PeerLifecycle timers.

    This checks the expiry projection, not an unobserved callback history.
    Rejection freezes last_input and replaces deadline by reject_time + 500.
    An unrejected deadline remains connect_time + 20000.
    """
    now, age, remaining = (row[k] for k in ('wall_msec', 'input_age_msec', 'deadline_remaining_msec'))
    need(type(row['joined']) is bool and all(type(v) is int for v in (now, age, remaining)), 'invalid lifecycle expiry projection types')
    if age < 0 or now < age:
        return 'INVALID'
    last_input = now - age
    if connected_at is not None:
        need(type(connected_at) is int and connected_at >= 0, 'invalid proved connection time')
        if last_input < connected_at:
            return 'INVALID'
    deadline = now + remaining
    possible = []
    initial_connection = deadline - 20000
    if (0 <= initial_connection <= last_input and (connected_at is None or initial_connection == connected_at)
            and (row['joined'] or initial_connection == last_input)):
        possible.append((not row['joined'] and remaining <= 0) or (row['joined'] and age >= 30000))
    rejected_at = deadline - 500
    if last_input <= rejected_at <= now:
        possible.append(remaining <= 0 or (row['joined'] and age >= 30000))
    if not possible or not any(possible):
        return 'INVALID'
    return 'CONSISTENT' if all(possible) else 'UNKNOWN'


class LifecycleHypotheses:
    """Persistent source timer alternatives for one observed peer generation.

    Rejection is absorbing. A later row intersects earlier alternatives rather
    than inventing a different connection/rejection to fit its local fields.
    Invalid prefixes are retained until expiry uses this bounded component;
    ordinary legacy schema fixtures are not promoted to emitter-faithful data.
    """
    UNREJECTED_HOOKS = {'peer_bound', 'input_received', 'input_accepted',
                        'input_decode_rejected', 'input_stream_rejected'}

    def __init__(self, row):
        now, age, remaining = (row[k] for k in ('wall_msec', 'input_age_msec', 'deadline_remaining_msec'))
        self.connected_at = now-age if age >= 0 and now >= age and age+remaining == 20000 else None
        self.states = ([] if self.connected_at is None else
                       [dict(rejected=False, deadline=self.connected_at+20000,
                             last=self.connected_at, joined=False, uncertain=False)])
        self.errors = []
        if row['joined'] or row['peer_bound'] or row['bound_actor']:
            self.errors.append('connection already claims an actor/admission')
            self.states = []
        self.time = now
        self.last = now-age if 0 <= age <= now else None
        self.joined = row['joined']
        self.accepted = row['counters'].get('input_accepted', 0)
        self.nonlocal_calls = 0
        self.uncertain = False
        self.detail = ''
        self.used_for_expiry = False

    def other_accepted(self):
        """An explicit other-peer hook cannot pay this identity's activity."""
        self.nonlocal_calls += 1

    def _advance(self, state, row, last, available):
        if not state['joined']:
            if not row['joined']:
                return False if last == state['last'] else None
            if (row['reason'] != 'peer_bound' or last < self.time
                    or (self.connected_at is not None and last >= self.connected_at+20000)):
                return None
            return False  # Observed local admission, not accepted activity.
        if not row['joined'] or last < state['last']:
            return None
        if last == state['last']:
            return False
        if last < self.time or self.time-state['last'] >= 30000:
            return None  # active() cannot revive an already-idle entry.
        required = (last-state['last']+29998)//29999
        if required > available:
            return None
        # A direct accepted hook proves its one local call. Any additional
        # needed hidden allocation from global counters remains unresolved.
        known = int(row['reason'] == 'input_accepted')
        return required > known

    def observe(self, row, actor):
        now, age, remaining = (row[k] for k in ('wall_msec', 'input_age_msec', 'deadline_remaining_msec'))
        accepted = row['counters'].get('input_accepted', 0)
        if (any(type(v) is not int for v in (now, age, remaining, accepted))
                or type(row['joined']) is not bool or age < 0 or age > now or now < self.time):
            self.errors.append('invalid/missing lifecycle time projection')
            self.states = []
            return
        last, deadline = now-age, now+remaining
        if (row['joined'] != bool(actor) or row['peer_bound'] != bool(actor)
                or row['bound_actor'] != actor):
            self.errors.append('joined/actor binding changed before disconnect')
        if row['reason'] in self.UNREJECTED_HOOKS-{'peer_bound'} and not row['joined']:
            self.errors.append('allow-input hook has no admitted lifecycle')
        available = accepted-self.accepted-self.nonlocal_calls
        if available < 0:
            self.errors.append('accepted-call ownership accounting regressed')
        if row['reason'] == 'input_accepted' and available < 1:
            self.errors.append('explicit local accepted call has no counter progress')
        if self.errors:
            self.states = []
        elif self.connected_at is None:
            # Missing legacy foundation never creates proof. Still preserve
            # definite source contradictions and activity ambiguity until expiry.
            if self.last is not None:
                uncertain = self._advance(dict(last=self.last, joined=self.joined), row, last, available)
                if uncertain is None:
                    self.errors.append('last_input/admission contradicts observed activity')
                else:
                    self.uncertain |= uncertain
        else:
            surviving = {}
            for state in self.states:
                if state['rejected']:
                    if (row['reason'] in self.UNREJECTED_HOOKS or deadline != state['deadline']
                            or last != state['last'] or row['joined'] != state['joined']):
                        continue
                    # Residual global calls cannot be attributed locally after
                    # rejection. An unobserved other-owner allocation is not proof.
                    alternatives = [dict(state, uncertain=state['uncertain'] or available > 0)]
                else:
                    uncertain = self._advance(state, row, last, available)
                    if uncertain is None:
                        continue
                    next_state = dict(state, last=last, joined=row['joined'],
                                      uncertain=state['uncertain'] or uncertain
                                      or available > int(row['reason'] == 'input_accepted'))
                    alternatives = []
                    if deadline == state['deadline']:
                        alternatives.append(next_state)
                    rejection = deadline-500
                    if (row['reason'] not in self.UNREJECTED_HOOKS
                            and self.time <= rejection <= now and last <= rejection):
                        alternatives.append(dict(next_state, rejected=True, deadline=deadline))
                for alternative in alternatives:
                    key = tuple(alternative[k] for k in ('rejected', 'deadline', 'last', 'joined'))
                    if key in surviving:
                        surviving[key]['uncertain'] |= alternative['uncertain']
                    else:
                        surviving[key] = alternative
            self.states = list(surviving.values())
        self.time, self.last, self.joined = now, last, row['joined']
        self.accepted, self.nonlocal_calls = accepted, 0

    def expiry(self, row, actor):
        self.used_for_expiry = True
        self.observe(row, actor)
        if self.errors:
            self.detail = '; '.join(self.errors)
            return 'INVALID'
        if self.connected_at is None:
            if expiry_projection(row) == 'INVALID':
                self.detail = 'local expiry predicate has no eligible source state'
                return 'INVALID'
            self.detail = 'expiry lacks a source-faithful prior lifecycle projection'
            return 'UNKNOWN'
        eligible = [((state['rejected'] or not state['joined']) and row['wall_msec'] >= state['deadline'])
                    or (state['joined'] and row['wall_msec']-state['last'] >= 30000) for state in self.states]
        if not eligible or not any(eligible):
            self.detail = 'no persistent eligible lifecycle hypothesis matches all observed prefixes'
            return 'INVALID'
        if not all(eligible):
            self.detail = 'expiry depends on unobserved rejection'
            return 'UNKNOWN'
        if any(state['uncertain'] for state in self.states):
            self.detail = 'global accepted activity has unresolved local expiry ownership'
            return 'UNKNOWN'
        return 'CONSISTENT'


def integral_feasible(node_count, edges):
    """Integral circulation with lower bounds, used for latent command origins."""
    graph = [[] for _ in range(node_count + 2)]
    balance = [0] * node_count
    def add(u, v, capacity):
        graph[u].append([v, capacity, len(graph[v])])
        graph[v].append([u, 0, len(graph[u]) - 1])
    for u, v, low, high in edges:
        if low < 0 or high < low:
            return False
        add(u, v, high - low)
        balance[u] -= low
        balance[v] += low
    source, sink, required = node_count, node_count + 1, 0
    for node, value in enumerate(balance):
        if value > 0:
            add(source, node, value)
            required += value
        elif value < 0:
            add(node, sink, -value)
    total = 0
    while total < required:
        level, queue = [-1] * len(graph), [source]
        level[source] = 0
        for u in queue:
            for v, capacity, _ in graph[u]:
                if capacity and level[v] < 0:
                    level[v] = level[u] + 1
                    queue.append(v)
        if level[sink] < 0:
            return False
        cursor = [0] * len(graph)
        def send(amount):
            u, path, limits = source, [], [amount]
            while True:
                if u == sink:
                    pushed = limits[-1]
                    for parent, index in path:
                        edge = graph[parent][index]
                        edge[1] -= pushed
                        graph[edge[0]][edge[2]][1] += pushed
                    return pushed
                while cursor[u] < len(graph[u]):
                    edge = graph[u][cursor[u]]
                    if edge[1] and level[edge[0]] == level[u] + 1:
                        path.append((u, cursor[u]))
                        limits.append(min(limits[-1], edge[1]))
                        u = edge[0]
                        break
                    cursor[u] += 1
                else:
                    if not path:
                        return 0
                    u, _ = path.pop()
                    limits.pop()
                    cursor[u] += 1
        while True:
            pushed = send(required - total)
            if not pushed:
                break
            total += pushed
    return True


class ReceiptHistory:
    """Persistent possible key origins and aggregate intent, with bounded search."""
    @staticmethod
    def empty():
        return dict(groups=[], known={}, popped={}, checkpoints={})

    @staticmethod
    def domain(group):
        return group['keys'] if group['keys'] is not None else range(group['low'], group['high'] + 1)

    @staticmethod
    def accept(history, value, count, ack):
        result = deepcopy(history)
        endpoints = {value['first'], value['last']}
        if count:
            exposed = {key for key in endpoints if key > max(ack, 0)} if value['count'] <= 2 else None
            result['groups'].append(dict(count=count, low=min(exposed) if exposed else max(ack, 0)+1,
                high=max(exposed) if exposed else max(ack, 0)+120, keys=exposed,
                endpoints=endpoints, endpoint_min=max(0, (1 if value['count'] == 1 else 2) - (value['count'] - count)),
                bounds={field:(max(0,value[field]-(value['count']-count)), min(count,value[field]))
                        for field in ('fire','reload','moving')}, observed=0,
                sums=dict(fire=0,reload=0,moving=0)))
        for key in endpoints:
            if key > max(ack, 0) and key not in result['known']:
                candidates = {i for i, group in enumerate(result['groups']) if key in ReceiptHistory.domain(group)}
                need(bool(candidates), 'endpoint has no feasible first receipt')
                result['known'][key] = candidates
        return result

    @staticmethod
    def pop(history, value):
        sequence = value['sequence']
        need(sequence not in history['popped'], 'receipt history replayed a popped command')
        candidates = history['known'].get(sequence, set(range(len(history['groups']))))
        results = []
        for index in candidates:
            group = history['groups'][index]
            if sequence not in ReceiptHistory.domain(group) or group['observed'] >= group['count']:
                continue
            result = deepcopy(history)
            current = result['groups'][index]
            current['observed'] += 1
            controls = dict(fire=int(value['fire']), reload=int(value['reload']), moving=int(value['move'] != [0.0,0.0]))
            for field, observed in controls.items():
                current['sums'][field] += observed
            if not all(current['sums'][field] <= high and current['sums'][field] + current['count'] - current['observed'] >= low
                       for field, (low, high) in current['bounds'].items()):
                continue
            result['popped'][sequence] = index
            results.append(result)
        return results

    @staticmethod
    def feasible(history, queue_count, ack):
        groups, known, popped = history['groups'], history['known'], history['popped']
        domains = [set(ReceiptHistory.domain(group)) - set(popped) for group in groups]
        if sum(map(len, domains)) > 100000:
            raise UnknownTransition('UNKNOWN receipt-origin flow exceeds bounded reader budget')
        sequences = sorted(set().union(*domains) if domains else set())
        # Preserve every past ACK/cardinality cutoff. A later feasible assignment
        # must also satisfy earlier observations, not invent a different past.
        removed = sum(group['count'] for group in groups) - queue_count
        checkpoints = history['checkpoints']
        if ack in checkpoints and checkpoints[ack] != removed:
            return False
        checkpoints[ack] = removed
        cutoffs = sorted(checkpoints)
        group_nodes = list(range(2, 2 + len(groups)))
        sequence_nodes = {key:2+len(groups)+i for i,key in enumerate(sequences)}
        first_bin = 2 + len(groups) + len(sequences)
        bins = list(range(first_bin, first_bin + len(cutoffs) + 1))
        next_node = first_bin + len(bins)
        total = sum(group['count'] - group['observed'] for group in groups)
        if not 0 <= queue_count <= total:
            return False
        edges = [(1,0,0,total), (bins[-1],1,queue_count,queue_count)]
        previous = 0
        for cutoff, node in zip(cutoffs, bins):
            target = checkpoints[cutoff] - sum(key <= cutoff for key in popped)
            edges.append((node,1,target-previous,target-previous))
            previous = target
        for index, group in enumerate(groups):
            remaining = group['count'] - group['observed']
            edges.append((0, group_nodes[index], remaining, remaining))
            endpoint_node = next_node
            next_node += 1
            already = sum(key in group['endpoints'] and owner == index for key,owner in popped.items())
            minimum = max(0, group['endpoint_min'] - already)
            edges.append((group_nodes[index], endpoint_node, minimum, len(group['endpoints'])))
            for key in domains[index]:
                if key in known and index not in known[key]:
                    continue
                target = sequence_nodes[key]
                edges.append((group_nodes[index], target, 0, 1))
                if key in group['endpoints']:
                    edges.append((endpoint_node, target, 0, 1))
        for key, node in sequence_nodes.items():
            edges.append((node, bins[bisect_left(cutoffs,key)], int(key in known), 1))
        if any(key not in sequence_nodes and key not in popped for key in known):
            return False
        return integral_feasible(next_node, edges)


def accepted_header(value, epoch, ack_low, ack_high):
    """Existence of a valid pre-accept ACK in an observed monotonic interval."""
    need(value['epoch'] == epoch and value['count'] in range(1, 13), 'accepted packet has wrong epoch or count')
    need(value['first'] >= 1 and value['last'] >= 1 and (value['count'] > 1 or value['first'] == value['last']),
         'accepted packet has invalid sequence endpoints')
    low = max(0, ack_low, value['first'] - 120, value['last'] - 120)
    high = max(0, ack_high)
    if value['count'] <= 2:
        high = min(high, max(value['first'], value['last']) - 1)
    need(low <= high, 'accepted packet has no valid ACK context for its input window/fresh intent')


class InputTransitions:
    """Necessary source transitions; never reconstruct missing packet bodies."""
    def __init__(self):
        self.prior = None
        self.streams = {}
        self.accepted_calls = {}
        self.consumed_calls = {}

    @staticmethod
    def consumed_identity(row):
        value = row['latest'].get('input_consumed', {})
        return (value.get('peer'), value.get('generation'))

    def observe(self, row, owners_before):
        if row['role'] != 'authority':
            return
        identity = row['peer'], row['generation']
        counters = row['counters']
        prior = self.prior
        for key, state in self.streams.items():
            if owners_before - {key}:
                state['exclusive'] = False
        delta = lambda stage, previous: counters.get(stage, 0) - previous['counters'].get(stage, 0)
        da = delta('input_accepted', prior) if prior else 0
        dc = delta('input_consumed', prior) if prior else 0
        if prior:
            need(row['authority_epoch'] >= prior['authority_epoch'], 'authority epoch regressed')
            resets = row['authority_epoch'] > prior['authority_epoch'] and not owners_before
            old, new = prior['stream_skipped'], row['stream_skipped']
            possible_skip = lambda value: value == 0 or 5 <= value <= 118 * dc
            need(possible_skip(new - old) or (resets and possible_skip(new)),
                 'skipped stream state has no corresponding pop/reset transition')

        state = self.streams.get(identity)
        if dc:
            consumed_owner = self.consumed_identity(row)
            need(consumed_owner in owners_before, 'new consumed metadata has no live binding')
            context = self.streams.get(consumed_owner)
            value = row['latest']['input_consumed']
            need(context and value['actor'] == context['row']['bound_actor'] and value['sequence'] > 0,
                 'new consumed metadata disagrees with its bound stream identity')
            if dc == 1:
                self.consumed_calls[counters['input_consumed']] = (consumed_owner, deepcopy(value))
            if consumed_owner != identity:
                old = context['row']
                if (old['authority_epoch'] != row['authority_epoch']
                        or delta('input_accepted', old) != 0 or delta('input_consumed', old) != 1):
                    raise UnknownTransition('UNKNOWN unselected consumed stream transition')
                skipped = max(0, old['queue_count'] - 2) if old['queue_count'] > 6 else 0
                need(row['stream_skipped'] - old['stream_skipped'] == skipped,
                     'unselected pop has inconsistent backlog skipping')
                inferred = {**row, 'peer': consumed_owner[0], 'generation': consumed_owner[1],
                            'bound_actor': old['bound_actor'], 'stream_ack': value['sequence'],
                            'queue_count': old['queue_count'] - skipped - 1}
                required, histories = self.queue_transition(context, inferred, 0, 1, skipped)
                self.streams[consumed_owner] = dict(row=inferred, required=required, histories=histories,
                                                  exclusive=not (owners_before - {consumed_owner}))
        owner = None
        if da:
            if row['reason'] == 'input_accepted':
                owner = identity
            elif len(owners_before) == 1:
                owner = next(iter(owners_before))
            elif da == 1 and state and delta('input_accepted', state['row']) == 1:
                previous = state['row']
                # A sole acceptance must supply a newly empty stream's pop,
                # or its otherwise unexplained queue growth. No packet is guessed.
                supplied_pop = (previous['queue_count'] == 0
                                and delta('input_consumed', previous) == 1
                                and self.consumed_identity(row) == identity
                                and row['stream_ack'] > previous['stream_ack'])
                if supplied_pop or row['queue_count'] > previous['queue_count']:
                    owner = identity
            need(bool(owners_before) or row['reason'] == 'input_accepted', 'acceptance has no live stream context')
            if owner is None:
                raise UnknownTransition('UNKNOWN acceptance ownership across multiple live streams')
            context = self.streams.get(owner)
            if context is None:
                raise UnknownTransition('UNKNOWN prior ACK context for newly counted acceptance')
            old = context['row']
            pop_amount = delta('input_consumed', old)
            proved_pops = [(index, projection) for index,(who,projection) in self.consumed_calls.items()
                           if old['counters'].get('input_consumed',0) < index <= counters.get('input_consumed',0)]
            if len(proved_pops) == pop_amount:
                owned_pops = [(index,projection) for index,projection in proved_pops
                              if (projection['peer'],projection['generation']) == owner]
                owner_pop_count = len(owned_pops)
                last_pop = max(owned_pops,default=(0,None),key=lambda item:item[0])[1]
            elif context['exclusive'] and self.consumed_identity(row) == owner:
                owner_pop_count, last_pop = pop_amount, row['latest']['input_consumed']
            else:
                owner_pop_count, last_pop = None, None
            validation_epoch = row['authority_epoch']
            crossed_epoch = old['authority_epoch'] != row['authority_epoch']
            if crossed_epoch and row['reason'] != 'input_accepted':
                if owner_pop_count != 0:
                    raise UnknownTransition('UNKNOWN acceptance/pop ordering across an epoch boundary')
                validation_epoch = row['latest']['input_accepted']['epoch']
                need(old['authority_epoch'] <= validation_epoch <= row['authority_epoch'],
                     'accepted call claims an epoch outside its observed interval')
                low = high = old['stream_ack'] if validation_epoch == old['authority_epoch'] else -1
            elif row['reason'] == 'input_accepted':
                low = high = row['stream_ack']
            else:
                low = old['stream_ack']
                if owner == identity:
                    high = row['stream_ack']
                elif owner_pop_count == 0:
                    high = low
                elif last_pop:
                    high = last_pop['sequence']
                else:
                    raise UnknownTransition('UNKNOWN hidden acceptance ACK interval for unselected stream')
                if owner_pop_count and last_pop:
                    at = row['latest']['input_accepted']['wall_msec']
                    ct = last_pop['wall_msec']
                    if ct < at:
                        low = high
                    elif at < ct or row['reason'] == 'input_consumed':
                        high = low if owner_pop_count == 1 else max(low, high - 1)
            accepted_header(row['latest']['input_accepted'], validation_epoch, low, high)
            if da == 1:
                self.accepted_calls[counters['input_accepted']] = (owner, deepcopy(row['latest']['input_accepted']))

        need(row['stream_ack'] == -1 or row['stream_ack'] > 0, 'stream ACK is neither absent nor a popped positive sequence')
        if row['generation'] <= 0 or row['reason'] in {'peer_connected', 'peer_bound'}:
            need(row['stream_ack'] == -1 and row['queue_count'] == 0, 'new/absent stream has queued input or an ACK')
        if row['generation'] > 0:
            required = {}
            histories = [ReceiptHistory.empty()]
            if state and row['reason'] not in {'peer_connected', 'peer_bound'}:
                previous = state['row']
                same_epoch = previous['authority_epoch'] == row['authority_epoch']
                a, c = delta('input_accepted', previous), delta('input_consumed', previous)
                k = row['stream_skipped'] - previous['stream_skipped']
                exact_a = a if state['exclusive'] else (0 if a == 0 else (1 if a == 1 and owner == identity else None))
                exact_c = c if state['exclusive'] else (0 if c == 0 else (int(self.consumed_identity(row) == identity) if c == 1 else None))
                local_packets = {}
                for stage, ledger, amount in (('input_accepted',self.accepted_calls,a), ('input_consumed',self.consumed_calls,c)):
                    proved = [entry for index,entry in ledger.items() if previous['counters'].get(stage,0) < index <= counters.get(stage,0)]
                    if len(proved) == amount:
                        owned = [projection for who,projection in proved if who == identity]
                        if stage == 'input_accepted':
                            exact_a = len(owned)
                        else:
                            exact_c = len(owned)
                        if len(owned) == 1:
                            local_packets[stage] = owned[0]
                exact_k = k if state['exclusive'] or (c == 1 and exact_c == 1) else (0 if exact_c == 0 else None)
                if (exact_k is None and exact_c == 1 and exact_a in (0,1)
                        and (not exact_a or 'input_accepted' in local_packets)
                        and previous['queue_count'] + (local_packets['input_accepted']['count'] if exact_a else 0) <= 6):
                    exact_k = 0
                if same_epoch:
                    need(row['stream_ack'] >= previous['stream_ack'], 'stream ACK regressed/cleared without reset')
                    if exact_c == 0:
                        need(row['stream_ack'] == previous['stream_ack'], 'stream ACK changed without a consumed call')
                    elif exact_c is not None:
                        need(row['stream_ack'] > previous['stream_ack'], 'nonnull pops did not advance stream ACK')
                    if c and self.consumed_identity(row) == identity:
                        need(row['stream_ack'] == row['latest']['input_consumed']['sequence'], 'stream ACK differs from its latest immutable pop')
                    need(k >= 0, 'skipped state regressed inside a live stream epoch')
                    max_add = 12 * a if exact_a is None or exact_a else 0
                    if a and exact_a == a and owner == identity:
                        value = row['latest']['input_accepted']
                        last_count = len({value['first'], value['last']}) if value['count'] <= 2 else value['count']
                        max_add = 12 * (a - 1) + last_count
                    cmin, cmax = (0, c) if exact_c is None else (exact_c, exact_c)
                    kmin, kmax = (0, k) if exact_k is None else (exact_k, exact_k)
                    need(max(0, previous['queue_count'] - cmax - kmax) <= row['queue_count'] <= min(120, previous['queue_count'] + max_add - cmin - kmin),
                         'queue cardinality has no accepted/pop/skipped transition')
                    need(sum(key <= row['stream_ack'] for key in state['required']) <= cmax + kmax,
                         'ACK passed more definite keys than pop/skipping could remove')
                    if cmin:
                        need(row['stream_ack'] >= max(previous['stream_ack'], 0) + cmin + kmin,
                             'ACK violates consumed/skipped unique sequence rank')
                    if exact_a in (0, 1) and exact_c in (0, 1) and exact_k is not None:
                        if (exact_a and 'input_accepted' not in local_packets) or (exact_c and 'input_consumed' not in local_packets):
                            raise UnknownTransition('UNKNOWN missing local call projection in persistent receipt history')
                        transition_row = {**row, 'latest':{**row['latest'], **local_packets}}
                        required, histories = self.queue_transition(state, transition_row, exact_a, exact_c, exact_k)
                    else:
                        raise UnknownTransition('UNKNOWN unexposed local call history for persistent receipt constraints')
                else:
                    # Both epoch operations clear queues/ACKs. Calls may straddle
                    # that boundary; current direct consumption still needs input.
                    need(row['queue_count'] <= min(120, 12 * a), 'epoch reset queue has no new accepted input')
                    need(row['stream_ack'] == -1 or c > 0, 'epoch reset ACK has no new consumed input')
                    if exact_a == exact_c == 0:
                        need(row['stream_ack'] == -1 and row['queue_count'] == 0, 'epoch reset failed to clear queue/ACK')
                    elif exact_a == 1 and exact_c == 0 and 'input_accepted' in local_packets:
                        if local_packets['input_accepted']['epoch'] == row['authority_epoch']:
                            fresh = dict(row={**previous, 'authority_epoch':row['authority_epoch'],
                                              'stream_ack':-1, 'queue_count':0},
                                         required={}, histories=[ReceiptHistory.empty()])
                            transition_row = {**row, 'latest':{**row['latest'], **local_packets}}
                            required, histories = self.queue_transition(fresh, transition_row, 1, 0, 0)
                        else:
                            need(row['stream_ack'] == -1 and row['queue_count'] == 0,
                                 'epoch reset retained input from an older accepted epoch')
                    else:
                        need(row['reason'] != 'input_consumed' or exact_a != 0, 'epoch-reset pop has no newly accepted input')
                        raise UnknownTransition('UNKNOWN receipt ordering across an unobserved epoch boundary')
            self.streams[identity] = dict(row=row, required=required, histories=histories,
                                          exclusive=not (owners_before - {identity}))
        self.prior = row

    @staticmethod
    def check_signature(signature, value):
        observed = dict(fire=value['fire'], reload=value['reload'], moving=value['move'] != [0.0, 0.0])
        need(all(expected is None or observed[field] == expected for field, expected in signature.items()),
             'popped command changed immutable queued intent')

    @staticmethod
    def queue_transition(state, row, accepts, pops, skipped):
        """Definite keys/signatures plus cardinality; middle bodies stay unknown."""
        packet = row['latest'].get('input_accepted')
        additions = row['queue_count'] - state['row']['queue_count'] + pops + skipped
        need(0 <= additions <= (packet['count'] if accepts else 0), 'queue additions exceed known accepted input')
        orders = [('accept', 'pop'), ('pop', 'accept')] if accepts and pops else [(('accept',) if accepts else ('pop',) if pops else ())]
        if accepts and pops:
            at, ct = packet['wall_msec'], row['latest']['input_consumed']['wall_msec']
            if row['reason'] == 'input_consumed' or at < ct:
                orders = [('accept', 'pop')]
            elif row['reason'] == 'input_accepted' or ct < at:
                orders = [('pop', 'accept')]
        alternatives = []
        for order in orders:
            required = {key: dict(value) for key, value in state['required'].items()}
            histories = deepcopy(state['histories'])
            ack, count, removed = state['row']['stream_ack'], state['row']['queue_count'], 0
            try:
                for event in order:
                    if event == 'accept':
                        accepted_header(packet, row['authority_epoch'], ack, ack)
                        endpoints = {key for key in (packet['first'], packet['last']) if key > max(ack, 0)}
                        unknown_slots = count - len(required)
                        unseen = endpoints - set(required)
                        need(additions >= max(int(count == 0), len(unseen) - unknown_slots), 'accepted input failed to retain definite fresh keys')
                        if packet['count'] <= 2:
                            need(additions <= len(unseen), 'exposed packet inflated its queued unique keys')
                        for sequence in endpoints:
                            if sequence not in required:
                                required[sequence] = ({field: (packet[field] == packet['count'] if packet[field] in (0, packet['count']) else None)
                                                       for field in ('fire', 'reload', 'moving')}
                                                      if unknown_slots == 0 else {})
                        count += additions
                        need(len(required) <= count <= 120, 'accepted queue cannot contain its definite keys')
                        histories = [ReceiptHistory.accept(history, packet, additions, ack) for history in histories]
                    else:
                        need(count > 0, 'empty queue cannot produce a pop')
                        discarded = count - 2 if count > 6 else 0
                        removed += discarded
                        value = row['latest']['input_consumed']
                        sequence = value['sequence']
                        remaining = count - discarded - 1
                        need(max(ack, 0) + discarded + 1 <= sequence
                             and sequence + remaining <= max(ack, 0) + 120,
                             'pop violates unique sequence order/window bounds')
                        need(sum(key < sequence for key in required) <= discarded,
                             'pop passed a definite older queued command')
                        InputTransitions.check_signature(required.get(sequence, {}), value)
                        histories = [variant for history in histories for variant in ReceiptHistory.pop(history, value)]
                        required = {key: signature for key, signature in required.items() if key > sequence}
                        need(len(required) <= remaining, 'pop/skipping removed a definite newer command')
                        count = remaining
                        ack = sequence
                need(count == row['queue_count'] and ack == row['stream_ack'], 'queue/ACK differs from source transition')
                need(removed == skipped, 'backlog skips differ from source transition')
                if len(histories) > 512:
                    raise UnknownTransition('UNKNOWN intermediate receipt alternatives exceed bounded reader budget')
                histories = [history for history in histories if ReceiptHistory.feasible(history, count, ack)]
                need(bool(histories), 'no persistent receipt/intent history remains feasible')
                alternatives.append((required, histories))
            except UnknownTransition:
                raise
            except ValueError:
                continue
        need(bool(alternatives), 'stream transition contradicts definite immutable commands')
        required = {key: dict(value) for key, value in alternatives[0][0].items()
                    if all(key in other for other,_ in alternatives[1:])}
        for sequence, signature in required.items():
            for field in signature:
                if any(other.get(sequence, {}).get(field) != signature[field] for other,_ in alternatives[1:]):
                    signature[field] = None
        histories = [history for _, variants in alternatives for history in variants]
        histories = list({json.dumps(history, sort_keys=True, default=sorted, separators=(',',':')):history
                          for history in histories}.values())
        if len(histories) > 128:
            raise UnknownTransition('UNKNOWN receipt alternatives exceed bounded reader budget')
        return required, histories


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
    need(snapshot == latest.get('snapshot_applied', {}), 'snapshot cache differs from its counted latest application')
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


def authority_lifecycle_foundation(rows):
    """Check observed authority identity/timer histories before packet inference.

    This proves only this projection. Unsupported failed-connect callbacks and
    anonymous activity allocations remain incomplete; raw rows are never repaired.
    """
    need(rows[0]['reason'] == 'ready', 'authority lifecycle lacks its fresh ready cut')
    peers, actors, histories = {}, {}, {}
    generation = last_peer = last_actor = 0
    unknown = []
    absent = dict(generation=-1, joined=False, input_age_msec=-1,
                  deadline_remaining_msec=-1, bound_actor=0, peer_bound=False)
    named = ROLE_STAGES['authority'] - {'ready', 'authority_tick'}
    for ordinal, row in enumerate(rows):
        reason, peer = row['reason'], row['peer']
        if reason == 'ready':
            need(ordinal == 0 and peer == 0 and row['last_bound_actor'] == 0
                 and all(row[key] == value for key, value in absent.items()),
                 'fresh authority ready has a live lifecycle projection')
            continue
        if reason in named:
            if peer > 0:
                last_peer = peer
            else:
                need(last_peer == 0, 'named authority hook lost its selected peer')
        else:
            need(peer == last_peer, 'authority tick changed selected peer without a hook')
        identity = (peer, row['generation'])
        if reason == 'peer_connected':
            if peer in peers or len(peers) >= 10:
                unknown.append('failed duplicate/capacity connection callback is outside the proved caller scope')
            else:
                need(peer > 0 and row['generation'] == generation + 1,
                     'successful connection skipped or reused the global generation')
                now, age, remaining = (row[key] for key in
                                       ('wall_msec', 'input_age_msec', 'deadline_remaining_msec'))
                need(0 <= age <= now and age + remaining == 20000
                     and not row['joined'] and not row['peer_bound'] and row['bound_actor'] == 0,
                     'successful connection has an impossible initial lifecycle projection')
                generation = row['generation']
                peers[peer] = generation
                histories[identity] = LifecycleHypotheses(row)
        if reason == 'peer_bound':
            need(peers.get(peer) == row['generation'] and identity in histories
                 and peer not in actors and row['bound_actor'] > 0
                 and row['bound_actor'] not in actors.values(),
                 'authority admission lacks a fresh unbound peer generation')
            actors[peer] = row['bound_actor']
        actor = actors.get(peer, 0)
        if reason in named and actor:
            last_actor = actor
        need(row['last_bound_actor'] == last_actor,
             'authority sticky actor changed without a bound-peer hook')
        if peer not in peers:
            need(all(row[key] == value for key, value in absent.items()),
                 'absent authority peer retains a live lifecycle projection')
        else:
            need(peers[peer] == row['generation'] and identity in histories,
                 'selected authority peer changed its live generation')
            history = histories[identity]
            if reason != 'peer_connected':
                history.observe(row, actor)
            need(not history.errors and bool(history.states),
                 'authority lifecycle history is impossible: ' + '; '.join(history.errors))
            if any(state['uncertain'] for state in history.states):
                unknown.append('anonymous accepted calls cannot prove this peer lifecycle')
        if reason == 'input_accepted':
            for other, history in histories.items():
                if other != identity:
                    history.other_accepted()
        if reason == 'peer_disconnected':
            peers.pop(peer, None)
            actors.pop(peer, None)
    if unknown:
        raise UnknownTransition('; '.join(dict.fromkeys(unknown)))


def analyze_role(rows, role):
    need(bool(rows), 'no observation records for ' + role)
    for row in rows:
        record_valid(row)
    coverage = set(rows[-1]['counters'])
    need(REQUIRED[role] <= coverage, 'missing pipeline stages: ' + ','.join(sorted(REQUIRED[role] - coverage)))
    observed_events = {row['reason'] for row in rows}
    need(REQUIRED[role] - {'snapshot_applied'} <= observed_events, 'missing direct pipeline event records')
    if role == 'authority':
        authority_lifecycle_foundation(rows)
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
    transitions = InputTransitions()
    expiry_unknowns = []
    lifecycle_history = {}
    for row in rows:
        owners_before = set(live_bindings)
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
                need(row['stream_rejected'] == expected or (reset_possible and row['stream_rejected'] <= rejections - previous_counters.get('input_stream_rejected', 0)),
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
            lifecycle_history[identity] = LifecycleHypotheses(row)
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
            if row['reason'] == 'peer_expired':
                need(identity in connected and live_peers.get(row['peer']) == row['generation'] and identity not in ended,
                     'expiry has no current connected peer generation')
                history = lifecycle_history[identity]
                status = history.expiry(row, bindings.get(identity, 0))
                need(status != 'INVALID', 'peer expiry contradicts lifecycle history: ' + history.detail)
                if status == 'UNKNOWN':
                    expiry_unknowns.append(history.detail + ' for peer %s generation %s' % identity)
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
                accepted_header(value, row['authority_epoch'], row['stream_ack'], row['stream_ack'])
                accepted.append({'index': row['index'], **value})
            else:
                # Receive is after the identity gate but before packet validation.
                # Its malformed payload fields can describe real rejected input.
                received.append({'index': row['index'], **value})
        if row['pending_count'] == 120:
            saturations.append(row['index'])
        transitions.observe(row, owners_before)
        if role == 'authority' and reason == 'input_accepted':
            for other_identity, history in lifecycle_history.items():
                if other_identity != identity:
                    history.other_accepted()
        if (role == 'authority' and identity in lifecycle_history
                and reason not in {'peer_connected', 'peer_expired'}):
            history = lifecycle_history[identity]
            history.observe(row, bindings.get(identity, 0))
            if history.used_for_expiry:
                need(not history.errors and (history.connected_at is None or bool(history.states)),
                     'later prefix contradicts the already observed expiry lifecycle')
        prior = row
    if role == 'authority':
        need(bool(consumed) and bool(accepted), 'acceptance and actual consumption need distinct observed events')
    if expiry_unknowns:
        raise UnknownTransition('; '.join(expiry_unknowns))
    return {'records': len(rows), 'coverage': sorted(coverage), 'counters': prior['counters'], 'max_observation_gap_msec': max_gap,
            'max_snapshot_age_msec': max(r['snapshot_age_msec'] for r in rows), 'pending_saturation_indices': saturations,
            'accepted_events': accepted, 'consumed_events': consumed, 'expiry_events': expiries, 'disconnect_events': disconnects,
            'welcome_events': welcomes, 'binding_events': binding_events,
            'local_attempts': prior['local_attempt']}


def analyze(client_text, authority_text):
    report = {'scope': 'Debug read-only stage observations; no qualification, physical latency or unobserved cause claim',
              'diagnostic_complete': False, 'transition_status': 'INCOMPLETE', 'cause_status': 'UNRESOLVED; observations identify executed stages and gaps only', 'roles': {}, 'errors': []}
    unknown_errors = 0
    for role, raw in [('client', client_text), ('authority', authority_text)]:
        try:
            report['roles'][role] = analyze_role(parse_log(raw), role)
        except UnknownTransition as error:
            unknown_errors += 1
            report['errors'].append(role + ': ' + str(error))
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
    report['transition_status'] = ('CONSISTENT' if not report['errors'] else
                                   'UNKNOWN' if len(report['errors']) == unknown_errors else 'INVALID')
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
