"""Authorized old-data negative read; no actual driver or separate input reader."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert os.sched_getaffinity(0)=={4};a.output.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('registered_inventory',a.data.parent/'check_archived_availability.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
sys.path.insert(0,str(a.source.resolve()/'scripts'));rows=[]
with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('subprocess.check_output',side_effect=AssertionError('Git forbidden')),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')):
    import windows_shutdown_study as study
    for name,root in audit.ROOTS.items():
        before=audit.inventory(root);registered=json.loads((a.data.parent/'archived-availability'/(name+'-before.json')).read_text());assert before==registered
        result=study.trial_evidence(root,context=None);after=audit.inventory(root);assert before==after
        assert result['strict_passed'] is False and result['evidence_complete'] is False
        for filename in ('controller-stdout.log','controller-stderr.log'):assert 'missing required file: '+filename in result['evidence_errors']
        (a.output/(name+'-result.json')).write_text(json.dumps(result,indent=2)+'\n')
        (a.output/(name+'-before.json')).write_text(json.dumps(before,indent=2)+'\n');(a.output/(name+'-after.json')).write_text(json.dumps(after,indent=2)+'\n')
        rows.append(dict(run=name,root=str(root),files=len(before),original_bytes=sum(row['bytes'] for row in before),originals_unchanged=True,
                         required_present=result['availability']['present_required_files'],strict_passed=False,errors=result['evidence_errors'],strict_errors=result['strict_errors'],native_invocations=0))
(a.output/'SUMMARY.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps([{k:row[k] for k in ('run','files','originals_unchanged','required_present','strict_passed','native_invocations')} for row in rows]))
