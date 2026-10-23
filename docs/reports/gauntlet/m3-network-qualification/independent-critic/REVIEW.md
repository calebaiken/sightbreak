# Independent networking qualification review

Verdict: accept the completed synthetic soak, twelve-condition campaign, protocol/privacy controls and separate recovery-contract diagnostic within their stated bounds. Whole G3 remains IN PROGRESS.

The original 18-second impaired lost-close trial FAILED: seven clients had not recovered, leaving three final authority bindings. That result is retained unchanged. The separate 30-second diagnostic passed the existing 20-second recovery episode contract; it does not replace or turn the failed 18-second trial green. No product correction was made for this observation-window finding.

Frozen runtime source is `0ca125dfba637868e6e8e9772ff9c40400413e32` in `/workspace/sightbreak-v1-qualification`. The reviewer launched no engines, altered no implementation files and spawned no child agents. Later documentation commits cannot relabel this runtime source. The exact assigned brief is retained in `BRIEF.txt`.

The bar is the G3 reliability/privacy/identity/integrity/impairment requirement and the retained SIGHTBREAK stabilization-v2 source `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`. This is a named historical regression comparison. Different sources and sessions prevent a controlled improvement or blind A/B claim. The mission acceptance document requires ten-client authoritative match behavior and result recovery; synthetic scripts do not alone close that gate.

Commands run by root on the frozen checkout:

```sh
python3 scripts/test_network_soak.py --clients 10 --port 29870 --out builds/session-qualification/ten-client-soak-r1
python3 scripts/run_network_campaign.py --clients 10 --seconds 18 --port 32500 --out builds/session-qualification/ten-client-campaign-r1
bash scripts/test_network.sh
bash scripts/test_protocol_compat.sh
bash scripts/test_handshake_hardening.sh
```

Independent read-only recomputation:

```sh
python3 recompute.py --source /workspace/sightbreak-v1-qualification --out /workspace/reviews/network-qualification-0ca125d --extra-condition /workspace/sightbreak-v1-qualification/builds/session-qualification/lost-close-clean --extra-condition /workspace/sightbreak-v1-qualification/builds/session-qualification/lost-close-impaired --extra-condition /workspace/sightbreak-v1-qualification/builds/session-qualification/lost-close-impaired-contract-window
```

`raw-checks.json` independently reconciles the individual client/server JSON with the campaign summary, final actor IDs, accepted snapshot freshness, server input ACKs, sampled authority and transport bounds, traffic totals and timing distributions. `raw-source-sha256.json` identifies the original raw files. The single primary `raw-evidence.tar.gz` archive retains producer logs/reports, exact command/exit receipts and integrated source-suite evidence, excluding engines, caches, historical copied projects and userdata. Its complete per-file manifest is `archive-files-sha256.json`.

The soak passes all eleven process reports, all eighty reconnects and six forced round resets. Each client retains its original actor ID; the ten IDs are distinct. Recovery waits for a snapshot accepted after the explicit close and an owner ACK above zero. It takes 0.433–0.517 seconds, median 0.450 seconds. Admission resets the actor ACK to zero, and reconnect clears the snapshot buffer, so the nonzero post-close ACK tests new input acceptance. The server reports peaks of ten actor bindings and ten transports, and zero temporary claims. All eleven logs identify Godot 4.7.2 and contain no logged errors or resource leaks.

The server exits with ten reservations, within its source-defined 60 simulation-second expiry window after client departure. Empty end-of-run binding/admission dictionaries are asserted by the fixture but their individual raw counts are not emitted. The six memory samples rise by 873,120 bytes; the historical fixture rises by 872,152 bytes. These short samples do not demonstrate long-duration leak freedom or reservation expiry cleanup.

The twelve-condition campaign passes all 217 independent checks. Each cutoff has ten distinct original actors, a fresh accepted snapshot per client, fresh server input and bounded sampled transports. The maximum accepted snapshot age is 103 ms, below the unchanged 750 ms fixture gate. Server tick p95 ranges from 5.932 to 6.871 ms; maximum tick-interval p95 is 16.991 ms. Shared measurement start offsets are at most 24 ms and stop lateness at most 30 ms. These are same-host headless diagnostics. Physical network, render, input and human play latency remain unmeasured.

| Condition | New cutoff max age (ms) | Historical max age (ms) | New tick p95 (ms) | New hard prediction corrections | Historical hard corrections |
| --- | ---: | ---: | ---: | ---: | ---: |
| rtt-0 | 56 | 40 | 6.631 | 0 | 0 |
| rtt-50 | 44 | 67 | 6.819 | 0 | 0 |
| rtt-100 | 39 | 37 | 6.522 | 0 | 0 |
| rtt-150 | 39 | 69 | 6.871 | 0 | 0 |
| rtt-200 | 45 | 49 | 6.394 | 0 | 0 |
| jitter | 43 | 74 | 6.364 | 0 | 0 |
| loss | 103 | 24 | 6.295 | 0 | 0 |
| reorder | 45 | 75 | 6.286 | 0 | 0 |
| impaired | 66 | 89 | 6.425 | 0 | 0 |
| blackout | 46 | 24 | 5.932 | 10 | 9 |
| reconnect | 100 | 83 | 6.750 | 9 | 8 |
| prediction-disabled | 50 | 61 | 6.609 | 0 | 0 |

Campaign reconnect welcome recovery takes 2.440–2.999 seconds and retains the same actor. That metric is latched upon welcome; it does not measure the first fresh input ACK. At the final cutoff, all ten server ACKs are 410–445 and accepted snapshot age is at most 100 ms. The regular reconnect condition closes at eight seconds, after its blackout at four through six seconds, so separate lost-close trials cover the historical saturation scenario below.

Prediction remains opt-in in product source. Enabled-prediction ACK error p95 ranges from 0.297 to 0.556 m. Blackout causes ten corrections greater than 2 m, and reconnect causes nine; historical counts are nine and eight. The emitted correction details include reversals of roughly 4 m after the two-second outage. These results establish eventual authority recovery while retaining a prediction-correction limitation. They do not establish smooth movement or acceptable player feel.

The overlapping lost-close controls use blackout 7.8–9.3 seconds, explicit close at eight seconds and two-second retry. The clean trial uses zero added RTT and passes its original 18-second cutoff: ten actors welcome back in 5.688–9.648 seconds, fresh accepted snapshot age at most 43 ms and final ACKs 14–249. The impaired trial adds 200 ms RTT, 50 ms jitter, 3% loss and 15% reordering, seed 7301. At its original 18-second cutoff only three clients are connected, with welcome recoveries 6.296, 7.188 and 9.671 seconds; seven remain connecting, authenticating or joining. Their last accepted snapshots are 10.198–10.256 seconds old. The server has three final authority bindings. No terminal rejection, duplicate authority, transport overflow or logged engine error accompanies that failure.

The existing recovery contract allows one 20-second episode starting at the disconnect, approximately measurement time eight through 28 seconds. An 18-second measurement observes approximately ten seconds after close. Historical `c14dbc0` probe source directly confirms `recovery_seconds = recovered_at - reconnect_at`; its retained maximum 11.602-second recovery would reach measurement time 19.602 seconds in the historical 24-second trial. Thus the failed shorter observation does not alone prove a deadline violation or permanent deadlock. The historical and current seeds and clean RTT differ, so these are scenario references rather than identical repeated benchmarks.

The separately named 30-second `lost-close-impaired-contract-window` diagnostic uses the same source, seed 7301 and impairment parameters as the failed run. All ten original actor IDs regain distinct authority bindings. Same-actor welcome recovery takes 6.233–14.657 seconds after close, within the 20-second contract. All final bindings have ACKs 428–933 and input idle at most 77 ms; accepted snapshot age is at most 99 ms. An independent occupancy calculation bounds first sampled positive server ACKs on replacement peers to 6.474–14.890 seconds after nominal close. This proves restored server input within the contract while keeping welcome and input acceptance measurements separate; it does not measure client ACK delivery latency. The calculation and its conservative bound are retained in `contract-first-ack-checks.json` and `recompute.py`.

Both controls and the diagnostic preserve transport occupancy at or below ten, sampled unique actor ownership, clean engine logs and no reported resource leaks. Root retained all three parent exit/reaping receipts; the reviewer’s final executable-aware process inventory finds zero remaining engines for the frozen checkout. Original soak/campaign runners did not retain per-child PIDs, so their post-run inventories retain that provenance limitation.

Actual frozen-source native network probes pass both clients with 119 aggregate inspected privacy dictionaries. The independent parser also verifies eight protocol combinations and eight hostile-handshake cases. The versioned current/future/prior mismatches reject without admission; unversioned clients are never admitted. Seven engine `ERROR:` lines occur only in the unversioned interoperability controls: six on the current server rejecting old packet shapes and one on the old server receiving current authentication. Both exact signatures and counts are present in the committed historical protocol raw logs. All seven are retained as legacy engine diagnostics. No protocol resource leaks were found. Exact identities are release `e67f2c8`, prior published protocol 5 `89c0e9`, current protocol 6 frozen `0ca125d`, and an isolated current copy with protocol incremented to 7. `protocol-checks.json` retains independent per-case outcomes and every error line.

Root source-suite output at `/workspace/sightbreak-v1-execution/builds/mission-m3/integrated-source-r1` reports tests at `77147c5`. The reviewer independently verified its game tree equals frozen `0ca125d` (`782c26464631f86ad63ddab9de36a969d4e44534`) and all 297 copied resource hashes match the frozen game files. Its ten suite rows have exit zero and clean logs; isolation and cleanup checks pass. Privacy has 55 passing checks, match 75, authority order 178 and movement prediction 725. This is inspection of actual retained native root execution, not a reviewer rerun. Its original test identity remains `77147c5`; identical game bytes permit applying those source checks to the frozen runtime.

The initial post-soak process inventory mistakenly matches its own Bash observer command. The corrected executable-aware root inventory and the reviewer’s independent exact-argv Godot inventory both find no remaining soak engines. The original defect is retained. The runner does not record original PIDs, so these are post-run absence checks rather than per-PID reaping receipts.

Largest remaining G3 deficiency is the lack of an exact-source, account-backed complete ten-client match with durable earned-result recovery on this integrated stack. These guest synthetic fixtures suppress ordinary match progression and claim no rewards. Longer reliability/expiry checks, production authentication deployment, actual network hosts, exported clients and human feedback remain outside this result. The 18-second harsh lost-close acceptance trial remains failed. The separately observed 20-second recovery contract holds in its diagnostic; long recovery and prediction snaps remain player-experience limits. These results establish no new product defect requiring a patch and do not close any whole release gate.

Final frozen source identity is clean: game tree `782c26464631f86ad63ddab9de36a969d4e44534`, shipping-content SHA256 `f8a849b90df3ff214037cace7bc32c0c7b5e184911558b424b0a6c0f798db781`, validation SHA256 `95844559cde01c1f9785d2835ea9f92a5e09e0315f87f0e7aa5029352456196c`. `source-identity.json` retains the independent final observation.

The raw archive is 17,669,441 bytes (683 files; 133,377,588 uncompressed bytes), SHA256 `ce06bdfd1331ec5d7022636084b322ba8e0436dd7907cd0fc904e59630cd08e7`. Independent extraction-stream validation matches every member byte count and SHA256 to `archive-files-sha256.json`; the archive is below the 32 MiB transfer limit. To reopen elsewhere, extract into a new directory. `qualification/` holds this frozen run and `integrated-source/` holds the earlier unchanged-resource suite receipts. Place the extracted qualification directory at `builds/session-qualification` in a clean checkout of the frozen source to use `recompute.py`; point `check_protocol.py` at the extracted raw protocol, network and hostile-handshake directories.
