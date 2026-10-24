"""Run the retained independent exhausted-primary oracle on this actual native suite."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_exhausted_rows import parse, audit


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('log', type=Path)
parser.add_argument('checkout', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
records, other = parse(args.log)
result = audit(records, args.checkout)
headers = [value for _, kind, value in records if kind == 'POLICY_HEADER']
terminals = [value for _, kind, value in records if kind == 'POLICY_RESULT']
checks = {
    'single_current_policy_header': len(headers) == 1 and all(headers[0].get(k) == v for k, v in
        {'range_cases_expected': 9, 'reserve_steps_expected': 20, 'total_policy_rows_expected': 1268}.items()),
    'single_current_policy_terminal': len(terminals) == 1 and all(terminals[0].get(k) == v for k, v in
        {'policy_rows': 1268, 'range_rows': 9, 'reserve_rows': 20, 'failures_so_far': []}.items()),
    'all_1268_emitted_rows_independently_reconstructed': sum(result['row_counts'][k] for k in
        ('CASE', 'STEP', 'CONTROL_STEP', 'POLICY_RANGE', 'POLICY_RESERVE_STEP')) == 1268,
}
result.update(checks=checks, all_exhausted_checks_passed=all(checks.values()),
              original_log_sha256=hashlib.sha256(args.log.read_bytes()).hexdigest(), nonrecord_stdout=other)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ('all_exhausted_checks_passed', 'independent_predicates',
                                              'row_counts', 'reported_fixture_checks')}))
