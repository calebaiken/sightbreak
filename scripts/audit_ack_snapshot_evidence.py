#!/usr/bin/env python3
"""Verify a retained matched ACK-observability ZIP without importing or running Godot."""
import argparse
import hashlib
import json
import zipfile

from measure_ack_snapshot_diagnostics import RUNTIME_DELTA, evaluate, legacy_projection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    args = parser.parse_args()
    checks = 0

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(label)

    with zipfile.ZipFile(args.archive) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        results, coverage = {}, {}
        for label, receipt in manifest['runs'].items():
            role = receipt['role']
            check(manifest['source_mapping'][label] == [role, receipt['source_commit']], label + ': mapping')
            raw = archive.read(label + '/observability.json')
            check(hashlib.sha256(raw).hexdigest() == receipt['result_sha256'], label + ': result hash')
            check(archive.read('blind/' + label + '.json') == raw, label + ': neutral/raw payload equality')
            results[role] = json.loads(raw)
            check(not results[role]['failures'], label + ': native assertions')
            for name, run in {**receipt['tests'], 'probe': receipt['probe']}.items():
                log = archive.read(label + '/' + name + '.log')
                check(hashlib.sha256(log).hexdigest() == run['log_sha256'], name + ': raw log hash')
                check(run['exit'] == 0 and not run['logged_error'], name + ': native exit/errors')
            check(receipt['shipping_sha256_by_path'] == receipt['shipping_after_sha256_by_path'], label + ': source frozen')
            coverage[role] = evaluate(results[role])
            check(coverage[role] == receipt['coverage'], label + ': position/coverage recomputation')
            check(coverage[role]['position_and_coverage_consistent'], label + ': geometry and bounds')
        check(legacy_projection(results['baseline']) == legacy_projection(results['candidate']), 'legacy movement and lifecycle outputs identical')
        check(not coverage['baseline']['complete_observability_gate'], 'unchanged baseline fails the new coverage bar')
        check(coverage['candidate']['complete_observability_gate'], 'candidate meets the new coverage bar')
        old, new = [r['shipping_sha256_by_path'] for r in manifest['runs'].values()]
        changed = {path for path in old.keys() | new.keys() if old.get(path) != new.get(path)}
        check(changed == RUNTIME_DELTA, 'only declared runtime paths differ')
    print(json.dumps({'checks': checks, 'failures': 0, 'coverage': coverage,
                      'legacy_outputs_identical': True,
                      'scope': 'author-run archived receipt and position-oracle audit; independent critic acceptance separate'}, indent=2))


if __name__ == '__main__':
    main()
