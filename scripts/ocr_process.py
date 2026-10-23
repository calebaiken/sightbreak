#!/usr/bin/env python3
"""Stream OCR I/O inside the caller's prelaunch process-containment boundary.

This worker does not provide standalone process-tree ownership. Its caller must
launch it through matrix_process.run_process before it creates the OCR child.
"""
import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--stdout', type=Path, required=True)
    parser.add_argument('--stderr', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('an OCR command is required')
    with args.input.open('rb') as image, args.stdout.open('wb') as output, args.stderr.open('wb') as error:
        return subprocess.run(command, stdin=image, stdout=output, stderr=error, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
