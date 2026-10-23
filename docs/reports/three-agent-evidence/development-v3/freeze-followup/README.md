# Last bounded freeze follow-up

The independent critic found one P2 Linux-facing test-mock defect: mutating the
shared `os.name` made POSIX-initialized pathlib select unsupported WindowsPath.
Its original failed reproduction, corrected comparison, source hashes and raw
ordinary controls remain unchanged under `raw/critic/`.

The production implementation was not changed. `TEST_ONLY_CHANGE.diff` isolates
the Windows mock to the module reference. The actual existing unit then passed
with POSIX-initialized CPython 3.13.15 stdlib pathlib on Windows, and all 17
matrix-process tests exited zero. This is synthetic platform evidence, **not an
actual Linux/Python 3.12 run**. Earlier 272 normal + 74 optimized executions are
not relabelled as having run after this later test-only change.

The first index audit also caught four archive-metadata newline transformations;
its failed JSON is retained. The unpublished archive was given byte-preserving
attributes, with only its attributes checksum updated. Original raw payloads and
the external copies were not changed. Final index verification is a separate
read-only operation, not a retrospective change to that failure.

Exceptional Linux supervisor-death cleanup remains explicitly unverified and
fails closed. No game, native audio, campaign, export, database or device work was
performed by this follow-up. No human/device/production/8.5 gate is waived.
