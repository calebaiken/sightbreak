"""Bind transferred original PNGs to native Linux receipts without OCR/rendering."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
READ=lambda p:json.loads(p.read_text())

def audit(root):
    receipt=READ(root/'receipts/evidence/layouts/results.json')
    cases=[]
    for case in receipt['cases']:
        size='x'.join(map(str,case['size']));directory=root/('images-'+size)
        index=READ(directory/'qa-receipts-index.json');bad=[]
        for item in index['files']:
            path=directory/item['archive_path']
            if path.stat().st_size!=item['bytes'] or SHA(path)!=item['sha256']:bad.append(item['path'])
        files={p.relative_to(directory).as_posix() for p in (directory/'evidence').rglob('*') if p.is_file()}
        named=[];ocr=[]
        for capture in case['captures']:
            path=directory/'evidence'/capture['name'];raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
            named.append({'name':capture['name'],'sha256':SHA(path),'receipt_hash_matches':SHA(path)==capture['sha256'],
                          'dimensions':list(struct.unpack('>II',raw[16:24]))})
        for command in case['ocr_commands']:
            path=directory/'evidence'/(command['label'].removesuffix('-footer')+'-ocr-original.png')
            ocr.append({'label':command['label'],'hash_matches':SHA(path)==command['original_sha256'],
                        'elapsed_seconds':command['elapsed_seconds'],'timeout_seconds':command['timeout_seconds'],
                        'exit_code':command.get('exit_code'),'thread_environment':command.get('thread_environment'),'error':command.get('error')})
        cases.append({'size':size,'original_index_hashes_match':not bad,
                      'complete_selected_file_set':files=={x['archive_path'] for x in index['files']},
                      'named_captures':named,'ocr_commands':ocr,
                      'all_named_hashes_and_dimensions_match':all(x['receipt_hash_matches'] and x['dimensions']==case['size'] for x in named),
                      'all_original_OCR_input_hashes_match':all(x['hash_matches'] for x in ocr),
                      'all_OCR_exits_successful_within_unchanged_limits':all(x['exit_code']==0 and x['elapsed_seconds']<x['timeout_seconds']<=12 and x['thread_environment']=={'OMP_THREAD_LIMIT':'1'} and x['error'] is None for x in ocr),
                      'TSV_bytes_retained':False})
    return {'cases':cases,'scope':'Original PNG bytes bound to native capture/OCR receipts; native TSV bytes are outside selected remote artifacts'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=audit(args.root);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sizes':len(result['cases']),'all_checks_passed':all(all(c[k] for k in ('original_index_hashes_match','complete_selected_file_set','all_named_hashes_and_dimensions_match','all_original_OCR_input_hashes_match','all_OCR_exits_successful_within_unchanged_limits')) for c in result['cases'])}))
