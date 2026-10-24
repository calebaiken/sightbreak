# Independent Linux GLES source review

Verdict on `3631f2d01403f9dfb9721773a9ec844e05806b1e`: **REJECT pending a maintained regression-test correction**. The controller matches the registered capability, but the rejection test can pass when its sampler exclusion is removed. No engine, export, native client, CI or service ran during this review. Root retains the native lane.

I reviewed the exact frozen candidate from a separate sparse worktree and branch, `critic/linux-gles-profile-recovered`, against base `917b143ba4e4b0d9644a7a0ddeee1dd64c139682`. I read the repository instructions, original Gauntlet and No AI Slop skills and eval, registration, controller, added tests, retained outputs and upstream source. This is a correctness comparison against the original controller; blind visual comparison does not apply.

## Required correction

`test_rejects_other_scenarios_seeds_budgets_and_sampler_before_side_effects` does not supply `--xvfb`. This recovered host has no Xvfb in PATH. Removing only `or args.linux_frame_diagnostics` from the new admission condition still passes all three new tests: the unchanged later Xvfb check rejects the invalid CLI. [The raw zero-exit mutant output](mutant-allow-sampler.txt) is the counterexample. This defeats the intended sampler-exclusion regression control.

Supply a nonempty fake Xvfb path and force an unused display socket in those pure negative cases. Assert the intended admission error where applicable, with output/source/process side effects forbidden. The builder owns the maintained correction. Freeze it and have this critic rerun the corrected tests and sampler-admission mutation before releasing the native attempt.

My separate fixture supplies `/pure-xvfb` and `:99107`, whose socket was absent. The unchanged candidate passes. Removing sampler exclusion, omitting the engine option, profiling by default, or appending the option after the user-argument separator each fails. [Mutation summary](mutation-summary.json), raw `nonvacuous-*` logs and [the independent test copy](nonvacuous-tests.py) retain the results. The sampler mutant reaches setup instead of the intended parser rejection, so the corrected test fails. The first staged whitespace check rejected trailing spaces emitted by unittest in failing raw logs. Their exact bytes are retained in gzip archives with hashes in `raw-review-archives.json`. Two initial critic mutation attempts stopped at the unexpected passing mutant; [the setup note](mutation-setup-failure.txt) corrects an initial mistaken whitespace diagnosis.

## Controller and upstream findings

I independently removed the three exact added text blocks, rather than relying only on the builder's AST stripping. The remaining controller is byte-for-byte equal to the base. The game tree is identical. The admission predicate matches all 1,152 tested combinations of opt-in, target, scenario, budget (including NaN/infinity), seed and sampler. [Audit receipt](independent-audit.json).

The option is inserted at initial argv index 1, before `--`; the default and reopened commands, budgets, graphics, authority, economy and protocol statements retain their exact base text. The native-platform restriction is unchanged. No new performance claim follows from this diagnostic capability.

I independently fetched all seven pinned Godot sources and resolved tag `4.7.2-stable` to `ed1daf0bf001b61586d9930840f2f1394092c079`. All seven lengths and SHA-256 values match the registration. [Fetch receipt](upstream-fetch.json). The uncommitted fetched source cache is `/workspace/review-cache/linux-gles-profile-recovered/upstream`.

The inspected implementation confirms the registered limits:

- `main.cpp` accepts `--gpu-profile` outside `TOOLS_ENABLED` and enables the rendering server's print profile.
- GLES uses three query buffers; its retrieval comment says frame minus two. Desktop GL supplies `GL_TIMESTAMP` query results. The rendering server reads buffered results after rendering, and stdout omits source-frame and phase identifiers.
- Adjacent GPU timestamp differences accumulate by the preceding name. Names beginning `<` or `>` are excluded. The loop divides accumulated sums by reporting-interval draw calls after strictly more than 1,000,000 host microseconds. Only averages strictly greater than 0.01 ms print, in hash-map order.
- A profile can remain retained when no new timestamps arrive. Reporting calls do not deduplicate source frames. The header total is the final relative GPU timestamp in the latest retained profile; it is not the row averaging statistic.

These bytes cannot support stdout-arrival phase tagging, unique-frame sample counts, row/header summation, CPU-function attribution, physical FPS, sampler/profiler overhead, causality or performance improvement. A future actual output can establish only the registered renderer-query capability and coarse intervals under llvmpipe.

## Verification and remaining gap

All independently rerun pure controls pass: three profile, 18 sampler, four role-guidance and 15 capture-fence tests, without skips. Compile, exact-base AST audit and whole-candidate whitespace checks pass. [Commands and exits](pure-summary.json), with raw outputs `pure-1.txt` through `pure-7.txt`. Both original setup-failure gzip archives match their compressed and decompressed hashes; the audit retains their original 370 and 8,698 byte lengths.

The largest remaining gap is actual profile output at the final reviewed source. Source review cannot establish native capability or teardown. The single future attempt must use a fresh source-bound export, Linux plant / seed 42 / timeout 180, sampler off, original settings and deadlines. Independently verify at least one intact finite nonnegative header and positive named task row, actual command/source/engine/export identities and owned-process cleanup. Preserve the ordinary next-buy result and whether restart was reached. The existing Linux next-buy failure and broader release gates remain open.
