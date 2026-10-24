# Independent ARM ordinary repeat verdict

Verdict: **FAIL** for the ordinary component in run
[`39906639650`](https://github.com/calebaiken/sightbreak/actions/runs/39906639650),
job `120260016569`, at exact approved source
`b2e0293a546961230afbd73e5cd2a1a307d69e94`. The corrected source controls passed,
but actual gameplay never reached Deploy. This report leaves the first failed
iteration `39904830917` and its four test-root errors unchanged.

The actual controller failed after 21.220 seconds with
`Owned visible window or its geometry changed before input`. It posted zero
CGEvents and accepted no captures. At 13.366 seconds it selected PID 14158 /
window 54 with bounds `[0,25,1024,684]`. The read-only background helper then
exited zero, capturing that same PID/window/bounds at scale 1. Its original
1024x684 PNG shows the Godot splash, not a ready home screen. The controller's
post-capture guard rejected the later owned-window context; focus diagnostics
subsequently observed the correct foreground PID but the guard still rejected.

The actual current rows/bounds that triggered rejection were not retained.
The evidence therefore cannot distinguish a missing/replaced window from a
changed rectangle, or identify the replacement geometry or cause. It does not
prove a particular resize, window-ID transition or renderer failure. No menu
target, stock match, living observation, fire/reload HUD, FIELD MENU or LEAVE
receipt exists for this ordinary attempt.

The native attempt does establish a narrow isolation capability in this exact
export. Before any input, the private engine-created `user://` log exists under
`/Users/runner/Library/Application Support/SIGHTBREAK-mac-ordinary-c63854eba9394d269d85dd10aa25a995`.
Its retained bytes have the pinned Godot 4.7.2 official header. All seven original
app file descriptors match the exact export manifest; the copied inventory adds
only the executable-sibling two-setting `override.cfg`, with matching literal
bytes/hash. Original payload file bytes/modes, executable and PCK descriptors
remain bound to the actual export. Original/copied payload and source are
reported unchanged, and the entire default userdata before/after inventories
are exactly equal, including file modes. Private caches/logs remain retained;
no private gameplay profile was fabricated. This capability is not gameplay or
successful ordinary-close acceptance.

Failure cleanup also remains failed ordinary-close evidence. Final controls
are neutral with no owned held inputs or release errors. The public AppKit
termination request was accepted, but its failure-path wait timed out. The
client required SIGTERM and exited -15. The client, compiler and background
helper groups are all gone; a forced cleanup cannot satisfy the ordinary-close
gate.

The original decoded job log and both bounded original artifact ZIPs are
retained here. Downloaded outer hashes match the published GitHub digests:

| Artifact | ID | SHA-256 |
| --- | --- | --- |
| Raw receipts | `12481064150` | `368bbfda7945603ff3b00148679769f9ec73dd922d6b36161d296089c8e80fb8` |
| QA and original PNGs | `12481084191` | `e7b03cc568f395931bf1599155855f0398a89a364d76a33df485acf9acc5577f` |

`audit_native.py` passes 658 read-only receipt/hash/state predicates while
explicitly recording `ordinary_component_passed=false`. All 206 indexed receipts
verify; 204 overlapping QA files are byte-identical. Of 12 original PNGs, eight
were newly visually inspected and four are byte-identical to already inspected
first-run pixels; `images.json` records every hash. All 140 retained QA logs
pass the unchanged strict native error/resource-leak scan. No local engine,
compiler, OCR, recording, native input or CI operation was performed by this
review.

Completed outputs have these separate passing scopes at `b2e0293`:

| Completed output | Bounded finding |
| --- | --- |
| Original source suites | 15 suites / 9,434 reported checks / zero failures. Exact 323-file game inventory matches; native exits and producer probes meet their original bounds. Recorded copied/source preservation and namespace/temp-project cleanup pass. |
| Dry-primary fixture | Actual 84 cases / 48 steps / 590 checks; observable recomputation passes 1,974 predicates. Unlogged full protected snapshots remain outside that recomputation. |
| Preflight/menu | Preflight ready in 5.942 seconds. Existing Settings/Escape menu passes in 37.760 seconds at PID 13811 / window 44, with five posts, original mapped home/settings/home pixels, neutral releases, ordinary exit zero and all six owned groups gone without signals. |
| Default graphical startup | Original exported-menu images inspected; five clean bounded current/frozen/minimal diagnostics. Hosted ANGLE/Apple Paravirtual startup proves no physical-device FPS or gameplay gate. |
| Unsigned iOS compile | 110.938 seconds total, actual Xcode device build 74.829 seconds; all 15 command groups report no live survivors or cleanup errors. Native unsigned arm64/PCK/134-resource attestation passes. The large final binary was not downloaded or independently reparsed; installation/simulator/device acceptance remains unverified. |

The actual Mac executable hash is
`7d9356c95460af116f80a113e800f570aa8fe5f01993257936cc610d49f2f33a`.
All source receipts bind game tree
`55691684d31d44f1680141954bbe530443de9d1f`, content hash
`bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50` and
validation hash
`d7cc1c07766131c54a17839c8236eddae6adc505f54f52b1c5e07b9c82458773`.
Completed outputs cannot transfer to a later source or erase this failed step.

The largest remaining gap is stable, observed owned-window readiness before
input, followed by the wholly unreached living gameplay/close gates. A future
source change must retain the missing current-window observations and remain
inside the existing budgets without resolution/quality or gameplay changes.
No further source or execution is approved by this native verdict.
