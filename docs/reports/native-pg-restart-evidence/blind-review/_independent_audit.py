"""Read-only analysis of the extracted packet; no service/application execution."""
import collections
import datetime as dt
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parent
STAGES = ['01-before', '02-committed-before-kill', '03-after-kill',
          '04-after-recovery', '05-after-second-restart']
PHASES = ['send', 'recovery', 'second-restart']
TABLES = ['players', 'items', 'listings', 'operations', 'ledger', 'audit',
          'loadouts', 'rewards', 'trades']
failures = []
checks = collections.Counter()


def check(value, context):
    checks['evaluated'] += 1
    if not value:
        failures.append(context)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'), parse_float=Decimal)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def one(seq):
    seq = list(seq)
    if len(seq) != 1:
        raise ValueError(f'Expected exactly one record, got {len(seq)}: {seq}')
    return seq[0]


def sqlns(timestamp):
    value = dt.datetime.fromisoformat(timestamp).astimezone(dt.timezone.utc)
    delta = value - dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    return ((delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds) * 1000


def delta(before, after):
    old = {row['id']: row for row in before}
    new = {row['id']: row for row in after}
    return {
        'added_rows': [v for k, v in new.items() if k not in old],
        'removed_rows': [v for k, v in old.items() if k not in new],
        'changed_rows': [{'before': old[k], 'after': v}
                         for k, v in new.items() if k in old and old[k] != v],
    }


manifest = load(ROOT / 'MANIFEST.json')
for name, spec in manifest['files'].items():
    data = (ROOT / name).read_bytes()
    check(len(data) == spec['bytes'] and sha(data) == spec['sha256'], 'manifest: ' + name)
observed = load(ROOT / 'OBSERVED_COMPARISON.json')
out = {'payloads_hashed': len(manifest['files']), 'cases': []}
for group in sorted(ROOT.glob('Set-*')):
    previous_final = None
    for case in sorted(group.glob('case-*')):
        label = f'{group.name}/{case.name}'
        ccheck = lambda condition, message: check(condition, label + ': ' + message)
        fixtures = load(case / 'fixture.redacted.json')
        states = [load(case / (s + '.json')) for s in STAGES]
        es = [s['economic_state'] for s in states]
        timeline = [json.loads(line, parse_float=Decimal)
                    for line in (case / 'timeline.jsonl').read_text().splitlines()]
        event = lambda kind, **filters: one(e for e in timeline if e['event'] == kind
                                            and all(e.get(k) == v for k, v in filters.items()))
        requests = [e for e in timeline if e['event'] == 'proxy_request']
        purchases = [e for e in requests if e['path'].endswith('/buy')]
        initial = one(e for e in purchases if e['phase'] == 'send')
        recovery = [e for e in purchases if e['phase'] == 'recovery']
        response = event('proxy_upstream_response', phase='send', path=initial['path'])
        price = initial['body']['expected_price']
        receipt = initial['body']['idempotency_key']
        ccheck(str(uuid.UUID(receipt)) == receipt, 'UUID receipt')
        ccheck(type(price) is int, 'original consent strict integer')
        ccheck(initial['method'] == 'POST' and initial['path'] == fixtures['path']
               == '/market/' + fixtures['listing'] + '/buy', 'purchase path and method')
        ccheck(initial['body'] == fixtures['payload'], 'dispatch equals fixture')
        for e in timeline:
            if e['event'] == 'proxy_request':
                ccheck((json.loads(e['raw_utf8'], parse_float=Decimal) if e['raw_utf8'] else None)
                       == e['body'], 'wire request JSON equality')
            elif e['event'] == 'proxy_upstream_response':
                ccheck(json.loads(e['raw_utf8'], parse_float=Decimal) == e['response'],
                       'wire response JSON equality')
        ccheck(all(e['method'] == 'GET' or e['path'] in ['/auth/login', fixtures['path']]
                   for e in requests), 'no other mutation request')

        ids = {k: fixtures[k] for k in ['owner', 'seller', 'item', 'listing']}
        getrow = lambda i, table, key: one(x for x in es[i][table] if x['id'] == key)
        buyer = [getrow(i, 'players', ids['owner'])['credits'] for i in range(5)]
        seller = [getrow(i, 'players', ids['seller'])['credits'] for i in range(5)]
        money = [sum(p['credits'] for p in state['players']) for state in es]
        fee = money[0] - money[1]
        ccheck(buyer[0] - buyer[1] == price, 'buyer debit')
        ccheck(seller[1] - seller[0] == price - fee, 'seller credit')
        ccheck(fee == price * 300 // 10000, 'observed fee consistent with integer-floor 300bps')
        ccheck(response['status'] == 200 and response['response']['fee'] == fee
               and response['response']['credits'] == buyer[1], 'initial success economic result')
        catalog = [e for e in timeline if e['event'] == 'proxy_upstream_response'
                   and e['path'] == '/catalog']
        ccheck(all(e['response']['market_fee_basis_points'] == 300 for e in catalog), 'catalog fee')
        deltas = {table: delta(es[0][table], es[1][table]) for table in TABLES}
        expected_changes = {'players': (0, 0, 2), 'items': (0, 0, 1),
                            'listings': (0, 0, 1), 'operations': (1, 0, 0),
                            'ledger': (2, 0, 0), 'audit': (1, 0, 0),
                            'loadouts': (0, 0, 0), 'rewards': (0, 0, 0), 'trades': (0, 0, 0)}
        for table, counts in expected_changes.items():
            ccheck(tuple(len(deltas[table][k]) for k in ['added_rows', 'removed_rows', 'changed_rows'])
                   == counts, 'exact changed-row counts ' + table)
        ccheck({r['after']['id'] for r in deltas['players']['changed_rows']}
               == {ids['owner'], ids['seller']}, 'only buyer and seller change')
        for row in deltas['players']['changed_rows']:
            ccheck({k for k in row['before'] if row['before'][k] != row['after'][k]} == {'credits'},
                   'only credits field changes')
        beforeitem, afteritem = getrow(0, 'items', ids['item']), getrow(1, 'items', ids['item'])
        ccheck(beforeitem['owner_id'] == ids['seller']
               and beforeitem['reservation'] == 'market:' + ids['listing'], 'item before')
        ccheck(afteritem == dict(beforeitem, owner_id=ids['owner'], reservation=None)
               and afteritem['consumed'] is False, 'item exact transfer and release')
        beforelisting, afterlisting = getrow(0, 'listings', ids['listing']), getrow(1, 'listings', ids['listing'])
        ccheck(beforelisting == {'id': ids['listing'], 'buyer_id': None, 'item_id': ids['item'],
                                 'price': price, 'seller_id': ids['seller'], 'state': 'active'}, 'active listing')
        ccheck(afterlisting == dict(beforelisting, buyer_id=ids['owner'], state='sold'), 'sold listing')
        operation = one(deltas['operations']['added_rows'])
        ccheck(operation['id'] == f"{ids['owner']}:buy:{ids['listing']}:{receipt}", 'operation receipt identity')
        ccheck(operation['request_hash'] == sha(initial['raw_utf8'].encode('utf-8')), 'operation request digest')
        ccheck(operation['response'] == response['response'], 'entire operation equals held response')
        for key in ['id', 'definition_id', 'rarity', 'pattern_seed', 'variant']:
            ccheck(response['response']['item'][key] == afteritem[key], 'response item ' + key)
        ccheck(response['response']['item']['wear'] == Decimal(afteritem['wear']) / 10000,
               'wear conversion')
        ccheck(response['response']['item']['acquired_at'] == afteritem['acquired_at'].replace(' ', 'T')
               and response['response']['item']['reserved'] is False, 'item response time/reservation')
        ledger = deltas['ledger']['added_rows']
        debit = one(x for x in ledger if x['player_id'] == ids['owner'])
        credit = one(x for x in ledger if x['player_id'] == ids['seller'])
        ccheck((debit['amount'], debit['balance_after'], debit['reason'], debit['reference'])
               == (-price, buyer[1], 'market_purchase', ids['listing']), 'exact debit ledger')
        ccheck((credit['amount'], credit['balance_after'], credit['reason'], credit['reference'])
               == (price - fee, seller[1], 'market_sale', ids['listing']), 'exact credit ledger')
        audit = one(deltas['audit']['added_rows'])
        ccheck(audit['action'] == 'market_settled' and audit['actor'] == ids['owner']
               and audit['details'] == {'fee': fee, 'from_player': ids['seller'], 'to_player': ids['owner'],
                                        'item_id': ids['item'], 'listing_id': ids['listing']}, 'exact settlement audit')
        for i, state in enumerate(es):
            for table in TABLES:
                ccheck(len({x['id'] for x in state[table]}) == len(state[table]), 'unique row IDs ' + STAGES[i] + '/' + table)
            for player in state['players']:
                entries = sorted((e for e in state['ledger'] if e['player_id'] == player['id']),
                                 key=lambda x: (sqlns(x['created_at']), x['id']))
                balance = 0
                for entry in entries:
                    balance += entry['amount']
                    ccheck(balance == entry['balance_after'], 'ledger running balance ' + entry['id'])
                ccheck(balance == player['credits'], 'player fully reconciles with ledger ' + player['id'])
            if i >= 2:
                ccheck(state == es[1], 'complete economic equality to commit ' + STAGES[i])
        if previous_final is not None:
            between = {table: delta(previous_final['economic_state'][table], es[0][table]) for table in TABLES}
            ccheck(all(not any(d.values()) for t, d in between.items() if t not in ['items', 'listings', 'audit']),
                   'earlier-case carryover without unrelated effects')
            ccheck(tuple(len(between[t]['added_rows']) for t in ['audit', 'listings']) == (1, 1)
                   and len(between['items']['changed_rows']) == 1, 'next fixture listing only')
            ccheck(previous_final['sessions'] == states[0]['sessions'], 'session continuity between cases')
        previous_final = states[-1]

        starts = {p: event('native_started', phase=p) for p in PHASES}
        ends = {p: event('native_finished', phase=('killed-client' if p == 'send' else p)) for p in PHASES}
        ccheck(len({s['pid'] for s in starts.values()}) == 3, 'distinct native PIDs')
        ccheck(all(not s['other_native_pids'] for s in starts.values()), 'recorded native isolation')
        ccheck(len({e['harness_pid'] for e in timeline}) == 1, 'one harness clock domain per case')
        ccheck(all(a['wall_ns'] <= b['wall_ns'] and a['monotonic_ns'] <= b['monotonic_ns']
                   for a, b in zip(timeline, timeline[1:])), 'timeline ordered within clock domains')
        snapshots = [event('postgresql_snapshot', name=s) for s in STAGES]
        for i, snapshot in enumerate(snapshots):
            pg = states[i]['postgresql']
            ccheck(snapshot['connection_pid'] == pg['pg_backend_pid'] and snapshot['database'] == pg['current_database'],
                   'SQL connection binding ' + STAGES[i])
            ccheck(pg['pg_backend_pid'] not in {s['pid'] for s in starts.values()}, 'separate SQL connection PID')
            ccheck(snapshot['state_sha256'] == sha(json.dumps(es[i], sort_keys=True, default=float).encode()), 'recomputed economic digest ' + STAGES[i])
            ccheck(sqlns(pg['clock_timestamp']) <= snapshot['wall_ns'], 'SQL clock precedes captured snapshot event')
        ccheck(len({s['postgresql']['current_database'] for s in states}) == 1
               and len({s['postgresql']['inet_server_port'] for s in states}) == 1, 'same recorded database')
        held, killed, confirmed, discarded = [event(k) for k in ['response_held_before_any_client_headers',
                                                              'kill_requested', 'kill_confirmed', 'held_response_discarded']]
        chain = [initial, response, held, snapshots[1], killed, ends['send'], confirmed,
                 snapshots[2], discarded, starts['recovery'], ends['recovery'], snapshots[3],
                 starts['second-restart'], ends['second-restart'], snapshots[4]]
        ccheck(all(a['wall_ns'] <= b['wall_ns'] and a['monotonic_ns'] <= b['monotonic_ns']
                   and timeline.index(a) < timeline.index(b)
                   for a, b in zip(chain, chain[1:])), 'commit/kill/exit/discard/restart exact ordering')
        ccheck(snapshots[1]['wall_ns'] < killed['wall_ns'] < ends['send']['wall_ns']
               <= confirmed['wall_ns'] < discarded['wall_ns'] < starts['recovery']['wall_ns'],
               'strict commit snapshot/kill/exit/discard/recovery boundaries')
        ccheck(held['wall_ns'] < sqlns(states[1]['postgresql']['clock_timestamp']) < killed['wall_ns'],
               'SQL commit visibility after response hold and before kill')
        ccheck(all(e['pid'] == starts['send']['pid'] for e in [killed, confirmed, ends['send']])
               and ends['send']['returncode'] == confirmed['returncode'] == 1, 'kill acknowledged for original native PID')
        ccheck(held['sent_bytes'] == killed['client_response_bytes'] == discarded['sent_bytes'] == 0,
               'zero response bytes recorded')
        ccheck(not any(e['event'] == 'proxy_response_delivered' and e.get('phase') == 'send'
                       and e.get('path') == initial['path'] for e in timeline), 'no original purchase response-delivery event')
        for p in PHASES[1:]:
            ccheck(ends[p]['pid'] == starts[p]['pid'] and ends[p]['returncode'] == 0, 'restart normal exit ' + p)

        natives = {}
        auth = {}
        native_files = dict(zip(PHASES, ['killed-client', 'recovery', 'second-restart']))
        for p, name in native_files.items():
            text = (case / (name + '.stdout.txt')).read_text()
            natives[p] = [json.loads(line.split('NATIVE_RECEIPT_EVENT ', 1)[1], parse_float=Decimal)
                          for line in text.splitlines() if line.startswith('NATIVE_RECEIPT_EVENT ')]
            ccheck((case / (name + '.stderr.txt')).read_bytes() == b'', 'empty stderr ' + p)
            ccheck(all(n['pid'] == starts[p]['pid'] and starts[p]['wall_ns'] <= int(n['unix_seconds'] * 10**9)
                       <= ends[p]['wall_ns'] for n in natives[p]), 'native PID/time lifetime ' + p)
            auth[p] = one(n for n in natives[p] if n['event'] == 'authenticated')
            ccheck(auth[p]['ok'] is True and auth[p]['owner'] == ids['owner'], 'same native account ' + p)
            loginreq = event('proxy_request', phase=p, path='/auth/login')
            loginresp = event('proxy_upstream_response', phase=p, path='/auth/login')
            logindelivered = event('proxy_response_delivered', phase=p, path='/auth/login')
            ccheck(loginreq['method'] == 'POST' and loginreq['body']['username'] == fixtures['username'], 'observed original login ' + p)
            ccheck(loginresp['status'] == 200 and loginresp['response']['player_id'] == ids['owner'], 'observed successful login ' + p)
            ccheck(starts[p]['wall_ns'] < loginreq['wall_ns'] < loginresp['wall_ns'] <= logindelivered['wall_ns']
                   < int(auth[p]['unix_seconds'] * 10**9), 'login ordering ' + p)
            authenticated_requests = [e for e in requests if e['phase'] == p and e['path'] != '/auth/login']
            ccheck(all(e['token_sha256'] == auth[p]['token_sha256'] for e in authenticated_requests),
                   'native digest matches all HTTP auth digests ' + p)
            stageindex = {'send': 1, 'recovery': 3, 'second-restart': 4}[p]
            earlierindex = {'send': 0, 'recovery': 2, 'second-restart': 3}[p]
            session = one(s for s in states[stageindex]['sessions'] if s['token_hash'] == auth[p]['token_sha256'])
            ccheck(session['player_id'] == ids['owner'] and sqlns(session['expires_at']) == sqlns(loginresp['response']['expires_at']),
                   'SQL session owner and exact expiry match ' + p)
            ccheck(auth[p]['token_sha256'] not in {s['token_hash'] for s in states[earlierindex]['sessions']},
                   'session digest fresh, absent at previous stage ' + p)
            ccheck([s for s in states[stageindex]['sessions'] if s not in states[earlierindex]['sessions']] == [session]
                   and all(s in states[stageindex]['sessions'] for s in states[earlierindex]['sessions']), 'exactly one added session ' + p)
        ccheck(len({a['token_sha256'] for a in auth.values()}) == 3, 'three distinct fresh sessions')
        ccheck(states[1]['sessions'] == states[2]['sessions'], 'no session mutation on kill')
        perform = one(n for n in natives['send'] if n['event'] == 'perform_entered')
        ccheck(perform['path'] == initial['path'] and perform['payload'] == initial['body']
               and type(perform['payload']['expected_price']) is int and perform['expected_price_is_int'] is True,
               'native original consent matches actual wire')
        ccheck(int(auth['send']['unix_seconds'] * 10**9) < int(perform['unix_seconds'] * 10**9)
               < initial['wall_ns'], 'authenticate then native perform then HTTP')
        ccheck(not any(n['event'] == 'completed' for n in natives['send']), 'no original native completed result')
        completed = {p: one(n for n in natives[p] if n['event'] == 'completed') for p in PHASES[1:]}
        for p, n in completed.items():
            ready = one(x for x in natives[p] if x['event'] == 'ui_ready')
            ccheck(n['pending_on_start'] == ready['pending'], 'native pending startup continuity ' + p)
            ccheck(n['pending_after'] == {}, 'native no pending at completion ' + p)
            ccheck(n['account']['player_id'] == ids['owner'] and n['account']['credits'] == buyer[1]
                   and one(x for x in n['inventory'] if x['id'] == ids['item']) == response['response']['item'],
                   'native refreshed state matches commit ' + p)

        journals = {}
        for name in ['before-kill', 'after-kill', 'after-recovery', 'after-second-restart']:
            j = load(case / ('journal-' + name + '.json'))
            rawpath = case / ('journal-' + name + '.raw.json')
            journals[name] = j
            if j['exists']:
                raw = rawpath.read_bytes()
                ccheck(len(raw) == j['bytes'] and sha(raw) == j['sha256'], 'journal independently hashed ' + name)
                ccheck(json.loads(raw) == j['record'], 'journal capture equals actual bytes ' + name)
                transaction = j['record']['transaction']
                ccheck(set(j['record']) == {'schema', 'transaction'} and j['record']['schema'] == 1
                       and set(transaction) == {'method', 'path', 'owner', 'server', 'payload', 'message'}
                       and set(transaction['payload']) == {'expected_price', 'idempotency_key'}, 'journal credential-free allowlisted fields ' + name)
                ccheck(not any(s in raw.lower() for s in [b'bearer', b'authorization', b'password', b'token']),
                       'journal actual bytes no bearer/credential markers ' + name)
                ccheck(transaction['owner'] == ids['owner'] and transaction['server'] == fixtures['url']
                       and transaction['path'] == initial['path'] and transaction['payload'] == initial['body']
                       and transaction['method'] == 2 and type(transaction['payload']['expected_price']) is int,
                       'journal original account/server/receipt/integer consent ' + name)
            else:
                ccheck(not rawpath.exists() and j['record'] is None and j['bytes'] == 0
                       and j['sha256'] == sha(b''), 'internally consistent captured journal absence ' + name)
        ccheck(journals['before-kill'] == journals['after-kill'], 'journal stable across kill')
        if journals['after-kill']['exists']:
            ccheck((case / 'journal-before-kill.raw.json').read_bytes() == (case / 'journal-after-kill.raw.json').read_bytes(),
                   'journal before/after byte identity')
            ccheck(completed['recovery']['pending_on_start'] == journals['after-kill']['record']['transaction'],
                   'journal exact transaction restored')
        else:
            ccheck(completed['recovery']['pending_on_start'] == {}, 'journal absent and pending empty')
        ccheck(not journals['after-recovery']['exists'] and not journals['after-second-restart']['exists'], 'journal absent after both restarts')

        exact_recovered = False
        replay_equal = None
        if recovery:
            replay = one(recovery)
            replay_response = event('proxy_upstream_response', phase='recovery', path=initial['path'])
            delivered = event('proxy_response_delivered', phase='recovery', path=initial['path'])
            replay_equal = replay['raw_utf8'] == initial['raw_utf8']
            ccheck(replay_equal and replay['body'] == initial['body'] and type(replay['body']['expected_price']) is int,
                   'replayed exact bytes and strict integer consent')
            ccheck(int(auth['recovery']['unix_seconds'] * 10**9) < replay['wall_ns'] < replay_response['wall_ns']
                   <= delivered['wall_ns'] < int(completed['recovery']['unix_seconds'] * 10**9), 'fresh authentication before recovery replay/result')
            exact_recovered = (replay_equal and replay_response['status'] == 200 and delivered['status'] == 200
                               and replay_response['response'] == operation['response'] == response['response']
                               == completed['recovery']['result'])
        ccheck(not [e for e in purchases if e['phase'] == 'second-restart'], 'zero second restart purchase requests')
        ccheck(completed['second-restart']['pending_on_start'] == {} and completed['second-restart']['result'] == {},
               'second restart is empty retry')

        counts = {STAGES[i] + '.json': {k: len(es[i][k]) for k in TABLES} for i in range(5)}
        semantic = load(case / 'semantic-comparison.json')
        ccheck(semantic['actual_economic_table_row_counts'] == counts, 'derived aid counts independently reproduced')
        ccheck(semantic['actual_persisted_operation'] == operation, 'derived aid operation independently reproduced')
        for i in range(1, 5):
            reproduced = {k: delta(es[0 if i == 1 else 1][k], es[i][k]) for k in TABLES}
            ccheck(semantic['actual_row_deltas'][STAGES[i] + '.json'] == reproduced, 'derived aid all row differences independently reproduced ' + STAGES[i])
        ccheck(semantic['observed_purchase_requests'] == purchases and semantic['recovery_body_bytes_equal_initial'] == replay_equal
               and semantic['native_recovery_result'] == completed['recovery']['result'], 'derived aid request/result equality')
        obs = one(x for x in observed['groups'][group.name] if x['case'] == case.name)
        ccheck(obs['before_economic_row_counts'] == counts['01-before.json']
               and obs['before_session_row_count'] == len(states[0]['sessions']) and obs['expected_price'] == price,
               'observed summary independently reproduced')
        result = load(case / 'result.json')
        ccheck(result['recovered'] == exact_recovered, 'producer recovery conclusion agrees with observed exact receipt outcome')
        for n in result['phases']:
            ccheck(n['completed'] == completed[n['phase']], 'producer native copy agrees with stdout')
        for p in result['purchases']:
            req = one(e for e in purchases if e['phase'] == p['phase'])
            resp = event('proxy_upstream_response', phase=p['phase'], path=initial['path'])
            ccheck(p['body'] == req['body'] and p['raw_utf8'] == req['raw_utf8'] and p['token_sha256'] == req['token_sha256']
                   and p['response'] == resp['response'] and p['response_raw_utf8'] == resp['raw_utf8'] and p['status'] == resp['status'],
                   'producer purchase copy agrees with trace ' + p['phase'])
        sessions_summary = [{'phase': p, 'pid': starts[p]['pid'], 'token_sha256': auth[p]['token_sha256'],
                             'player_id': ids['owner']} for p in PHASES]
        ccheck(result['logins'] == [{k: v for k, v in s.items() if k != 'pid'} for s in sessions_summary],
               'producer login summary agrees with native plus SQL session rows')
        out['cases'].append({
            'label': label, 'price': price, 'receipt': receipt, 'ids': ids,
            'buyer_balances_B_C_K_R_S': buyer, 'seller_balances_B_C_K_R_S': seller,
            'all_player_credits_B_C_K_R_S': money, 'fee': fee,
            'table_counts': counts, 'session_counts_B_C_K_R_S': [len(s['sessions']) for s in states],
            'item_ownership_counts_B_C_K_R_S': {who: [sum(x['owner_id'] == ids[who] for x in s['items']) for s in es]
                                                 for who in ['owner', 'seller']},
            'added_operation': operation, 'added_ledger': ledger, 'added_audit': audit,
            'purchase_counts_send_recovery_second': [sum(e['phase'] == p for e in purchases) for p in PHASES],
            'fresh_logins': sessions_summary, 'recorded_server': fixtures['url'],
            'sql_clocks_B_C_K_R_S': [s['postgresql'] for s in states],
            'key_timeline': [dict(e, line=timeline.index(e) + 1) for e in chain],
            'journal_bytes_before_after': [journals[n]['bytes'] for n in ['before-kill', 'after-kill']],
            'journal_sha256': journals['after-kill']['sha256'],
            'recovery_result': completed['recovery']['result'], 'exact_recovered': exact_recovered,
            'status': 'supported' if exact_recovered else 'failed',
            'producer_flags': {'authoritative_pass': result['authoritative_pass'],
                               'complete_result': result['checks']['complete_result'],
                               'stable_journal_at_kill': result['checks']['stable_journal_at_kill'],
                               'recovered': result['recovered']},
        })

out['integrity_or_consistency_failures'] = failures
out['checks_evaluated'] = checks['evaluated']
out['scope'] = 'Observed stable postcommit withheld-response native-process termination and exact fresh-session receipt recovery; no source provenance, arbitrary instruction-window, power-loss, or manual-UI qualification.'
(ROOT / '_independent_audit.json').write_text(json.dumps(out, indent=2, default=float), encoding='utf-8')
print('PAYLOADS', out['payloads_hashed'], 'CASES', len(out['cases']), 'SQL_STAGES', len(out['cases']) * 5,
      'CHECKS', out['checks_evaluated'], 'CONSISTENCY_FAILURES', len(failures))
for failure in failures:
    print('FAIL', failure)
for row in out['cases']:
    print(json.dumps({k: row[k] for k in ['label', 'price', 'receipt', 'ids', 'buyer_balances_B_C_K_R_S',
                                        'seller_balances_B_C_K_R_S', 'all_player_credits_B_C_K_R_S', 'fee',
                                        'session_counts_B_C_K_R_S', 'purchase_counts_send_recovery_second',
                                        'journal_bytes_before_after', 'status', 'producer_flags']}, default=str))
    print('ROWCOUNTS players/items/listings/operations/ledger/audit/loadouts/rewards/trades',
          [list(row['table_counts'][s + '.json'].values()) for s in STAGES])
    print('PIDS', [x['pid'] for x in row['fresh_logins']], 'JOURNAL_SHA256', row['journal_sha256'])
