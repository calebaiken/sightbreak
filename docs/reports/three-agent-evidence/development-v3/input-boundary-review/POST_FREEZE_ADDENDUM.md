# Post-freeze addendum — component only

This document adds source binding **after** the independent component freeze `d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78` and main neutral freeze at01:05:20 UTC were rehashed. It does not amend their bytes or reopen their neutral outcome judgment.

- The component mapping is verified against Git-object identities, recorded SHA256 and retained projects: bd249c=f3ceaad98e089aa393c7f5fa650a52695094d979;05ec6c=701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd.
- The former adds an empty-staged-work guard, explaining false for fully ACKed replay while queued/unACKed retries stay valid. Both consume the same original payloads.
- The identical Match RPC source returns before its later lifecycle.active, conditional last_activity and last_peer_input updates on accept=false. This is **source inference, not executed Match/timers**.
- Both21/0 summaries are expected: the two compared return values are deliberately recorded, not asserted. Source also reveals check21 directly calls component forget and tests three map removals; no traced post-forget state or actual disconnect was retained. The old live-disconnect limitation is unchanged.
- Twenty event predicates per sample and all22 serialized instances are independently rechecked offline. Actor fire, movement, lifecycle,30s expiry, DEFLATE/UDP, real client behavior and unprovided helper internals are not proven.
- All historical failures, raw logs and exact source/probe/driver/config snapshots remain published; engine binary and generated caches are omitted/indexed. No native run or staging/commit occurred.

Local-record ordering and matching hashes are not signed execution or trusted timestamps. No large-network identity key or broader PR20 source/controller/release mapping was opened. No full-network win, release approval or PR20 integration follows from this component alone. See REPORT.md, SOURCE_BINDING.json and PROBE_ASSERTIONS.json for exact evidence and limits.
