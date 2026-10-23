# Independent source verdict: d370774c rejected

The original fail-closed path wins this round. The explicit owned-AX candidate improves target selection in its synthetic happy path, but it can post expired events and accept replaced evidence. Verdict: **REJECTED SOURCE ONLY**. No native attempt, gameplay qualification or gate closure follows.

Review criteria were committed/pushed as c63f071d before candidate implementation, output or diff inspection. The critic is separate from the builder. The examined source is exact d370774c40f2ad63774519e0c258f06d765b9e0a on base db9d305f. Review uses fetched source and original retained evidence, with a disclosed source comparison rather than a blind visual claim.

The largest correctness gap is the time between SemanticDeployTarget.point() and the real CGEventPost. MacOrdinaryUI.post validates before calling the original superclass post; that superclass sets event flags and writes its trace before the OS post. A synthetic 5.001-second delay in that existing trace causes a move at5.201 seconds against expiry5.0, and a down at5.401 against expiry5.0. The down case completes the synthetic schedule with PASS/code0. A final guard must follow trace work and be adjacent to the actual OS post, without renewing the deadline or changing budgets.

Independent controls also show:

| Boundary | Observed result at exact candidate | Required behavior |
| --- | --- | --- |
| Replace original focused PNG with identical bytes/new inode after movement | Synthetic PASS0; down/up posted | Reject before down |
| Replace original focused JSON with identical bytes/new inode after movement | Synthetic PASS0; down/up posted | Reject before down |
| Replace AX JSON with identical bytes/new inode after movement | Synthetic PASS0; down/up posted | Reject before down |
| FIFO evidence (stat size0) | Reaches ordinary Path.read_text | Reject special file before any read |
| File grows after initial stat beyond512KiB | JSON reader reads/returns the oversized content | Enforce actual read bound with stable ordinary-file identity |
| Window PID float, CG owner PID float, examined count float, zero-event/permission booleans | New private_shape plus contract accepts all five individual mutations | Reject malformed native field types |
| Exception after synthetic down delivery | Original cleanup posts up; owned set empty | Pass: preserve release behavior |

The complete adversarial control is test_independent_boundaries.py. Original output independent-d370774c.log has five failures across four methods; r2 adds deadline checks, r3 corrects the audit to count only events while the semantic target is active, and r4 adds five independently baseline-validated malformed-field cases. The correction removes later FIELD MENU events from the stale-target set; the first expired Deploy down remains a decisive failure. No production source was changed by the critic.

The builder independently reported another retained defect while review was in progress: acquire_target rehashes PNG/JSON without comparing with the earlier capture() accepted hashes, allowing pre-acquisition replacement preserving IHDR. That reported failure is not substituted for this critic's independent after-movement controls. The builder is preparing a new exact revision.

The independent full mode/blob union passes: base507 non-doc paths, candidate527,503 unchanged,24 bounded additions/changes, zero undeclared delta; all13 exact d5277180 imports and every declared SHA256 match. Game tree1632ae1175028665ddb4cb72e0afba56f723de5d and desktop-alpha workflow are unchanged. The initial source-union control mistakenly prepended an already complete fixture path; source-union-first-control.json retains that invalid control output, and verify_source_union.py corrects it. The candidate's initial HANDOFF game-tree typo was sent to the builder; it is not a game-source change.

Fresh independent exact depth-one initialization has HEAD d370774c, shallow=true, one commit and clean source. The same150 top-level maintained methods pass (136 Mac,9 input preflight,5 strict log, no skips), including nested alias checks. The ordinary default OCR route, original confidence0.5 rejection against0.8, original game and workflow are preserved within source scope. Passing maintained tests do not overturn the independent failures.

Setup limitations are retained explicitly. An initial local fetch using the abbreviated SHA fails before checkout. A full-SHA unfiltered local fetch is stopped after roughly47 seconds before transfer, because it enumerates the large report tree; it was not CPU-pinned. A filtered fetch from the builder's partial shallow repository fails on a missing promisor blob. A fresh supported remote depth-one filtered fetch then obtains the exact candidate; the temporary invalid remote config is removed. No failed setup is called passing. All substantive Python source controls and pure replay run with taskset CPU4. No Godot, native input, import/export, render, CI or runtime observer runs here.

After the source defects are corrected and independently retested, the largest remaining qualification gap will still be actual ordinary ARM Mac Deploy/input/gameplay under the original budgets. Source review cannot establish actual post timing, input consumption, per-call native/CF lifetime telemetry, full descendant absence, binary reparse, Intel/iOS/physical or whole-release acceptance.
