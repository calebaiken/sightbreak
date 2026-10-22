# Manual ARM Mac lane

Criteria declared for this separate increment: only an explicit manual
`lane=arm-macos-ios` selects the existing ARM Mac host. Default dispatch,
explicit `all` and push keep the exact original four-host matrix. Every other
workflow field, step, gate, permission, timeout and artifact setting must remain
identical to frozen SDK candidate `90740e0`.

The registered `desktop-alpha.yml` now exposes that choice. The selected host
still runs every existing ARM Mac source regression, package inspection,
startup diagnostic and unsigned iOS compile gate. This reduces host selection;
it does not qualify Windows, Linux or Intel Mac.

The [evaluation script](evaluate_matrix.py) parses the actual YAML, evaluates
its limited GitHub Actions expression for six cases, and compares every other
field against the baseline. It requires the already available PyYAML 6.0.3 and
adds no workflow step or runner dependency. Reproduce from this checkout:

```sh
python docs/reports/gauntlet/m2-ios-compile/arm-lane/evaluate_matrix.py --baseline-ref 90740e0
```

The [recorded output](matrix-evaluation.json) includes both workflow hashes and
the exact expression. Independent review is required before dispatch. After
review, the existing workflow can select the lane with:

```sh
gh workflow run desktop-alpha.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability -f lane=arm-macos-ios
```
