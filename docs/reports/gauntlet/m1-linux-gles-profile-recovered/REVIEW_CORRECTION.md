# Maintained admission control correction

The fresh critic rejected `3631f2d01403f9dfb9721773a9ec844e05806b1e` pending
one test correction. Its review and original counterexample are retained at
[`1b7eb213`](https://github.com/calebaiken/sightbreak/blob/1b7eb2135a48651861876ae0c16c16520e8c5e91/docs/reports/gauntlet/m1-linux-gles-profile-recovered/independent-review/SOURCE_REVIEW.md).
No controller defect was found, and no native slot was released.

The original negative cases omitted `--xvfb`. Because the recovered host has no
Xvfb in PATH, the unchanged display check could reject malformed commands even
after the new sampler exclusion was deleted. Thus the original three-test pass
did not establish the intended admission regression boundary. The original
maintained test, its passing raw output and the critic's passing sampler mutant
remain in Git; they are not relabeled as valid mutation rejection evidence.

The maintained correction supplies `/pure-xvfb` and display `:99107`, forces
only that display's socket to be absent, and asserts the specific GPU-profile
admission message for malformed profile options. The target-mismatch case
asserts its original native-platform message. Source and Popen mocks now raise
on use; the cases still assert neither was called and no output directory
exists. Host-description and signal mocks prevent a broken mutant from making
unrelated subprocess calls or changing the test runner's signal handlers.

The corrected three tests pass with no skips. Their fresh raw output is
[`pure-controls-r2/gpu-profile.txt`](pure-controls-r2/gpu-profile.txt).
The complete base AST comparison still passes in
[`source-audit.json`](pure-controls-r2/source-audit.json). Compile and full-base
whitespace checks pass. The controller remains byte-identical to `3631f2d`,
SHA-256 `f6f45ed28feceb1140e02bf5faffc6293c7d3cac96e83a5e1ab2d70dd07baabf`.
No game code, budgets, graphics, reopened command or runtime behavior changed.

[`mutation_controls.py`](mutation_controls.py) copies each controller variant
into an isolated temporary import path and runs the maintained tests. It never
edits the working controller. Every variant compiles before testing; all native
process, UI, engine and source receipts are intercepted by the maintained pure
fixture. These are test mutations, not additional native experiment arms.

| Isolated case | Exit | Observed regression boundary |
| --- | ---: | --- |
| Current candidate | 0 | All three corrected tests pass |
| Remove sampler exclusion | 1 | Malformed combined options reach the forbidden source check |
| Omit engine profile option | 1 | Opt-in initial argv differs from required engine argv |
| Profile initial client by default | 1 | Default initial argv differs from the original command |
| Append profile option after `--` | 1 | Opt-in initial argv places the option in user arguments |

All five outcomes meet their registered expectation. The
[`mutation summary`](pure-controls-r2/mutations/summary.json) records exact
controller/test hashes, commands, exits, raw-byte hashes and gzip hashes. Each
gzip decompresses byte-for-byte to its captured raw output; failed unittest
trailing spaces remain intact. Reproduce into a fresh output directory:

```sh
python3 scripts/test_linux_gpu_profile.py -v
python3 docs/reports/gauntlet/m1-linux-gles-profile-recovered/mutation_controls.py --output /tmp/sightbreak-profile-mutations-new
python3 docs/reports/gauntlet/m1-linux-gles-profile-recovered/source_audit.py
python3 -m py_compile scripts/verify_offline_match.py scripts/test_linux_gpu_profile.py docs/reports/gauntlet/m1-linux-gles-profile-recovered/mutation_controls.py
git diff 917b143ba4e4b0d9644a7a0ddeee1dd64c139682 --check
```

Fresh independent re-review remains pending at the corrected exact source.
Actual profiled output remains the largest capability gap. No engine, export,
native client, CI or service ran; the original Linux next-buy gate stays FAILED.
