#!/usr/bin/env python3
"""Dedicated blocked-by-retention four-attempt ordinary/verbose shutdown study.

No native action occurs for `preflight` or `package`. Current source preflight is
BLOCKED, so `collect` also cannot invoke the living driver. Separate root release
and independent Windows admission are still required for any later candidate.
"""
import argparse
import contextlib
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import struct
import sys
import time
import traceback

import shutdown_study_retention as retention
from native_log import failed

ROOT=Path(__file__).resolve().parents[1]
ORDER=retention.TRIALS
SAFETY_SECONDS=5.


def require(value,message):
    if not value:raise RuntimeError(message)


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


class WindowsOwner:
    """One outer job; birth-bound handles never target a PID discovered globally."""
    def __init__(self):
        require(os.name=='nt' and C.sizeof(C.c_void_p)==8,'native Windows x64 only')
        from verify_integration_export import windows_job
        self.kernel,self.job=windows_job();self.baseline=os.getpid();self.handles={};self.queries=[]
        k=self.kernel
        signatures={
          'OpenProcess':([C.c_uint32,C.c_int,C.c_uint32],C.c_void_p),
          'GetProcessId':([C.c_void_p],C.c_uint32),
          'GetProcessTimes':([C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p],C.c_int),
          'IsProcessInJob':([C.c_void_p,C.c_void_p,C.c_void_p],C.c_int),
          'WaitForSingleObject':([C.c_void_p,C.c_uint32],C.c_uint32),
          'TerminateProcess':([C.c_void_p,C.c_uint32],C.c_int),
          'GetExitCodeProcess':([C.c_void_p,C.c_void_p],C.c_int),
          'CloseHandle':([C.c_void_p],C.c_int)}
        for name,(args,result) in signatures.items():
            getattr(k,name).argtypes=args;getattr(k,name).restype=result
        self.baseline_identity=self.capture(self.baseline)

    def checked(self,value):
        if not value:raise C.WinError(C.get_last_error())
        return value

    def capture(self,pid):
        h=self.checked(self.kernel.OpenProcess(0x1000|0x00100000|0x0001,False,pid))
        try:
            require(self.kernel.GetProcessId(h)==pid,'opened owned process ID mismatch')
            member=C.c_int()
            self.checked(self.kernel.IsProcessInJob(h,self.job,C.byref(member)))
            require(member.value==1,'source-queried process is outside owned job')
            creation=C.c_uint64();exit_time=C.c_uint64();kernel=C.c_uint64();user=C.c_uint64()
            self.checked(self.kernel.GetProcessTimes(h,C.byref(creation),C.byref(exit_time),C.byref(kernel),C.byref(user)))
            key=(pid,creation.value)
            if key in self.handles:self.kernel.CloseHandle(h)
            else:self.handles[key]=h
            return dict(pid=pid,creation_filetime=creation.value,handle_value=int(self.handles[key]),member_of_outer_job=True)
        except BaseException:
            self.kernel.CloseHandle(h);raise

    def query(self,label):
        row=dict(label=label,monotonic=time.monotonic(),wall_unix_ns=time.time_ns(),job_handle=int(self.job),baseline_pid=self.baseline)
        self.queries.append(row)  # Failed queries remain part of the receipt.
        try:
            accounting=C.create_string_buffer(48)
            self.checked(self.kernel.QueryInformationJobObject(self.job,1,accounting,len(accounting),None))
            row.update(total_processes=C.c_uint32.from_buffer(accounting,36).value,
                       active_processes=C.c_uint32.from_buffer(accounting,40).value,
                       terminated_processes=C.c_uint32.from_buffer(accounting,44).value)
            # Observe at most4096 owned IDs; overflow/inconsistent counts fail,
            # never silently drop IDs or reinterpret a partial query as empty.
            ids=C.create_string_buffer(8+4096*8)
            self.checked(self.kernel.QueryInformationJobObject(self.job,3,ids,len(ids),None))
            assigned=C.c_uint32.from_buffer(ids,0).value;n=C.c_uint32.from_buffer(ids,4).value
            require(assigned==n==row['active_processes'] and n<=4096,'job accounting/process-list disagreement')
            pids=[C.c_uint64.from_buffer(ids,8+8*i).value for i in range(n)]
            require(len(set(pids))==n and self.baseline in pids,'job baseline/process IDs invalid')
            row['process_ids']=pids;row['processes']=[self.capture(pid) for pid in pids]
            baseline=next(p for p in row['processes'] if p['pid']==self.baseline)
            require(baseline==self.baseline_identity,'controller birth/handle identity changed')
            row['held_processes']=self.completion_records()
            row['verified']=True
        except BaseException as error:
            row.update(verified=False,error=type(error).__name__+': '+str(error));raise
        return row

    def completion_records(self):
        records=[]
        for (pid,birth),h in self.handles.items():
            state=self.kernel.WaitForSingleObject(h,0)
            require(state in (0,258),'owned process wait failed')
            code=C.c_uint32();self.checked(self.kernel.GetExitCodeProcess(h,C.byref(code)))
            records.append(dict(pid=pid,creation_filetime=birth,handle_value=int(h),observed_exited=state==0,exit_code=code.value))
        return records

    def baseline_only(self,row):
        return row.get('verified') is True and row.get('active_processes')==1 and row.get('process_ids')==[self.baseline]

    def safety_cleanup(self,*,clock=time.monotonic):
        start=clock();deadline=start+SAFETY_SECONDS;signals=[];errors=[]
        try:self.query('failure_safety_before')
        except BaseException as error:errors.append(str(error))
        # Only handles proven to belong to this job, never PID-based kill.
        for (pid,birth),h in list(self.handles.items()):
            if pid==self.baseline:continue
            try:
                if self.kernel.WaitForSingleObject(h,0)==258:
                    self.checked(self.kernel.TerminateProcess(h,1));signals.append(dict(pid=pid,creation_filetime=birth,handle_value=int(h)))
            except BaseException as error:errors.append(str(error))
        for (pid,_),h in list(self.handles.items()):
            if pid==self.baseline:continue
            left=deadline-clock()
            if left<=0:errors.append('failure safety deadline expired');break
            state=self.kernel.WaitForSingleObject(h,max(0,int(left*1000)))
            if state!=0:errors.append('owned process completion not observed')
        after=None
        try:after=self.query('failure_safety_after')
        except BaseException as error:errors.append(str(error))
        finished=clock()
        return dict(passed=not errors and finished<=deadline and self.baseline_only(after or {}),
                    failure_only=True,never_normal_close=True,started=start,deadline=deadline,
                    finished=finished,terminated=signals,errors=errors,after=after)

    def close_handles(self):
        for h in self.handles.values():self.kernel.CloseHandle(h)
        # Retain the job handle until process exit: it contains this controller.


def driver_arguments(output,verbose):
    return ['scripts/verify_offline_export.py','--target','windows','--hosted-render-priority','below-normal',
            '--display',':102','--timeout','300','--output',str(output),*(['--reopened-verbose'] if verbose else [])]


def trial_evidence(directory, *, context=None):
    from shutdown_study_evidence import validate_trial
    return validate_trial(directory,context=context,leak_parser=typed_leak_rows)


def typed_leak_rows(raw):
    instances=[];unparsed=[];cache=[]
    pattern=re.compile(r'^Leaked instance: ([A-Za-z_][A-Za-z_0-9]*):([0-9]+)(?: - (Reference count|Resource path): (.*))?$')
    for line in raw.decode('utf-8',errors='replace').splitlines():
        match=pattern.fullmatch(line)
        if match:
            klass,decimal_id,kind,value=match.groups()
            row=dict(raw=line,class_name=klass,decimal_id=decimal_id,process_local_id_only=True)
            if kind=='Reference count' and value.isdecimal():row['reference_count']=int(value)
            elif kind=='Resource path':row['resource_path']=value
            elif kind is not None:unparsed.append(line);continue
            instances.append(row)
        elif line.startswith('Leaked instance:'):unparsed.append(line)
        elif 'Resource still in use:' in line or line.startswith('ResourceCache:'):cache.append(line)
    return dict(instances=instances,unparsed_instance_rows=unparsed,resource_cache_rows=cache,
                retaining_owner='UNRESOLVED',allocation_stack='UNAVAILABLE',old_failure_identity='NOT_ATTRIBUTED')


def collect_trials(output,identity,owner,driver,*,identity_reader,load_evidence=None):
    """Pure orchestration seam. The public command is separately preflight gated."""
    output=Path(output);require(not output.exists(),'preserve existing study output');output.mkdir(parents=True)
    report=dict(schema=1,order=list(ORDER),identity=identity,trials=[],attempts=0,
                passed=False,scope='Four diagnostic trials only; original defect remains open',
                observer='existing offline trace in both arms; not observer-free shipping')
    write(output/'study.json',report)
    try:
        for index,arm in enumerate(ORDER,1):
            trial=dict(index=index,arm=arm,verbose=arm=='verbose',attempted=False,job_queries=[],
                       output=str(output/f'{index:02}-{arm}'),profile='new isolated driver-owned state',
                       flow_seconds=300,close_seconds=20)
            report['trials'].append(trial)
            fatal=[]
            def observe(event,**details):
                row=dict(event=event,monotonic=time.monotonic(),wall_unix_ns=time.time_ns(),**details)
                try:
                    row['job']=owner.query(f'trial{index}/{event}')
                    if event=='native_launch':
                        # Popen still retains this actual root's OS handle even
                        # after a very early exit; do not lose its birth merely
                        # because it vanished from the active job-ID list.
                        row['native_root_identity']=owner.capture(details['pid'])
                except BaseException as error:row['ownership_error']=str(error);fatal.append(str(error))
                trial.setdefault('observations',[]).append(row)
                write(output/'study.json',report)
                require(not row.get('ownership_error'),'ownership uncertain during flow: '+row.get('ownership_error',''))
                return row
            try:
                require(identity_reader()==identity,'source/export/host identity changed before trial')
                before=owner.query(f'trial{index}/before');trial['job_queries'].append(before)
                require(owner.baseline_only(before),'owned job not controller-only before trial')
                require(not Path(trial['output']).exists(),'trial profile/output already exists')
                trial['driver_arguments']=driver_arguments(trial['output'],trial['verbose'])
                trial['attempted']=True;report['attempts']+=1
                trial['started_monotonic']=time.monotonic();trial['started_wall_unix_ns']=time.time_ns()
                try:driver(trial['driver_arguments'],observe,Path(trial['output']))
                except BaseException as error:
                    trial['driver_error']=type(error).__name__+': '+str(error)
                    trial['driver_exception_traceback']=traceback.format_exc()
                finally:
                    # This accounting is unconditional, including early/failed
                    # flow and missing results. Empty cleanup_errors is no proof.
                    trial['finished_monotonic']=time.monotonic();trial['finished_wall_unix_ns']=time.time_ns()
                    after=owner.query(f'trial{index}/after');trial['job_queries'].append(after)
                    require(owner.baseline_only(after),'owned descendant survives attempted flow')
                require(not fatal,'ownership observation failed during flow')
                require(identity_reader()==identity,'source/export/host identity changed after trial')
                # A model loader may veto, never replace actual retained-file
                # validation or authorize an optimistic/incomplete receipt.
                veto_passed=True
                if load_evidence is not None:
                    try:
                        model=load_evidence(Path(trial['output']))
                        veto_passed=type(model) is dict and model.get('strict_passed') is True
                    except BaseException as error:
                        veto_passed=False;trial['evidence_loader_error']=type(error).__name__+': '+str(error)
                try:
                    trial['evidence']=trial_evidence(Path(trial['output']),context=dict(identity=identity,trial=trial))
                    if trial['evidence']['evidence_errors']:
                        trial['evidence_error']='; '.join(trial['evidence']['evidence_errors'])
                except BaseException as error:trial['evidence_error']=type(error).__name__+': '+str(error)
                trial['strict_passed']=(not trial.get('driver_error') and veto_passed and
                                        trial.get('evidence',{}).get('evidence_complete') is True and
                                        trial.get('evidence',{}).get('strict_passed') is True)
                # Ordinary strict failure still consumes this arm. It is never
                # replaced or retried. Ownership/source uncertainty stops all.
            except BaseException as error:
                trial['stop_error']=type(error).__name__+': '+str(error)
                report['failure_safety_used']=True
                try:trial['failure_safety_cleanup']=owner.safety_cleanup()
                except BaseException as cleanup_error:trial['failure_safety_cleanup']=dict(passed=False,error=str(cleanup_error))
                report['stopped']=True;break
            finally:write(output/'study.json',report)
        report['completed_all_four']=report['attempts']==4 and not report.get('stopped')
        report['passed']=report['completed_all_four'] and all(t.get('strict_passed') is True for t in report['trials'])
    finally:
        try:report['final_job']=owner.query('study/final');require(owner.baseline_only(report['final_job']),'final job not controller-only')
        except BaseException as error:
            report.update(passed=False,final_ownership_error=str(error))
            if not report.get('failure_safety_used'):
                report['failure_safety_used']=True
                try:report['final_failure_safety_cleanup']=owner.safety_cleanup()
                except BaseException as cleanup_error:report['final_failure_safety_cleanup']=dict(passed=False,error=str(cleanup_error))
            else:
                report['final_safety_not_repeated']='One failure-only safety budget already consumed; unresolved ownership retained'
        report['job_queries']=owner.queries
        write(output/'study.json',report)
    return report


def embedded_pck_identity(path):
    """Exact embedded byte range from the existing Godot trailer contract."""
    with Path(path).open('rb') as stream:
        stream.seek(0,2);length=stream.tell();require(length>=44,'embedded pack too short')
        stream.seek(-12,2);size,magic=struct.unpack('<QI',stream.read(12))
        require(magic==0x43504447 and 32<=size<=length-12,'embedded pack trailer invalid')
        start=length-12-size;stream.seek(start)
        header=stream.read(32);fields=struct.unpack('<6IQ',header)
        require(fields[0]==0x43504447 and fields[1] in (3,4),'embedded pack header invalid')
        digest=hashlib.sha256(header);left=size-32
        while left:
            block=stream.read(min(left,1024*1024));require(block,'short embedded pack')
            digest.update(block);left-=len(block)
        return dict(storage='embedded exact original pack range',offset=start,bytes=size,sha256=digest.hexdigest(),
                    pack_version=fields[1],engine_version=list(fields[2:5]))


def runtime_identity(expected):
    from build_manifest import BUILDS,source,validate_record,payload
    before=source();require(before['source_commit']==expected,'runtime source mismatch')
    record=validate_record('windows',before)
    files=payload('windows')
    require(any(r['path'].endswith('SIGHTBREAK.exe') for r in files),'export executable identity missing')
    return dict(source=before,artifact_record=record,payload=files,
                embedded_pck=embedded_pck_identity(BUILDS/'windows/SIGHTBREAK.exe'),
                host=dict(node=platform.node(),platform=platform.platform(),python=platform.python_version()))


def real_driver(arguments,observer,directory):
    import shutil
    import verify_offline_export
    directory=Path(directory)
    directory.mkdir()
    capture=directory.with_name(directory.name+'.controller-capture')
    capture.mkdir()  # Fresh owned sibling inside the overall study evidence tree.
    old=sys.argv;invocation_error=None;publication_errors=[]
    try:
        sys.argv=list(arguments)
        with (capture/'controller-stdout.log').open('x') as out,(capture/'controller-stderr.log').open('x') as err:
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                verify_offline_export.main(study_observer=observer)
    except BaseException as error:
        invocation_error=error
    finally:
        sys.argv=old
        # Keep capture originals even after publication. Exclusive destination
        # creation never overwrites a collision; partial copies are retained.
        for name in ('controller-stdout.log','controller-stderr.log'):
            source=capture/name;target=directory/name
            try:
                with source.open('rb') as reader,target.open('xb') as writer:
                    shutil.copyfileobj(reader,writer)
            except BaseException as error:publication_errors.append(dict(path=str(target),error=type(error).__name__+': '+str(error)))
        try:
            write(capture/'publication.json',dict(invocation_error=None if invocation_error is None else
                  type(invocation_error).__name__+': '+str(invocation_error),publication_errors=publication_errors,
                  capture_scope='Complete original streams retained; publication never overwrites',
                  files=[dict(path=name,bytes=(capture/name).stat().st_size,sha256=retention.sha((capture/name).read_bytes()))
                         for name in ('controller-stdout.log','controller-stderr.log') if (capture/name).is_file()]))
        except BaseException as error:
            publication_errors.append(dict(path=str(capture/'publication.json'),error=type(error).__name__+': '+str(error)))
    if publication_errors:raise RuntimeError('Controller stream publication failed; originals and partial files retained: '+str(publication_errors)) from invocation_error
    if invocation_error is not None:raise invocation_error


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('preflight','collect','package'))
    p.add_argument('--expected-source',required=True);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--source',type=Path,help='Complete evidence source for package mode only')
    args=p.parse_args()
    if args.mode=='package':
        retention.source_binding(args.expected_source)
        require(args.source is not None,'complete evidence source required')
        print(json.dumps(retention.complete_archives(args.source,args.output)));return
    check=retention.preflight(args.expected_source)
    if args.mode=='preflight':
        require(not args.output.exists(),'preserve old preflight');write(args.output,check)
        print(json.dumps(check));raise SystemExit(0 if check['status']=='ADMITTED' else 2)
    require(check['status']=='ADMITTED' and check['execution_authorized'] is True,
            'BLOCKED before any process action: complete four-trial retention has no source-backed proof')
    # Unreachable for current frozen source. Future admission requires reviewed
    # source changes, independent critic and pushed root release; no CLI bypass.
    require(os.name=='nt','Windows only')
    owner=WindowsOwner()
    try:
        identity=runtime_identity(args.expected_source)
        report=collect_trials(args.output,identity,owner,real_driver,identity_reader=lambda:runtime_identity(args.expected_source))
        raise SystemExit(not report['passed'])
    finally:owner.close_handles()


if __name__=='__main__':main()
