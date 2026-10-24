# Retained pure-log timing parity failure

The v2 audit then reached the pure unittest stderr logs and failed because
independent runs print different elapsed durations. Raw unittest text is not
expected byte-identical across initialized views. Preserve that audit/stderr too.
Before the next audit, require exact selected method/name/failure/error/skip
counts for both views and retain all raw logs separately. Do not include pure
run text in case-input/result byte parity; no timing equivalence is claimed.
All actual fixture/result parity rules remain unchanged, including the single
explicit corrected-fixture JSON key ordering exception already adjudicated.
