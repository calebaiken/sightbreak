# Independent second-trial archive review

Accept archive integrity at builder commit `08fd5cc`. All 58 indexed files match
the SHA-256 manifest and their committed Git blobs. All 50 native output files
and five original preflight/driver files are byte-identical to the original
completed run. Three later replay/cleanup/verdict receipts are identified
separately. The only omitted original runtime files are the empty stop marker
and SQLite lock.

The archive commit changes no game, backend, server or harness source relative
to frozen `3b5cf7640e256dff404b401bf2b27ffaff157bdd`. Its game tree is unchanged.
All 62 first-trial archive/manifest/handoff files remain byte-identical to
`e689416`. That first trial remains BLOCKED, including its missed 0.597 ms
post-replay observation and original flawed independent observer.

The reproducible check is `check_trial_2_archive.py`; the result is
`trial-2-archive-integrity.json`. The independently accepted bounded stock-match
and process-crash recovery verdict remains in `TRIAL_2_REVIEW.md`. Archive
integrity adds no broader qualification. G3 and G16 remain in progress.
