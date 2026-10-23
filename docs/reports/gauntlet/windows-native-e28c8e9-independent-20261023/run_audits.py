"""Run read-only original-receipt audits, preserving every command and outcome."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('receipts', type=Path)
    p.add_argument('full', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = Path(__file__).resolve().parent
    checkout = report.parents[3]
    a.output.mkdir(parents=True, exist_ok=False)
    def run(spec):
        name, script, args = spec
        command = [sys.executable, str(report/script), *map(str,args), '--output', str(a.output/(name+'.json'))]
        began = time.monotonic()
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180, cwd=checkout)
        log = a.output/(name+'.log')
        log.write_bytes(result.stdout)
        return {'name': name, 'command': command, 'exit': result.returncode,
                'wall_seconds': time.monotonic()-began, 'log_bytes': len(result.stdout),
                'log_sha256': hashlib.sha256(result.stdout).hexdigest()}
    source = run(('source-Windows-recomputed','audit_windows_source.py',[checkout,a.receipts]))
    native = a.output/'source-Windows-recomputed.json'
    specs = [
        ('raw-recomputed','verify_receipts.py',[a.receipts]),
        ('native-commands-recomputed','audit_native_commands.py',[a.receipts]),
        ('journey-OCR-recomputed','audit_journey_ocr.py',[a.receipts]),
        ('phase-captures-recomputed','audit_phase_captures.py',[a.receipts,'--full',a.full]),
        ('focus-actual-recomputed','audit_focus_actual.py',[a.receipts,a.full]),
        ('objective-stages-recomputed','audit_objective_stages.py',[a.receipts]),
        ('settings-route-recomputed','audit_settings_route.py',[a.receipts]),
        ('failure-diagnostics','audit_failure_diagnostics.py',[a.receipts]),
        ('raw-sources-logs-recomputed','audit_raw_sources_logs.py',[a.receipts,'--source-audit',native]),
        ('export-identity-recomputed','audit_export_identity.py',[a.receipts,native]),
        ('full-QA-crosscheck','audit_full_qa.py',[a.receipts,a.full]),
        ('gunplay-recomputed','audit_gunplay.py',[a.receipts/'evidence/regressions/gunplay_rules.log']),
        ('dry-observable-recomputed','recompute_dry_observable.py',['--mode','candidate',a.receipts/'evidence/regressions/bot_dry_weapon.log']),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = [source,*pool.map(run,specs)]
    records.append(run(('runtime-completeness','audit_runtime_complete.py',[a.receipts,a.full,a.output])))
    manifest = {'source_commit': 'e28c8e90b9ef2d0c766bd9152c194e3197ceba9a', 'run_id': 39926044462,
                'records': records, 'scope': 'Read-only pure review of retained native original outputs; no engine, OCR, native input, compiler or CI.'}
    (a.output/'commands.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'records': len(records), 'command_failures': [r['name'] for r in records if r['exit']],
                      'output': str(a.output)}))


if __name__ == '__main__':
    main()
