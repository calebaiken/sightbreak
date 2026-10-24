"""Exact old benchmark; only source-label adapter changes in the second run."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert os.sched_getaffinity(0)=={4};a.output.mkdir(parents=True,exist_ok=False)
source=a.source.resolve();os.environ['STUDY_REVIEW_SOURCE_ROOT']=str(source)
folder=a.data/'builder-handoff/frozen-own'
literal=(folder/'old75-propagation-original.py').read_bytes();adapted=(folder/'old75-propagation-replay.py').read_bytes()
assert literal.replace(b"source='c90fedfd56a09bd0ba13cce5565ccd160891c3fb'",b"source='0f478a078277fdb0d711837bef67cf14262d9d8f'",1)==adapted
rows=[]
with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('subprocess.check_output',side_effect=AssertionError('Git forbidden')),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')):
    for mode,raw in [('literal',literal),('metadata-adapted',adapted)]:
        file=a.output/(mode+'.py');file.write_bytes(raw);label=mode+'-result';os.environ['STUDY_REVIEW_RUN_LABEL']=label
        with (a.output/(mode+'.stdout')).open('w') as stream,contextlib.redirect_stdout(stream):
            exec(compile(raw,str(file),'exec'),dict(__name__='__main__',__file__=str(file.resolve())))
        result=json.loads((a.output/(label+'.json')).read_text())
        assert result['actual_passed'] is False and result['calls']==4 and result['cleanup_calls']==0
        assert all(trial['strict_passed'] is False for trial in result['report']['trials'])
        rows.append(dict(mode=mode,original_source_label=result['source'],actual_module_path=str(sys.modules['windows_shutdown_study'].__file__),
                         actual_frozen_source='0f478a078277fdb0d711837bef67cf14262d9d8f',code_sha256=hashlib.sha256(raw).hexdigest(),passed=False,attempts=4,cleanup_calls=0))
(a.output/'SUMMARY.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
