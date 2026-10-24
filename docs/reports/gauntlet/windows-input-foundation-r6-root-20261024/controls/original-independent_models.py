#!/usr/bin/env python3
"""Independent bounded forward witnesses; no engine/process observation."""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class Forward:
    def __init__(self, seed):
        self.rows = deepcopy(seed)
        self.prototype = deepcopy(seed[-1])
        self.count = Counter(seed[-1]['counters'])
        self.latest = deepcopy(seed[-1]['latest'])
        self.entries = {9: [1, 22000, 9000, 1]}
        self.queue = {9: {}}
        self.ack = {9: 1}
        self.actor = {1: deepcopy(seed[-1]['actor'])}
        self.selected, self.sticky, self.serial, self.epoch = 9, 1, 1, 1
        self.rejections = self.skips = 0
        self.last_emit = self.now = 11000
        self.sim = seed[-1]['simulation_tick']
        self.edges = {'input_received': (1, 0, 0), 'input_accepted': (1, 0, 0),
                      'input_consumed': (True, False, (0.0, 0.0))}
        self.trace = []

    @staticmethod
    def command(seq, fire):
        return dict(sequence=seq, fire=bool(fire), reload=False, move=[0.0, 0.0])

    def hook(self, kind, now, peer=None, metadata=None):
        assert now >= self.now
        self.now = now
        self.count[kind] += 1
        if peer is not None:
            self.selected = peer
            if peer in self.entries and self.entries[peer][3]:
                self.sticky = self.entries[peer][3]
        if metadata is not None:
            self.latest[kind] = dict(deepcopy(metadata), wall_msec=now)
        if kind in ('input_received', 'input_accepted'):
            edge = tuple(metadata[x] for x in ('fire', 'reload', 'moving'))
        elif kind == 'input_consumed':
            edge = (metadata['fire'], metadata['reload'], tuple(metadata['move']))
        else:
            edge = None
        changed = self.edges.get(kind) != edge
        self.edges[kind] = edge
        emit = (kind in ('peer_connected', 'peer_bound', 'peer_disconnected')
                or kind in ('input_received', 'input_accepted', 'input_consumed') and changed
                or kind == 'authority_tick' and now - self.last_emit >= 1000)
        self.trace.append(dict(kind=kind, now=now, peer=peer, metadata=metadata, emit=emit))
        if not emit:
            return
        e = self.entries.get(self.selected)
        actor_id = e[3] if e else 0
        r = deepcopy(self.prototype)
        r.update(reason=kind, index=len(self.rows)+1, wall_msec=now, wall_unix_msec=100000+now,
                 process_frames=100+len(self.rows), physics_frames=200+len(self.rows),
                 drawn_frames=100+len(self.rows), peer=self.selected, generation=e[0] if e else -1,
                 input_age_msec=now-e[2] if e else -1, deadline_remaining_msec=e[1]-now if e else -1,
                 joined=bool(actor_id), peer_bound=bool(actor_id), bound_actor=actor_id,
                 last_bound_actor=self.sticky, authority_epoch=self.epoch, simulation_tick=self.sim,
                 stream_ack=self.ack.get(self.selected, -1), queue_count=len(self.queue.get(self.selected, {})),
                 stream_rejected=self.rejections, stream_skipped=self.skips,
                 counters=dict(self.count), latest=deepcopy(self.latest), actor=deepcopy(self.actor.get(self.sticky, {})))
        self.rows.append(r)
        self.last_emit = now

    def rpc(self, seq, fire, now, phase, reject=False, peer=9):
        assert peer in self.entries and self.entries[peer][3] and now-self.entries[peer][2] < 30000
        value = dict(epoch=self.epoch+int(reject), count=1, first=seq, last=seq,
                     fire=int(fire), reload=0, moving=0)
        self.hook('input_received', now, peer, value)
        ack = self.ack.get(peer, 0)
        if reject or not 1 <= seq <= ack+120 or seq <= ack:
            self.rejections += 1
            self.hook('input_stream_rejected', now+phase, peer, value)
        else:
            self.queue[peer].setdefault(seq, self.command(seq, fire))
            self.entries[peer][2] = now+phase
            self.hook('input_accepted', now+phase, peer, value)

    def tick(self, now):
        self.sim += 1
        self.hook('authority_tick', now)

    def pop(self, now, phase=0, peer=9):
        self.tick(now)
        q = self.queue[peer]
        assert q and len(q) <= 6
        seq = min(q)
        command = q.pop(seq)
        self.ack[peer] = seq
        e = self.entries[peer]
        self.actor[e[3]]['input'] = deepcopy(command)
        self.hook('input_consumed', now+phase, peer, dict(command, peer=peer, actor=e[3], generation=e[0]))

    def connect(self, peer, now):
        # The failure branch keeps state; nested disconnection remains outside this witness.
        succeeded = peer not in self.entries and len(self.entries) < 10
        if succeeded:
            self.serial += 1
            self.entries[peer] = [self.serial, now+20000, now, 0]
            self.queue[peer] = {}
        self.hook('peer_connected', now, peer)
        return succeeded

    def admit(self, peer, actor, now):
        assert peer in self.entries and not self.entries[peer][3] and now < self.entries[peer][1]
        self.entries[peer][2:] = [now, actor]
        self.actor[actor] = dict(deepcopy(self.prototype['actor']), id=actor, input=self.command(-1, False))
        self.hook('peer_bound', now, peer)

    def disconnect(self, peer, now):
        self.hook('peer_disconnected', now, peer)
        del self.entries[peer]
        self.queue.pop(peer, None)
        self.ack.pop(peer, None)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(a.source.resolve()/'scripts'))
    import analyze_input_consumption as reader
    from test_input_consumption_observation import declared_rows, text
    expected_sha = '104d998dc504e30fb6702426025b611aa5ee86390a1734f06142d92a3473e4d4'
    assert hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest() == expected_sha
    seed, client = declared_rows('authority'), declared_rows('client')
    (a.output/'SEED.json').write_text(json.dumps(dict(authority=seed, client=client), indent=2)+'\n')
    results, failures = [], []
    status = Counter()
    with gzip.open(a.output/'CASES.jsonl.gz', 'wt') as ledger:
        def check(name, model, expected, rows=None):
            rows = model.rows if rows is None else rows
            before = deepcopy(rows)
            result = reader.analyze(text(client), text(rows))
            actual = result['transition_status']
            ok = actual in expected and result['diagnostic_complete'] == (actual == 'CONSISTENT') and rows == before
            item = dict(name=name, expected=expected, actual=actual, matched=ok,
                        input_sha256=digest(rows), trace_sha256=digest(model.trace), errors=result['errors'])
            ledger.write(json.dumps(item, sort_keys=True)+'\n')
            results.append(item)
            status[actual] += 1
            if not ok:
                failures.append(item)
                dest=a.output/('failure-%04d.json'%len(failures))
                dest.write_text(json.dumps(dict(item=item, client=client, authority=rows, trace=model.trace, result=result), indent=2)+'\n')

        witnesses = 0
        for length in range(1, 5):
            for word in itertools.product(('A0', 'A1', 'J0', 'J1', 'P'), repeat=length):
                for phase in (0, 1):
                    m = Forward(seed)
                    legal = True
                    seq = 2
                    for k, op in enumerate(word):
                        now = 11200+k*20
                        if op == 'P':
                            if not m.queue[9]:
                                legal = False
                                break
                            m.pop(now, phase)
                        else:
                            m.rpc(seq, op[1] == '1', now, phase, reject=op[0] == 'J')
                            seq += 1
                    if not legal:
                        continue
                    m.tick(13500)
                    witnesses += 1
                    name='words/%s/phase%d'%(''.join(word),phase)
                    check(name, m, ['CONSISTENT','UNKNOWN'])
                    bad=deepcopy(m.rows);bad[-1]['counters']['input_received'] += 1
                    check(name+'/receive-surplus',m,['INVALID'],bad)
                    bad=deepcopy(m.rows);bad[-1]['stream_rejected']=bad[-1]['counters'].get('input_stream_rejected',0)+1
                    check(name+'/rejection-surplus',m,['INVALID'],bad)

        # Explicit source siblings, not arbitrary rows repaired into a positive.
        for mode in ('queued-duplicate', 'acked-duplicate', 'wrong-epoch', 'two-peer', 'duplicate-callback', 'capacity-callback'):
            m=Forward(seed)
            if mode == 'queued-duplicate':
                m.rpc(2,False,11200,0);m.rpc(2,True,11300,1);m.pop(11400)
            elif mode == 'acked-duplicate':
                m.rpc(2,False,11200,0);m.pop(11300);m.rpc(2,False,11400,1)
            elif mode == 'wrong-epoch':
                m.rpc(2,False,11200,1,reject=True)
            elif mode == 'two-peer':
                m.connect(10,11200);m.admit(10,2,11300)
                m.rpc(2,True,11400,1);m.rpc(1,True,11500,1,peer=10)
            elif mode == 'duplicate-callback':
                assert not m.connect(9,11200)
            else:
                for k,peer in enumerate(range(10,19)):assert m.connect(peer,11200+k*10)
                assert not m.connect(19,11300)
            m.tick(14000)
            expected=['UNKNOWN'] if mode in ('two-peer','duplicate-callback','capacity-callback') else ['CONSISTENT','UNKNOWN']
            check('siblings/'+mode,m,expected)
            for field in ('process_frames','physics_frames','drawn_frames'):
                bad=deepcopy(m.rows);bad[-1][field]=1
                check('siblings/'+mode+'/'+field,m,['INVALID'],bad)
    summary=dict(source='8b52601ca29d807f54ed318114d10d849c267e83',reader_sha256=expected_sha,
                 witnesses=witnesses,expectations=len(results),matches=len(results)-len(failures),
                 statuses=dict(status),failures=failures,scope='bounded projection witnesses; no native/full fixture proof')
    (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
