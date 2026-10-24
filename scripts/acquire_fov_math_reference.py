#!/usr/bin/env python3
"""One future root-admitted isolated Godot math acquisition. Never auto-retry."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import time

import fov_math_reference as reference
from native_log import failed

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'tools/fov_math_reference'
ENGINE = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
ENGINE_SHA256 = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
WHOLE_SECONDS = 60.
CLEANUP_SECONDS = 5.
STREAM_LIMITS = {'stdout': 8*1024*1024, 'stderr': 1024*1024}
COMPONENT = ['scripts/fov_math_reference.py','scripts/acquire_fov_math_reference.py','scripts/test_fov_math_reference.py',
             'tools/fov_math_reference/project.godot','tools/fov_math_reference/reference.gd','tools/fov_math_reference/cases.json',
             'scripts/test_fov_binary_input.py','tools/fov_math_reference/cases-binary64-v2.json',
             'scripts/fixtures/fov_actual_input_roundtrip_550.json','scripts/fixtures/fov_binary_protected_segments.json']
CASES_NAME = reference.BINARY_CASES_NAME


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def source_binding(expected,*,deadline,clock=time.monotonic):
    def remaining():
        value=deadline-clock()
        require(value>0,"source binding exceeded whole deadline")
        return value
    require(len(expected)==40 and all(c in '0123456789abcdef' for c in expected),'full frozen source required')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=remaining()).strip()
    require(actual==expected,'source HEAD mismatch')
    for staged in (False,True):
        command=['git','diff',*(['--cached'] if staged else []),'--quiet','--','.',':!docs/']
        require(subprocess.run(command,cwd=ROOT,timeout=remaining()).returncode==0,'source has tracked non-doc changes')
    extras=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*COMPONENT],cwd=ROOT,timeout=remaining())
    require(not extras,'untracked component source')
    files={}
    for path in COMPONENT:
        remaining();files[path]=digest(ROOT/path);remaining()
    return dict(commit=actual,files=files)


class LinuxKernel:
    """Only this supervisor's descendant tree; no global process/environment scan."""
    def __init__(self):
        self.supervisor=os.getpid()

    def enable_subreaper(self):
        require(self.identity(self.supervisor) is not None,'supervisor identity unavailable before native launch')
        # An unavailable children interface cannot establish an empty owned tree.
        # Check our still-live supervisor before creating the sole native child.
        self.children(self.supervisor)
        require(hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'),'owned pidfd API unavailable')
        libc=ctypes.CDLL(None,use_errno=True)
        require(libc.prctl(36,1,0,0,0)==0,'cannot enable owned child subreaper')
        value=ctypes.c_int()
        require(libc.prctl(37,ctypes.byref(value),0,0,0)==0 and value.value==1,'subreaper readback failed')

    def identity(self,pid):
        try:
            tail=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
            return dict(pid=pid,state=tail[0],ppid=int(tail[1]),pgrp=int(tail[2]),session=int(tail[3]),start_ticks=int(tail[19]))
        except FileNotFoundError:
            return None

    def children(self,pid):
        result=set()
        parent=Path(f'/proc/{pid}')
        try:
            tasks=list((parent/'task').iterdir())
        except FileNotFoundError:
            require(not parent.exists(),'owned process task interface unavailable for existing parent')
            return []
        require(tasks or not parent.exists(),'owned process task interface empty for existing parent')
        for task in tasks:
            try:
                values=(task/'children').read_text().split()
            except FileNotFoundError:
                require(not task.exists(),'owned process child-list interface unavailable for existing task')
                continue
            require(all(value.isascii() and value.isdecimal() and int(value)>0 for value in values),'malformed owned process child-list')
            result.update(int(value) for value in values)
        return sorted(result)

    def open_pid(self,pid):
        return os.pidfd_open(pid)

    def close_pid(self,fd):
        os.close(fd)

    def send(self,fd,signum):
        signal.pidfd_send_signal(fd,signum)

    def reap(self,pid):
        try:
            return os.waitpid(pid,os.WNOHANG)
        except ChildProcessError:
            return (0,0)

    def affinity(self,pid):
        return sorted(os.sched_getaffinity(pid))

    def executable(self,pid):
        return os.readlink(f'/proc/{pid}/exe')


class OwnedTree:
    def __init__(self,kernel,root_pid):
        self.kernel,self.root_pid=kernel,root_pid
        self.seen={};self.signals=[];self.reaped=[]
        self.supervisor_identity=None

    @staticmethod
    def key(value):
        return value['pid'],value['start_ticks']

    def supervisor_key(self):
        current=self.kernel.identity(self.kernel.supervisor)
        require(current is not None,'supervisor birth identity unavailable')
        if self.supervisor_identity is None:self.supervisor_identity=current
        require(self.key(current)==self.key(self.supervisor_identity),'supervisor birth identity changed')
        return self.key(current)

    def bind_root(self):
        self.supervisor_key()
        current=self.kernel.identity(self.root_pid)
        require(current is not None,'known Popen root identity unavailable')
        require(current['ppid']==self.kernel.supervisor,'known Popen root parent mismatch')
        key=self.key(current)
        fd=self.kernel.open_pid(self.root_pid)
        try:
            after=self.kernel.identity(self.root_pid)
            require(after is not None and self.key(after)==key and after['ppid']==self.kernel.supervisor,
                    'known Popen root birth/parent changed during binding')
        except BaseException:
            self.kernel.close_pid(fd)
            raise
        self.seen[key]=dict(identity=current,fd=fd)
        return after

    def observe(self):
        queue=[self.supervisor_key()];visited=set()
        while queue:
            parent_key=queue.pop();parent=parent_key[0]
            if parent_key in visited:continue
            visited.add(parent_key)
            def parent_alive():
                value=self.kernel.identity(parent)
                if value is None:
                    require(parent!=self.kernel.supervisor,'supervisor identity disappeared')
                    return False
                require(self.key(value)==parent_key,'queued owned parent birth identity changed')
                return True
            if not parent_alive():continue
            children=self.kernel.children(parent)
            if not parent_alive():continue
            for pid in children:
                current=self.kernel.identity(pid)
                if current is None:continue
                require(pid!=self.kernel.supervisor and current['ppid']==parent,'child ancestry differs from observed owned parent')
                if not parent_alive():break
                key=self.key(current)
                if key not in self.seen:
                    fd=self.kernel.open_pid(pid)
                    try:
                        after=self.kernel.identity(pid)
                        require(after is not None and self.key(after)==key and after['ppid']==parent and parent_alive(),
                                'owned process birth identity or ancestry changed during observation')
                    except BaseException:
                        self.kernel.close_pid(fd)
                        raise
                    self.seen[key]=dict(identity=current,fd=fd)
                queue.append(key)
        return self.live()

    def live(self):
        result=[]
        for key,entry in self.seen.items():
            value=self.kernel.identity(key[0])
            if value is not None and self.key(value)==key:result.append(value)
        return result

    def reap_descendants(self):
        for value in self.live():
            if value['pid']!=self.root_pid and value['ppid']==self.kernel.supervisor and value['state']=='Z':
                result=self.kernel.reap(value['pid'])
                if result[0]:self.reaped.append(dict(pid=result[0],status=result[1]))

    def signal_all(self,signum):
        self.supervisor_key()
        for value in self.live():
            entry=self.seen[self.key(value)]
            try:
                self.kernel.send(entry['fd'],signum)
                self.signals.append(dict(pid=value['pid'],start_ticks=value['start_ticks'],signal=signum))
            except ProcessLookupError:
                pass

    def close(self):
        for entry in self.seen.values():self.kernel.close_pid(entry['fd'])


class Streams:
    def __init__(self,process,out):
        self.selector=selectors.DefaultSelector();self.files={};self.counts={k:0 for k in STREAM_LIMITS};self.retained=dict(self.counts);self.eof={k:False for k in STREAM_LIMITS}
        for name in STREAM_LIMITS:
            stream=getattr(process,name);os.set_blocking(stream.fileno(),False)
            self.selector.register(stream,selectors.EVENT_READ,name)
            self.files[name]=(out/(name+'.log')).open('wb')

    def read(self,timeout):
        overflow=False
        for key,_ in self.selector.select(max(0,timeout)):
            name=key.data
            data=os.read(key.fileobj.fileno(),65536)
            if not data:
                self.eof[name]=True;self.selector.unregister(key.fileobj);key.fileobj.close();continue
            self.counts[name]+=len(data)
            keep=max(0,STREAM_LIMITS[name]-self.retained[name]);chunk=data[:keep]
            self.files[name].write(chunk);self.retained[name]+=len(chunk)
            overflow=overflow or self.counts[name]>STREAM_LIMITS[name]
        return overflow

    def pending(self):
        return bool(self.selector.get_map())

    def close(self):
        for key in list(self.selector.get_map().values()):
            self.selector.unregister(key.fileobj);key.fileobj.close()
        self.selector.close()
        for stream in self.files.values():stream.close()


def cleanup(process,tree,deadline,*,streams=None,clock=time.monotonic,sleep=time.sleep):
    start=clock();escalated=False;drain_error=None
    tree.observe();process.poll();tree.reap_descendants()
    root_bound=any(key[0]==tree.root_pid for key in tree.seen)
    if process.poll() is None and not any(value['pid']==tree.root_pid for value in tree.live()):
        # Discovery is never allowed to erase the child returned by Popen.
        process.kill()
        tree.signals.append(dict(pid=process.pid,start_ticks=None,signal=int(signal.SIGKILL),via='owned Popen safety cleanup'))
    if tree.live():tree.signal_all(signal.SIGTERM)
    while clock()<deadline:
        tree.observe();process.poll();tree.reap_descendants()
        if streams is not None and streams.pending() and drain_error is None:
            try:streams.read(min(.02,max(0,deadline-clock())))
            except BaseException as error:drain_error=type(error).__name__+': '+str(error)
        pending=streams is not None and streams.pending()
        root_code=process.poll()
        if root_code is not None and not tree.live() and not tree.kernel.children(tree.kernel.supervisor) and (not pending or drain_error):
            waited=process.wait(timeout=max(0,deadline-clock()))
            require(waited==root_code,'known Popen root wait status mismatch')
            return dict(passed=clock()<=deadline and not drain_error and root_bound,signals=tree.signals,reaped=tree.reaped,
                        survivors=[],stream_drain_error=drain_error,root_birth_bound=root_bound,
                        root_exit_code=root_code,root_popen_waited=True)
        if not escalated and clock()-start>=CLEANUP_SECONDS/2:
            tree.signal_all(signal.SIGKILL);escalated=True
        sleep(min(.02,max(0,deadline-clock())))
    tree.observe();process.poll();tree.reap_descendants()
    return dict(passed=False,signals=tree.signals,reaped=tree.reaped,survivors=tree.live(),
                late=True,stream_drain_error=drain_error,root_birth_bound=root_bound,
                root_exit_code=process.poll(),root_popen_waited=False)


def monitor(process,tree,streams,deadline,*,clock=time.monotonic):
    while True:
        require(clock()<deadline,'whole math deadline exceeded before observed completion')
        tree.observe()
        for owned in tree.live():
            require(tree.kernel.affinity(owned['pid'])==[0,1],'owned native affinity changed')
        require(not streams.read(min(.02,max(0,deadline-clock()))),'native stream cap exceeded')
        code=process.poll();tree.reap_descendants()
        observed=clock()
        require(observed<deadline,'native completion or drain observed after whole deadline')
        if code is not None and not streams.pending():
            require(not tree.live() and not tree.kernel.children(tree.kernel.supervisor),'owned child survives native completion')
            return code,observed


def acquire(output,expected_source,*,clock=time.monotonic,sleep=time.sleep,process_factory=subprocess.Popen,kernel=None,stream_factory=Streams):
    started=clock();deadline=started+WHOLE_SECONDS
    require(sys.platform=='linux','isolated math acquisition requires Linux')
    require(sorted(os.sched_getaffinity(0))==[4],'supervisor requires CPU4 only')
    require(output.is_absolute() and not output.exists(),'absolute absent output required')
    require(ROOT!=output and ROOT not in output.parents,'output must be outside source checkout')
    output.mkdir()
    report=dict(scope='isolated native vector math only; no gameplay/LOS/physical proof',passed=False,
                started_monotonic=started,whole_deadline=deadline,whole_seconds=WHOLE_SECONDS,cleanup_seconds=CLEANUP_SECONDS,
                native_invocations=0,engine_path=str(ENGINE),engine_sha256_expected=ENGINE_SHA256,
                supervisor_cpu_affinity=[4],native_cpu_affinity=[0,1],output=str(output))
    process=tree=streams=None
    try:
        binding=source_binding(expected_source,deadline=deadline,clock=clock);report['source']=binding
        require(digest(ENGINE)==ENGINE_SHA256,'pinned native engine checksum mismatch')
        require(clock()<deadline,'preparation exceeded whole deadline')
        payload=json.loads((PROJECT/CASES_NAME).read_text());reference.validate_binary_cases(payload)
        target=output/'project';target.mkdir()
        for name in ('project.godot','reference.gd',CASES_NAME):shutil.copyfile(PROJECT/name,target/name)
        payload_hash=reference.sha((target/CASES_NAME).read_bytes());program_hash=digest(target/'reference.gd')
        require(payload_hash==binding['files']['tools/fov_math_reference/'+CASES_NAME] and program_hash==binding['files']['tools/fov_math_reference/reference.gd'],'copied payload mismatch')
        env=os.environ.copy();isolated={}
        for key,part in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
            path=output/'user'/part;path.mkdir(parents=True);env[key]=str(path);isolated[key]=str(path)
        report['isolated_user_paths']=isolated
        require(not set(isolated)&{'HOME','CODEX_HOME'},'unsupported environment mutation')
        command=[str(ENGINE),'--headless','--path',str(target),'--script',str(target/'reference.gd'),'--',
                 '--cases='+str(target/CASES_NAME),'--expected-cases-sha256='+payload_hash]
        report['command']=command
        kernel=kernel or LinuxKernel();kernel.enable_subreaper()
        require(clock()<deadline,'prelaunch exceeded whole deadline')
        report['native_invocations']+=1
        process=process_factory(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=target,env=env,
                                start_new_session=True,preexec_fn=lambda:os.sched_setaffinity(0,{0,1}))
        report['spawned_pid']=process.pid  # Intended child only; birth/ownership still require readback.
        tree=OwnedTree(kernel,process.pid)
        streams=stream_factory(process,output)
        tree.bind_root()
        tree.observe()
        roots=[v for v in tree.live() if v['pid']==process.pid]
        require(len(roots)==1 and roots[0]['pgrp']==process.pid and roots[0]['session']==process.pid,'owned native root identity/session not observed')
        require(kernel.affinity(process.pid)==[0,1],'native affinity mismatch')
        require(kernel.executable(process.pid)==str(ENGINE.resolve()),'native root executable readback mismatch')
        report['root_identity']=roots[0]
        report['root_executable']=kernel.executable(process.pid)
        code,observed=monitor(process,tree,streams,deadline,clock=clock)
        report.update(native_exit=code,completion_observed_monotonic=observed)
        report['stream_counts']=dict(streams.counts);report['stream_retained']=dict(streams.retained)
        report['stream_truncated']={name:streams.counts[name]>streams.retained[name] for name in STREAM_LIMITS}
        report['stream_eof']=dict(streams.eof)
        report['failure_log_coverage_complete']=all(streams.eof.values()) and not any(report['stream_truncated'].values())
        streams.close();streams=None
        require(code==0,'native math process failed')
        stdout=(output/'stdout.log').read_bytes();stderr=(output/'stderr.log').read_bytes()
        require(not stderr and not failed(stdout.decode('utf-8',errors='strict')),'native strict log failure')
        report['math']=reference.parse_binary_output(stdout,payload,cases_sha256=payload_hash,program_sha256=program_hash)
        require(source_binding(expected_source,deadline=deadline,clock=clock)==binding and digest(ENGINE)==ENGINE_SHA256,'source or engine changed during math acquisition')
        require(all(digest(target/name)==binding['files']['tools/fov_math_reference/'+name] for name in ('project.godot','reference.gd',CASES_NAME)),'copied payload changed during acquisition')
        require(clock()<deadline,'validation exceeded whole acquisition deadline')
        report['passed']=True
    except BaseException as error:
        report.update(error_type=type(error).__name__,error=str(error),passed=False)
    finally:
        if tree is not None:
            cleanup_deadline=clock()+CLEANUP_SECONDS
            try:
                report['cleanup']=cleanup(process,tree,cleanup_deadline,streams=streams,clock=clock,sleep=sleep)
                report['observed_processes']=[e['identity'] for e in tree.seen.values()]
                if not report['cleanup']['passed'] or report['cleanup']['signals']:report['passed']=False
            except BaseException as error:
                report.update(passed=False,cleanup_error=type(error).__name__+': '+str(error))
                # The Popen child remains owned even when observation fails.
                # Reap it before returning; unknown descendant state stays failed.
                stop=cleanup_deadline
                try:
                    if process.poll() is None:process.kill()
                    process.wait(timeout=max(0,stop-clock()))
                    while streams is not None and streams.pending() and clock()<stop:
                        streams.read(min(.02,max(0,stop-clock())))
                except BaseException as stop_error:
                    report['root_stop_error']=type(stop_error).__name__+': '+str(stop_error)
            finally:tree.close()
        if streams is not None:
            report['stream_counts']=dict(streams.counts);report['stream_retained']=dict(streams.retained)
            report['stream_truncated']={name:streams.counts[name]>streams.retained[name] for name in STREAM_LIMITS}
            report['stream_eof']=dict(streams.eof)
            report['failure_log_coverage_complete']=all(streams.eof.values()) and not any(report['stream_truncated'].values())
            if not report['failure_log_coverage_complete']:report['passed']=False
            streams.close()
        elif process is not None and 'stream_eof' not in report:
            report['failure_log_coverage_complete']=False
            report['stream_coverage_error']='retention setup unavailable; unread coverage unresolved'
            report['passed']=False
        if process is not None:
            for name in STREAM_LIMITS:
                stream=getattr(process,name,None)
                if stream is not None and not stream.closed:stream.close()
        report['finished_monotonic']=clock();report['elapsed_seconds']=report['finished_monotonic']-started
        if report['passed'] and report['finished_monotonic']>=deadline:
            report.update(passed=False,error='whole deadline expired before final cleanup observation')
        report['logs']={}
        for name in STREAM_LIMITS:
            path=output/(name+'.log')
            if path.exists():report['logs'][name]=dict(bytes=path.stat().st_size,sha256=digest(path))
        (output/'receipt.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--expected-source',required=True)
    args=parser.parse_args()
    report=acquire(args.output,args.expected_source)
    print(json.dumps(dict(passed=report['passed'],receipt=str(args.output/'receipt.json'),native_invocations=report['native_invocations'])))
    raise SystemExit(not report['passed'])


if __name__=='__main__':main()
