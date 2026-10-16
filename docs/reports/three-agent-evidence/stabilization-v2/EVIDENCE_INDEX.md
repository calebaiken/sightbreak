# Evidence layout

The previous campaign remains outside this directory, unchanged. `source-manifest-r2.json` binds the complete V2 campaign and final exports to 701ce2c; the original `source-manifest.json` binds the earlier partial aee6 attempt. Source identity and all recorded failed attempts remain explicit.

Independent reports are retained verbatim: `ai/REVIEW.md`, `audio/CAUSALITY_REVIEW.md`, `timing/REPORT.md`, `network-review/NETWORK_REVIEW.md`, and `graphics/GRAPHICS_REVIEW.md`. Their absolute links identify the reviewer's real source/evidence files in the current workspace. The adjacent probes, JSON and raw logs provide portable source/command/result records.

`aborted-matrix/` retains the partial aee6 attempt: the natural bot match completed but leaked 13 deferred audio objects, prompting the same teardown fix before the complete frozen rerun. `aborted-network-r2/` retains the orchestration mistake of starting before editor import completed. Its first server failed to resolve TacticalMatch; it is not classified as a product networking defect. The complete imported campaign is retained separately.

Graphics retain all 232 accepted-original hashes, eight contact sheets, all command/CSV records, and selected decisive originals including normal074/078 and consecutive calm066/067. The full 232 PNG collection remains at `/workspace/reviews/stabilization-v2-20261016/graphics/`; it is not all committed as duplicate binary imagery. Unsupported snapshot-argument output is explicitly discarded in the review. Timing retains raw failed controls, per-frame clock records and selected source-bound failed WAVs; complete WAV outputs remain in the external review directory.

The broad negative-control wrapper's single unexplained baseline failure stays preserved in `audio-maintained-negative-controls.txt`; it did not run its mutations. Subsequent exact maintained baseline runs 10/10 and isolated A5/A6/A7 controls 3/3 are separate evidence; neither overwrites the earlier failure. There is no claim of universal audio determinism.

The final SHA256SUMS file covers each retained evidence file. Its verification is separate from platform package checksums and the GitHub aggregate artifact digest.

## Final V2 records

- `matrix-r2/MATRIX.md` and `summary.json`: complete clean frozen **74/74** campaign; original 64/70 is unchanged. All top-level and nested raw logs, including userdata logs, are retained. Deliberate legacy handshake diagnostics and staged historical logs remain distinguishable from current product failures.
- `network-r2-imported/`: all **12/12** ten-client condition summaries, raw client/server/frame records and campaign index; complete import precedes execution.
- `builds/`: final local package manifest, five SHA256 descriptors, source records and actual package verification. These are local hashes; use the CI bundle's own checksums for CI Android packages signed with its key.
- `native-network-r2/`: actual exported ELF input/authority receipts, screenshots and logs; later `08-settled.png` proves rendered reload completion.
- `native-offline-r2-live-input/`: accepted living-player **14/60 → 15/59** fire/reload flow, separately hashed a9d873e controller, original screenshots, OCR/result and clean native logs. `native-offline-r2/` and `native-offline-r2-live/` retain earlier weak/failed driver attempts, not accepted gameplay proof.
- `actions-v2-final-run.json`, jobs/artifact/download receipts and decoded job log: completed successful V2 delivery, frozen 701 source, aggregate artifact digest and successful supported-connector download. The earlier `actions-v2-runs.json` is an in-progress snapshot only.
- `final-source-heads.json` and `gemini-after-freeze-compare.json`: final remote preservation check and Gemini's newer 48eb058, expressly unvalidated and not integrated into V2.
- `graphics-maintained-negative-controls.txt`: N25/N26/N27 caught; audio controls and the earlier broad-wrapper failure remain separate.
- `final-review/`: verbatim final independent audit, payload/source/checksum, native evidence, network, matrix and delivery audits. Pending snapshots remain historical; the final addendum governs completed results.

The external review root retains complete PNG/WAV collections and machine caches. No cache binaries or full duplicated fixture source trees are added here. Raw logs are retained verbatim even when nested under state directories; local state configuration and cache databases are excluded. The overall V2 report and reproduction guide are the authored navigation layer.
