"""Read-only availability/metadata; never imports a candidate reader or producer."""
import hashlib
import json
import os
from pathlib import Path
import stat

REPORT=Path(__file__).resolve().parent
ROOTS={
    '40089125575':Path('/workspace/reviews/windows-route-clock-actual-20261024/.local/windows40089125575/full/offline-input'),
    '40080238905':Path('/workspace/reviews/windows-collector-actual-20261024/.local/windows40080238905/full/offline-input'),
}


def inventory(root):
    result=[]
    for file in sorted(root.rglob('*')):
        before=file.lstat()
        if stat.S_ISDIR(before.st_mode):
            continue
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('nonregular original: '+str(file))
        raw=file.read_bytes();after=file.lstat()
        key=lambda item:(item.st_dev,item.st_ino,item.st_size,item.st_mtime_ns,item.st_ctime_ns,item.st_mode)
        assert key(before)==key(after),'original changed during read: '+str(file)
        result.append(dict(path=str(file.relative_to(root)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    return result


def main():
    assert os.sched_getaffinity(0)=={4}
    output=REPORT/'archived-availability';output.mkdir(exist_ok=False)
    oracle=json.loads((REPORT/'phase-a-fixture-adjudication/SOURCE_AND_PROPOSAL_BINDING.json').read_text())
    required=set(oracle['required_baseline_paths']+oracle['controller_additions'])
    assert len(required)==53
    rows=[]
    for name,root in ROOTS.items():
        before=inventory(root)
        (output/(name+'-before.json')).write_text(json.dumps(before,indent=2)+'\n')
        paths={r['path'] for r in before};result=json.loads((root/'results.json').read_bytes())
        warning=[]
        for log in ['client.log','reopened.log']:
            text=(root/log).read_bytes().decode('utf-8',errors='replace')
            lines=[line for line in text.splitlines() if 'WARNING' in line or 'ANGLE' in line]
            warning.append(dict(path=log,warning_or_angle_lines=lines,count=len(lines)))
        after=inventory(root);assert before==after,name+' originals changed'
        (output/(name+'-after.json')).write_text(json.dumps(after,indent=2)+'\n')
        callbacks=result.get('shutdown_study_observations')
        rows.append(dict(run=name,root=str(root),files=len(paths),bytes=sum(x['bytes'] for x in before),
                         required_present=len(required&paths),missing_required=sorted(required-paths),extras=sorted(paths-required),
                         original_driver_passed=result.get('passed'),callback_copy_field_present='shutdown_study_observations' in result,
                         callback_copy_type=type(callbacks).__name__,callback_copy_count=len(callbacks) if type(callbacks) is list else None,
                         original_warnings=warning,originals_unchanged=True,
                         scope='availability/metadata only; candidate loader unexecuted; new study/native qualification not accepted'))
    (output/'RESULT.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps([{k:row[k] for k in ['run','files','required_present','missing_required','original_driver_passed','callback_copy_field_present','originals_unchanged']} for row in rows]))


if __name__=='__main__':main()
