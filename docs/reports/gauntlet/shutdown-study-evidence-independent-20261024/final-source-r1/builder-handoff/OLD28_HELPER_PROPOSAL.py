# PROPOSAL ONLY. Do not apply before independent construction adjudication.
# All28 test_* methods/113 assertion calls and original Owner class remain exact.
def run_generated(self,*,failures=(),owner=None,identity_reader=None,observe=False,evidence=True):
    from shutdown_evidence_fixtures import fixture_identity,write_complete_trial
    temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)/'study';calls=[]
    owner=owner or Owner();identity=fixture_identity()
    original_query=owner.query;live=set();held={}
    def process_identity(pid):
        return dict(pid=pid,creation_filetime=pid+1000,handle_value=pid+2000,member_of_outer_job=True)
    def query(label):
        # Preserve all original injected query failures/survivors and rows.
        row=original_query(label)
        row.update(job_handle=7,baseline_pid=99)
        if row.get('verified') and row.get('active_processes')==1 and row.get('process_ids')==[99]:
            row.update(active_processes=1+len(live),process_ids=[99,*sorted(live)])
        row['processes']=[process_identity(pid) for pid in row['process_ids']]
        row['held_processes']=[dict(pid=pid,creation_filetime=record['creation_filetime'],handle_value=record['handle_value'],
                                    observed_exited=pid not in live,exit_code=0 if pid not in live else 259)
                              for pid,record in sorted(held.items())]
        return row
    owner.query=query
    flat={'source':'exact','exe':'same','pck':'same','host':'same'}
    def read_identity():
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
            if event=='native_launch':live.add(pid);held[pid]=process_identity(pid)
            else:live.discard(pid)
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
        finally:
            # Fake driver cleanup mirrors completed/failure-owned cleanup. The
            # original Owner survivor/query faults remain independent and exact.
            live.clear()
    result=study.collect_trials(root,identity,owner,driver,identity_reader=read_identity,
                                load_evidence=lambda _:dict(strict_passed=evidence))
    return result,calls,owner,root
