"""Read-only native-layout/source audit; never launches the game or OCR."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import zipfile

REVIEW = Path(__file__).resolve().parent
SOURCE = '872a57618c079c5854dea47d361cc7da732378ec'
CHECKOUT = REVIEW/'worktree'
ORIGINAL = Path('/workspace/sightbreak-linux-872a576/builds/layouts-872a576')
EXPORT = Path('/workspace/sightbreak-linux-872a576/builds/linux-872a576/linux/sightbreak.x86_64')
SHA = lambda data: hashlib.sha256(data).hexdigest()
READ = lambda path: json.loads(path.read_text())

def git(*args):
    return subprocess.check_output(['git', *args], cwd=CHECKOUT)

def source_identity():
    paths = git('ls-tree','-rz','--name-only',SOURCE).decode().split('\0')[:-1]
    shipping = hashlib.sha256()
    validation = hashlib.sha256()
    inventory = []
    groups = [[p for p in paths if p.startswith('game/') and 'tests' not in Path(p).parts and '.godot' not in Path(p).parts]]
    groups += [[p for p in paths if p.startswith(directory+'/')] for directory in ('scripts','.github','game/tests')]
    for index,group in enumerate(groups):
        for path in sorted(group):
            if any(p in ('__pycache__','.godot') for p in Path(path).parts) or path.endswith('.pyc'):
                continue
            raw = git('show',SOURCE+':'+path)
            name = path.removeprefix('game/') if index == 0 else path
            (shipping if index == 0 else validation).update(name.encode()+b'\0'+raw+b'\0')
            inventory.append({'scope':'shipping' if index == 0 else 'validation','path':path,'bytes':len(raw),'sha256':SHA(raw)})
    return {'source_commit':SOURCE,'source_game_tree':git('rev-parse',SOURCE+':game').decode().strip(),
            'source_content_sha256':shipping.hexdigest(),'source_validation_sha256':validation.hexdigest(),
            'method':'Independent framed SHA256 of sorted tracked Git-object bytes, with shipping tests excluded and validation directories in declared order',
            'files':inventory}

def png_size(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    return list(struct.unpack('>II',raw[16:24]))

def words(path):
    return [row['text'] for row in csv.DictReader(io.StringIO(path.read_text()),delimiter='\t') if row.get('text','').strip()]

def audit():
    result = READ(ORIGINAL/'results.json')
    identity = source_identity()
    checks = {'exact_git_source':git('rev-parse','HEAD').decode().strip()==SOURCE,
              'receipt_source_matches_git_objects':all(result['source'][k]==identity[k] for k in ('source_commit','source_game_tree','source_content_sha256','source_validation_sha256')),
              'receipt_clean_source':not result['source']['source_dirty'] and not result['source']['source_game_dirty'],
              'actual_ELF_matches_receipt':SHA(EXPORT.read_bytes())==result['executable_sha256']==result['artifact_source']['artifact']['sha256'],
              'four_original_sizes':result['requested_sizes']==[[960,540],[1280,720],[1920,1080],[1280,800]],
              'aggregate_pass_with_original_budget':result['capture_generation_passed'] and result['elapsed_seconds']<520,
              'receipt_source_unchanged':result['exact_source_unchanged'],
              'pinned_engine':result['engine']=='4.7.2.stable.official.ed1daf0bf'}
    cases = []
    for case in result['cases']:
        directory = ORIGINAL/('x'.join(map(str,case['size'])))
        captures = case['captures']
        fences = [a for a in case['actions'] if a['event']=='rendered_ui_fence']
        ocr=[]
        for command in case['ocr_commands']:
            label=command['label'];stem=label.removesuffix('-footer')
            original=directory/(stem+'-ocr-original.png');tsv=directory/(label+'.tsv')
            ocr.append({'label':label,'original_sha256':SHA(original.read_bytes()),'receipt_hash_matches':SHA(original.read_bytes())==command['original_sha256'],
                        'tsv_sha256':SHA(tsv.read_bytes()),'tsv_bytes':tsv.stat().st_size,
                        'tsv_nonempty_words':len(words(tsv)),'elapsed_seconds':command['elapsed_seconds'],'timeout_seconds':command['timeout_seconds'],
                        'exit_code':command.get('exit_code'),'thread_environment':command.get('thread_environment'),'error':command.get('error')})
        named=[]
        for capture in captures:
            path=directory/capture['name'];named.append({'name':capture['name'],'sha256':SHA(path.read_bytes()),'receipt_hash_matches':SHA(path.read_bytes())==capture['sha256'],
                                                      'dimensions':png_size(path),'dimensions_match':png_size(path)==case['size']})
        menu = next(o for o in reversed(ocr) if o['label'].startswith('menu-ready-'))
        menu_words={re.sub('[^A-Z]','',w.upper()) for w in words(directory/(menu['label']+'.tsv'))}
        case_checks={'case_pass_with_original_budget':case['capture_generation_passed'] and case['elapsed_seconds']<120,
                     'matching_standalone_case':READ(directory/'results.json')==case,
                     'native_exits_and_owned_cleanup':case['native_menu_exit']==case['native_live_exit']==0 and case['cleanup_errors']==[] and all(c['exit_code']==0 for c in case['commands']),
                     'two_drawn_frame_fences':len(fences)==(7 if case['size']==[1280,720] else 3) and all(f['final_drawn_frames']>=f['first_drawn_frames']+2 for f in fences),
                     'original_named_capture_bytes_and_dimensions':all(c['receipt_hash_matches'] and c['dimensions_match'] for c in named),
                     'all_original_OCR_inputs_match':all(o['receipt_hash_matches'] for o in ocr),
                     'all_native_OCR_commands_successful_and_bounded':all(o['exit_code']==0 and not o['error'] and o['elapsed_seconds']<o['timeout_seconds']<=12 and o['thread_environment']=={'OMP_THREAD_LIMIT':'1'} for o in ocr),
                     'actual_retained_final_menu_TSV_contains_required_words':{'SIGHTBREAK','DEPLOY'}.issubset(menu_words),
                     'demo_scope_declared':'--demo' in next(c['command'] for c in case['commands'] if c['label']=='live-layout')}
        cases.append({'size':case['size'],'checks':case_checks,'all_checks_passed':all(case_checks.values()),'elapsed_seconds':case['elapsed_seconds'],
                      'named_captures':named,'ocr':ocr,'fences':[{'label':f['label'],'first':f['first_drawn_frames'],'final':f['final_drawn_frames']} for f in fences],
                      'native_menu_exit':case['native_menu_exit'],'native_live_exit':case['native_live_exit'],'cleanup_errors':case['cleanup_errors'],'touch_toggle':case['touch_toggle']})
    (REVIEW/'source-reconstruction.json').write_text(json.dumps(identity,indent=2)+'\n')
    output={'checks':checks,'all_checks_passed':all(checks.values()) and all(c['all_checks_passed'] for c in cases),
            'aggregate_wall_seconds':result['elapsed_seconds'],'actual_ELF_sha256':SHA(EXPORT.read_bytes()),'cases':cases,
            'scope':'Independent read-only local capture-generation audit. No native/OCR execution, physical performance, complete journey, full match or visual score is implied.'}
    (REVIEW/'local-recomputed.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'checks':checks,'all_checks_passed':output['all_checks_passed'],'case_checks':[c['checks'] for c in cases]}))

def archive():
    destination=REVIEW/'local-layouts-originals.zip'
    if destination.exists():
        raise RuntimeError('Preserve original archive; refusing to overwrite')
    files=[]
    for path in sorted(ORIGINAL.rglob('*')):
        relative=path.relative_to(ORIGINAL)
        if any(p in ('cache','.cache','shader_cache','.godot','__pycache__') for p in relative.parts):continue
        if path.is_symlink():raise RuntimeError('Unexpected symlink')
        if not path.is_file():continue
        if path.suffix not in ('.png','.json','.jsonl','.log','.tsv'):raise RuntimeError('Unexpected evidence suffix')
        raw=path.read_bytes();files.append({'path':relative.as_posix(),'bytes':len(raw),'sha256':SHA(raw)})
    with zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as bundle:
        for item in files:
            info=zipfile.ZipInfo('originals/'+item['path'],(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            raw=(ORIGINAL/item['path']).read_bytes()
            assert len(raw)==item['bytes'] and SHA(raw)==item['sha256']
            bundle.writestr(info,raw,compresslevel=1)
    index={'original_directory':str(ORIGINAL),'archive':destination.name,'bytes':destination.stat().st_size,'sha256':SHA(destination.read_bytes()),
           'excluded':'Only developer/import/shader caches; all original PNG, TSV, JSON, JSONL and log evidence is retained byte for byte',
           'files':files}
    (REVIEW/'local-archive-index.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps({'archive':destination.name,'bytes':index['bytes'],'sha256':index['sha256'],'files':len(files)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout',type=Path,default=CHECKOUT)
    parser.add_argument('--original',type=Path,default=ORIGINAL)
    parser.add_argument('--export',type=Path,default=EXPORT)
    parser.add_argument('--output',type=Path,default=REVIEW)
    parser.add_argument('--no-archive',action='store_true',help='Audit only, without creating another archive')
    args=parser.parse_args()
    CHECKOUT,ORIGINAL,EXPORT,REVIEW=args.checkout,args.original,args.export,args.output
    REVIEW.mkdir(parents=True,exist_ok=True)
    audit()
    if not args.no_archive:archive()
