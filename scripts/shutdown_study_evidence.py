"""Pure, fail-closed checks of the frozen Windows study's evidence envelope.

This checks retained formats and producer relationships. It cannot approve pixels,
gameplay, native ownership or execution. The public retention gate stays blocked.
"""
import hashlib
import csv
import io
import json
import math
from pathlib import Path
import re
import stat
import struct
import zlib

from native_log import failed

CAPTURES = ('01-menu','02-offline-spawn','03-requisition','04-move-aim','05-after-fire',
 '06-after-reload','06b-scoreboard','06c-next-round','06d-funded-requisition','06e-purchased-smg',
 '06f-switched-sidearm','06g-switched-primary','07-field-menu','07b-field-settings',
 '07c-settings-changed','07d-explicit-resume','08-return-menu','09-reopened-menu',
 '10-reopened-loaded-settings','11a-restored-focus-still-paused','11b-resumed-held-input-neutral','11c-fresh-press-movement')
PROFILE_PATH='state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json'
TRACES=('initial-offline-trace','restart-profile-trace')
OCR_SPECS=[]
for name in ('05-after-fire','06-after-reload','UI','06e-purchased-smg','06f-switched-sidearm','06g-switched-primary','UI','UI','07d-explicit-resume','UI'):
    if name=='UI':OCR_SPECS.append(('current-native-ui',11))
    else:OCR_SPECS.extend(((name+':(0, 630, 450, 720)',6),(name+':(980, 648, 1280, 680)',7)))
BASE_REQUIRED=tuple(name+'.png' for name in CAPTURES)+('ocr-current.png',)+tuple('ocr-stdout/%03d.log'%i for i in range(1,17))+(
 'commands.json','actions.json','ocr-commands.json','results.json','client.log','reopened.log','ocr-stderr.log',
 'initial-offline-trace/events.jsonl','initial-offline-trace/status.json','restart-profile-trace/events.jsonl','restart-profile-trace/status.json',PROFILE_PATH)
REQUIRED=BASE_REQUIRED+('controller-stdout.log','controller-stderr.log')
assert len(BASE_REQUIRED)==51 and len(REQUIRED)==53 and len(OCR_SPECS)==16
SOURCE_FIELDS=('source_commit','source_game_tree','source_content_sha256','source_validation_sha256')
WARNING=re.compile(r'\bWARNING\b',re.I)  # Root's strict study policy, separate from native_log.failed.


def need(condition,message):
    if not condition:raise ValueError(message)


def number(value,minimum=0):
    return finite(value) and value>=minimum


def integer(value,minimum=0):
    return type(value) is int and value>=minimum


def pid(value):return integer(value,1) and value<=0xffffffff


def unsigned(value,bits,minimum=0):
    return integer(value,minimum) and value<2**bits


def owned_identity(value):
    need(type(value) is dict and pid(value.get('pid')) and
         unsigned(value.get('creation_filetime'),64,1) and
         unsigned(value.get('handle_value'),64,1) and
         value.get('member_of_outer_job') is True,'invalid owned process identity')
    return value['pid'],value['creation_filetime'],value['handle_value']


def digest(data):return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'duplicate JSON key: '+key);result[key]=value
        return result
    def invalid(value):raise ValueError('nonfinite JSON number: '+value)
    def floating(value):
        result=float(value);need(math.isfinite(result),'nonfinite JSON number');return result
    return json.loads(data.decode('utf-8',errors='strict'),object_pairs_hook=pairs,parse_constant=invalid,parse_float=floating)


def png_dimensions(data):
    """Verify PNG chunk CRCs and complete noninterlaced 8-bit capture raster.

    Windows ImageGrab emits RGB8. RGBA and grayscale8 captures also have a fully
    checked raster. Unsupported formats fail explicitly, never inherit success.
    No Pillow import/dependency can run before the workflow's retention gate.
    """
    need(data.startswith(b'\x89PNG\r\n\x1a\n'),'invalid PNG signature')
    offset=8;chunks=[];payload=[];ended=False;idat_ended=False;seen_idat=False
    while offset<len(data):
        need(offset+12<=len(data),'truncated PNG chunk')
        size=struct.unpack('>I',data[offset:offset+4])[0];kind=data[offset+4:offset+8];offset+=8
        need(offset+size+4<=len(data),'truncated PNG payload')
        body=data[offset:offset+size];crc=struct.unpack('>I',data[offset+size:offset+size+4])[0];offset+=size+4
        need(zlib.crc32(kind+body)&0xffffffff==crc,'PNG CRC mismatch')
        need(all(65<=b<=90 or 97<=b<=122 for b in kind),'invalid PNG chunk name')
        if kind==b'IDAT':need(not idat_ended,'noncontiguous PNG IDAT');seen_idat=True;payload.append(body)
        elif seen_idat:idat_ended=True
        if kind==b'PLTE':need(not seen_idat and 0<len(body)<=768 and len(body)%3==0 and not any(k==b'PLTE' for k,_ in chunks),'invalid PNG palette')
        chunks.append((kind,body))
        if kind==b'IEND':need(not body and offset==len(data),'invalid PNG end/trailing bytes');ended=True;break
        if kind[0]&32==0:need(kind in (b'IHDR',b'PLTE',b'IDAT'),'unknown critical PNG chunk')
    need(ended and chunks and chunks[0][0]==b'IHDR' and len(chunks[0][1])==13,'PNG header/end missing')
    need(sum(kind==b'IHDR' for kind,_ in chunks)==1 and seen_idat,'duplicate header or absent PNG raster')
    width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',chunks[0][1])
    need(width>0 and height>0 and depth==8 and color in (0,2,4,6) and compression==filtering==interlace==0,'unsupported capture PNG format')
    need(color not in (0,4) or not any(kind==b'PLTE' for kind,_ in chunks),'grayscale PNG palette forbidden')
    stride=1+width*{0:1,2:3,4:2,6:4}[color];expected=stride*height;count=0;decoder=zlib.decompressobj()
    for block in payload:
        pending=block
        while pending:
            raw=decoder.decompress(pending,65536);pending=decoder.unconsumed_tail
            for index in range((-count)%stride,len(raw),stride):need(raw[index]<=4,'invalid PNG raster filter')
            count+=len(raw);need(count<=expected,'PNG raster exceeds dimensions')
            need(not decoder.unused_data,'trailing PNG compressed data')
    tail=decoder.flush()
    for index in range((-count)%stride,len(tail),stride):need(tail[index]<=4,'invalid PNG raster filter')
    count+=len(tail);need(decoder.eof and not decoder.unused_data and count==expected,'incomplete PNG raster')
    return [width,height]


def finite(value):
    if type(value) not in (int,float):return False
    try:return math.isfinite(value)
    except OverflowError:return False


def seed(value):
    return type(value) is str and len(value)<=20 and re.fullmatch(r'(?:0|-?[1-9][0-9]*)',value) is not None and -(2**63)<=int(value)<2**63


def profile_shape(value,defaults):
    need(type(value) is dict and set(value)==set(defaults),'profile fields differ')
    for field in ('schema','xp','level','credits','matches','wins','kills','deaths'):need(integer(value.get(field)),'profile counter type differs: '+field)
    need(value['schema']==1 and value.get('scope')=='offline_training' and type(value.get('display_name')) is str and type(value.get('last_daily')) is str and type(value.get('history')) is list,'profile schema/types differ')
    settings=value.get('settings');need(type(settings) is dict and set(settings)==set(defaults['settings']),'profile setting fields differ')
    for name,expected in defaults['settings'].items():
        actual=settings[name]
        if type(expected) in (int,float):need(finite(actual),'profile numeric type differs: '+name)
        else:need(type(actual) is type(expected),'profile setting type differs: '+name)


def snapshot_shape(value):
    fields=('schema','scope','scenario','wall_msec','elapsed','drawn_frames','simulation_tick','time_scale','phase','time_left','round_number','attack_score','defend_score','objective_state','objective_timer','objective_carrier','objective_position','interaction_progress','local_contribution','local_actor','actors','completion_calls','events_dropped','frame_diagnostics','local_input','ui')
    need(type(value) is dict and all(field in value for field in fields),'incomplete snapshot fields')
    need(type(value['schema']) is int and value['schema']==1 and value['scope']=='debug_offline_read_only_observation' and value['scenario']=='standard','snapshot schema/scope differs')
    for field in ('wall_msec','drawn_frames','simulation_tick','round_number','attack_score','defend_score','objective_carrier','local_contribution','completion_calls','events_dropped'):need(integer(value[field]),'snapshot counter invalid: '+field)
    for field in ('elapsed','time_scale','time_left','objective_timer','interaction_progress'):need(finite(value[field]),'snapshot number invalid: '+field)
    need(value['time_scale']==1 and value['events_dropped']==0 and type(value['phase']) is str and type(value['objective_state']) is str,'snapshot observation incomplete')
    def vector(v,size):return type(v) is list and len(v)==size and all(finite(x) for x in v)
    need(vector(value['objective_position'],3),'snapshot objective vector invalid')
    actors=value['actors'];local=value['local_actor'];need(type(actors) is list and bool(actors) and type(local) is dict,'snapshot actors absent')
    for actor in [*actors,local]:
        need(type(actor) is dict and integer(actor.get('id'),1) and type(actor.get('team')) is int and type(actor.get('alive')) is bool,'actor identity/types invalid')
        need(vector(actor.get('position'),3) and vector(actor.get('velocity'),3),'actor vectors invalid')
        for field in ('yaw','pitch','health','reload'):need(finite(actor.get(field)),'actor number invalid: '+field)
        for field in ('ammo','reserve','credits','grenades','smokes','kills','deaths','assists'):need(integer(actor.get(field)),'actor counter invalid: '+field)
        need(type(actor.get('weapon')) is str and type(actor.get('inventory')) is list,'actor weapon/inventory absent')
    ids=[actor['id'] for actor in actors];need(len(ids)==len(set(ids)) and local['id'] in ids,'actor identity duplicated/unbound')
    need(same(local,actors[ids.index(local['id'])]),'snapshot local actor differs from actor projection')
    need(value['local_input'].keys()>={'interact','fire','reload','move'} and all(type(value['local_input'][key]) is bool for key in ('interact','fire','reload')) and vector(value['local_input']['move'],2),'local input snapshot incomplete')
    ui=value['ui'];need(type(ui) is dict and all(field in ui for field in ('screen','paused','focused','waiting_for_input_release','window_size')) and type(ui['screen']) is str and all(type(ui[field]) is bool for field in ('paused','focused','waiting_for_input_release')) and type(ui['window_size']) is list and len(ui['window_size'])==2 and all(integer(v,1) for v in ui['window_size']),'UI snapshot incomplete')
    need(all(field in ui for field in ('status_text','scoreboard_visible','touch_controls','capabilities','mouse_mode','window_mode')) and type(ui['status_text']) is str and all(type(ui[field]) is bool for field in ('scoreboard_visible','touch_controls')) and type(ui['capabilities']) is dict and integer(ui['mouse_mode']) and integer(ui['window_mode']),'UI diagnostic fields incomplete')
    frame=value['frame_diagnostics'];need(type(frame) is dict and integer(frame.get('read_begin_usec')) and integer(frame.get('read_end_usec')) and frame['read_begin_usec']<=frame['read_end_usec'],'frame diagnostics incomplete')
    for field in ('max_physics_steps_per_frame','physics_ticks_per_second','max_fps','process_frames','physics_frames','drawn_frames','draw_calls_last_rendered_frame','primitives_last_rendered_frame'):need(integer(frame.get(field)),'frame counter absent: '+field)
    for field in ('physics_jitter_fix','process_max_seconds_last_engine_window','physics_step_max_seconds_last_engine_window','viewport_3d_scale'):need(finite(frame.get(field)),'frame number absent: '+field)
    for field in ('viewport_visible_size','viewport_texture_size_pixels'):need(vector(frame.get(field),2),'viewport dimensions absent')
    target=frame.get('internal_3d_target_size');need(type(target) is dict and target.get('available') is False and type(target.get('reason')) is str and bool(target['reason']),'unavailable internal-target scope missing')


class Evidence:
    def __init__(self,directory,context):
        self.root=Path(directory);self.context=context;self.data={};self.records=[];self.errors=[];self.strict_errors=[];self.details={}
    def check(self,label,action):
        try:action()
        except (ValueError,OSError,TypeError,KeyError,IndexError,AttributeError,OverflowError,UnicodeError,struct.error,zlib.error) as error:
            self.errors.append(label+': '+type(error).__name__+': '+str(error))
    def files(self):
        need(self.root.is_dir() and not self.root.is_symlink(),'trial directory missing/symlinked')
        for path in sorted(self.root.rglob('*')):
            relative=path.relative_to(self.root).as_posix()
            def read():
                before=path.lstat();need(not path.is_symlink(),'symlinked evidence: '+relative)
                if stat.S_ISDIR(before.st_mode):return
                need(stat.S_ISREG(before.st_mode),'nonregular evidence: '+relative)
                first=path.read_bytes();second=path.read_bytes();after=path.lstat()
                def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode)
                need(first==second and identity(before)==identity(after),'evidence changed during read: '+relative)
                self.data[relative]=first;self.records.append(dict(path=relative,bytes=len(first),sha256=digest(first)))
            self.check(relative,read)
        for name in REQUIRED:
            if name not in self.data:self.errors.append('missing required file: '+name)
    def json(self,name,kind=dict):
        value=strict_json(self.data[name]);need(type(value) is kind,name+' has wrong JSON container');return value
    def result(self):
        self.result_data=self.json('results.json');self.commands=self.json('commands.json',list);self.actions=self.json('actions.json',list);self.ocr=self.json('ocr-commands.json',list)
        need(self.result_data.get('passed') is True,'driver result is failed/incomplete')
        need(self.result_data.get('target')=='windows','Windows study result required')
        need(same(self.result_data.get('commands'),self.commands) and same(self.result_data.get('ocr_commands'),self.ocr),'result receipt mirrors differ')
        need(self.result_data.get('events')==list(CAPTURES),'result capture event order differs')
        need(type(self.result_data.get('cleanup_errors')) is list and not self.result_data['cleanup_errors'],'driver cleanup failed/unresolved')
        for field in ('clean_exit','settings_restart_equal','natural_round_completed','purchase_and_weapon_switch','settings_loaded_into_reopened_process','explicit_resume','incomplete_training_unchanged_after_reopened_exit'):
            need(self.result_data.get(field) is True,'missing successful result: '+field)
        for field in ('exit','initial_exit','reopened_exit'):need(type(self.result_data.get(field)) is int and self.result_data[field]==0,'nonzero/unresolved result exit: '+field)
        need(number(self.result_data.get('elapsed_seconds')),'invalid reported elapsed time')
        need(self.result_data.get('exit_method')=='completion-driven WM_CLOSE','wrong close method')
        expected_controller=digest(Path(__file__).with_name('verify_offline_export.py').read_bytes())
        need(self.result_data.get('controller_sha256')==expected_controller,'stale/default driver source hash')
    def captures(self):
        rows=self.result_data['captures'];need(type(rows) is list and len(rows)==len(CAPTURES),'capture count differs')
        for name,row in zip(CAPTURES,rows):
            need(type(row) is dict and row.get('name')==name,'capture name/order differs')
            dimensions=png_dimensions(self.data[name+'.png']);need(row.get('dimensions')==dimensions and all(type(v) is int for v in row['dimensions']),'capture dimensions differ')
        png_dimensions(self.data['ocr-current.png'])
        need(self.actions and all(type(row) is dict and type(row.get('event')) is str and number(row.get('seconds')) and integer(row.get('wall_unix_msec')) and type(row.get('held_keys')) is list and all(type(key) is str for key in row['held_keys']) for row in self.actions),'invalid/empty action records')
        need(all(a['seconds']<=b['seconds'] for a,b in zip(self.actions,self.actions[1:])),'action clock regressed')
        begins=[row for row in self.actions if row['event']=='capture_begin'];ends=[row for row in self.actions if row['event']=='capture_end']
        need([row.get('capture') for row in begins]==list(CAPTURES) and [row.get('capture') for row in ends]==list(CAPTURES),'missing/misordered capture actions')
        expected_actions=[(event,name) for name in CAPTURES for event in ('capture_begin','capture_end')]
        need([(row['event'],row.get('capture')) for row in self.actions if row['event'] in ('capture_begin','capture_end')]==expected_actions,'capture actions are not paired in producer order')
        for begin,end,row in zip(begins,ends,rows):need(begin['seconds']<=end['seconds'] and end.get('dimensions')==row['dimensions'],'capture action dimensions/time differ')
    def ocr_records(self):
        need(len(self.ocr)==16,'OCR count differs')
        for index,(row,(label,psm)) in enumerate(zip(self.ocr,OCR_SPECS),1):
            need(type(row) is dict and row.get('label')==label,'OCR label/order differs')
            command=row.get('command');need(type(command) is list and len(command)==(6 if psm==11 else 5) and type(command[0]) is str and bool(command[0]) and command[1:]==['stdin','stdout','--psm',str(psm)]+(['tsv'] if psm==11 else []),'OCR command differs')
            name='ocr-stdout/%03d.log'%index;raw=self.data[name]
            need(row.get('stdout_path')==name and integer(row.get('stdout_total_bytes')) and integer(row.get('stdout_retained_bytes')) and row['stdout_total_bytes']==row['stdout_retained_bytes']==len(raw)<=2*1024*1024,'OCR byte count/path differs')
            need(row.get('stdout_sha256')==digest(raw),'OCR stdout hash differs')
            need(row.get('stdout_complete') is True and row.get('stdout_truncated') is False and row.get('timed_out',False) is False and type(row.get('exit_code')) is int and row['exit_code']==0,'OCR incomplete/nonzero/timeout')
            need(number(row.get('started_seconds')) and number(row.get('finished_seconds')) and row['started_seconds']<=row['finished_seconds'],'OCR clocks invalid')
            raw.decode('utf-8',errors='strict')
        need(all(a['finished_seconds']<=b['started_seconds'] for a,b in zip(self.ocr,self.ocr[1:])),'OCR command time order differs')
        begin={row['capture']:row['seconds'] for row in self.actions if row['event']=='capture_begin'}
        end={row['capture']:row['seconds'] for row in self.actions if row['event']=='capture_end'}
        anchors=[('05-after-fire','06-after-reload')]*2+[('06-after-reload','06b-scoreboard')]*2+[('06d-funded-requisition','06e-purchased-smg')]+[('06e-purchased-smg','06f-switched-sidearm')]*2+[('06f-switched-sidearm','06g-switched-primary')]*2+[('06g-switched-primary','07-field-menu')]*2+[('07-field-menu','07b-field-settings'),('07b-field-settings','07c-settings-changed')]+[('07d-explicit-resume','08-return-menu')]*3
        for row,(before,after) in zip(self.ocr,anchors):need(end[before]<=row['started_seconds']<=row['finished_seconds']<=begin[after],'OCR time does not bind its producer capture interval')
        markers=[line[4:] for line in self.data['ocr-stderr.log'].decode('utf-8',errors='strict').splitlines() if line.startswith('OCR ')]
        need(markers==[label for label,_ in OCR_SPECS],'OCR stderr command markers differ')
    def source_and_commands(self):
        need(type(self.context) is dict and type(self.context.get('identity')) is dict and type(self.context.get('trial')) is dict,'trusted collection context missing')
        self.identity=self.context['identity'];self.trial=self.context['trial'];source=self.identity['source'];record=self.identity['artifact_record']
        need(type(source) is dict and type(record) is dict,'source/export identity missing')
        for field in SOURCE_FIELDS:
            size=40 if field in ('source_commit','source_game_tree') else 64
            need(type(source.get(field)) is str and re.fullmatch('[0-9a-f]{'+str(size)+'}',source[field]) is not None,'invalid source identity: '+field)
            need(record.get(field)==source[field],'export source identity differs: '+field)
        need(source.get('source_dirty') is False and source.get('source_game_dirty') is False and record.get('source_dirty') is False and record.get('source_game_dirty') is False,'dirty/unresolved source identity')
        need(record.get('target')=='windows' and record.get('export_completed') is True and record.get('version')=='0.3.3-dev' and type(record.get('build_number')) is int and record['build_number']==6,'unresolved Windows export')
        need(same(self.result_data.get('source'),source) and same(self.result_data.get('artifact_source'),record),'result source/export context differs')
        artifact=record['artifact'];payload=self.identity['payload']
        need(type(artifact) is dict and type(payload) is list and bool(payload) and record.get('payload')==payload and artifact in payload,'payload/artifact identity differs')
        need(type(artifact.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',artifact['sha256']) is not None and integer(artifact.get('bytes'),1) and artifact.get('path')=='windows/SIGHTBREAK.exe','invalid executable identity')
        need(self.result_data.get('executable_sha256')==artifact['sha256'],'result executable hash differs')
        pack=self.identity['embedded_pck'];need(type(pack) is dict and integer(pack.get('bytes'),32) and integer(pack.get('offset')) and type(pack.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',pack['sha256']) is not None,'embedded pack identity missing')
        need(pack.get('storage')=='embedded exact original pack range' and type(pack.get('pack_version')) is int and pack['pack_version'] in (3,4) and same(pack.get('engine_version'),[4,7,2]) and pack['offset']+pack['bytes']+12==artifact['bytes'],'embedded pack range/version differs')
        host=self.identity['host'];need(type(host) is dict and all(type(host.get(key)) is str and bool(host[key]) for key in ('node','platform','python')),'host identity missing')
        need(self.result_data.get('host')==host['platform'],'result host differs')
        from toolchain import ENGINE
        need(self.result_data.get('engine')==ENGINE,'unresolved/stale engine identity')
        need(integer(self.trial.get('index'),1) and self.trial['index']<=4 and self.trial.get('arm')==('ordinary','verbose','verbose','ordinary')[self.trial['index']-1] and self.trial.get('flow_seconds')==300 and type(self.trial.get('flow_seconds')) is int and self.trial.get('close_seconds')==20 and type(self.trial.get('close_seconds')) is int,'trial order/original budget context invalid')
        need(self.trial.get('attempted') is True and 'driver_error' not in self.trial and 'stop_error' not in self.trial,'collection driver failed/unresolved')
        need(self.trial.get('arm') in ('ordinary','verbose') and self.trial.get('verbose') is (self.trial['arm']=='verbose'),'trial arm unresolved')
        need(Path(self.trial['output']).resolve()==self.root.resolve(),'trial evidence path differs')
        arguments=self.trial['driver_arguments'];need(type(arguments) is list,'driver command context missing')
        expected=['scripts/verify_offline_export.py','--target','windows','--hosted-render-priority','below-normal','--display',':102','--timeout','300','--output',str(self.trial['output'])]+(['--reopened-verbose'] if self.trial['verbose'] else [])
        need(arguments==expected,'driver arguments/schedule differ')
        import sys
        need(self.result_data.get('controller_command')==[sys.executable,*arguments],'result controller command differs')
        need(len(self.commands)==2 and [row.get('name') for row in self.commands]==['client','reopened'],'native command count/order differs')
        self.pids={};executable=None
        for name,row,trace in zip(('client','reopened'),self.commands,TRACES):
            need(type(row) is dict and pid(row.get('pid')) and type(row.get('exit_code')) is int and row['exit_code']==0 and number(row.get('started_seconds')),'invalid native process command')
            self.pids[name]=row['pid'];command=row['command'];need(type(command) is list and all(type(arg) is str for arg in command) and bool(command),'invalid native argv')
            if executable is None:executable=command[0]
            need(command[0]==executable and executable.replace('\\','/').endswith('/windows/SIGHTBREAK.exe'),'unbound native executable path')
            need(len(command)>=10 and re.fullmatch(r'[0-9]+x[0-9]+',command[6]) is not None,'native requested resolution absent')
            width,height=map(int,command[6].split('x'));need(640<=width<=1280 and width%16==0 and height==width*9//16,'native requested resolution differs from source')
            if name=='client':requested_resolution=command[6]
            need(command[6]==requested_resolution,'native requested resolution changed across restart')
            expected_tail=['--audio-driver','Dummy','--position','0,0','--resolution',requested_resolution]+(['--verbose'] if name=='reopened' and self.trial['verbose'] else [])+['--','--offline-validation','--offline-trace-dir='+str(self.root.resolve()/trace)]
            need(command[1:]==expected_tail,'native argv/trace/verbosity differs')
        begins={row['capture']:row['seconds'] for row in self.actions if row['event']=='capture_begin'}
        ends={row['capture']:row['seconds'] for row in self.actions if row['event']=='capture_end'}
        need(self.commands[0]['started_seconds']<=begins['01-menu'] and ends['08-return-menu']<=self.commands[1]['started_seconds']<=begins['09-reopened-menu'],'native launch/capture order differs')
        need(len(set(self.pids.values()))==2 and self.commands[0]['started_seconds']<=self.commands[1]['started_seconds'],'native PID/start order differs')
        need(self.result_data.get('profile_observation_path')==str(self.root.resolve()/PROFILE_PATH),'saved profile path differs')
    def traces_and_profile(self):
        self.initials=[];trace_receipts=[]
        for trace in TRACES:
            lines=self.data[trace+'/events.jsonl'].splitlines();need(bool(lines) and all(line.strip() for line in lines),'empty trace/event line')
            rows=[strict_json(line) for line in lines]
            for index,row in enumerate(rows):
                need(type(row) is dict and row.get('event_index')==index and type(row.get('event_index')) is int and type(row.get('event')) is str and bool(row['event']) and integer(row.get('observer_wall_msec')),'invalid trace index/type')
                if 'wall_msec' in row:need(integer(row['wall_msec']) and row['wall_msec']<=row['observer_wall_msec'],'invalid trace snapshot clock')
                for field in ('elapsed','simulation_tick'):
                    if field in row:need(number(row[field]),'invalid trace counter: '+field)
            need(all(a['observer_wall_msec']<=b['observer_wall_msec'] for a,b in zip(rows,rows[1:])),'trace clock regressed')
            initial=rows[0];need(initial['event']=='initial' and sum(row['event']=='initial' for row in rows)==1,'initial trace event missing/duplicated')
            need(initial.get('initial_conditions')=='stock_spawns_teams_random_seeds','non-stock initial conditions')
            need(seed(initial.get('match_seed')),'initial match seed unresolved')
            seeds=initial.get('actor_spread_seeds');actors=initial.get('actors')
            need(type(actors) is list and bool(actors) and all(type(actor) is dict and integer(actor.get('id'),1) for actor in actors),'initial actor identity missing')
            need(type(seeds) is dict and set(seeds)=={str(actor['id']) for actor in actors} and all(seed(value) for value in seeds.values()),'actor seed identities missing')
            need(initial.get('difficulty')=='normal' and type(initial.get('rules')) is dict and initial['rules']==dict(buy_seconds=15,round_seconds=100,device_seconds=35,plant_seconds=3,defuse_seconds=5,win_score=7) and all(finite(value) for value in initial['rules'].values()) and type(initial.get('protocol')) is int and initial['protocol']==6 and initial.get('prediction_enabled') is False,'initial settings/protocol missing')
            status=self.json(trace+'/status.json')
            full_events={'initial','local_shot','phase','round_number','objective_state','local_contribution','reload','weapon','alive','utility','completed','duplicate_completion'}
            for row in rows:
                need(row['event'] in full_events|{'notification','local_interact_input'},'unknown frozen trace event kind')
                if row['event'] in full_events:snapshot_shape(row)
                elif row['event']=='notification':need(type(row.get('message')) is str and number(row.get('elapsed')) and integer(row.get('simulation_tick')),'incomplete notification event')
                else:need(type(row.get('held')) is bool and number(row.get('elapsed')) and integer(row.get('simulation_tick')) and integer(row.get('round_number'),1) and number(row.get('interaction_progress')),'incomplete interaction event')
            snapshot_shape(status)
            for snapshot in (initial,status):
                need(snapshot.get('schema')==1 and type(snapshot.get('schema')) is int and snapshot.get('scope')=='debug_offline_read_only_observation' and snapshot.get('scenario')=='standard' and type(snapshot.get('time_scale')) in (int,float) and snapshot['time_scale']==1,'trace snapshot schema/scope/scenario differs')
                need(integer(snapshot.get('wall_msec')) and integer(snapshot.get('drawn_frames')) and integer(snapshot.get('simulation_tick')) and snapshot.get('events_dropped')==0 and type(snapshot.get('events_dropped')) is int,'snapshot counters/drop count invalid')
                need(type(snapshot.get('local_actor')) is dict and integer(snapshot['local_actor'].get('id'),1),'trace local actor missing')
            need(status['wall_msec']>=initial['wall_msec'] and status['simulation_tick']>=initial['simulation_tick'],'status predates initial event')
            self.initials.append(initial);trace_receipts.append(dict(path=trace+'/events.jsonl',rows=len(rows),bytes=len(self.data[trace+'/events.jsonl']),sha256=digest(self.data[trace+'/events.jsonl']),status_sha256=digest(self.data[trace+'/status.json'])))
        self.profile=self.json(PROFILE_PATH)
        profile_source=Path(__file__).resolve().parents[1]/'game/scripts/profile.gd'
        defaults=strict_json(profile_source.read_text().split('const DEFAULTS := ',1)[1].split('\nvar data:',1)[0].encode())
        profile_shape(self.initials[0].get('initial_profile'),defaults)
        profile_shape(self.profile,defaults)
        profile_shape(self.initials[1].get('initial_profile'),defaults)
        need(self.initials[0].get('initial_profile')==defaults,'first process did not load fresh source defaults')
        need(self.profile.get('schema')==1 and type(self.profile.get('schema')) is int and self.profile.get('scope')=='offline_training' and type(self.profile.get('settings')) is dict,'saved profile schema invalid')
        need(number(self.profile['settings'].get('sensitivity')) and 0.0005<=self.profile['settings']['sensitivity']<=0.008 and self.profile['settings']['sensitivity']!=defaults['settings']['sensitivity'],'native settings change absent')
        expected_profile=json.loads(json.dumps(defaults));expected_profile['settings']['sensitivity']=self.profile['settings']['sensitivity']
        need(self.profile==expected_profile,'unexpected training/profile changes in incomplete ordinary matches')
        need(self.initials[1].get('initial_profile')==self.profile,'reopened initial profile differs from saved profile')
        self.details['traces']=trace_receipts
        self.details['process_seed_initial_events']=[dict(process_trace=trace,initial_event=initial,provenance='retained event; source/PID association requires complete capture fences') for trace,initial in zip(TRACES,self.initials)]
        need(type(self.identity.get('source')) is dict and bool(self.pids),'source/process context missing for trace provenance')
        fences=self.result_data['phase_capture_fences']
        for capture,name,trace,initial in zip(('06c-next-round','10-reopened-loaded-settings'),('client','reopened'),TRACES,self.initials):
            fence=fences[capture];expected=dict(source=self.identity['source'],process_pid=self.pids[name],process_running=True,trace_directory=str((self.root/trace).resolve()))
            if name=='reopened':expected.update(loaded_initial_event=initial,stored_profile=self.profile)
            for field in ('expected_binding','binding_before_capture','binding_after_capture'):need(same(fence.get(field),expected),'capture process/source/trace/profile binding differs: '+capture+'/'+field)
            need(fence.get('capture')==capture and integer(fence.get('expected_actor_id'),1) and fence['expected_actor_id']==initial['local_actor']['id'] and type(fence.get('expected_round')) is int and fence['expected_round']==(2 if name=='client' else 1) and fence.get('expected_phase')=='buy' and type(fence.get('additional_drawn_frames_required')) is int and fence['additional_drawn_frames_required']==2,'capture fence identity/schema incomplete')
            need(number(fence.get('absolute_deadline_monotonic')) and number(fence.get('remaining_original_budget_seconds')) and fence['remaining_original_budget_seconds']>0,'capture fence budget fields incomplete')
            for field in ('acknowledged','ready','before_capture','after_capture_barrier','after_capture'):snapshot_shape(fence[field])
        self.details['traces']=trace_receipts
        self.details['process_seed_initial_events']=[dict(process_trace=trace,initial_event=initial,provenance='retained event, bound through commands and source/PID capture fences') for trace,initial in zip(TRACES,self.initials)]
    def process_and_closes(self):
        receipts=self.result_data.get('shutdown_study_observations');need(type(receipts) is list and len(receipts)==2,'two result close receipts missing')
        trial=self.trial;need(all(field in trial for field in ('started_monotonic','finished_monotonic','started_wall_unix_ns','finished_wall_unix_ns')),'trusted trial process interval missing')
        start=trial['started_monotonic'];finish=trial['finished_monotonic']
        need(integer(trial['started_wall_unix_ns'],1) and integer(trial['finished_wall_unix_ns'],1),'trial wall clock fields invalid')
        need(number(start) and number(finish) and start<=finish,'trusted trial interval invalid')
        observations=trial.get('observations');need(type(observations) is list and len(observations)==4,'two launches/two closes missing')
        need([row.get('event') for row in observations]==['native_launch','close_wait_finished','native_launch','close_wait_finished'],'observer callback order differs')
        queries=trial['job_queries'];need(type(queries) is list and len(queries)==2,'before/after job queries missing')
        before,after=queries;baseline=before['baseline_pid'];handle=before['job_handle']
        need(pid(baseline) and unsigned(handle,64,1),'owned controller identity missing')
        need([row.get('label') for row in queries]==['trial'+str(trial['index'])+'/before','trial'+str(trial['index'])+'/after'],'before/after query labels differ')
        for row in queries:
            need(row.get('verified') is True and row.get('baseline_pid')==baseline and row.get('job_handle')==handle and row.get('active_processes')==1 and type(row.get('active_processes')) is int and row.get('process_ids')==[baseline],'before/after ownership unresolved')
        all_queries=[before,*[row['job'] for row in observations],after]
        controller_identity=None;previous_held={}
        for row in all_queries:
            need(row.get('verified') is True and unsigned(row.get('job_handle'),64,1) and row['job_handle']==handle and pid(row.get('baseline_pid')) and row['baseline_pid']==baseline and integer(row.get('total_processes'),1) and integer(row.get('terminated_processes')) and integer(row.get('active_processes'),1),'job accounting incomplete')
            need(type(row.get('process_ids')) is list and len(row['process_ids'])==row['active_processes'] and len(set(row['process_ids']))==len(row['process_ids']) and baseline in row['process_ids'] and all(integer(value,1) and value<=0xffffffff for value in row['process_ids']),'job process list incomplete')
            need(row['total_processes']>=row['active_processes'] and row['total_processes']<=0xffffffff and row['terminated_processes']<=row['total_processes'] and row['active_processes']<=4096 and number(row.get('monotonic')) and integer(row.get('wall_unix_ns'),1),'job count/clock invalid')
            held=row.get('held_processes');need(type(held) is list and bool(held),'held process evidence absent')
            need(all(type(p) is dict and pid(p.get('pid')) and unsigned(p.get('creation_filetime'),64,1) and unsigned(p.get('handle_value'),64,1) and type(p.get('observed_exited')) is bool and unsigned(p.get('exit_code'),32) for p in held),'held process types incomplete')
            need(len({(p['pid'],p['creation_filetime']) for p in held})==len(held) and len({p['handle_value'] for p in held})==len(held) and row['total_processes']>=len(held),'duplicate/unaccounted held process identities')
            held_by_birth={(p['pid'],p['creation_filetime']):p for p in held}
            need(previous_held.keys()<=held_by_birth.keys(),'held process history disappeared')
            for key,old in previous_held.items():
                current=held_by_birth[key]
                need(current['handle_value']==old['handle_value'],'held birth changed handle')
                if old['observed_exited']:
                    need(current['observed_exited'] and current['exit_code']==old['exit_code'],'observed process completion regressed')
            previous_held=held_by_birth
            processes=row.get('processes')
            need(type(processes) is list and [p.get('pid') if type(p) is dict else None for p in processes]==row['process_ids'],'active process identities missing or misordered')
            for process in processes:
                process_id,birth,process_handle=owned_identity(process)
                need((process_id,birth) in held_by_birth and held_by_birth[(process_id,birth)]['handle_value']==process_handle,'active identity differs from held birth')
            controller=[p for p in held if p.get('pid')==baseline]
            need(len(controller)==1 and controller[0].get('observed_exited') is False and controller[0].get('exit_code')==259 and integer(controller[0].get('creation_filetime'),1) and integer(controller[0].get('handle_value'),1),'alive controller birth evidence missing')
            current=(controller[0]['creation_filetime'],controller[0]['handle_value'])
            if controller_identity is None:controller_identity=current
            need(current==controller_identity,'controller held birth/handle changed')
        need(all(a['total_processes']<=b['total_processes'] and a['terminated_processes']<=b['terminated_processes'] for a,b in zip(all_queries,all_queries[1:])),'job cumulative accounting regressed')
        need(all(a['monotonic']<=b['monotonic'] for a,b in zip(all_queries,all_queries[1:])),'job query clock order regressed')
        need(before['monotonic']<=start and finish<=after['monotonic'],'job query does not enclose trial interval')
        need(after['total_processes']-before['total_processes']>=51,'known successful driver descendants absent from accounting')
        receipts=self.result_data.get('shutdown_study_observations');need(type(receipts) is list and len(receipts)==2,'two result close receipts missing')
        need([r.get('process') for r in receipts]==['client','reopened'],'close order differs')
        births={};origins_upper=[finish-self.result_data['elapsed_seconds']];origins_lower=[start]
        for index,(name,receipt,command) in enumerate(zip(('client','reopened'),receipts,self.commands)):
            launch,closed=observations[2*index:2*index+2]
            for callback in (launch,closed):
                need(not callback.get('ownership_error') and number(callback.get('monotonic')) and start<=callback['monotonic']<=finish and integer(callback.get('wall_unix_ns'),1),'observer clock/ownership invalid')
                query=callback['job']
                need(query.get('label')=='trial'+str(trial['index'])+'/'+callback['event'],'callback job label differs')
                need(callback['monotonic']<=query['monotonic']<=finish,'callback query clock differs')
            need(launch['job']['monotonic']<=closed['monotonic'],'launch query follows close callback')
            process_id=self.pids[name];need(launch.get('name')==name and launch.get('pid')==process_id and type(launch.get('pid')) is int,'native launch PID/name differs')
            birth=launch.get('native_root_identity');owned_identity(birth);need(birth['pid']==process_id,'owned root PID differs')
            active=[p for p in launch['job']['processes'] if p['pid']==process_id]
            need(not active or same(active[0],birth),'launch root differs from active birth')
            births[name]=birth
            completed=[p for p in after['held_processes'] if p.get('pid')==process_id and p.get('creation_filetime')==birth['creation_filetime'] and p.get('handle_value')==birth['handle_value']]
            need(len(completed)==1 and completed[0].get('observed_exited') is True and type(completed[0].get('exit_code')) is int and completed[0]['exit_code']==0,'owned root exit/birth association absent')
            need(receipt.get('pid')==process_id and type(receipt.get('pid')) is int and type(receipt.get('close_limit_seconds')) is int and receipt['close_limit_seconds']==20 and type(receipt.get('exit_code')) is int and receipt['exit_code']==0 and 'original_close_error' not in receipt,'close PID/exit/limit/error invalid')
            clocks=[receipt.get(field) for field in ('request_before_monotonic','request_returned_monotonic','wait_finished_monotonic')]
            need(all(number(value) for value in clocks) and start<=clocks[0]<=clocks[1]<=clocks[2]<=finish and clocks[2]-clocks[0]<=20,'close observation exceeds original interval/budget')
            need(launch['monotonic']<=clocks[0]<=clocks[2]<=closed['monotonic'],'close precedes launch/observer callback')
            for field in ('request_before_wall_unix_ns','request_returned_wall_unix_ns','wait_finished_wall_unix_ns'):need(integer(receipt.get(field),1),'close wall timestamp missing')
            need(all(field in closed and same(closed[field],value) for field,value in receipt.items()),'close result/callback copy differs')
            origins_upper.extend((launch['monotonic']-command['started_seconds'],clocks[0]))
            origins_lower.extend((closed['monotonic']-self.result_data['elapsed_seconds'],clocks[2]-300))
        need(observations[1]['monotonic']<=observations[2]['monotonic'],'reopened launched before initial close')
        need(observations[1]['job']['monotonic']<=observations[2]['monotonic'],'initial close query follows reopened launch')
        need(max(origins_lower)<=min(origins_upper),'no possible source driver start fits observed clocks')
        need(all(row['started_seconds']<=self.result_data['elapsed_seconds'] for row in self.commands),'command beyond driver elapsed')
        need(all(row['seconds']<=self.result_data['elapsed_seconds'] for row in self.actions) and all(row['finished_seconds']<=self.result_data['elapsed_seconds'] for row in self.ocr),'action/OCR beyond driver elapsed')
        self.details['owned_roots']=births
    def logs(self):
        logs=[]
        for name in ('client.log','reopened.log','ocr-stderr.log','controller-stdout.log','controller-stderr.log'):
            if name not in self.data:continue
            text=self.data[name].decode('utf-8',errors='strict');bad=failed(text);warnings=WARNING.findall(text)
            logs.append(dict(path=name,bytes=len(self.data[name]),sha256=digest(self.data[name]),strict_failure=bad,warning_count=len(warnings)))
            if bad:self.strict_errors.append('native/controller error or leak: '+name)
            if warnings:self.strict_errors.append('strict study warning: '+name)
        self.details['native_logs']=logs
        suffix=json.dumps(self.result_data,indent=2,allow_nan=False)+'\n'
        expected='\n'.join(CAPTURES)+'\n'+suffix
        need('controller-stdout.log' in self.data,'required controller stdout missing')
        need(self.data['controller-stdout.log'] in (expected.encode('utf-8'),expected.replace('\n','\r\n').encode('utf-8')),'controller stdout/result/captures differ')
        if self.data.get('controller-stderr.log'):self.strict_errors.append('nonempty controller stderr')
    def hud_and_subreceipts(self):
        # Validate byte/receipt relationships, not rendered gameplay quality.
        projected={}
        for capture,first,second in (('05-after-fire',1,2),('06-after-reload',3,4),('06e-purchased-smg',6,7),('06f-switched-sidearm',8,9),('06g-switched-primary',10,11),('07d-explicit-resume',14,15)):
            health_text=self.data['ocr-stdout/%03d.log'%first].decode('utf-8');ammo_text=self.data['ocr-stdout/%03d.log'%second].decode('utf-8')
            health=re.search(r'(?<!\d)(\d{1,3})\s*[^A-Z0-9]*HEALTH',health_text.upper());ammo=re.search(r'(\d+)\s*/\s*(\d+)',ammo_text)
            need(health is not None and ammo is not None and 0<int(health[1])<=100 and 'ELIMINATED' not in health_text.upper() and 'SPECTATING' not in health_text.upper(),'invalid retained HUD OCR')
            projected[capture]=dict(health=int(health[1]),ammo=int(ammo[1]),reserve=int(ammo[2]),status_ocr=health_text,ammo_ocr=ammo_text)
        for name,capture in (('fired_hud','05-after-fire'),('reloaded_hud','06-after-reload'),('resumed_hud','07d-explicit-resume')):
            need(same(self.result_data.get(name),projected[capture]),'HUD result differs from raw OCR: '+name)
        for index,words in ((5,('VECTORLINE',)),(12,('SETTINGS',)),(13,('MOUSE',)),(16,('FIELD MENU','LEAVE MATCH'))):
            parser=csv.DictReader(io.StringIO(self.data['ocr-stdout/%03d.log'%index].decode('utf-8')),delimiter='\t')
            names=parser.fieldnames
            need(names is not None and len(names)==len(set(names)) and set(names)>={'text','left','top','width','height','page_num','block_num','par_num','line_num'},'UI OCR header incomplete')
            rows=[row for row in parser if row.get('text','').strip()]
            need(bool(rows),'UI OCR has no recognized words')
            for row in rows:
                need(None not in row,'UI OCR row width differs')
                for field in ('left','top','width','height'):row[field]=int(row[field])//2
            for caption in words:
                if index!=16:need(any(row['text'].upper()==caption for row in rows),'required UI OCR text absent: '+caption)
                else:
                    lines={}
                    for row in rows:
                        identity=tuple(row.get(key) for key in ('page_num','block_num','par_num','line_num'))
                        if all(value not in (None,'') for value in identity):lines.setdefault(identity,[]).append(row)
                    matches=sum([row['text'].upper() for row in sorted(line,key=lambda r:r['left'])]==caption.split() for line in lines.values())
                    need(matches==1,'required UI caption absent/ambiguous: '+caption)
        required={
          'native_reload':('before','started','completed','capture_ready','input_seconds','wall_seconds_after_input','observed_simulation_seconds','completion_watchdog_seconds','whole_flow_deadline_unchanged','after_capture'),
          'native_settings_resume':('paused_before_settings','paused_after_settings','resumed','capture_ready','after_capture','transition_watchdog_seconds','same_living_player_required'),
          'native_focus_recovery':('scope','passed','context_fence','fresh_press','capture_context','held_input_acknowledged','lost','restored_paused','held_neutral_samples','released','fresh_press_movement'),
          'settings_cover_route':('status','scope','requested','start','observations','original_second_live_absolute_deadline','after','endpoint','remaining_original_second_live_budget')}
        for name,fields in required.items():
            row=self.result_data.get(name);need(type(row) is dict and all(field in row for field in fields),'required producer subreceipt missing: '+name)
        need(self.result_data['native_focus_recovery'].get('passed') is True and self.result_data['native_focus_recovery']['context_fence'].get('status')=='LIVING_CONTEXT_PRESERVED_THROUGH_CAPTURE','focus receipt incomplete')
        pauses=self.result_data.get('hud_analysis_pauses');need(type(pauses) is list and bool(pauses),'saved HUD analysis receipts missing')
        names=[row.get('capture') for row in pauses];need(len(names)==len(set(names)) and set(names)<=set(projected),'HUD pause capture identities invalid')
        for row in pauses:
            for field in ('before','paused','after_analysis'):snapshot_shape(row[field])
            need(type(row.get('resume_after_analysis')) is bool,'HUD pause resume state absent')
            if row['resume_after_analysis']:snapshot_shape(row['resumed'])
        snapshot_fields={'native_reload':('before','started','completed','capture_ready','after_capture'),
                         'native_settings_resume':('paused_before_settings','paused_after_settings','resumed','capture_ready','after_capture'),
                         'native_focus_recovery':('held_input_acknowledged','lost','restored_paused','released','fresh_press_movement'),
                         'settings_cover_route':('start','after')}
        for name,fields in snapshot_fields.items():
            for field in fields:snapshot_shape(self.result_data[name][field])
        neutral=self.result_data['native_focus_recovery']['held_neutral_samples'];need(type(neutral) is list and len(neutral)>=3,'held-neutral focus samples incomplete')
        for row in neutral:snapshot_shape(row)
        capture_context=self.result_data['native_focus_recovery']['capture_context']
        for name in ('11a-restored-focus-still-paused','11b-resumed-held-input-neutral','11c-fresh-press-movement'):
            for field in ('before','after'):snapshot_shape(capture_context[name][field])
    def producer_links(self):
        model=ProducerLinks(self)
        for name in ('named_captures','hud_pauses','reload','settings','focus'):
            self.check('producer '+name,getattr(model,name))


class ProducerLinks:
    """Source-emitted receipt predicates and operation links, without native IO.

    A matching envelope is not an independent gameplay/quality qualification.
    Direct untraced status reads are not invented as observed-return actions.
    """
    def __init__(self,evidence):
        self.e=evidence;self.result=evidence.result_data;self.actions=evidence.actions
    def observed(self,label,state,budget=None,cap=None):
        rows=[(index,row) for index,row in enumerate(self.actions)
              if row.get('event')=='offline_observation' and row.get('label')==label]
        need(len(rows)==1 and same(rows[0][1].get('state'),state),'missing/mismatched observed return: '+label)
        index,row=rows[0]
        need(index>=2,'observed return lacks wait actions: '+label)
        begin,completed=self.actions[index-2:index]
        need(begin.get('event')=='wait_begin' and completed.get('event')=='wait_completed' and begin.get('label')==completed.get('label')==label,'observed wait/action order differs: '+label)
        value=begin.get('budget_seconds');need(number(value,0) and value>0,'observed wait budget invalid: '+label)
        if budget is not None:need(type(value) is int and value==budget,'observed source wait budget differs: '+label)
        if cap is not None:need(value<=cap,'observed transition budget exceeds source cap: '+label)
        return index,row
    def capture(self,name,event):
        rows=[(index,row) for index,row in enumerate(self.actions) if row.get('event')==event and row.get('capture')==name]
        need(len(rows)==1,'capture action missing: '+name+'/'+event);return rows[0]
    @staticmethod
    def context(state,baseline,*,phase=None,fields=('id',),ui=False):
        snapshot_shape(state)
        actor=state['local_actor'];original=baseline['local_actor']
        need(state['time_scale']==1 and state['phase']==(baseline['phase'] if phase is None else phase) and
             state['round_number']==baseline['round_number'] and actor['alive'] is True and
             all(same(actor[field],original[field]) for field in fields),'living actor/phase context changed')
        if ui:need(state['ui']['screen']=='game' and state['ui']['focused'] is True,'living UI context changed')
    @staticmethod
    def counters(states,*,fresh_wall=False):
        for before,after in zip(states,states[1:]):
            need(all(after[field]>=before[field] for field in ('wall_msec','simulation_tick','drawn_frames')),'producer snapshot counter regressed')
            if fresh_wall:need(after['wall_msec']>before['wall_msec'],'producer observed return is not fresh')
    def named_captures(self):
        fences=self.result['phase_capture_fences']
        need(type(fences) is dict and set(fences)=={'06c-next-round','10-reopened-loaded-settings'},'named capture transactions missing')
        fields=('acknowledged','ready','before_capture','after_capture_barrier','after_capture')
        labels=('Named living buy phase','Two drawn frames before named capture','Fresh named context immediately before capture','Observation barrier after raw capture','Fresh named context beyond post-capture barrier')
        for name,fence in fences.items():
            need(name in ('06c-next-round','10-reopened-loaded-settings'),'unexpected named capture transaction')
            need(not any(key in fence for key in ('counter_regression','rejected_binding')),'named capture retained failure')
            watchdog=160 if name=='06c-next-round' else 30
            need(type(fence.get('transition_watchdog_seconds')) is int and fence['transition_watchdog_seconds']==watchdog,'named source watchdog differs')
            states=[fence[field] for field in fields];origin=states[0]
            indices=[]
            for state,label in zip(states,labels):
                self.context(state,origin,phase='buy',ui=True)
                need(state['round_number']==fence['expected_round'] and state['local_actor']['id']==fence['expected_actor_id'] and
                     0<state['local_actor']['health']<=100 and state['ui']['paused'] is False and state['ui']['scoreboard_visible'] is False,'named capture lost required living context')
                indices.append(self.observed(label+': '+name,state,cap=watchdog)[0])
            self.counters(states,fresh_wall=True)
            need(all(state['drawn_frames']>=origin['drawn_frames']+2 for state in states[1:]),'named capture lacks two additional drawn frames')
            begin,_=self.capture(name,'capture_begin');end,_=self.capture(name,'capture_end')
            need(indices==sorted(indices) and indices[2]<begin<end<indices[3],'named observation/capture order differs')
    def hud_pauses(self):
        for receipt in self.result['hud_analysis_pauses']:
            name=receipt['capture'];before=receipt['before'];paused=receipt['paused'];after=receipt['after_analysis']
            need(receipt.get('scope')=='ordinary native pause for saved-pixel OCR' and before['ui']['paused'] is False,'HUD pause source transaction differs')
            self.context(before,before,ui=True)
            for state in (paused,after):
                self.context(state,before,fields=('id','weapon','ammo','reserve'))
                need(state['ui']['paused'] is True,'HUD analysis was not paused')
            need(paused['elapsed']==after['elapsed'] and paused['local_actor']['health']==after['local_actor']['health'],'paused HUD gameplay advanced')
            self.counters((before,paused,after))
            need(after['wall_msec']>paused['wall_msec']>before['wall_msec'],'HUD pause observations are stale')
            first,first_action=self.observed('Native pause before saved-HUD OCR: '+name,paused,budget=10)
            last,last_action=self.observed('Fresh paused observation after saved-HUD OCR: '+name,after,budget=5)
            capture_end,_=self.capture(name,'capture_end')
            ocr=[row for row in self.e.ocr if row['label'].startswith(name+':')]
            need(len(ocr)==2 and capture_end<first<last and first_action['seconds']<=ocr[0]['started_seconds']<=ocr[-1]['finished_seconds']<=last_action['seconds'],'HUD OCR does not bind its paused transaction')
            expected=name not in ('06g-switched-primary','07d-explicit-resume')
            need(receipt['resume_after_analysis'] is expected,'HUD resume policy differs from source call')
            if expected:
                resumed=receipt['resumed'];self.context(resumed,before,fields=('id','weapon','ammo','reserve'))
                need(resumed['ui']['paused'] is False,'HUD analysis did not resume')
                self.counters((after,resumed));index,_=self.observed('Explicit native resume after saved-HUD OCR: '+name,resumed,budget=10)
                need(last<index,'HUD resume precedes analysis')
        # The source can read an already-paused HUD without appending a receipt.
        # Only the conditional require_context branch emits its extra fresh read.
    def reload(self):
        receipt=self.result['native_reload'];before=receipt['before'];started=receipt['started'];completed=receipt['completed'];ready=receipt['capture_ready'];after=receipt['after_capture']
        for state in (before,started,completed,ready,after):
            self.context(state,before,phase='live')
            need(state['local_actor']['weapon']=='sidearm','reload weapon differs')
        actor=before['local_actor'];need(0<actor['ammo']<15 and actor['reserve']==60 and actor['reload']==0,'fire acknowledgement differs')
        need(started['local_actor']['reload']>0 and all(started['local_actor'][field]==actor[field] for field in ('ammo','reserve')),'reload start changed ammunition')
        amount=15-actor['ammo']
        for state in (completed,ready,after):
            current=state['local_actor'];need(current['reload']<=0 and current['ammo']==15 and current['reserve']==actor['reserve']-amount,'reload transfer differs')
            need(state['elapsed']-started['elapsed']>=started['local_actor']['reload']-1/60,'reload completed before its countdown')
        need(ready['drawn_frames']>=completed['drawn_frames']+2,'reload capture lacks two rendered frames')
        self.counters((before,started,completed,ready,after))
        need(started['wall_msec']>before['wall_msec'] and completed['wall_msec']>started['wall_msec'] and ready['wall_msec']>completed['wall_msec'],'reload observed return is stale')
        need(type(receipt.get('completion_watchdog_seconds')) is int and receipt['completion_watchdog_seconds']==15 and receipt.get('whole_flow_deadline_unchanged') is True,'reload source constants differ')
        need(same(receipt.get('observed_simulation_seconds'),completed['elapsed']-started['elapsed']) and number(receipt.get('input_seconds')) and number(receipt.get('wall_seconds_after_input')),'reload duration receipt differs')
        labels=('Authoritative depleted sidearm and two drawn frames','Real R input starts authoritative offline reload','Authoritative offline reload completion','Two rendered frames after authoritative reload transfer')
        rows=[self.observed(label,state,budget=budget) for label,state,budget in zip(labels,(before,started,completed,ready),(5,5,15,5))]
        begin05,_=self.capture('05-after-fire','capture_begin');begin06,begin_action=self.capture('06-after-reload','capture_begin')
        need(rows[0][0]<begin05<rows[1][0]<rows[2][0]<rows[3][0]<begin06,'reload operation/capture order differs')
        pause=next((row for row in self.result['hud_analysis_pauses'] if row['capture']=='05-after-fire'),None)
        if pause:self.counters((before,pause['before'],pause.get('resumed',pause['after_analysis']),started))
        need(self.result['fired_hud']['ammo']==actor['ammo'] and self.result['fired_hud']['reserve']==actor['reserve'],'fired HUD differs from authoritative acknowledgement')
        need(self.result['reloaded_hud']['ammo']==15 and self.result['reloaded_hud']['reserve']<self.result['fired_hud']['reserve'] and sum(self.result['reloaded_hud'][key] for key in ('ammo','reserve'))==sum(self.result['fired_hud'][key] for key in ('ammo','reserve')),'rendered reload did not conserve ammunition')
        need(receipt['input_seconds']<=rows[1][1]['seconds'] and rows[3][1]['seconds']<=begin_action['seconds'],'reload relative clock order differs')
    def settings(self):
        receipt=self.result['native_settings_resume'];before=receipt['paused_before_settings'];changed=receipt['paused_after_settings'];resumed=receipt['resumed'];ready=receipt['capture_ready'];after=receipt['after_capture']
        pauses=[row for row in self.result['hud_analysis_pauses'] if CAPTURES.index(row['capture'])<CAPTURES.index('07-field-menu')]
        need(bool(pauses) and same(before,pauses[-1]['after_analysis']),'settings did not inherit the retained paused transaction')
        for state in (before,changed,resumed,ready,after):self.context(state,before,fields=('id','weapon','ammo','reserve'),ui=True)
        need(before['ui']['paused'] is True and changed['ui']['paused'] is True and resumed['ui']['paused'] is False and ready['ui']['paused'] is False,'settings pause/resume transaction differs')
        need(before['elapsed']==changed['elapsed'] and before['local_actor']['health']==changed['local_actor']['health'],'settings pause advanced gameplay')
        self.counters((before,changed,resumed,ready,after))
        need(changed['wall_msec']>before['wall_msec'] and resumed['wall_msec']>changed['wall_msec'] and ready['wall_msec']>resumed['wall_msec'] and ready['drawn_frames']>=resumed['drawn_frames']+2,'settings resume observations are stale')
        need(type(receipt.get('transition_watchdog_seconds')) is int and receipt['transition_watchdog_seconds']==10 and receipt.get('same_living_player_required') is True,'settings source constants differ')
        a,_=self.observed('Fresh paused player after native settings change',changed,budget=5)
        b,_=self.observed('Actual living player explicitly resumes after field settings',resumed,cap=10)
        c,_=self.observed('Two drawn frames after explicit native settings resume',ready,cap=10)
        end,_=self.capture('07c-settings-changed','capture_end');begin,_=self.capture('07d-explicit-resume','capture_begin')
        need(end<a<b<c<begin,'settings source operation order differs')
        # after_capture deliberately has no universal pausedFalse requirement.
    def focus(self):
        from native_focus_fence import FocusContextFence
        receipt=self.result['native_focus_recovery'];context=receipt['context_fence'];capture=receipt['capture_context']
        need(not any(key in context for key in ('precondition_loss',)) and context.get('status')=='LIVING_CONTEXT_PRESERVED_THROUGH_CAPTURE','focus precondition failed')
        try:
            snapshot_shape(context['baseline'])
            fence=FocusContextFence(context['baseline'],{})
            held=receipt['held_input_acknowledged'];lost=receipt['lost'];restored=receipt['restored_paused']
            for state,focused,paused in ((held,True,False),(lost,False,True),(restored,True,True)):
                snapshot_shape(state);fence.require(state,'retained producer link',focused=focused,paused=paused)
            need(held['local_input']['fire'] is True and held['local_input']['move']!=[0,0] and restored['ui']['mouse_mode']==0,'focus held input/restored pointer differs')
            need(same(capture['11a-restored-focus-still-paused']['before'],restored),'restored capture copy differs')
            fence.require(capture['11a-restored-focus-still-paused']['after'],'restored capture',focused=True,paused=True)
            neutral=receipt['held_neutral_samples'];original=restored['local_actor']
            for state in neutral:
                snapshot_shape(state);fence.require(state,'held-neutral sample',focused=True,paused=False)
                actor=state['local_actor'];inputs=state['local_input']
                need(inputs['move']==[0,0] and all(inputs[field] is False for field in ('fire','interact','reload')) and all(actor[field]==original[field] for field in ('ammo','weapon')) and abs(actor['yaw']-original['yaw'])<=.000001 and abs(actor['pitch']-original['pitch'])<=.000001,'held input altered living player')
            need(all(abs(neutral[-3]['local_actor']['velocity'][axis])<=.01 for axis in (0,2)) and all(row['local_actor']['position']==neutral[-3]['local_actor']['position'] for row in neutral[-2:]),'held-input endpoint did not settle')
            need(neutral[-3]['elapsed']-neutral[0]['elapsed']<=1,'held-input inertia exceeded source bound')
            need(same(capture['11b-resumed-held-input-neutral']['before'],neutral[-1]),'neutral capture copy differs')
            fence.require(capture['11b-resumed-held-input-neutral']['after'],'neutral capture',focused=True,paused=False)
            released=receipt['released'];fresh=receipt['fresh_press']
            fence.require(released,'released controls',focused=True,paused=False)
            need(released['ui']['waiting_for_input_release'] is False and released['local_input']['move']==[0,0] and released['local_input']['fire'] is False,'focus controls not released')
            need(same(fresh.get('released'),released) and fresh.get('key_down_dispatched') is True and fresh.get('status')=='LIVING_MOVEMENT_OBSERVED','fresh press source receipt differs')
            before=fresh['before_key'];moved=fresh['moved'];snapshot_shape(before);snapshot_shape(moved)
            fence.require(before,'before fresh key',focused=True,paused=False,released=True);fence.require(moved,'fresh movement',focused=True,paused=False)
            need(moved['local_input']['move']!=[0,0] and moved['simulation_tick']>before['simulation_tick'] and moved['local_actor']['position']!=before['local_actor']['position'],'fresh press movement absent')
            need(same(fresh.get('last_after_key'),moved) and same(receipt['fresh_press_movement'],moved) and same(capture['11c-fresh-press-movement']['before'],moved),'fresh movement copies differ')
            after=capture['11c-fresh-press-movement']['after'];fence.require(after,'fresh movement capture',focused=True,paused=False)
            need(same(context.get('last_valid_state'),after),'final focus context differs')
        except RuntimeError as error:raise ValueError('focus source context: '+str(error)) from error
        labels=[('Fresh stock match reaches a living active player before native focus loss',context['baseline'],60),('Game consumed physical W and LMB before native focus loss',held,10),('Native focus loss pauses actual offline match',lost,10),('Actual game observes restored focus',restored,10)]
        for label,state,budget in labels:self.observed(label,state,budget=budget)
        self.observed('Explicit resume with W and LMB still physically held',neutral[0],budget=10)
        for index,state in enumerate(neutral[1:]):
            label=('Neutral held input while ordinary inertia settles' if index<len(neutral)-3 else 'Fresh held-input guard sample '+str(index-(len(neutral)-3)+1))
            self.observed(label,state,budget=10)
        self.observed('Released held focus-test controls',released,budget=10)
        self.observed('Fresh W press moves actual player after focus recovery',moved,budget=10)


def same(left,right):
    if type(left) is not type(right):return False
    if isinstance(left,dict):return set(left)==set(right) and all(same(left[key],right[key]) for key in left)
    if isinstance(left,list):return len(left)==len(right) and all(same(a,b) for a,b in zip(left,right))
    return left==right


def validate_trial(directory,*,context=None,leak_parser=None):
    evidence=Evidence(directory,context)
    evidence.result_data={};evidence.commands=[];evidence.actions=[];evidence.ocr=[];evidence.identity={};evidence.trial={};evidence.pids={}
    evidence.check('inventory',evidence.files)
    for name in ('result','captures','ocr_records','source_and_commands','traces_and_profile','process_and_closes','logs','hud_and_subreceipts','producer_links'):
        evidence.check(name,getattr(evidence,name))
    if leak_parser is not None:
        evidence.details['typed_leak_observations']=[]
        for name in ('client.log','reopened.log'):
            if name in evidence.data:
                evidence.check('typed leak rows/'+name,lambda name=name:evidence.details['typed_leak_observations'].append(dict(path=name,**leak_parser(evidence.data[name]))))
    complete=not evidence.errors
    return dict(schema=1,scope='Retained producer evidence envelope only; independent gameplay/native qualification required',
                availability=dict(required_files=len(REQUIRED),present_required_files=sum(name in evidence.data for name in REQUIRED),baseline_files=len(BASE_REQUIRED)),
                evidence_complete=complete,strict_passed=complete and not evidence.strict_errors,
                evidence_errors=evidence.errors,strict_errors=evidence.strict_errors,
                independent_qualification='UNREVIEWED',all_files=evidence.records,
                extra_files=[row['path'] for row in evidence.records if row['path'] not in REQUIRED],
                result=evidence.result_data,close_observations=evidence.result_data.get('shutdown_study_observations',[]),
                original_stream_retention_complete=complete,**evidence.details)
