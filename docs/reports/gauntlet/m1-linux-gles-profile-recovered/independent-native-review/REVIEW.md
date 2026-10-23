# Independent actual-output verdict

**ACCEPT the registered renderer-query capability and retained data integrity at tested source `b1a131ab4790ac84371b54ee236441a66faf4125`. The ordinary gameplay attempt FAILED.** It timed out waiting for initial LIVE while still in BUY. Plant, next buy and restart were unreached. This diagnostic does not close the earlier Linux next-buy failure or a release-performance gate.

I inspected the actual files from evidence commit `afb4d173cb60478af22177cb5c76bb7ba31c8b10` in a separate sparse worktree, `/workspace/reviews/linux-gles-profile-native`, on `critic/linux-gles-profile-native`. I wrote and ran [an independent read-only audit](audit.py); I did not use the builder's `native_audit.py` or `native-recomputed.json` to produce my result. [Independent recomputation](recomputed.json) retains all parsed profile blocks, archive checks, resource checks and terminal cleanup probes. No engine, native game, export, OCR, profiler or service ran during this review.

## Exact source and retained bytes

All 29 indexed archived payloads match their compressed and decompressed lengths and SHA-256 values, and each matches the original local file. The archive contains exactly those payloads plus its index: 1,200,024 raw bytes / 1,135,195 archived bytes. Every one of the 124 files inventoried as retained locally also matches its original length and SHA-256. The complete executable remains at its recorded ignored path; it has not been copied into this report or removed.

The seven frozen source copies match exact Git blobs at `b1a131ab`. I independently recomputed the shipping-content and validation hashes from that Git tree and checked all preflight, manifest, controller and post-run source identities:

| Identity | Verified value |
| --- | --- |
| Game tree | `1ba89edb14eaa7c322a501387a56e8491130ae48` |
| Shipping SHA-256 | `f61d63f00b841cf243af747d8d198f164167f115d2b1bc04a1619bd548cdaa50` |
| Validation SHA-256 | `1255fec1fd645d2d3d30d86bfb13a658f82c9dd1c2e292fe70afdde1085d53af` |
| Controller SHA-256 | `f6f45ed28feceb1140e02bf5faffc6293c7d3cac96e83a5e1ab2d70dd07baabf` |

The recorded preflight and post-run identities are clean and equal. The current evidence source has no game, script or validation diff from the tested source. Earlier independent source acceptance `8a1df18c` applies to these unchanged controller bytes; the corrected maintained rejection test and the original rejected test evidence remain in their respective commits.

I independently hashed the editor and template archives against the SHA-512 pins in the frozen `toolchain.py`. Their extracted member hashes and lengths match the installed editor and Linux debug template. The actual import/export receipts both exit zero and their raw logs identify `4.7.2.stable.official.ed1daf0bf`; the actual client identifies the same engine. The export wrapper exits zero in 11.172328 seconds. I did not execute an engine version check.

The retained 84,232,632-byte executable matches manifest/controller SHA-256 `3af3d08f2265e797dcb7ff78267cb904c373f4e3ba500070b810384859d8a718`. Independent parsing verifies a little-endian 64-bit x86_64 ELF and embedded Godot 4.7.2 / pack-format-4 data beginning at byte 73,703,800. The pack is 10,528,820 bytes. All 134 resource offsets are within bounds and every resource MD5 passes; resource names match the recorded export inventory. `scripts/offline_diagnostics.gdc` is present, with no shipped `tests` directory. All four manifest payloads, including the wrapper and licenses, match their retained bytes. The parser follows the inspected pinned [Godot pack reader](https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf001b61586d9930840f2f1394092c079/core/io/file_access_pack.cpp); its retrieval hash is retained in [additional-upstream.json](additional-upstream.json).

## Actual command, input and failure

The controller receipt records Linux plant / explicit seed 42 / timeout 180 / `--linux-gpu-profile`. The actual child commands are only Xvfb and the initial client. `--gpu-profile` is at client argv index 1, before `--`; there is no reopened client and no sampler command or sample file. Xvfb selects 1280x720. The source sets software rendering and two Mesa workers; the actual log identifies GL Compatibility and Mesa llvmpipe. This review did not observe the live client's environment directly.

The initial authority record contains protocol 6, prediction off, seed `"42"`, ten living 100-health actors, the original rules and a fresh empty offline profile. Settings retain Standard (quality 1), scale 1 and cap 60. The terminal native readbacks retain 60 Hz physics, maximum eight physics steps per frame, scale 1 and 1280x720 visible/output texture sizes; internal 3D target size is explicitly unavailable. The V-Sync unsupported warning and Xvfb directory warning remain in the raw outputs.

I directly viewed both original PNGs without OCR. The menu shows an empty device training record. The initial arena shows ROUND 01 / BUY, YOU ATTACK, DEVICE / CARRIED, 100 HEALTH and sidearm 15 / 60. Both are 1280x720. The action log records a focused target window and a native Deploy click at (248, 319), followed by the initial read-only state and a fresh rendered BUY capture. All nine action rows retain neutral held keys and released left mouse state. These captures establish menu/initial BUY only; they supply no LIVE, plant or restart evidence and no visual-quality acceptance.

The unchanged controller waits 45 seconds for initial LIVE. The recorded driver bracket from initial capture end to failure is 45.075967 seconds. At failure the actual observation is BUY / round 1 / tick 844 / elapsed 14.066667 simulation seconds, with 0.933333 seconds left on the original 15-second BUY timer. The controller ends after 58.557768 seconds, wrapper exit 1. `partial_checks` is empty. Initial and reopened normal-exit fields are null. The 12-second next-buy bound is unchanged but was never entered in this attempt. The failure remains a failure, without a longer budget or inferred completion.

## Profile capability and interpretation

Parsing only the actual client log, I independently count 35 intact profile headers and 34 row-bearing blocks. All headers are finite and nonnegative; every printed task value is finite and greater than 0.01 ms. This satisfies the preregistered capability condition. The empty startup block with total 0.0 is retained. The internal Godot log reproduces the profile blocks; it differs from stdout in warning indentation, so the two files are preserved separately and not counted twice.

`Render Opaque Pass` is the largest printed named interval in all 34 row-bearing blocks. Its emitted interval averages range from 260.763997 to 1,403.713379 ms. Header totals separately range from 0.0 to 486.349 ms. These are ranges of emitted statistics, with no unique-frame, percentile or gameplay-phase assignment.

The independently inspected pinned engine source already establishes historical query buffering, retained profiles and reporting-interval task averaging. The header total uses the latest retained profile's final relative timestamp. The stdout bytes omit source-frame and phase identifiers. Consequently, the profile rows cannot be phase-tagged by arrival, counted as independent unique frames, summed with the header, converted to physical FPS, used to partition CPU functions or used to quantify sampler/profiler overhead, causality or improvement. This attempt and the earlier sampler-on attempt are not a controlled performance comparison.

## Cleanup and next investigation

The controller records `cleanup_errors=[]`, Xvfb exit 0 and client exit -15 from failure teardown. My independent terminal probes find declared controller PID 9725, Xvfb PID 9770 and client PID 9816 absent; child process groups 9770 and 9816 are absent; the :123 socket and lock are absent. The recomputation records the probe time. This checks the declared identities and groups without signals other than existence probes; it does not claim a host-wide process or resource audit.

The largest remaining deficiency is controlled cost attribution and measurement overhead. The emitted opaque interval provides a concrete next source investigation. In the pinned [GLES scene renderer](https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp), the marker at line 2811 precedes pass setup and `_render_list_template<PASS_MODE_COLOR>`; the following marker is conditional (camera feed or sky), so the interval is broader than one CPU function. Its source hash is retained in `additional-upstream.json`. Map that path's draw/material/shader work and design a separately registered unchanged-camera, unchanged-settings attribution/overhead experiment before proposing a product change. This evidence authorizes no further native attempt and supplies no performance fix.

Two critic audit setup failures are retained: [incorrect nested report-root depth](attempt-1-path-setup.txt), then [an integer-seed assertion](attempt-2-stderr.txt). The frozen observer explicitly serializes seed values as strings; correcting the assertion to `"42"` preserves the actual record. The final audit passes. No original runtime bytes were edited to resolve either failure.
