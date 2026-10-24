"""UNEXECUTED additive V3 construction-only proposal, not production evidence or native IO.

The approved clock definition and proposed five-site helper seam are separate.
This draft must be independently adjudicated before copying/calling it.
"""
import copy
import json
import math
import os
import stat
import hashlib
from pathlib import Path
import tempfile


def write_declared_trial(directory,identity,*,clock,format_writer,snapshot,
                         verbose=False,client_pid=101,reopened_pid=201,observer=None):
    """Stage a synthetic predicate/operation model; never invoke the real main.

    format_writer is the preserved V1 synthetic byte constructor, with no
    observer. Its temporary content is only a precomputation, not retained native
    evidence or a completed trial. Actual target outputs are emitted by stages.
    """
    with tempfile.TemporaryDirectory(prefix='synthetic-content-only-') as temporary:
        template_root=Path(temporary)/'trial'
        content=format_writer(template_root,identity,verbose=verbose,client_pid=client_pid,
                              reopened_pid=reopened_pid,observer=None)
        files={p.relative_to(template_root).as_posix():p.read_bytes()
               for p in template_root.rglob('*') if p.is_file()}
    producer=DeclaredProducer(directory,content,files,clock=clock,snapshot=snapshot,
                              observer=observer,template_root=template_root)
    return producer.run()


class DeclaredProducer:
    """One staged graph, one held set and one explicitly advanced fixture clock.

    Solid PNG/OCR/game snapshots and symbolic OS receipts are synthetic format
    inputs. No code here proves physics, actual timing or physical delivery.
    """
    def __init__(self,directory,content,files,*,clock,snapshot,observer,template_root):
        original=Path(directory)
        if original.is_symlink() or (original.exists() and not original.is_dir()):
            raise ValueError('synthetic fixture needs a real fresh output directory')
        self.root=original.absolute();self.root.mkdir(parents=True,exist_ok=True)
        self.root=self.root.resolve();self.files=files;self.clock=clock
        self.snapshot=snapshot;self.observer=observer;self.pending=copy.deepcopy(content)
        self.owned={};self.directories={};self.held=set();self.lmb=False;self.focused=True
        self.window_visible=False;self.menu_visible=False;self.window_pid=None
        self.root_identity=self.directory_identity(self.root.lstat())
        self.actions=[];self.commands=[];self.ocr=[];self.closes=[];self.captures=[];self.names=[]
        self.started=clock.monotonic();self.deadline=self.started+300
        self.current=None;self.native={};self.previous={}
        self.stdout=bytearray();self.settings_until=None
        for name in files:
            target=self.root/name
            if target.exists() or target.is_symlink():raise ValueError('existing producer output: '+name)
            for parent in target.parents:
                if parent==self.root.parent:break
                if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                    raise ValueError('unsafe fixture output parent')
        old=str(template_root.resolve())
        for row in self.pending['commands']:
            row['command']=[arg.replace('--offline-trace-dir='+old,'--offline-trace-dir='+str(self.root),1)
                            if arg.startswith('--offline-trace-dir='+old+'/') else arg for arg in row['command']]
        arguments=self.pending['controller_command'];arguments[arguments.index('--output')+1]=str(self.root)
        self.pending['profile_observation_path']=str(self.root/'state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json')
        for fence in self.pending['phase_capture_fences'].values():
            for field in ('expected_binding','binding_before_capture','binding_after_capture'):
                binding=fence[field];relative=Path(binding['trace_directory']).relative_to(template_root)
                binding['trace_directory']=str(self.root/relative)
        self.ocr_templates=copy.deepcopy(self.pending['ocr_commands'])
        self.command_templates=copy.deepcopy(self.pending['commands'])
        self.progress=dict(passed=False,target='windows',host=self.pending['host'],
                           controller_command=self.pending['controller_command'],captures=self.captures,
                           shutdown_study_observations=self.closes)
    def remaining(self):
        value=self.deadline-self.clock.monotonic()
        if value<=0:raise ValueError('declared original flow budget expired')
        return value
    def advance(self,seconds):
        if seconds>=self.remaining():raise ValueError('declared operation exceeds original flow')
        self.clock.advance(seconds)
    @staticmethod
    def file_identity(info):
        return (info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
    @staticmethod
    def directory_identity(info):return info.st_dev,info.st_ino,stat.S_IFMT(info.st_mode)
    def parents(self,path):
        if self.root.is_symlink() or self.directory_identity(self.root.lstat())!=self.root_identity:
            raise ValueError('fixture root identity changed')
        current=self.root
        for part in path.parent.relative_to(self.root).parts:
            current=current/part
            if current.is_symlink() or (current.exists() and not current.is_dir()):
                raise ValueError('unsafe output directory')
            current.mkdir(exist_ok=True)
            identity=self.directory_identity(current.lstat())
            if current in self.directories and self.directories[current]!=identity:
                raise ValueError('output directory identity changed')
            self.directories[current]=identity
    def owned_before_update(self,name,record):
        path=self.root/name;stream=record['stream']
        if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError('owned output is no longer a regular file: '+name)
        expected=record['identity'];before=self.file_identity(os.fstat(stream.fileno()))
        if before!=expected or self.file_identity(path.lstat())!=expected:
            raise ValueError('owned output changed/replaced: '+name)
        stream.seek(0);first=stream.read();middle=self.file_identity(os.fstat(stream.fileno()))
        stream.seek(0);second=stream.read();after=self.file_identity(os.fstat(stream.fileno()))
        if not (before==middle==after==expected and first==second==record['raw']):
            raise ValueError('owned output preimage changed: '+name)
    def retain_preimage(self,name,raw):
        directory=self.root/'construction-failure-preimages';self.parents(directory/'placeholder')
        stem=hashlib.sha256(name.encode()).hexdigest();index=0
        while True:
            path=directory/(stem+'-'+str(index)+'.bin')
            try:
                with path.open('xb') as stream:stream.write(raw)
                return
            except FileExistsError:index+=1
    def put(self,name,raw):
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe relative output')
        path=self.root/relative;self.parents(path);record=self.owned.get(name)
        if record is None:
            stream=path.open('x+b')
            record=dict(stream=stream,identity=self.file_identity(os.fstat(stream.fileno())),raw=b'')
            self.owned[name]=record
        try:
            self.owned_before_update(name,record)
            stream=record['stream'];stream.seek(0);stream.write(raw);stream.truncate(len(raw));stream.flush()
            identity=self.file_identity(os.fstat(stream.fileno()))
            if path.is_symlink() or self.file_identity(path.lstat())!=identity:
                raise ValueError('output path changed during owned write: '+name)
            stream.seek(0);observed=stream.read()
            if observed!=raw or self.file_identity(os.fstat(stream.fileno()))!=identity:
                raise ValueError('owned write did not retain its exact bytes: '+name)
            record.update(identity=identity,raw=raw)
        except BaseException as error:
            # The previous owned bytes are known synthetic content. Keep them as
            # extra failure evidence as well as any current/replacement pathname.
            try:self.retain_preimage(name,record['raw'])
            except BaseException as secondary:
                raise RuntimeError('Synthetic preimage retention incomplete: '+type(secondary).__name__+': '+str(secondary)) from error
            raise
    def close_owned(self):
        errors=[]
        for name,record in self.owned.items():
            try:record['stream'].close()
            except BaseException as error:errors.append(name+': '+type(error).__name__+': '+str(error))
        return errors
    def json(self,name,value):self.put(name,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
    def diagnostics(self):
        return dict(target_window=1001,foreground_window=1001 if self.focused else 2002,
                    target_focused=self.focused,lmb_down=self.lmb,
                    keys_down={key:key in self.held for key in ('r','d','w')},
                    state_source='GetForegroundWindow/GetAsyncKeyState; zero is not delivery proof')
    def trace(self,event,**fields):
        row=dict(event=event,seconds=self.clock.monotonic()-self.started,
                 wall_unix_msec=self.clock.time_ns()//1000000,
                 held_keys=sorted(self.held),native_state=self.diagnostics(),**fields)
        self.actions.append(row);self.json('actions.json',self.actions)
    def wait(self,label,budget,duration=.11,publish=None,*,predicate):
        if not callable(predicate):raise ValueError('explicit source wait predicate required')
        if not 0<duration<budget or duration>=self.remaining():raise ValueError('invalid declared source wait')
        until=min(self.deadline,self.clock.monotonic()+budget)
        self.trace('wait_begin',label=label,budget_seconds=budget)
        self.advance(duration)
        if publish is not None:publish()
        if not predicate():
            # No producer effect will occur in this declared failed branch.
            # Polling emits no extra actions; consume only the original boundary.
            left=until-self.clock.monotonic()
            if left>0:self.clock.advance(left)
            raise TimeoutError('declared source predicate not observed: '+label)
        self.trace('wait_completed',label=label)
    def observed(self,label,state,budget=5,duration=.11,*,after=None,before_publish=None):
        expected=copy.deepcopy(state)
        if after is None:after=self.previous[self.current]['wall_msec']
        def publish():
            if before_publish is not None:before_publish()
            self.publish(state)
        def predicate():
            path=self.root/self.current/'status.json'
            if not path.is_file():return False
            actual=json.loads(path.read_bytes())
            return actual==expected and actual.get('wall_msec',-1)>after
        self.wait(label,budget,duration,publish,predicate=predicate)
        self.trace('offline_observation',label=label,state=copy.deepcopy(state))
        return state
    def key(self,name,down):
        self.remaining();self.trace('key_before',key=name,down=down)
        (self.held.add if down else self.held.discard)(name)
        self.trace('key_after',key=name,down=down)
    def direct_escape(self,down,scope):
        (self.held.add if down else self.held.discard)('Escape')
        self.trace('key_after',key='Escape',down=down,scope=scope)
    def tap(self,name):self.key(name,True);self.advance(.3);self.key(name,False);self.advance(1)
    def button(self,down):self.trace('button',down=down);self.lmb=down
    def click(self):self.advance(.25);self.advance(.2)
    def capture(self,name):
        self.remaining();self.trace('capture_begin',capture=name)
        self.put(name+'.png',self.files[name+'.png']);self.advance(.02);self.remaining()
        row=next(row for row in self.pending['captures'] if row['name']==name)
        self.captures.append(copy.deepcopy(row));self.names.append(name)
        self.stdout.extend((name+'\n').encode());self.put('controller-stdout.log',bytes(self.stdout))
        self.trace('capture_end',capture=name,dimensions=row['dimensions'])
    def native_event(self,kind,state):
        row=copy.deepcopy(state);rows=self.native[self.current]
        row.update(event=kind,event_index=len(rows),observer_wall_msec=state['wall_msec']+1)
        rows.append(row)
        self.put(self.current+'/events.jsonl',b''.join((json.dumps(r,allow_nan=False)+'\n').encode() for r in rows))
    def announce(self,message,state):
        rows=self.native[self.current]
        row=dict(message=message,elapsed=state['elapsed'],simulation_tick=state['simulation_tick'],
                 event='notification',event_index=len(rows),observer_wall_msec=state['wall_msec']+1)
        rows.append(row)
        self.put(self.current+'/events.jsonl',b''.join((json.dumps(r,allow_nan=False)+'\n').encode() for r in rows))
        name=self.commands[-1]['name']+'.log';record=self.owned[name]
        self.put(name,record['raw']+('MATCH: '+message+'\n').encode())
    def live_transition(self,state):
        self.announce('Round live. Secure Relay Yard.',state);self.publish(state)
    def round_transition(self,state):
        self.announce('Round '+str(state['round_number'])+' • prepare your equipment',state);self.publish(state)
    def publish(self,state):
        prior=self.previous[self.current]
        for field in ('phase','round_number','objective_state','local_contribution'):
            if state[field]!=prior[field]:self.native_event(field,state)
        actor=state['local_actor'];old=prior['local_actor']
        for kind,changed in [('reload',(actor['reload']>0)!=(old['reload']>0)),
                             ('weapon',actor['weapon']!=old['weapon']),('alive',actor['alive']!=old['alive']),
                             ('utility',actor['grenades']!=old['grenades'] or actor['smokes']!=old['smokes'])]:
            if changed:self.native_event(kind,state)
        self.json(self.current+'/status.json',state);self.previous[self.current]=copy.deepcopy(state)
    def begin_native_trace(self,name):
        self.current=name;initial=json.loads(self.files[name+'/events.jsonl'].splitlines()[0])
        status={key:value for key,value in initial.items() if key not in ('event','event_index','observer_wall_msec')}
        self.native[name]=[initial];self.previous[name]=copy.deepcopy(status)
        self.put(name+'/events.jsonl',(json.dumps(initial,allow_nan=False)+'\n').encode())
        self.json(name+'/status.json',status)
    def launch(self,index):
        row=copy.deepcopy(self.command_templates[index]);row['started_seconds']=self.clock.monotonic()-self.started
        row.pop('exit_code',None);self.commands.append(row);self.json('commands.json',self.commands)
        header=self.files[row['name']+'.log'].splitlines(keepends=True)[0]
        self.put(row['name']+'.log',header)
        self.window_pid=row['pid'];self.window_visible=False;self.menu_visible=False
        if self.observer is not None:self.observer('native_launch',name=row['name'],pid=row['pid'])
    def close(self,index):
        command=self.commands[index]  # Logs are already staged; never paste future contents here.
        receipt=dict(process=command['name'],pid=command['pid'],close_limit_seconds=20,
                     request_before_monotonic=self.clock.monotonic(),request_before_wall_unix_ns=self.clock.time_ns())
        self.advance(.01);receipt.update(request_returned_monotonic=self.clock.monotonic(),request_returned_wall_unix_ns=self.clock.time_ns())
        self.advance(.01);receipt.update(wait_finished_monotonic=self.clock.monotonic(),wait_finished_wall_unix_ns=self.clock.time_ns(),exit_code=0)
        self.closes.append(receipt);command['exit_code']=0
        if self.observer is not None:self.observer('close_wait_finished',**copy.deepcopy(receipt))
    def ocr_call(self,number):
        row=copy.deepcopy(self.ocr_templates[number-1]);row['started_seconds']=self.clock.monotonic()-self.started
        if row['label']=='current-native-ui':self.put('ocr-current.png',self.files['ocr-current.png'])
        self.put(row['stdout_path'],self.files[row['stdout_path']])
        stderr=(self.root/'ocr-stderr.log').read_bytes() if 'ocr-stderr.log' in self.owned else b''
        self.put('ocr-stderr.log',stderr+('\nOCR '+row['label']+'\n').encode())
        self.advance(.02);row['finished_seconds']=self.clock.monotonic()-self.started
        self.ocr.append(row);self.json('ocr-commands.json',self.ocr)
    def click_text(self,number,word,caption=None,heading=None):
        self.ocr_call(number);self.click();self.trace('click_text',text=word,caption=caption,heading=heading);self.advance(1)
    def hud(self,name,first):
        receipt=next(row for row in self.pending['hud_analysis_pauses'] if row['capture']==name)
        self.publish(receipt['before']);self.key('Escape',True);self.advance(.1)
        self.direct_escape(False,'saved_hud_analysis')
        self.observed('Native pause before saved-HUD OCR: '+name,receipt['paused'],10)
        self.ocr_call(first);self.ocr_call(first+1)
        self.observed('Fresh paused observation after saved-HUD OCR: '+name,receipt['after_analysis'],5)
        if receipt['resume_after_analysis']:
            self.direct_escape(True,'saved_hud_analysis_cleanup');self.advance(.1);self.direct_escape(False,'saved_hud_analysis')
            self.observed('Explicit native resume after saved-HUD OCR: '+name,receipt['resumed'],10)
    def named(self,name,until):
        fence=self.pending['phase_capture_fences'][name];fence['absolute_deadline_monotonic']=until
        def budget():return min(self.remaining(),until-self.clock.monotonic())
        after=(self.initial_ready['wall_msec'] if name=='06c-next-round' else self.native[self.current][0]['wall_msec'])
        for field,label in [('acknowledged','Named living buy phase'),('ready','Two drawn frames before named capture'),('before_capture','Fresh named context immediately before capture')]:
            self.observed(label+': '+name,fence[field],budget(),after=after);after=fence[field]['wall_msec']
        self.capture(name)
        for field,label in [('after_capture_barrier','Observation barrier after raw capture'),('after_capture','Fresh named context beyond post-capture barrier')]:
            self.observed(label+': '+name,fence[field],budget())
        fence['remaining_original_budget_seconds']=budget()
    def pulse(self,keys,seconds,deadline):
        self.trace('settings_route_native_pulse_before',keys=list(keys),requested_seconds=seconds)
        self.held.update(keys);clock=self.clock;q=.0001
        receipt=dict(status='IN_PROGRESS',keys=list(keys),requested_seconds=seconds,absolute_deadline=deadline,
                     edges=[],os_states=[],down_checks=[],attempted_keys=[],released_keys=[],release_errors=[],
                     release_complete=False,scope='in-process SendInput API brackets and GetAsyncKeyState; gameplay unverified')
        receipt.update(operation_initial_monotonic=clock.monotonic(),elapsed_watchdog_start=clock.perf_counter(),
                       elapsed_watchdog_budget_seconds=deadline-clock.monotonic())
        down=set()
        def state(label):
            self.advance(q);begin=clock.monotonic();self.advance(q)
            return dict(label=label,read_begin_monotonic=begin,read_end_monotonic=clock.monotonic(),
                        target_window=1001,expected_pid=self.commands[0]['pid'],window_pid=self.commands[0]['pid'],
                        window_thread=77,visible=True,foreground_window=1001,
                        keys_down={key:key in down for key in ('w','a','s','d')},lmb_down=False)
        receipt['os_states'].append(state('before_down'));self.advance(q)
        receipt['hold_until_monotonic']=min(clock.monotonic()+seconds,deadline)
        for key in keys:
            check=dict(key=key,owned_keys=list(receipt['attempted_keys']),os_states=[],read_begin_monotonic=clock.monotonic(),status='CHECKED')
            check['os_states'].append(state('before_key_down'));self.advance(q);check['read_end_monotonic']=clock.monotonic()
            receipt['down_checks'].append(check);receipt['attempted_keys'].append(key)
            edge=dict(key=key,down=True,before_monotonic=clock.monotonic());self.advance(q);down.add(key);edge['after_monotonic']=clock.monotonic();receipt['edges'].append(edge)
        receipt['os_states'].append(state('after_down'));self.advance(q)
        wait=receipt['hold_until_monotonic']-clock.monotonic()
        if wait<=0:raise ValueError('declared native pulse exhausted its original hold')
        sample=dict(before_monotonic=clock.monotonic(),requested_sleep_seconds=wait)
        self.advance(wait);self.advance(q);sample['after_monotonic']=clock.monotonic()
        receipt.update(sleep_calls=1,first_wait=sample,last_wait=sample)
        for key in keys:
            edge=dict(key=key,down=False,before_monotonic=clock.monotonic());self.advance(q);down.discard(key)
            edge['after_monotonic']=clock.monotonic();receipt['edges'].append(edge);receipt['released_keys'].append(key)
        receipt['os_states'].append(state('after_release'));self.advance(q)
        if clock.monotonic()>=deadline:raise ValueError('declared route deadline expired')
        receipt.update(status='API_RETURNED_WITH_OS_RELEASE',release_complete=True,finished_monotonic=clock.monotonic())
        self.held.difference_update(keys);self.trace('settings_route_native_pulse_after',receipt=receipt)
        return receipt
    def route(self,until):
        route=self.pending['settings_cover_route'];route['original_second_live_absolute_deadline']=until
        route['observations']=[copy.deepcopy(route['start'])];route['native_pulses']=[]
        for key in ('w','a','s','d'):self.key(key,False)
        positions=(-4.4,-5.0,-5.6,-6.2,-6.8,-7.3,-7.8)
        wall_start=route['start']['wall_msec'];wall_end=route['after']['wall_msec'];sample_index=0
        states=[]
        def read(x):
            nonlocal sample_index
            self.advance(.05);self.advance(.01);sample_index+=1
            wall=wall_start+(wall_end-wall_start)*sample_index//14
            state=self.snapshot(wall,round_number=2,phase='live',weapon='smg',ammo=30,reserve=120)
            state['local_actor']['position']=[x,.05,-21.]
            state['actors'][0]=copy.deepcopy(state['local_actor']);states.append(state);route['observations'].append(copy.deepcopy(state));self.publish(state)
            return state
        latest=route['start']
        # First source approach read may equal the already-checked start and is
        # deduplicated. Two later neutral ticks establish the first settle.
        for index,x in enumerate(positions):
            first=read(x);latest=read(x)
            if index==len(positions)-1:
                endpoint=latest['local_actor']['position'];distance=math.hypot(-7.8-endpoint[0],-21-endpoint[2])
                self.trace('settings_route_movement_completed',origin=route['start']['local_actor']['position'],destination=endpoint,
                           requested=[-7.8,-21.],target_distance=distance,horizontal_speed=0.,
                           settled_simulation_ticks=[first['simulation_tick'],latest['simulation_tick']]);break
            distance=math.hypot(-7.8-x,0.);duration=min(.125,math.sqrt(max(.01,distance-.2)/28.))
            self.trace('settings_route_movement_control',mode='pulse',distance=distance,simulation_per_wall=1.,pulse_wall_seconds=duration)
            receipt=self.pulse(('a',),min(duration,until-self.clock.monotonic()),until);route['native_pulses'].append(receipt)
            self.trace('settings_route_movement_pulse_released',requested=[-7.8,-21.],released_after_tick=latest['simulation_tick'])
        for key in ('w','a','s','d'):self.key(key,False)
        route.update(status='FIXED_ROUTE_REACHED',after=copy.deepcopy(latest),endpoint=latest['local_actor']['position'],
                     remaining_original_second_live_budget=until-self.clock.monotonic())
    def focus(self):
        receipt=self.pending['native_focus_recovery']
        self.observed('Fresh stock match reaches a living active player before native focus loss',receipt['context_fence']['baseline'],60,duration=10,
                      before_publish=lambda:self.announce('Round live. Secure Relay Yard.',receipt['context_fence']['baseline']))
        self.key('w',True);self.button(True)
        self.observed('Game consumed physical W and LMB before native focus loss',receipt['held_input_acknowledged'],10)
        self.trace('native_focus_held_input_acknowledged',state=receipt['held_input_acknowledged'])
        self.trace('native_focus_loss_before',method='ShowWindow(SW_MINIMIZE)');self.focused=False;self.trace('native_focus_loss_after')
        self.observed('Native focus loss pauses actual offline match',receipt['lost'],10)
        self.trace('native_focus_restore_before');self.focused=True
        self.wait('Restore actual native input focus',10,predicate=lambda:self.focused);self.trace('native_focus_restore_after')
        self.observed('Actual game observes restored focus',receipt['restored_paused'],10)
        self.capture('11a-restored-focus-still-paused');self.publish(receipt['capture_context']['11a-restored-focus-still-paused']['after'])
        self.key('Escape',True);self.advance(.3);self.key('Escape',False)
        samples=receipt['held_neutral_samples']
        self.observed('Explicit resume with W and LMB still physically held',samples[0],10)
        for index,state in enumerate(samples[1:]):
            label=('Neutral held input while ordinary inertia settles' if index<len(samples)-3 else 'Fresh held-input guard sample '+str(index-(len(samples)-3)+1))
            self.observed(label,state,10)
        self.capture('11b-resumed-held-input-neutral');self.publish(receipt['capture_context']['11b-resumed-held-input-neutral']['after'])
        self.key('w',False);self.button(False);self.observed('Released held focus-test controls',receipt['released'],10)
        self.publish(receipt['fresh_press']['before_key']);self.key('w',True)
        self.observed('Fresh W press moves actual player after focus recovery',receipt['fresh_press_movement'],10)
        self.key('w',False);self.capture('11c-fresh-press-movement');self.publish(receipt['capture_context']['11c-fresh-press-movement']['after'])
    def run(self):
        failure=None
        try:
            self.json('results.json',self.progress)
            self.put('controller-stdout.log',b'');self.put('controller-stderr.log',b'')
            self.launch(0)
            self.wait('Native export window',30,duration=1.2,publish=lambda:setattr(self,'window_visible',True),predicate=lambda:self.window_visible and self.window_pid==self.commands[0]['pid'] and self.focused)
            self.wait('Native menu',60,publish=lambda:setattr(self,'menu_visible',True),predicate=lambda:self.menu_visible)
            self.capture('01-menu');self.trace('deploy_click_before',x=248,y=319);self.click();self.trace('deploy_click_after',x=248,y=319)
            self.begin_native_trace('initial-offline-trace')
            self.initial_ready=self.snapshot(1100)
            self.observed('Real offline match readiness after one Deploy click',self.initial_ready,30,after=-1)
            self.advance(3);self.capture('02-offline-spawn');self.tap('b');self.capture('03-requisition');self.tap('Escape')
            self.wait('Actual offline live phase',60,duration=9,publish=lambda:self.live_transition(self.snapshot(15000,phase='live')),predicate=lambda:'MATCH: Round live. Secure Relay Yard.' in (self.root/'client.log').read_text())
            self.wait('Living-player input focus',5,predicate=lambda:self.focused and self.window_pid==self.commands[0]['pid'])
            self.key('d',True);self.advance(.3);self.key('d',False);self.trace('relative_motion',dx=50,dy=-10)
            self.capture('04-move-aim');self.advance(.25);self.publish(self.snapshot(17000,phase='live'))
            reload=self.pending['native_reload']
            for ammo,wall in ((14,19900),(13,20000)):
                self.button(True);self.advance(1);self.native_event('local_shot',self.snapshot(wall,phase='live',ammo=ammo));self.button(False);self.advance(.35)
            self.observed('Authoritative depleted sidearm and two drawn frames',reload['before'],5)
            self.capture('05-after-fire');self.hud('05-after-fire',1)
            reload['input_seconds']=self.clock.monotonic()-self.started
            self.key('r',True);self.observed('Real R input starts authoritative offline reload',reload['started'],5);self.key('r',False)
            self.observed('Authoritative offline reload completion',reload['completed'],15,duration=1.4)
            self.observed('Two rendered frames after authoritative reload transfer',reload['capture_ready'],5)
            reload['wall_seconds_after_input']=self.clock.monotonic()-self.started-reload['input_seconds']
            self.capture('06-after-reload');self.publish(reload['after_capture']);self.hud('06-after-reload',3)
            self.key('Tab',True);self.advance(.8);self.capture('06b-scoreboard');self.key('Tab',False)
            until=min(self.deadline,self.clock.monotonic()+160)
            self.wait('Natural exported round completion',min(self.remaining(),until-self.clock.monotonic()),duration=18,
                      publish=lambda:self.round_transition(self.pending['phase_capture_fences']['06c-next-round']['acknowledged']),
                      predicate=lambda:'MATCH: Round 2' in (self.root/'client.log').read_text())
            self.named('06c-next-round',until);self.tap('b');self.capture('06d-funded-requisition')
            self.click_text(5,'VECTORLINE');self.capture('06e-purchased-smg');self.hud('06e-purchased-smg',6)
            until=min(self.deadline,self.clock.monotonic()+35)
            self.wait('Second active round for weapon switching',min(self.remaining(),until-self.clock.monotonic()),duration=13,
                      publish=lambda:self.live_transition(self.pending['settings_cover_route']['start']),
                      predicate=lambda:(self.root/'client.log').read_text().count('MATCH: Round live.')>=2)
            self.observed('Living second-round player before fixed settings route',self.pending['settings_cover_route']['start'],min(self.remaining(),until-self.clock.monotonic()),
                          after=self.pending['phase_capture_fences']['06c-next-round']['after_capture']['wall_msec'])
            self.route(until);self.tap('2');self.capture('06f-switched-sidearm');self.hud('06f-switched-sidearm',8)
            self.tap('1');self.capture('06g-switched-primary');self.hud('06g-switched-primary',10)
            self.capture('07-field-menu');self.click_text(12,'SETTINGS');self.capture('07b-field-settings')
            self.ocr_call(13);self.click();self.trace('settings_slider_click');self.advance(1)
            self.put('state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json',self.files['state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json'])
            self.capture('07c-settings-changed');settings=self.pending['native_settings_resume']
            self.observed('Fresh paused player after native settings change',settings['paused_after_settings'],5)
            until=min(self.deadline,self.clock.monotonic()+10);self.key('Escape',True)
            self.observed('Actual living player explicitly resumes after field settings',settings['resumed'],until-self.clock.monotonic())
            self.direct_escape(False,'field_settings_resume')
            self.observed('Two drawn frames after explicit native settings resume',settings['capture_ready'],until-self.clock.monotonic())
            self.capture('07d-explicit-resume');self.publish(settings['after_capture']);self.hud('07d-explicit-resume',14)
            self.click_text(16,'LEAVE',caption='LEAVE MATCH',heading='FIELD MENU')
            self.wait('Return from offline match',30,publish=lambda:setattr(self,'menu_visible',True),predicate=lambda:self.menu_visible);self.capture('08-return-menu');self.close(0)
            self.launch(1)
            self.wait('Reopened native window',30,duration=4,publish=lambda:setattr(self,'window_visible',True),predicate=lambda:self.window_visible and self.window_pid==self.commands[1]['pid'] and self.focused)
            self.wait('Reopened native menu',45,publish=lambda:setattr(self,'menu_visible',True),predicate=lambda:self.menu_visible)
            self.capture('09-reopened-menu');self.trace('reopened_deploy_click_before',x=248,y=319);self.click();self.trace('reopened_deploy_click_after',x=248,y=319)
            until=min(self.deadline,self.clock.monotonic()+30)
            self.wait('Reopened process loaded profile into ordinary offline match',until-self.clock.monotonic(),
                      publish=lambda:self.begin_native_trace('restart-profile-trace'),
                      predicate=lambda:(self.root/'restart-profile-trace/events.jsonl').is_file())
            self.named('10-reopened-loaded-settings',until)
            self.focus();self.close(1);self.advance(.01)
            result=copy.deepcopy(self.pending)
            result.update(passed=True,commands=self.commands,ocr_commands=self.ocr,captures=self.captures,
                          shutdown_study_observations=self.closes,events=self.names,
                          elapsed_seconds=self.clock.monotonic()-self.started,
                          last_offline_observation=self.previous[self.current])
            self.json('commands.json',self.commands);self.json('ocr-commands.json',self.ocr);self.json('results.json',result)
            self.stdout.extend((json.dumps(result,indent=2,allow_nan=False)+'\n').encode());self.put('controller-stdout.log',bytes(self.stdout))
            return result
        except BaseException as error:
            failure=error;metadata_errors=[]
            self.progress.update(passed=False,error=type(error).__name__+': '+str(error),commands=self.commands,
                                 ocr_commands=self.ocr,events=self.names,elapsed_seconds=self.clock.monotonic()-self.started)
            try:self.json('results.json',self.progress)
            except BaseException as secondary:metadata_errors.append('results: '+type(secondary).__name__+': '+str(secondary))
            self.stdout.extend((json.dumps({'offline_input_failure':self.progress,'recent_actions':self.actions[-12:]},indent=2)+'\n').encode())
            try:self.put('controller-stdout.log',bytes(self.stdout))
            except BaseException as secondary:metadata_errors.append('stdout: '+type(secondary).__name__+': '+str(secondary))
            if metadata_errors:
                failure=RuntimeError('Synthetic failure metadata retained incompletely: '+str(metadata_errors))
                raise failure from error
            raise
        finally:
            close_errors=self.close_owned()
            if close_errors:raise RuntimeError('Synthetic owned file close failed: '+str(close_errors)) from failure
