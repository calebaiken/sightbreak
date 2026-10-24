#!/usr/bin/env python3
"""Ordinary-only retained AX observer. No input, trust prompt or AX action."""
import argparse
import os
import signal
from pathlib import Path
from macos_ax_live import serve

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pid', type=int, required=True)
parser.add_argument('--window', type=int, required=True)
parser.add_argument('--bounds', type=float, nargs=4, required=True)
parser.add_argument('--nonce', required=True)
parser.add_argument('--budget', type=float, required=True)
parser.add_argument('--deadline', type=float, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
if os.path.lexists(args.report): parser.error('Preserve original AX evidence')
def interrupted(signum, _frame):
    raise SystemExit('Retained AX helper interrupted by signal '+str(signum))
for signum in (signal.SIGTERM, signal.SIGINT): signal.signal(signum, interrupted)
for descriptor in (0, 1): os.set_blocking(descriptor, False)
raise SystemExit(serve(args.pid, args.window, args.bounds, args.nonce, args.budget, args.deadline, args.report))
