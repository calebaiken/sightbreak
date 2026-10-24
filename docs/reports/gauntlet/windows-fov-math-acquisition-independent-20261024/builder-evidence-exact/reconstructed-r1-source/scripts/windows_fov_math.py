"""Source-prepared one-attempt Windows isolated math acquisition.

No import-time OS/API/process action. Public collect remains blocked until the
complete-original artifact envelope has an independently admitted finite proof.
Pure injected models exercise the proposed supervisor; they prove no Windows API.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import time
import zipfile

import fov_math_reference as reference
from native_log import failed

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'tools/fov_math_reference/'
MEMBER = 'Godot_v4.7.2-stable_win64.exe'
SDK_URL = 'https://github.com/godotengine/godot/releases/download/4.7.2-stable/' + MEMBER + '.zip'
SDK_BYTES = 86013866
SDK_SHA512 = '83decd58fdf67b9d657958a1ae6bf1929c20785315a81effe245874cdc57acb709bf868e00778a96984338c1b29dafdb453c6847747694621c6ecf5da2259993'
SDK_SHA256 = '731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953'
WHOLE = 60.
FAILURE_CLEANUP = 5.
MIB = 1024 * 1024
LIMITS = {'stdout': 8*MIB, 'stderr': MIB}
USER_LIMIT = 8*MIB
MAX_USER_FILES = 64
MAX_EVENTS = 128
RECEIPT_LIMIT = MIB
INNER_LIMIT = 16*MIB
DELIVERED_LIMIT = 32*MIB
MAX_ARCHIVES = 2
MAX_NAME = 240
# Complete arbitrary Godot failure-file bytes are not bounded by the fixed corpus.
# A bounded prefix is useful failure evidence but cannot discharge that contract.
ARTIFACT_PROOF = False
SOURCE_FILES = (
    'scripts/windows_fov_math.py', 'scripts/fov_math_reference.py', 'scripts/native_log.py',
    '.github/workflows/windows-fov-math.yml',
    *(PROJECT + name for name in ('project.godot','reference.gd','cases.json',reference.BINARY_CASES_NAME)),
)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path, algorithm='sha256', *, deadline=None, clock=time.monotonic):
    value = hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        while True:
            require(deadline is None or clock() < deadline, 'hash deadline expired')
            block = stream.read(65536)
            if not block:
                return value.hexdigest()
            value.update(block)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def write_json(path, value, cap=RECEIPT_LIMIT):
    raw = encoded(value)
    require(len(raw) <= cap, 'receipt exceeds declared limit')
    Path(path).write_bytes(raw)


def source_binding(root, manifest, expected_manifest, expected_head, *, deadline, clock=time.monotonic):
    """Bind direct materialized bytes, not Git object bytes/status flags.

    The external release pins both detached checkout HEAD and manifest SHA. The
    manifest is produced AFTER source freeze and is intentionally outside itself.
    No Git helper subprocess is started in the owned job.
    """
    root, manifest = Path(root), Path(manifest)
    require(re.fullmatch('[0-9a-f]{40}',expected_head) is not None, 'exact source SHA required')
    require(re.fullmatch('[0-9a-f]{64}',expected_manifest) is not None, 'manifest digest required')
    dotgit = root/'.git'
    if dotgit.is_file():
        value = dotgit.read_text().strip()
        require(value.startswith('gitdir: '), 'invalid worktree gitdir')
        gitdir = (root/value[8:]).resolve()
    else:
        gitdir = dotgit
    require((gitdir/'HEAD').read_text().strip() == expected_head, 'detached exact checkout required')
    require(digest(manifest,deadline=deadline,clock=clock)==expected_manifest, 'source manifest mismatch')
    record = json.loads(manifest.read_bytes())
    require(type(record) is dict and set(record)=={'schema','source_commit','files'} and record['schema']==1, 'source manifest schema')
    require(record['source_commit']==expected_head, 'source manifest commit mismatch')
    require(type(record['files']) is dict and set(record['files'])==set(SOURCE_FILES), 'source manifest coverage')
    result = {}
    for name in SOURCE_FILES:
        require(clock()<deadline, 'source binding deadline expired')
        entry=record['files'][name]
        require(type(entry) is dict and set(entry)=={'sha256','bytes'} and type(entry['bytes']) is int and entry['bytes']>=0, 'source member schema')
        path=root/name
        require(path.is_file() and not path.is_symlink() and root.resolve() in path.resolve().parents, 'source member missing or redirected')
        require(path.stat().st_size==entry['bytes'] and digest(path,deadline=deadline,clock=clock)==entry['sha256'], 'materialized source mismatch: '+name)
        result[name]=dict(entry)
    return dict(source_commit=expected_head,manifest_sha256=expected_manifest,files=result)


def sdk_member(archive, target, *, deadline, clock=time.monotonic):
    """Authenticate archive and extract only the direct GUI member; never run it."""
    archive,target=Path(archive),Path(target)
    require(not target.exists() and target.is_absolute(), 'SDK target must be absolute and absent')
    require(archive.stat().st_size==SDK_BYTES, 'SDK archive size mismatch')
    require(digest(archive,'sha512',deadline=deadline,clock=clock)==SDK_SHA512 and digest(archive,deadline=deadline,clock=clock)==SDK_SHA256, 'SDK archive digest mismatch')
    with zipfile.ZipFile(archive) as bundle:
        members=[m for m in bundle.infolist() if m.filename==MEMBER]
        require(len(members)==1 and not members[0].is_dir(), 'direct GUI member missing/duplicate')
        info=members[0]
        require(0 < info.file_size <= 256*MIB and not info.flag_bits & 1 and (info.external_attr>>16)&0o170000 != 0o120000, 'SDK GUI member invalid')
        target.mkdir(parents=True)
        path=target/MEMBER
        with bundle.open(info) as source, path.open('xb') as dest:
            count=0
            while True:
                require(clock()<deadline, 'SDK extraction deadline expired')
                block=source.read(65536)
                if not block:break
                count+=len(block);require(count<=info.file_size, 'SDK extraction size overflow');dest.write(block)
        require(count==info.file_size, 'SDK member short read')
    with path.open('rb') as stream:
        header=stream.read(4096)
    pe_gui(header)
    return path, dict(url=SDK_URL,archive_bytes=SDK_BYTES,archive_sha512=SDK_SHA512,archive_sha256=SDK_SHA256,
                      member=MEMBER,member_bytes=count,member_sha256=digest(path,deadline=deadline,clock=clock),
                      provenance='member measured from authenticated archive; no independent SDK reparse')


def pe_gui(header):
    require(len(header)>=64 and header[:2]==b'MZ', 'SDK DOS header')
    offset=struct.unpack_from('<I',header,60)[0]
    require(offset+94<=len(header) and header[offset:offset+4]==b'PE\0\0', 'SDK PE header')
    require(struct.unpack_from('<H',header,offset+4)[0]==0x8664, 'SDK AMD64 required')
    require(struct.unpack_from('<H',header,offset+24)[0]==0x20b, 'SDK PE32+ required')
    require(struct.unpack_from('<H',header,offset+24+68)[0]==2, 'direct GUI subsystem required')


class WindowsJob:
    """Explicit outer job + retained Popen HANDLE, no systemwide enumeration.

    No API is loaded until construction on an admitted Windows execution. The
    controller-containing KILL_ON_JOB_CLOSE handle intentionally lives until OS
    process teardown; explicitly closing it here would kill our own controller.
    """
    _keep_jobs=[]

    def __init__(self):
        require(sys.platform=='win32' and sys.version_info[:3]==(3,12,10), 'exact Windows CPython3.12.10 required')
        self.k=C.WinDLL('kernel32',use_last_error=True)
        signatures={
            'CreateJobObjectW':([C.c_void_p,C.c_wchar_p],C.c_void_p),
            'SetInformationJobObject':([C.c_void_p,C.c_int,C.c_void_p,C.c_uint32],C.c_int),
            'AssignProcessToJobObject':([C.c_void_p,C.c_void_p],C.c_int),
            'QueryInformationJobObject':([C.c_void_p,C.c_int,C.c_void_p,C.c_uint32,C.c_void_p],C.c_int),
            'GetCurrentProcess':([],C.c_void_p),'GetCurrentProcessId':([],C.c_uint32),
            'GetProcessId':([C.c_void_p],C.c_uint32),
            'GetProcessTimes':([C.c_void_p,*([C.c_void_p]*4)],C.c_int),
            'WaitForSingleObject':([C.c_void_p,C.c_uint32],C.c_uint32),
            'GetExitCodeProcess':([C.c_void_p,C.c_void_p],C.c_int),
            'IsProcessInJob':([C.c_void_p,C.c_void_p,C.c_void_p],C.c_int),
            'OpenProcess':([C.c_uint32,C.c_int,C.c_uint32],C.c_void_p),
            'TerminateProcess':([C.c_void_p,C.c_uint32],C.c_int),
            'CloseHandle':([C.c_void_p],C.c_int),
        }
        for name,(args,result) in signatures.items():
            function=getattr(self.k,name);function.argtypes=args;function.restype=result
        self.pid=int(self.k.GetCurrentProcessId())
        self.handles={};self.owned_handles=[]
        self.job=self.k.CreateJobObjectW(None,None)
        self.ok(self.job,'create outer job')
        # JOBOBJECT_EXTENDED_LIMIT_INFORMATION is144 bytes on AMD64.
        # LimitFlags offset16, only JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
        require(C.sizeof(C.c_void_p)==8, 'AMD64 controller required')
        limits=C.create_string_buffer(144);struct.pack_into('<I',limits,16,0x2000)
        try:
            self.ok(self.k.SetInformationJobObject(self.job,9,limits,len(limits)), 'set outer job limits')
            self.ok(self.k.AssignProcessToJobObject(self.job,self.k.GetCurrentProcess()), 'assign controller outer job')
        except BaseException:
            self.k.CloseHandle(self.job);raise
        self._keep_jobs.append(self.job)
        self.baseline=self.sample()
        require(self.baseline['total']==1 and self.baseline['active']==1 and self.baseline['ids']==[self.pid], 'outer job baseline is not controller-only')
        self.controller=self.identity(self.k.GetCurrentProcess())

    @staticmethod
    def ok(value,label):
        if not value:raise OSError(C.get_last_error(),label)
        return value

    def identity(self,handle):
        pid=int(self.k.GetProcessId(handle));self.ok(pid,'GetProcessId held handle')
        times=[C.c_uint64() for _ in range(4)]
        self.ok(self.k.GetProcessTimes(handle,*[C.byref(v) for v in times]), 'GetProcessTimes held handle')
        status=int(self.k.WaitForSingleObject(handle,0))
        require(status in (0,258), 'held process wait failed')
        code=C.c_uint32();self.ok(self.k.GetExitCodeProcess(handle,C.byref(code)), 'GetExitCodeProcess held handle')
        return dict(pid=pid,birth=times[0].value,exit_time=times[1].value,exited=status==0,exit_code=code.value)

    def bind(self,process):
        handle=int(process._handle)  # Popen-owned HANDLE, never reopened by PID.
        identity=self.identity(handle)
        require(identity['pid']==process.pid and identity['birth']>0, 'Popen held root identity mismatch')
        inside=C.c_int();self.ok(self.k.IsProcessInJob(handle,self.job,C.byref(inside)), 'root explicit outer membership')
        require(inside.value==1, 'root not in inherited outer job')
        self.handles[process.pid]=(handle,identity['birth'])
        return identity

    def root(self,process):
        value=self.identity(int(process._handle))
        entry=self.handles.get(process.pid)
        require(entry is not None and (value['pid'],value['birth'])==(process.pid,entry[1]), 'held root birth changed')
        return value

    def sample(self):
        def account():
            raw=C.create_string_buffer(48)
            self.ok(self.k.QueryInformationJobObject(self.job,1,raw,len(raw),None), 'outer accounting query')
            faults,total,active,terminated=struct.unpack_from('<IIII',raw,32)
            return dict(total=total,active=active,terminated=terminated,page_faults=faults)
        before=account()
        raw=C.create_string_buffer(8+64*8)
        self.ok(self.k.QueryInformationJobObject(self.job,3,raw,len(raw),None), 'outer process ID list query')
        assigned,count=struct.unpack_from('<II',raw)
        require(assigned==count and count<=64, 'outer process list incomplete')
        ids=list(struct.unpack_from('<'+'Q'*count,raw,8))
        after=account()
        require(before['total']==after['total'] and before['active']==after['active']==count and len(set(ids))==count, 'racing/inconsistent outer accounting')
        return dict(after,ids=sorted(ids))

    def hold_unexpected(self,pid):
        require(pid!=self.pid, 'never open/terminate baseline controller')
        if pid not in self.handles:
            handle=self.ok(self.k.OpenProcess(0x00100000|0x1000|0x0001,False,pid), 'open owned unexpected handle')
            self.owned_handles.append(handle)
            identity=self.identity(handle)
            inside=C.c_int();self.ok(self.k.IsProcessInJob(handle,self.job,C.byref(inside)), 'unexpected membership')
            require(identity['pid']==pid and inside.value, 'unexpected owned identity mismatch')
            self.handles[pid]=(handle,identity['birth'])
        return self.identity(self.handles[pid][0])

    def terminate(self,pid):
        require(pid!=self.pid and pid in self.handles, 'unheld or baseline process termination forbidden')
        handle,birth=self.handles[pid]
        identity=self.identity(handle)
        require(identity['pid']==pid and identity['birth']==birth, 'termination held identity mismatch')
        if not identity['exited']:self.ok(self.k.TerminateProcess(handle,1), 'terminate held owned process')

    def close_held(self):
        for handle in self.owned_handles:self.ok(self.k.CloseHandle(handle), 'close owned identity handle')
        self.owned_handles=[]  # Popen owns root handle; outer job remains held.


class PipeRetention:
    """Raw Windows3.12 nonblocking pipes, with no selector/thread assumption."""
    def __init__(self,out,*,read=os.read,set_blocking=os.set_blocking):
        self.read,self.set_blocking=read,set_blocking
        self.files={name:(Path(out)/(name+'.log')).open('xb') for name in LIMITS}
        self.pipes={};self.nonblocking=set();self.counts={name:0 for name in LIMITS}
        self.retained=dict(self.counts);self.eof={name:False for name in LIMITS};self.errors={}

    def attach(self,process):
        self.pipes={name:getattr(process,name) for name in LIMITS}
        for name,pipe in self.pipes.items():
            try:self.set_blocking(pipe.fileno(),False);self.nonblocking.add(name)
            except BaseException as error:
                self.errors[name]=type(error).__name__+': '+str(error)[:512]
                raise

    def poll(self,deadline,clock=time.monotonic):
        for name in LIMITS:
            if self.eof[name] or name not in self.nonblocking:continue
            for _ in range(4):
                require(clock()<deadline,'pipe read deadline expired')
                try:data=self.read(self.pipes[name].fileno(),65536)
                except BlockingIOError:break
                if not data:self.eof[name]=True;break
                self.counts[name]+=len(data)
                data=data[:max(0,LIMITS[name]-self.retained[name])]
                self.files[name].write(data);self.retained[name]+=len(data)
        return any(self.counts[name]>LIMITS[name] for name in LIMITS)

    def state(self):
        truncated={name:self.counts[name]>self.retained[name] for name in LIMITS}
        return dict(observed_bytes=dict(self.counts),retained_bytes=dict(self.retained),eof=dict(self.eof),
                    truncated=truncated,attachment_errors=dict(self.errors),
                    complete=all(self.eof.values()) and not any(truncated.values()) and not self.errors)

    def close(self):
        for file in self.files.values():file.close()
        for pipe in self.pipes.values():
            if not pipe.closed:pipe.close()


class Audit:
    def __init__(self,job,process):
        self.job,self.process=job,process;self.events=[];self.samples=0;self.last=None
        self.root_identity=None;self.overflow=False

    def observe(self):
        sample=self.job.sample();self.samples+=1;self.last=sample
        if not self.events or any(sample[key]!=self.events[-1][key] for key in ('total','active','terminated','ids')):
            require(len(self.events)<MAX_EVENTS,'owned accounting event cap exceeded')
            self.events.append(sample)
        # Bind every listed unexpected identity before rejecting, for safety cleanup.
        extra=[pid for pid in sample['ids'] if pid not in (self.job.pid,self.process.pid)]
        for pid in extra:self.job.hold_unexpected(pid)
        require(not extra and sample['total']==2 and self.job.pid in sample['ids'], 'unexpected owned process/count')
        self.root_identity=self.job.root(self.process)
        expected=[self.job.pid] if self.root_identity['exited'] else sorted([self.job.pid,self.process.pid])
        require(sample['ids']==expected and sample['active']==len(expected), 'root handle/job list disagree')
        return self.root_identity

    def receipt(self):
        return dict(samples=self.samples,transitions=self.events,last=self.last,root=self.root_identity)


def supervise(process,job,streams,deadline,*,clock=time.monotonic,sleep=time.sleep):
    """Fixed absolute deadline through observed completion and EOF."""
    audit=Audit(job,process)
    # Stream sinks already exist; attach must precede any native identity query.
    streams.attach(process)
    job.bind(process)
    while True:
        require(clock()<deadline,'whole acquisition deadline expired')
        overflow=streams.poll(deadline,clock)
        root=audit.observe()
        require(not overflow,'native stream overflow')
        if root['exited'] and all(streams.eof.values()):
            code=process.wait(timeout=max(0,deadline-clock()))
            require(code==root['exit_code'],'Popen/held exit code disagree')
            require(clock()<deadline,'completion observation late')
            return dict(exit_code=code,completion_observed=clock(),audit=audit.receipt())
        sleep(min(.01,max(0,deadline-clock())))


def safety_cleanup(process,job,streams,deadline,*,clock=time.monotonic,sleep=time.sleep):
    """Failure-only bounded safety cleanup; never changes failed status."""
    result=dict(passed=False,terminated=[],errors=[],accounting=[],root=None)
    while clock()<deadline:
        try:
            sample=job.sample()
            if len(result['accounting'])<MAX_EVENTS and (not result['accounting'] or sample!=result['accounting'][-1]):result['accounting'].append(sample)
            for pid in sample['ids']:
                if pid==job.pid:continue
                if pid!=process.pid:job.hold_unexpected(pid)
                if pid==process.pid and pid not in job.handles:job.bind(process)
                job.terminate(pid)
                if pid not in result['terminated']:result['terminated'].append(pid)
            # Popen handle remains safety-owned even if job queries/initial bind fail.
            if process.poll() is None:process.kill();result['popen_safety_kill']=True
            root=job.root(process);result['root']=root
            if streams is not None:streams.poll(deadline,clock)
            if root['exited'] and sample['ids']==[job.pid] and sample['active']==1:
                process.wait(timeout=max(0,deadline-clock()))
                result['passed']=True
                if streams is None or all(streams.eof.values()):break
        except BaseException as error:
            if len(result['errors'])<16:result['errors'].append(type(error).__name__+': '+str(error)[:512])
            try:
                if process.poll() is None:process.kill();result['popen_safety_kill']=True
                process.wait(timeout=max(0,min(.02,deadline-clock())))
            except BaseException:pass
            if streams is not None:
                try:streams.poll(deadline,clock)
                except BaseException:pass
        sleep(min(.01,max(0,deadline-clock())))
    # Final unconditional accounting, including any observation/cleanup failures.
    try:
        sample=job.sample();result['final']=sample
        root=job.root(process);result['root']=root
        result['passed']=result['passed'] and root['exited'] and sample['ids']==[job.pid] and sample['active']==1
    except BaseException as error:result['passed']=False;result['errors'].append(type(error).__name__+': '+str(error)[:512])
    result['finished']=clock()
    return result


def execute_prepared(engine,target,output,payload,deadline,*,clock=time.monotonic,sleep=time.sleep,
                     process_factory=subprocess.Popen,job_factory=WindowsJob,stream_factory=PipeRetention):
    """Proposed one-child integration, injected in pure tests; public gate blocked.

    Caller must have authenticated engine, copied/bound exact source/input and
    isolated output. Every post-spawn path retains streams and owned accounting.
    """
    result=dict(passed=False,native_invocations=0,spawn_attempts=0,popen_returned=False)
    process=job=streams=None
    started=clock()
    try:
        require(clock()<deadline,'preparation deadline expired')
        reference.validate_binary_cases(payload)
        require(Path(engine).name==MEMBER,'only direct GUI engine allowed')
        command=[str(engine),'--headless','--path',str(target),'--script',str(Path(target)/'reference.gd'),'--',
                 '--cases='+str(Path(target)/reference.BINARY_CASES_NAME),
                 '--expected-cases-sha256='+reference.sha((Path(target)/reference.BINARY_CASES_NAME).read_bytes())]
        isolated={name:str(Path(output)/'user'/part) for name,part in [('APPDATA','roaming'),('LOCALAPPDATA','local')]}
        for path in isolated.values():Path(path).mkdir(parents=True,exist_ok=False)
        env=os.environ.copy();env.update(isolated)
        result.update(command=command,isolated_user_paths=isolated)
        streams=stream_factory(output)  # All retention sinks before first spawn.
        job=job_factory()
        result['controller_identity']=job.controller
        result['baseline']=job.baseline
        require(clock()<deadline,'prelaunch deadline expired')
        result['spawn_attempts']=1
        result['native_invocations']=None  # Failed Popen may not prove whether CreateProcess ran.
        process=process_factory(command,executable=str(engine),cwd=target,env=env,
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.DEVNULL,
                                close_fds=True,bufsize=0,creationflags=0)
        result.update(popen_pid=process.pid,popen_returned=True,native_invocations=1)
        result.update(supervise(process,job,streams,deadline,clock=clock,sleep=sleep))
        require(result['exit_code']==0,'native process failed')
        # Final ordinary cleanup/accounting is inside the original whole deadline.
        final=job.sample();root=job.root(process)
        result['ordinary_cleanup']=dict(accounting=final,root=root)
        require(final['ids']==[job.pid] and final['active']==1 and final['total']==2 and root['exited'], 'ordinary cleanup/accounting incomplete')
        require(streams.state()['complete'],'incomplete native stream coverage')
        for stream in streams.files.values():stream.flush()
        stdout=(Path(output)/'stdout.log').read_bytes();stderr=(Path(output)/'stderr.log').read_bytes()
        require(not stderr and not failed(stdout.decode('utf-8',errors='strict')),'strict native log failure')
        result['math']=reference.parse_binary_output(stdout,payload,
            cases_sha256=reference.sha((Path(target)/reference.BINARY_CASES_NAME).read_bytes()),
            program_sha256=digest(Path(target)/'reference.gd',deadline=deadline,clock=clock))
        require(clock()<deadline,'native parse/cleanup exceeded whole deadline')
        result['passed']=True
    except BaseException as error:
        result.update(passed=False,error_type=type(error).__name__,error=str(error)[:4096])
    finally:
        if process is not None:
            # Always retain final accounting, even if attach/bind/monitor failed.
            if not result['passed']:
                try:result['failure_cleanup']=safety_cleanup(process,job,streams,clock()+FAILURE_CLEANUP,clock=clock,sleep=sleep)
                except BaseException as error:result['cleanup_error']=type(error).__name__+': '+str(error)[:4096]
            else:
                try:
                    result['final_accounting']=job.sample();result['final_root']=job.root(process)
                    require(result['final_accounting']['total']==2 and result['final_accounting']['ids']==[job.pid] and result['final_root']['exited'], 'final owned state changed')
                except BaseException as error:
                    result.update(passed=False,final_audit_error=str(error)[:4096])
                    try:result['failure_cleanup']=safety_cleanup(process,job,streams,clock()+FAILURE_CLEANUP,clock=clock,sleep=sleep)
                    except BaseException as stop_error:result['cleanup_error']=str(stop_error)[:4096]
        if streams is not None:
            result['streams']=streams.state()
            if not result['streams']['complete']:result['passed']=False
            streams.close()
        if job is not None:
            try:job.close_held()
            except BaseException as error:result.update(passed=False,handle_close_error=str(error)[:4096])
        result['finished']=clock();result['elapsed']=result['finished']-started
        if result['passed'] and result['finished']>=deadline:result.update(passed=False,error='whole deadline expired before final return')
    return result


def artifact_preflight(source_bytes):
    """Finite retained-prefix envelope; full-original admission stays blocked."""
    # A:9MiB streams + source/project inputs +1MiB receipt +1MiB index/error.
    # B:8MiB user retention +1MiB inventory. Each ZIP adds <=1MiB fixed headers.
    a=sum(LIMITS.values())+source_bytes+2*MIB+MIB
    b=USER_LIMIT+MIB+MIB
    return dict(status='BLOCKED',execution_admitted=False,complete_original_proof=ARTIFACT_PROOF,
                reason='Godot failure userfiles/logs have no source-proved finite byte ceiling; prefixes are incomplete originals',
                retained_prefix_upper_bounds=[a,b],inner_limit=INNER_LIMIT,delivered_limit=DELIVERED_LIMIT,
                maximum_archives=MAX_ARCHIVES,prefix_envelope_fits=a<=INNER_LIMIT and b<=INNER_LIMIT,
                outer_wrapper_proof='UNRESOLVED; actual pinned uploader overhead must be bounded before admission')


def collect(output,archive,manifest,expected_manifest,expected_head,*,root=ROOT,clock=time.monotonic):
    """Public entry currently rejects before SDK/API/Popen due missing proof."""
    started=clock();deadline=started+WHOLE;output=Path(output)
    require(output.is_absolute() and not output.exists() and root.resolve() not in output.resolve().parents, 'absolute absent outside-source output required')
    output.mkdir(parents=True)
    report=dict(passed=False,native_invocations=0,scope='isolated exact native math only',started=started,deadline=deadline)
    try:
        report['source']=source_binding(root,manifest,expected_manifest,expected_head,deadline=deadline,clock=clock)
        report['preflight']=artifact_preflight(sum(v['bytes'] for v in report['source']['files'].values()))
        require(report['preflight']['execution_admitted'],'artifact feasibility BLOCKED before native preparation')
        # No public path to a Windows API, SDK extraction or engine while blocked.
        raise AssertionError('admission implementation requires separate reviewed source amendment')
    except BaseException as error:report.update(error_type=type(error).__name__,error=str(error)[:4096])
    # No engine was reached; retain the complete generated preflight failure.
    # Runtime acquisition originals remain unproduced/unqualified.
    report['finished']=clock();report['elapsed']=report['finished']-started
    report['evidence_complete']=True
    report['evidence_files']={}
    if Path(manifest).is_file() and Path(manifest).stat().st_size<=MIB:
        shutil.copyfile(manifest,output/'source-manifest.json')
        report['evidence_files']['source-manifest.json']=dict(bytes=(output/'source-manifest.json').stat().st_size,sha256=digest(output/'source-manifest.json'))
    else:
        report['evidence_complete']=False
        report['manifest_retention']='missing or exceeds declared1MiB original cap'
    write_json(output/'receipt.json',report)
    return report


def package(root,destination):
    """Lossless deterministic TWO-archive package of a COMPLETE declared tree.

    Never packages a partial/truncated original as complete. No SDK inputs,
    symlinks, unknown files, compression-size assumptions or omission routes.
    """
    root,destination=Path(root),Path(destination)
    require(not destination.exists(),'absent package destination required')
    receipt=json.loads((root/'receipt.json').read_bytes())
    require(receipt.get('evidence_complete') is True,'incomplete evidence cannot be packaged as originals')
    expected=receipt.get('evidence_files')
    require(type(expected) is dict and 0<len(expected)<=128,'package inventory schema/count')
    files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())
    require(set(files)==set(expected)|{'receipt.json'},'missing/unexpected declared evidence')
    groups=[[],[]]
    for name in files:
        path=root/name
        require(len(name.encode())<=MAX_NAME and not path.is_symlink() and '..' not in PurePosixPath(name).parts,'package member path')
        if name!='receipt.json':
            record=expected[name]
            require(record==dict(bytes=path.stat().st_size,sha256=digest(path)),'package original mismatch')
        groups[int(name.startswith('user/'))].append(name)
    for group in groups:
        bound=sum((root/name).stat().st_size+76+2*len(name.encode()) for name in group)+22
        require(bound<=INNER_LIMIT,'stored archive exceeds conservative inner bound')
    destination.mkdir(parents=True)
    result=[]
    for index,group in enumerate(groups):
        path=destination/('math-'+str(index+1)+'.zip')
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_STORED,allowZip64=False) as bundle:
            for name in group:
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_STORED
                bundle.writestr(info,(root/name).read_bytes())
        require(path.stat().st_size<=INNER_LIMIT,'inner archive size changed')
        with zipfile.ZipFile(path) as bundle:
            require(bundle.namelist()==group,'package members differ')
            for name in group:require(bundle.read(name)==(root/name).read_bytes(),'package original bytes differ')
        result.append(dict(name=path.name,bytes=path.stat().st_size,sha256=digest(path),members=group))
    return dict(archives=result,delivered_outer_size='UNRESOLVED; enforce <=32MiB before download',complete=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    acquire=sub.add_parser('collect')
    acquire.add_argument('--output',type=Path,required=True);acquire.add_argument('--archive',type=Path,required=True)
    acquire.add_argument('--manifest',type=Path,required=True);acquire.add_argument('--manifest-sha256',required=True);acquire.add_argument('--source',required=True)
    pack=sub.add_parser('package');pack.add_argument('--root',type=Path,required=True);pack.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='package':
        print(json.dumps(package(args.root,args.output)));return
    result=collect(args.output,args.archive,args.manifest,args.manifest_sha256,args.source)
    print(json.dumps(dict(passed=result['passed'],native_invocations=result['native_invocations'],receipt=str(args.output/'receipt.json'))))
    raise SystemExit(not result['passed'])


if __name__=='__main__':main()
