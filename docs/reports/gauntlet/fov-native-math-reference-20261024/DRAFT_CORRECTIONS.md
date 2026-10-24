# Retained pre-freeze source review corrections

The existing independent critic inspected mutable source only, before its final
frozen tests/admission. These were draft source defects, not native failures.
No engine was invoked. All executed pure outputs remain as r1 through r5.

1. Original draft created Streams only after root identity/executable checks and
   closed streams before cleanup. A failed early readback could discard all
   pipes, and pending failure bytes could be unretained without an explicit EOF
   limit. Final550e creates retention immediately after spawn, drains during the
   same5s cleanup, and reports retained/observed byte counts, EOF, truncation and
   complete-versus-unresolved failure coverage. Pure early-readback and pending-
   tail controls retain those failure paths. Capped prefixes are never complete.
2. Original source_binding check_output/run calls had no timeout. Final550e
   passes the remaining original whole deadline to every Git child and checks
   the same budget around source reads; pure controls inspect the decreasing
   timeout arguments and reject a late start before any Git call.
3. Original schema accepted internally consistent numerical rows even if a
   coordinated dot/bits/predicate corruption changed a known analytical axis.
   Final550e enforces exact axis/zero/equality/recent and exact38m-axis controls,
   and rejects coordinated dot+bits+predicate/toward corruption. General float64/
   nominal-f32 differences remain UNRESOLVED instead of being forced equal.
4. Corpus provenance is150 original opposite-team actor pairs, including liveness
   metadata, plus1 explicitly synthetic changed-yaw pair. The group name captured
   contains151 rows; it does not mean151 living captured pairs.

The original draft snippets were respectively `streams=stream_factory(...)`
after root readbacks, `streams.close()` before cleanup, and Git subprocess calls
without `timeout=remaining()`. They were corrected before the first source freeze.
Pure iterations17/18/18/20/22 all passed; static defects are retained here rather
than relabeled as passing native behavior. No baseline, original fixture or
historical native failure was overwritten.
