# Concrete bounded pure controls before executing the clock draft

Bind exact 7686 proposal and old0f helper. Execute only the clock class and
extracted pure Owner/run_generated functions; import no R2 production validator
or native controller. Reconstruct the proposed helper by the five exact patch
replacements in its frozen proposal, assert each old span occurs once and the
result changes no other AST nodes. Preserve the reconstructed helper as data.

Eight controls on CPU4:

1. All reads remain pure and share one integer-ns state; perf/monotonic origins
   are distinct and differences match explicit advances.
2. Explicit 0, .1, .3, 1ns and 300s advances match rounded nanoseconds and produce
   finite numeric reads. No positive read call advances the clock.
3. Integer negative/positive wall steps affect only wall reads; bool/noninteger
   wall steps reject without state mutation.
4. Negative, bool, string, None, NaN and infinity durations reject without state
   mutation. Record explicit exceptions rather than converting a harness error
   into a passing model.
5. Challenge finite-read/exception atomicity with two enormous *integer*
   durations of 10**308 seconds. If the first is accepted, every successful read
   must remain finite; a rejected second update must not commit unusable state.
   This tests the draft's stated finite-numeric interface, not a plausible study
   schedule. Keep this limit distinct from the intended four bounded trials.
6. Prove helper delta consists of the five registered construction sites only;
   old28 method/113 assertion/Owner AST and non-helper source remain unchanged.
7. Extracted helper with fake study and fake fixture writer must pass exactly
   one shared clock to all four writer calls and healthy queries; reads and the
   patch context must not alter the standard-library time module. Verify facade
   restoration on normal return.
8. Restoration on collector exception; failed-arm helper path retains its
   original artifact/partial result, original callback/identity/query/fault
   ordering and never calls the future success writer. No automatic clock tick.

Fake study is a control stub, not the candidate collector/reader: its returns
are not model scores. Guard real Popen/subprocess execution, os signal calls and
ctypes library activation during the controls; Git/file audits run outside that
guard. No sleeps, driver, API, engine, helper/native process or proc reads.
Retain raw unittest failure output, state transitions and exact test source.
