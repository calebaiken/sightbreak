# Test-owned temporary roots after actual ARM source-control failure

Actual run `39904830917`, job `120254254021`, exported combined source
`34dbd97a99068642cf07fa62288fe7437751c37e`. The supported GitHub decoded-job-log
connector supplied the completed original log. It is retained in full as
`job-120254254021-decoded.txt`; `jobs-final.json` retains completed step metadata.
The earlier unavailable-log response is also preserved.

At 05:20:43 UTC the new helper command ran 14 tests and failed with four errors.
All four tracebacks report `NativePrerequisiteBlocked: Symlink in native isolation
path: /var`. They originate in the test-owned temporary fixtures for file-mode
inventory, non-native refusal, private userdata logs and exact app staging. The
ordinary gameplay step was skipped. Bash stopped before running the subsequent
mocked-controller test command. There is no ordinary gameplay or private-override
runtime result from this attempt.

Before editing tests, reproduce that failure locally with a freshly owned symlink
as TMPDIR. Run both pure test commands with the alias in a child environment and
retain their original output. No engine, native input or OCR may execute.

The correction will resolve only each test-owned TemporaryDirectory root before
passing a fixture to the guarded runtime. Preserve descendant symlinks used as
negative controls. Production scripts `macos_ordinary_input.py` and
`verify_macos_ordinary.py` must remain byte-identical to frozen `bd9ac47`. Retain
all production no-symlink, default/private userdata, source/artifact, gameplay,
deadline and cleanup guards. Original platform tests, budgets and strict suites
remain unchanged.

Add a pure aliased-temp-storage control that runs the two full new test modules
against a deliberately symlinked temporary root on Linux as well as macOS. It must
also prove that the unchanged runtime still rejects that raw alias and accepts
its owned canonical target. Run normal and aliased pure controls, retain logs and
source hashes, then freeze and push the test-only correction. A fresh independent
source review and combined-source integration review must precede any repeat CI.
The original failed attempt remains failed; fixing fixture paths cannot confer
native gameplay acceptance.
