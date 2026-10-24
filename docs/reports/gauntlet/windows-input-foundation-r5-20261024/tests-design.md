# R5 deterministic-phase test construction freeze

Builder test-author role only; this document is not an approval. Registered
before candidate execution, after PREREGISTRATION.md at 0988ba43. The only owned
code is the new scripts/test_input_consumption_deterministic_phase.py. Reader,
old helper, old tests and retained R3/R4 evidence remain outside this author's
edit scope. Root pins the reader separately before any candidate test runs.

## Inspected source and construction boundary

The fixed bar is Match._input_rpc at game/scripts/gameplay/match.gd:1054-1078,
the observer at 1266-1318, SBPeerLifecycle at
game/scripts/network/peer_lifecycle.gd:11-64, and SBInputStream.accept/pop/reset
at game/scripts/network/input_stream.gd:14-47,67-93. They establish:

- One gated decoded RX callback has one synchronous A or J outcome. Only the
  direct RX observation can expose the callback before that outcome. Thus
  R=A+J+pending, with pending exactly one for a direct input_received row.
- accepted calls update lifecycle activity; rejected stream packets do not.
  Connection fixes D=C+20000, admission resets L, accepted activity resets L.
  Named operation clocks produce age=t-L and remaining=D-t at each new cut.
- The observer updates counters, latest projections and selected/sticky identity
  before coalescing. RX/A emit only on aggregate-edge change. J is never a
  direct emitted reason under this observer; J witnesses use a later tick.
- The global receive ordinal identifies the matching outcome ordinal. Compare
  known projections only when that outcome ordinal is proved. Direct A and
  a suffix containing just one outcome kind establish ordinals; mixed hidden
  A/J does not establish an arbitrary latest RX/A pair. A known receive cannot
  occur after its matching outcome.
- Packet acceptance has immutable per-sequence queue entries. A physics pop
  removes the oldest command, advances its ACK, and applies those controls.
  The new witness never exceeds six queued commands, so no backlog truncation
  is inferred. Empty guest reset replaces InputStream and begin_round advances
  the epoch again; diagnostic counters/latest observations remain cumulative.

TimedAuthority starts from amended declared_rows('authority') with its exact
existing seven rows. Its own seed state is explicitly C9=2000,A9=3000,L9=9000,
D9=22000,ACK9=1,queue9 empty. New rows arise only from named forward operations
with supplied clocks. The constructor never receives arbitrary rows to fix,
never changes old helper rows, never restamps an old test, and never calls the
candidate to derive expected results. Mutations occur on independent copies
after a source-positive construction is complete. Other frame/resource/client
fields remain synthetic and cannot establish full native-emitter provenance.

## Frozen expectations

Eleven methods cover the following source-derived controls before execution:

1. Direct pending RX and resolved direct A are CONSISTENT. Independent R/A/J
   counter inflation is INVALID.
2. Direct A matches its exact RX ordinal; changed endpoints/action aggregate
   are INVALID.
3. Hidden wrong-epoch J preserves L/D and matches its RX. Source witness is
   CONSISTENT; changed known J projection is INVALID.
4. Sole hidden A after an exposed RX stays UNKNOWN under anonymous-activity
   policy. Changed exact paired projection or outcome preceding RX is INVALID.
5. Multiple hidden same-kind A/J use the final receive ordinal, rather than
   the first known receive. A remains UNKNOWN, J CONSISTENT; wrong final
   projection is INVALID.
6. Mixed hidden A/J with different latest RX/A epochs stays UNKNOWN. A receive
   surplus outside a direct pending RX is INVALID.
7. Hidden A with an independently impossible count, endpoint or epoch is INVALID
   despite a valid UNKNOWN activity parent.
8. Later regressed frames/index/epoch, negative skipped count or omitted lifecycle
   count is INVALID after an earlier foundation UNKNOWN.
9. Multi-peer hidden activity stays UNKNOWN; later direct acceptance with an
   empty queue, wrong binding or impossible ACK is INVALID.
10. Later direct consumption must match actor controls and live owner even after
    earlier UNKNOWN. Both independent contradictions are INVALID.
11. Zero-bound epoch reset legitimately clears stream rejection/ACK state while
    preserving counted rejections. The positive is CONSISTENT; missing epoch
    change, inflated stream rejection or retained absent-stream ACK is INVALID.

No candidate execution occurred before this freeze. All initial failures must
be retained. A construction conflict requires its own narrow additive source
adjudication and retained original outcome; expectations are not adjusted to
make the candidate pass. Exact retained R4/R3 corpora, historical baseline,
unchanged focused methods and source-union checks are root-owned execution.
No full-suite/native/207 replay readiness follows from these controls.
