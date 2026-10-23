# Native source coverage candidate

The native runner now maintains fourteen suites. `transaction_journal` and
`gunplay_rules` follow the original twelve in both the default order and CLI
choices. The only command exception is an explicit gunplay argument list for
`gunplay_rules_probe.gd` with `--audio-driver Dummy`, matching the accepted
validator invocation. Journal uses the existing standard filename convention.

This candidate is based on `ecc2690dc783a3243291f8ac3438d44fe0151117`.
[Criteria](CRITERIA.md) were committed as `5e18bea` before the runner edit.
Implementation is limited to `scripts/run_native_regressions.py`; its final
SHA-256 is recorded below. No game, test, warning-parser, diagnostic, validator
or workflow file changed. The two original runner lines changed only to append
the suites and select the explicit argument exception. Suite execution still
uses the same 120 second limit and existing isolation, strict-log, producer,
inventory and cleanup paths.

Runner SHA-256:
`4d13e981f9a16581ba8247028dc3688f06db814e357b1a0b346257b13e93f5af`.

## Pure verification

Commands ran from `/workspace/sightbreak-native-new-systems-coverage` with
Python 3.12.14. Every command exited zero:

```sh
PYTHONPATH=scripts python3 -m unittest -v scripts.test_diagnose_native_input_mode scripts.test_native_first_leak
PYTHONPATH=scripts python3 -m unittest -v scripts.test_build_manifest
python3 scripts/run_native_regressions.py --help
git diff --check
```

The [diagnostic output](diagnostic-controls.log) retains all fourteen passing
methods, including expected fake-process timeout and rejection receipts. The
[manifest output](manifest-controls.log) retains twenty-two passing provenance
methods and two passing native log-parser methods. The
[CLI output](cli-help.txt) exposes all fourteen maintained choices. No new tests
were added. These existing controls exercise fake processes or temporary
fixtures; no native engine, OCR, service or CI process was launched.

## Review and remaining evidence

Independent source review is pending. The builder has not approved this
candidate. The parent will arrange actual private Linux execution of the two
new suites and the complete aggregate, followed by actual Windows and ARM
lanes after acceptance. Pure checks do not establish native suite completion,
cleanup on those platforms, player experience or release-gate acceptance.

The largest remaining gap is actual native execution on the integrated source.
Earlier platform failures and strict leak gates remain part of their original
evidence; this registration does not change their result.
