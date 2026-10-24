#!/usr/bin/env python3
"""Replay sealed original full-stream falsifier on actual source bytes."""
import argparse
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4] and not a.output.exists()
sys.path.insert(0,str(a.source.resolve()/'scripts'));v=importlib.import_module('verify_bot_objective_observation')
raw=gzip.decompress(a.input.read_bytes());error=None
try:detail=v.verify(raw.decode(),a.source.resolve())
except (ValueError,KeyError,TypeError) as e:accepted=False;error=str(e);detail=None
else:accepted=True
receipt=dict(checkout_head=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),cpu_affinity=[4],reader_sha256=hashlib.sha256((a.source/'scripts/verify_bot_objective_observation.py').read_bytes()).hexdigest(),raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),gzip_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),expected_accepted=False,actual_accepted=accepted,error=error,detail=detail,met_expectation=not accepted)
a.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));raise SystemExit(accepted)
