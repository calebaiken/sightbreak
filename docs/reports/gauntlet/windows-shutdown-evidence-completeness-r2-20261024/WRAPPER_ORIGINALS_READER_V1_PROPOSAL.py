"""UNEXECUTED G3 reader block for separate adjudication; not yet source code.

Copy after existing strict_json/digest/need definitions only if independently
approved. It imports no fixture and never invokes a controller or native API.
The existing Evidence.check handles per-file errors without deleting inputs.
"""
from pathlib import Path
import stat


WRAPPER_STREAMS=('controller-stdout.log','controller-stderr.log')
WRAPPER_REQUIRED=WRAPPER_STREAMS+('publication.json',)
WRAPPER_SCOPE='Complete original streams retained; publication never overwrites'


def wrapper_identity(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_size,
            info.st_mtime_ns,info.st_ctime_ns)


def retained_wrapper_originals(evidence):
    """Measure the sibling scope; observed extras are retained and inventoried.

    Finite reads are not an atomic directory snapshot or native attribution.
    A trusted invocation error is still rejected by process_and_closes.
    """
    root=evidence.root.with_name(evidence.root.name+'.controller-capture')
    data={};records=[];directories={};start=len(evidence.errors)
    detail=dict(directory=str(root),required_files=len(WRAPPER_REQUIRED),
                present_required_files=0,all_files=records,extra_files=[],
                publication=None,complete=False)
    evidence.details['wrapper_originals']=detail
    first=root.lstat()
    need(stat.S_ISDIR(first.st_mode),'wrapper originals directory missing/nonregular/symlinked')
    directories[root]=wrapper_identity(first)
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root).as_posix()
        def read(path=path,relative=relative):
            before=path.lstat()
            if stat.S_ISDIR(before.st_mode):
                directories[path]=wrapper_identity(before);return
            need(stat.S_ISREG(before.st_mode),'nonregular wrapper original: '+relative)
            first_bytes=path.read_bytes();second_bytes=path.read_bytes();after=path.lstat()
            need(first_bytes==second_bytes and wrapper_identity(before)==wrapper_identity(after),
                 'wrapper original changed during read: '+relative)
            data[relative]=first_bytes
            records.append(dict(path=relative,bytes=len(first_bytes),sha256=digest(first_bytes)))
        evidence.check('wrapper/'+relative,read)
    for directory,before in directories.items():
        evidence.check('wrapper directory/'+str(directory.relative_to(root)),
                       lambda directory=directory,before=before:
                       need(wrapper_identity(directory.lstat())==before,
                            'wrapper directory changed during inventory: '+str(directory)))
    for name in WRAPPER_REQUIRED:
        if name not in data:evidence.errors.append('missing required wrapper file: '+name)
    detail['present_required_files']=sum(name in data for name in WRAPPER_REQUIRED)
    detail['extra_files']=[row['path'] for row in records if row['path'] not in WRAPPER_REQUIRED]
    need(len(evidence.errors)==start,'wrapper original inventory incomplete')
    publication=strict_json(data['publication.json'])
    detail['publication']=publication
    need(type(publication) is dict and set(publication)==
         {'invocation_error','publication_errors','capture_scope','files'},
         'wrapper publication keys/container differ')
    need(publication['invocation_error'] is None,'wrapper invocation failed')
    need(type(publication['publication_errors']) is list and
         not publication['publication_errors'],'wrapper publication failed/unresolved')
    need(publication['capture_scope']==WRAPPER_SCOPE,'wrapper publication scope differs')
    receipts=publication['files']
    need(type(receipts) is list and len(receipts)==len(WRAPPER_STREAMS),
         'wrapper stream receipt count differs')
    for name,row in zip(WRAPPER_STREAMS,receipts):
        need(type(row) is dict and set(row)=={'path','bytes','sha256'} and row['path']==name,
             'wrapper stream receipt name/order/keys differ')
        need(type(row['bytes']) is int and row['bytes']>=0 and
             row['bytes']==len(data[name]),'wrapper stream byte count differs: '+name)
        need(type(row['sha256']) is str and row['sha256']==digest(data[name]),
             'wrapper stream hash differs: '+name)
        need(name in evidence.data and evidence.data[name]==data[name],
             'wrapper original/published bytes differ: '+name)
    detail['complete']=True
    evidence.original_streams_complete=True
