# PROPOSAL ONLY. Do not apply before independent construction adjudication.
# All28 test_* methods/113 assertion calls and original Owner class remain exact.
def run_generated(self,*,failures=(),owner=None,identity_reader=None,observe=False,evidence=True):
    import time
    from shutdown_evidence_fixtures import fixture_identity,write_complete_trial
    temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)/'study';calls=[]
    owner=owner or Owner();identity=fixture_identity()
    original_query=owner.query;live={99};held={};accounting={'total':5}
    def process_identity(pid):
        return dict(pid=pid,creation_filetime=pid+1000,handle_value=pid+2000,member_of_outer_job=True)
    held[99]=process_identity(99)
    def query(label):
        # Preserve all original injected query failures/survivors and rows.
        row=original_query(label)
        healthy=row.get('verified') and row.get('active_processes')==1 and row.get('process_ids')==[99]
        if healthy:
            total=accounting['total']
            row.update(monotonic=time.monotonic(),wall_unix_ns=time.time_ns(),job_handle=7,baseline_pid=99,
                       total_processes=total,terminated_processes=0,
                       active_processes=len(live),process_ids=sorted(live))
            row['processes']=[process_identity(pid) for pid in row['process_ids']]
            row['held_processes']=[dict(pid=pid,creation_filetime=record['creation_filetime'],handle_value=record['handle_value'],
                                        observed_exited=pid not in live,exit_code=0 if pid not in live else 259)
                                  for pid,record in sorted(held.items())]
        return row
    owner.query=query
    flat={'source':'exact','exe':'same','pck':'same','host':'same'}
    def read_identity():
        accounting['total']+=4  # actual modeled source() call, including changed identities
        if identity_reader is None:return copy.deepcopy(identity)
        original=identity_reader();result=copy.deepcopy(identity)
        # Preserve each original mutation and the original read-call schedule.
        for field in flat:
            if original.get(field)!=flat[field]:
                if field=='source':result['source']['source_commit']=original.get(field)
                elif field=='exe':result['artifact_record']['artifact']['sha256']=original.get(field)
                elif field=='pck':result['embedded_pck']['sha256']=original.get(field)
                else:result['host']['platform']=original.get(field)
        return result
    def driver(args,callback,directory):
        index=len(calls)+1;calls.append((args,directory))
        directory.mkdir();(directory/'original-failure.bin').write_bytes(bytes([index])*7)
        def emit(event,**details):
            pid=details['pid']
            if event=='native_launch':
                accounting['total']+=6 if details['name']=='client' else 1
                live.add(pid);held[pid]=process_identity(pid)
            else:
                accounting['total']+=28 if details['process']=='client' else 12
                live.discard(pid)
            return callback(event,**details)
        try:
            if index in failures:
                # Source-shaped partial/unreached-close negative, not a full
                # successful fixture followed by a contradictory forced failure.
                (directory/'results.json').write_text('{"passed":false}\n')
                if observe:emit('native_launch',name='client',pid=100+index)
                raise RuntimeError('preserved failure '+str(index))
            write_complete_trial(directory,identity,verbose='--reopened-verbose' in args,
                                 client_pid=100+index,reopened_pid=200+index,observer=emit)
            accounting['total']+=4  # final source() comparison before successful driver return
        finally:
            # Fake driver cleanup mirrors completed/failure-owned cleanup. The
            # original Owner survivor/query faults remain independent and exact.
            live.intersection_update({99})
    result=study.collect_trials(root,identity,owner,driver,identity_reader=read_identity,
                                load_evidence=lambda _:dict(strict_passed=evidence))
    return result,calls,owner,root
