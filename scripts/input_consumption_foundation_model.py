"""Executable PeerLifecycle/observer projection model for pre-edit adjudication.

This is a pure test model, not a game emitter or a qualification reader. It models
only named authority lifecycle/selected-identity cuts. Other full-row fields in
versioned fixtures remain synthetic schema/control data. No candidate import.
"""
from copy import deepcopy

JOIN = 20000
IDLE = 30000
REJECT = 500
MAX_PEERS = 10
PROJECTION = ('peer','generation','joined','input_age_msec','deadline_remaining_msec',
              'bound_actor','last_bound_actor','peer_bound')


def require(value,message):
    if not value:raise ValueError(message)


class PeerLifecycle:
    """Literal state updates from fixed SBPeerLifecycle; time is supplied."""
    def __init__(self):
        self.peers={};self.generation=0;self.clock=0;self.operations=[]

    def tick(self,now):
        require(type(now) is int and now>=self.clock,'model clock regressed/noninteger')
        self.clock=now

    def connected(self,peer,now):
        self.tick(now)
        require(type(peer) is int and peer>0,'model transport peer must be positive')
        if peer in self.peers or len(self.peers)>=MAX_PEERS:
            self.operations.append(dict(call='connected',peer=peer,now=now,result=False));return False
        self.generation+=1
        self.peers[peer]=dict(generation=self.generation,deadline=now+JOIN,joined=False,
                              attempted=False,rejected=False,last_input=now,rate_start=now,rate_count=0)
        self.operations.append(dict(call='connected',peer=peer,now=now,result=True));return True

    def begin_join(self,peer,now):
        self.tick(now);entry=self.peers.get(peer)
        result=-1
        if entry and not entry['attempted'] and not entry['rejected'] and now<entry['deadline']:
            entry['attempted']=True;result=entry['generation']
        self.operations.append(dict(call='begin_join',peer=peer,now=now,result=result));return result

    def current(self,peer,attempt,now):
        self.tick(now);entry=self.peers.get(peer)
        return bool(entry and entry['generation']==attempt and not entry['rejected'] and now<entry['deadline'])

    def admitted(self,peer,attempt,now):
        allowed=self.current(peer,attempt,now)
        if allowed:self.peers[peer].update(joined=True,last_input=now)
        self.operations.append(dict(call='admitted',peer=peer,now=now,attempt=attempt,result=allowed));return allowed

    def reject(self,peer,now):
        self.tick(now);entry=self.peers.get(peer)
        if entry and not entry['rejected']:entry.update(rejected=True,deadline=now+REJECT)
        self.operations.append(dict(call='reject',peer=peer,now=now))

    def allow_input(self,peer,now):
        self.tick(now);entry=self.peers.get(peer)
        allowed=False
        if entry and entry['joined'] and not entry['rejected'] and now-entry['last_input']<IDLE:
            if now-entry['rate_start']>=1000:entry.update(rate_start=now,rate_count=0)
            entry['rate_count']+=1;allowed=entry['rate_count']<=90
        self.operations.append(dict(call='allow_input',peer=peer,now=now,result=allowed));return allowed

    def active(self,peer,now):
        self.tick(now);entry=self.peers.get(peer)
        if entry and entry['joined'] and not entry['rejected'] and now-entry['last_input']<IDLE:entry['last_input']=now
        self.operations.append(dict(call='active',peer=peer,now=now))

    def expired(self,now):
        self.tick(now);result=[]
        for peer,entry in self.peers.items():
            if (entry['rejected'] or not entry['joined']) and now>=entry['deadline']:result.append(peer)
            elif entry['joined'] and now-entry['last_input']>=IDLE:result.append(peer)
        self.operations.append(dict(call='expired',now=now,result=list(result)));return result

    def forget(self,peer):
        self.peers.pop(peer,None);self.operations.append(dict(call='forget',peer=peer,now=self.clock))


class AuthorityProjectionEmitter:
    """Match's selected peer/sticky actor and declared observable hook cuts.

    Captures are explicit, not a simulation of coalescing/frame/native scheduling.
    All rows are lifecycle/identity projections with supplied operation clocks.
    """
    def __init__(self):
        self.lifecycle=PeerLifecycle();self.actors={};self.last_peer=0;self.last_actor=0;self.rows=[]

    def capture(self,reason,now,peer=0):
        self.lifecycle.tick(now)
        if peer>0:
            self.last_peer=peer
            if peer in self.actors:self.last_actor=self.actors[peer]
        selected=self.last_peer;entry=self.lifecycle.peers.get(selected)
        bound=self.actors.get(selected,0)
        row=dict(reason=reason,wall_msec=now,peer=selected,generation=entry['generation'] if entry else -1,
                 joined=entry['joined'] if entry else False,input_age_msec=now-entry['last_input'] if entry else -1,
                 deadline_remaining_msec=entry['deadline']-now if entry else -1,
                 bound_actor=bound,last_bound_actor=self.last_actor,peer_bound=bound>0)
        self.rows.append(row);return deepcopy(row)

    def connect(self,peer,call,capture=None):
        result=self.lifecycle.connected(peer,call)
        # SceneMultiplayer explicit disconnect suppresses the local callback.
        # Match still executes this unconditional observer hook after failure.
        row=self.capture('peer_connected',call if capture is None else capture,peer)
        return result,row

    def bind(self,peer,actor,call,capture=None):
        require(1<=actor<=10 and actor not in self.actors.values(),'model actor already bound/out of roster')
        attempt=self.lifecycle.begin_join(peer,call)
        require(attempt>0 and self.lifecycle.admitted(peer,attempt,call),'model join not admitted')
        self.actors[peer]=actor
        return self.capture('peer_bound',call if capture is None else capture,peer)

    def disconnect(self,peer,capture):
        row=self.capture('peer_disconnected',capture,peer)
        self.lifecycle.forget(peer);self.actors.pop(peer,None)
        return row

    def service(self,call):
        for peer in self.lifecycle.expired(call):
            self.capture('peer_expired',call,peer)
            self.disconnect(peer,call)


def reproject_authority_rows(original):
    """Versioned bounded correction; unrelated fields are unchanged synthetic data.

    This is a proposed constructor delta for independent pre-edit adjudication,
    not a rewrite of old helper/source and not full native-emitter provenance.
    """
    result=deepcopy(original);model=AuthorityProjectionEmitter()
    for row in result:
        reason,now,peer=row['reason'],row['wall_msec'],row['peer']
        if reason=='peer_connected':
            accepted,projection=model.connect(peer,now);require(accepted,'versioned fixture requires successful source connect')
        elif reason=='peer_bound':projection=model.bind(peer,row['bound_actor'],now)
        else:
            if reason=='input_received':require(model.lifecycle.allow_input(peer,now),'versioned fixture input gate must pass')
            if reason=='input_accepted':model.lifecycle.active(peer,now)
            projection=model.capture(reason,now,peer if reason.startswith('input_') else 0)
        row.update({key:projection[key] for key in PROJECTION})
    return result,model


def source_successful_connection(row):
    """An independently proved necessary projection; not a general validator."""
    age,remaining,now=row['input_age_msec'],row['deadline_remaining_msec'],row['wall_msec']
    return (type(row['generation']) is int and row['generation']>0
            and type(row['joined']) is bool and type(row['peer_bound']) is bool and not row['joined'] and not row['peer_bound'] and row['bound_actor']==0
            and type(age) is int and type(remaining) is int and 0<=age<=now and age+remaining==JOIN)


def declared_histories():
    """Concrete executable source witnesses; never finite-grid absence proofs."""
    output=[]
    for connected in (0,1,1000):
        for delay in (0,1,19999,20000,20001):
            model=AuthorityProjectionEmitter();model.capture('ready',connected)
            _,row=model.connect(9,connected,connected+delay)
            output.append(dict(id=f'connect/{connected}/{delay}',operations=deepcopy(model.lifecycle.operations),rows=deepcopy(model.rows),kind='source_projection_witness'))
    for connected in (0,1000):
        for admission_delay in (0,1,19999):
            for capture_delay in (0,1,30000):
                model=AuthorityProjectionEmitter();model.capture('ready',connected);model.connect(9,connected)
                model.bind(9,1,connected+admission_delay,connected+admission_delay+capture_delay)
                output.append(dict(id=f'admit/{connected}/{admission_delay}/{capture_delay}',operations=deepcopy(model.lifecycle.operations),rows=deepcopy(model.rows),kind='source_projection_witness'))
    for joined in (False,True):
        for rejection_delay in (0,1,19999):
            for observed_delay in (499,500,501):
                model=AuthorityProjectionEmitter();model.capture('ready',0);model.connect(9,0)
                if joined:model.bind(9,1,0)
                model.lifecycle.reject(9,rejection_delay)
                model.capture('authority_tick',rejection_delay+observed_delay)
                model.service(rejection_delay+observed_delay)
                output.append(dict(id=f'reject/{int(joined)}/{rejection_delay}/{observed_delay}',operations=deepcopy(model.lifecycle.operations),rows=deepcopy(model.rows),kind='source_projection_witness'))
    for active_delay in (29999,30000,30001):
        model=AuthorityProjectionEmitter();model.capture('ready',0);model.connect(9,0);model.bind(9,1,0)
        gate=model.lifecycle.allow_input(9,min(active_delay,29999))
        require(gate,'source witness gate must pass')
        model.lifecycle.active(9,active_delay)
        model.capture('input_accepted',active_delay)
        model.service(active_delay)
        output.append(dict(id=f'active/{active_delay}',operations=deepcopy(model.lifecycle.operations),rows=deepcopy(model.rows),kind='source_projection_witness'))
    return output
