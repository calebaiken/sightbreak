# Independent diagnostic source admission

Verdict: **CONDITIONAL ACCEPT for one root-owned read-only ARM AX diagnostic** at exact source `d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53`. Preregistration `6cfc5d8d` was committed and pushed before any new dispatch or output was inspected. No actual native output has been inspected for this decision.

The root may create the fresh frozen qualifier ref `qualifier/m2-mac-ax-r2-read-only-d6cb78aa` at that source and issue exactly:

```sh
gh workflow run desktop-alpha.yml -R calebaiken/sightbreak --ref qualifier/m2-mac-ax-r2-read-only-d6cb78aa -f lane=arm-macos-ax-read-only
```

Root must verify and record the remote qualifier object and the run's full head SHA. This admission does not cover a different combined commit until its full SHA and exact source binding have been independently checked. A rejected dispatch request does not authorize a fallback normal lane or full-journey retry. This critic will not dispatch.

## Inspected route and controls

The exact workflow has only two job definitions. The `native` job excludes a workflow_dispatch with `lane=arm-macos-ax-read-only`. The separate `macos_ax_read_only` job requires the public repository, workflow_dispatch event and that exact lane, runs solely on `macos-15` with a 20-minute outer job timeout, and runs the source/privacy tests, pinned native editor/template setup, exact macOS export, one read-only controller invocation, then always-on bounded evidence retention. The diagnostic controller step has a six-minute outer ceiling. No normal input, gameplay, strict native suite, iOS or unrelated diagnostic step is reachable in this job. The explicit input is required; default `all` is outside this admission.

The controller imports the unchanged original budgets: total 300, compile 60, window 30, menu 60, focus 5, capture 25 and close 20 seconds. Its single capture-helper compile uses that compile ceiling; its exact launch amendment is public `--accessibility always` before the existing separator. It pins one owned PID/window, requests public AppKit focus once, observes native menu pixels and then runs one bounded observer. Guarded calls reject late returns under the original deadlines. The AX caps remain 5 seconds, three snapshots at 0.1-second spacing, cumulative 256 nodes, depth 16, 512 KiB receipt, complete titles within 512 UTF-8 bytes and 0.25 seconds per AX call. Native call interruption itself remains unproved.

The read API/attribute allowlists, text-entry pruning, title-role restriction and AppKit selector allowlist exclude CGEvents, AX actions, AX attribute setters, permission prompts, global search and account/text values. Public typed AXValue geometry decoding is used solely for CGPoint/CGSize. The exact native PNG/Vision defaults and the ordinary 0.8 selector remain unchanged. The observer emits semantic-exposure metadata, and the contract returns no click target. Menu-owned private default profile creation is disclosed and inventoried by hash; profile fields are not parsed or retained, no Deploy/reward action is sent, and a match trace fails finalization. Source, staged payload, default userdata, ordinary exit and owned-group cleanup remain required.

Supplemental pure replay on CPU 4 passes 25 AX structural/native-boundary/source tests and eight mocked controller tests. These include exact normal-workflow preservation, unchanged helper/runtime hashes, no extra read APIs, launch/caps, late returns, CF +1 ownership, complete UTF-8/UTF-16/NUL/control behavior, profile disclosure, failed cleanup and deadline falsifiers. Console observations and exact source/file fingerprints are retained in [source-admission-receipt.json](source-admission-receipt.json). The separate fresh source critic's full acceptance and retained rejection are preserved at `114f22249d9fe9f8aad8869ff00688b438e4f194` and `12ec93dd3ccfdaab63ab1d16facbfdb725d9c8b5`; this scoped replay does not replace them.

## Required actual decision

No native ABI, actual TCC trust, AX string conversion, exported menu tree, scale/frame agreement, native timing or cleanup is established by source admission. Trust denial or missing/ambiguous/late semantics must remain a blocker or failure. Original ARM run `39920948579` and its 0.5 native/fixed 2x OCR rejection stay failed. No new ordinary journey, gameplay input, earned progression, broad accessibility or release acceptance is authorized. After root supplies run/job IDs, the independent actual review will reopen original logs, bounded raw JSON/PNG artifacts and provenance under the preregistered gates, then report the winner, why and largest remaining deficiency without a numeric score.
