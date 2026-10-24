"""Fail-closed retention admission for the four-trial shutdown diagnosis.

This source currently CANNOT admit execution: unchanged producers have no finite
lossless byte maxima. Old observed sizes are evidence, never future maxima.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_COUNT = 2
ARCHIVE_BYTES = 32 * 1024 * 1024
TRIALS = ('ordinary', 'verbose', 'verbose', 'ordinary')
BYTE_FAMILIES = ('png_bytes','native_combined_stdout_stderr_bytes','trace_jsonl_bytes',
                 'actions_status_results_profile_state_bytes','ocr_stderr_bytes','controller_job_receipts_bytes')
MODEL_PATHS = ('scripts/verify_offline_export.py', 'scripts/verify_integration_export.py',
               'scripts/native_observation.py', 'game/scripts/offline_diagnostics.gd',
               'scripts/shutdown_study_retention.py')


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def physical_source_file(path, expected, mode, *, windows=False):
    """Compare real checkout bytes; Git index flags never establish this proof."""
    path=Path(path)
    before=path.lstat()
    require(stat.S_ISREG(before.st_mode) and not path.is_symlink(),'source must be a regular physical file: '+str(path))
    require(mode in ('100644','100755'),'unsupported source mode: '+mode)
    actual=path.read_bytes()
    after=path.lstat()
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_mode)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_mode),
            'source changed during physical read: '+str(path))
    conversion='none'
    if actual!=expected:
        # Only ordinary Windows text checkout conversion is allowed. No Git
        # attribute/filter command can redefine the expected frozen bytes.
        require(windows and b'\0' not in expected and b'\r' not in expected,
                'physical source bytes differ: '+str(path))
        expected.decode('utf-8',errors='strict')
        require(actual==expected.replace(b'\n',b'\r\n'),'physical source bytes differ: '+str(path))
        conversion='Windows LF to CRLF'
    measured_mode=None if windows else ('100755' if before.st_mode & stat.S_IXUSR else '100644')
    require(measured_mode is None or measured_mode==mode,'physical source executable mode differs: '+str(path))
    return dict(bytes=len(actual),sha256=sha(actual),canonical_sha256=sha(expected),
                canonical_mode=mode,physical_mode=measured_mode,checkout_conversion=conversion,
                mode_scope='NTFS executable bits not measured' if windows else 'POSIX owner executable bit')


def source_binding(expected, root=ROOT):
    require(type(expected) is str and len(expected)==40 and all(c in '0123456789abcdef' for c in expected),'exact source required')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=root,timeout=20)
    require(git('rev-parse','HEAD').decode().strip()==expected,'source HEAD mismatch')
    require(not git('status','--porcelain','--untracked-files=all'),'source must be fully clean')
    records=[];physical={}
    for line in git('ls-tree','-r','-z',expected).split(b'\0'):
        if not line:continue
        identity,path=line.split(b'\t',1)
        identity,path=identity.decode('ascii'),path.decode('utf-8')
        if not path.startswith('docs/'):
            mode,kind,blob=identity.split()
            require(kind=='blob','unexpected source object type')
            physical[path]=physical_source_file(Path(root)/path,git('show',expected+':'+path),mode,windows=os.name=='nt')
            records.append(dict(path=path,identity=identity))
    # Every required source is materialized and checked, including model sources.
    # A sparse Git object alone is insufficient to authorize executing that path.
    models={path:sha(git('show',expected+':'+path)) for path in MODEL_PATHS}
    return dict(commit=expected,non_doc_union_sha256=sha(canonical(records)),non_doc_paths=len(records),
                model_sources=models,physical_sources=physical)


def fixed_model():
    return dict(trial_count=4,order=list(TRIALS),flow_seconds=300,close_seconds=20,
                named_acceptance_pngs=22,overwritten_ocr_pngs=1,ocr_stdout_files=16,
                ocr_stdout_prefix_bytes=2*1024*1024,
                # No finite aggregate bound follows from existing code.
                png_bytes=None,native_combined_stdout_stderr_bytes=None,
                trace_jsonl_bytes=None,actions_status_results_profile_state_bytes=None,
                ocr_stderr_bytes=None,controller_job_receipts_bytes=None,
                complete_ocr_stdout_on_overflow=False)


def assess(model, *, archive_count=ARCHIVE_COUNT, archive_bytes=ARCHIVE_BYTES):
    """Pure conservative model. Finite generated controls exercise packing math."""
    require(archive_count==2 and archive_bytes==32*1024*1024,'original two 32MiB archives required')
    require(model['trial_count']==4 and model['order']==list(TRIALS),'fixed four-arm order required')
    unknown=[key for key in BYTE_FAMILIES if model.get(key) is None]
    reasons=['No source-backed finite maximum: '+key for key in unknown]
    if model.get('complete_ocr_stdout_on_overflow') is not True:
        reasons.append('Existing OCR overflow keeps a prefix; complete failure stream not guaranteed')
    prefix=model['ocr_stdout_files']*model['ocr_stdout_prefix_bytes']
    fixed=0
    for key in BYTE_FAMILIES:
        value=model.get(key)
        if value is not None:
            require(type(value) is int and value>=0,'invalid byte maximum')
            fixed+=value
    # ZIP_STORED needs member headers/names/index, not just payload bytes. Finite
    # controls must explicitly supply a maximum for all that overhead as well.
    overhead=model.get('all_zip_headers_indexes_bytes')
    if overhead is None:reasons.append('No source-backed maximum for ZIP members/names/index overhead')
    if overhead is not None:require(type(overhead) is int and overhead>=0,'invalid archive overhead maximum')
    total=None if unknown or overhead is None else (prefix+fixed)*4+overhead
    if total is not None and total>archive_count*archive_bytes:
        reasons.append('Conservative complete evidence exceeds original total capacity')
    # A total alone cannot guarantee a two-bin partition of indivisible files.
    if model.get('largest_member_with_headers_bytes') is None:
        reasons.append('No source-backed maximum indivisible archive member')
    elif model['largest_member_with_headers_bytes']>archive_bytes:
        reasons.append('An indivisible required member exceeds one original archive')
    return dict(status='BLOCKED' if reasons else 'RETENTION_MODEL_ONLY',reasons=reasons,
                archive_count=archive_count,archive_bytes=archive_bytes,
                ocr_prefix_capacity_per_trial=prefix,conservative_all_trials_bytes=total,
                execution_authorized=False)


def preflight(expected, root=ROOT):
    binding=source_binding(expected,root)
    model=fixed_model()
    return dict(schema=1,source=binding,model=model,**assess(model),
                scope='Source-only retention preflight; old observations cannot certify future maxima')


def inventory(source):
    """Every regular file, including unknown/partial failures; never suffix-filter."""
    source=Path(source);records=[]
    for p in sorted(source.rglob('*')):
        require(not p.is_symlink(),'symlinked evidence rejected')
        if p.is_file():
            b=p.read_bytes();records.append(dict(path=p.relative_to(source).as_posix(),bytes=len(b),sha256=sha(b)))
    return records


def complete_archives(source, output, *, archive_bytes=ARCHIVE_BYTES):
    """Exactly two lossless STORED archives, atomic publication or none.

    This is post-acquisition preservation, never a substitute for the preflight.
    Infeasible packing fails and leaves all originals. No smaller-output retry.
    """
    require(0<archive_bytes<=ARCHIVE_BYTES,'cannot raise original archive limit')
    source,output=Path(source).resolve(),Path(output).resolve()
    require(source.is_dir() and not output.exists() and not output.is_relative_to(source),'fresh archive destination required')
    records=inventory(source);require(records,'empty evidence')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='shutdown-study-pack-',dir=output.parent) as temp:
        temp=Path(temp);bins=[[],[]];sizes=[22,22]
        # Deterministic fail-closed first-fit; a rejected packing is not retried
        # with another route/compressor/order. No claim of optimal bin packing.
        for record in sorted(records,key=lambda r:(-r['bytes'],r['path'])):
            overhead=76+2*len(('evidence/'+record['path']).encode('utf-8'))
            choices=[i for i in range(2) if sizes[i]+record['bytes']+overhead<=archive_bytes]
            require(choices,'complete required evidence cannot fit two archives')
            i=min(choices,key=lambda k:sizes[k]);bins[i].append(record);sizes[i]+=record['bytes']+overhead
        reports=[]
        for i,members in enumerate(bins):
            p=temp/('evidence-'+str(i+1)+'.zip')
            with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_STORED,allowZip64=False) as z:
                for record in sorted(members,key=lambda r:r['path']):
                    b=(source/record['path']).read_bytes()
                    require(len(b)==record['bytes'] and sha(b)==record['sha256'],'evidence changed during packaging')
                    info=zipfile.ZipInfo('evidence/'+record['path'],(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_STORED
                    z.writestr(info,b)
            require(p.stat().st_size<=archive_bytes,'complete ZIP exceeds original archive limit')
            reports.append(dict(name=p.name,members=members))
        require(inventory(source)==records,'evidence changed after packaging')
        (temp/'index.json').write_text(json.dumps(dict(archives=reports,all_files=records),indent=2)+'\n')
        # Index is duplicated INSIDE both archives and counted in actual bytes.
        index=(temp/'index.json').read_bytes()
        for report in reports:
            p=temp/report['name']
            with zipfile.ZipFile(p,'a',compression=zipfile.ZIP_STORED) as z:z.writestr('index.json',index)
            require(p.stat().st_size<=archive_bytes,'complete archive index exceeds original limit')
        (temp/'index.json').unlink()
        # Publish the complete directory in one same-filesystem rename.
        temp.replace(output)
    return [dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(output.iterdir())]
