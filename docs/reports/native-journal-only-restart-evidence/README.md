# Journal-only native restart evidence

See [results and reproduction](../NATIVE_JOURNAL_ONLY_RESTART_RESULTS.md) and the
[premeasurement protocol](../NATIVE_JOURNAL_ONLY_RESTART_PROTOCOL.md).

- `r2/baseline-701/`: one price-400 case, exact `701ce2c4`, 0/1 recovered.
- `r2/candidate-7b6f379/`: one price-400 case, exact `7b6f379`, 1/1 recovered.
- Both used harness/probe frozen at `7be70f73` before either measurement.
- Each arm includes actual economic stages 01–05, request/response timelines,
  native outputs, journals or their absence, session digests and source/cache
  manifests. Each launch additionally has a redacted config and input binding.
- All four restart configs contain exactly six keys. Their original private-file
  hashes/lengths/key lists match the native probe's actual-read events.
- `verification.json` and `verify-observations.py` reconstruct these claims from
  retained observations offline; they do not run a client, service or SQL query.
  From the repository, run `python docs/reports/native-journal-only-restart-evidence/verify-observations.py docs/reports/native-journal-only-restart-evidence/r2 <new-verification-output.json>`.
- `prior-review/_FROZEN_VERDICT.md` is the exact frozen prior six-case verdict,
  copied only after checking its supplied SHA-256. It is not a verdict on this
  follow-up and is excluded from the new neutral packet.
- `r1/` retains the authenticated PostgreSQL connection timeout before database
  creation, plus the first restoration's server log. No native purchase case ran.
- `resume/` records restoration of the same dedicated portable cluster after the
  next session restart, successful authenticated health and failed-attempt DB
  absence. The server log is a byte snapshot at publication, not a server shutdown.

Synthetic passwords and bearer tokens are redacted. A private-fixture hash binds
the prelaunch file to the native read; it cannot be re-derived from a published
redacted config. Environment and redacted-config hashes are independently
recomputable in these source-labelled observations. Neutral copies subsequently
replace disclosed machine/source identities and retain separate hash bindings.

The original six-case campaign, original 36/37 native-economy failure and separate
37/37 DNS calibration remain in the earlier evidence publication. This follow-up
does not rerun them. See the publication manifest and separate Git-blob proof for
the exact bytes retained here.
