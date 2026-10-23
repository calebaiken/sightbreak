# Independent combined-source integration review

Verdict: **APPROVE INTEGRATION** at
`34dbd97a99068642cf07fa62288fe7437751c37e` for the planned single
`arm-macos-ios` qualification lane. This approves the inspected source
integration for execution. It does not accept any native component result.

The root checkout was clean at that exact HEAD before and after inspection.
All four Mac scripts and `desktop-alpha.yml` are byte-identical to approved
`bd9ac47`; the existing Mac input/preflight/capture/menu, build manifest,
observation reader, export/toolchain and strict native-log dependencies are
unchanged. Source approval conditions and original component budgets therefore
carry through this integration.

The only additional product change against the approved Mac source is the
accepted three-line bot guard that skips a known-dry holstered primary. The
bot source, common fixture/UID, maintained native registry and validate command
match accepted `8e8d13e` exactly. The independent comparison verdict `f947350`
qualifies that narrow correction; it does not qualify this new whole source.
The fixture hash remains
`059a49bdf1e755a049e0fa4a904d303eb5fc9ce1fd05cbfc993ee9881aa46863`.

The native registry has all 14 original suites in order plus `bot_dry_weapon`,
using the accepted explicit headless/Dummy command and unchanged 120-second
suite limit. The original strict error/leak function, per-suite userdata
isolation, failure propagation and finalization remain intact. The new fixture's
previous 590-check result is historical evidence; its actual ARM result must be
read from the new run. Existing `tests/*` export exclusions remain unchanged.

The additional market oracle, recovery/guard/refresh tests and standalone pure
workflow match accepted `985a9d71` exactly. They do not enter the Mac controller,
exporter, native registry or desktop workflow. Their service campaign is not
invoked by the ARM lane.

The desktop workflow is unchanged from the approved freeze, including host
selection, original journey/objective/full-match commands, stage limits and
strict failures. Selecting `arm-macos-ios` produces one `macos-15` matrix entry;
it does not select the independent local Linux diagnostic. A failed native
suite remains a failed gate even where the existing workflow retains later
diagnostics or narrower component evidence.

An immutable `git archive` snapshot of the combined source, with exact tracked
screen-identity and first-leak fixtures, passes 80 pure checks: the 9 independent
controller groups, all 57 candidate/original Mac checks, 6 first-failed-leak
controls and 8 verbose-diagnostic controls. Every process exit is zero. Commands,
counts and retained raw output are in `integration-tests.json` and `logs/`.
Code/workflow diff whitespace checks pass. The unrestricted historical-report
diff reports trailing whitespace in retained raw logs; those bytes were
preserved and are not source or workflow defects.

The independently recomputed identity matches the clean root receipt:

| Identity | Value |
| --- | --- |
| Executing source under review | `34dbd97a99068642cf07fa62288fe7437751c37e` |
| Game tree | `55691684d31d44f1680141954bbe530443de9d1f` |
| Shipping content SHA-256 | `bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50` |
| Validation SHA-256 | `408ff238275cea29a466ed5b99c03f82ee8d1d18205100fe158d07bda0251671` |

`integration-source.json` also binds the five unchanged Mac file hashes. A
metadata-only successor is covered only if explicitly identified and its
game/scripts/workflow bytes and these content/validation hashes remain equal.
The export manifest and native receipts must name that actual executing HEAD;
neither `bd9ac47` nor old native results can substitute for it.

The largest remaining gap is fresh actual ARM evidence for this combined
artifact: private userdata before Deploy, actual living fire/reload and original
pixels, FIELD MENU/LEAVE, original deadlines, neutral ordinary close and strict
cleanup. No export, engine, compiler, service, CI dispatch or native input was
run during this integration review.
