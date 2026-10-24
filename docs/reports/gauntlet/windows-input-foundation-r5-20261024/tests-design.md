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

## Additive operation-word registration before execution

The initial eleven-method source is preserved at 9e0549b5. Root reports that
the pinned initial candidate 644f8834 passed those methods, with original raw
first-new-tests.* retained. This author has not executed candidate code. The
following added method and expectations are frozen before its first execution;
the preceding eleven methods and TimedAuthority constructor remain unchanged.

Enumerate all words of lengths one, two and three over A0,A1,J0,J1. A means a
successful same-epoch acceptance; J means the explicit wrong-epoch rejection;
0/1 is the single command's fire flag. There are 4+16+64=84 words. For each word
construct two independent forward witnesses, with outcome at the receive clock
or one millisecond later. Position p starts at zero: command sequence=2+p,
receive clock=11200+10*p, outcome clock=receive+phase. Each callback completes
before the next callback begins. No pop is generated and at most three commands
are queued. The final tick is fixed at 13200, more than 1000ms after every
possible last control emission, so its row is explicitly emitted. Connection,
admission, rate and idle bounds remain within the seed witness's source limits.

These 168 operation witnesses each have three independently assessed variants:

- Source-positive rows must be CONSISTENT or policy UNKNOWN, never INVALID.
  A successful positive is not forced to certify anonymous activity or receipt
  ownership, and diagnostic_complete must agree with its returned status.
- A separate copy increments only the final cumulative RX counter by one.
  The final row is an authority tick, so there is no pending synchronous RX.
  Its excess R violates R=A+J and must be INVALID.
- Another separate copy changes final stream_rejected to cumulative J+1.
  There is no epoch reset or hidden uncounted reject operation in any witness.
  The source's stream rejection count cannot exceed counted J and must be INVALID.

This registers 504 outcome expectations. Word, phase and variant are separate
subtest labels; failures remain visible while the other independent variants
continue. No raw constructor input is retimed or repaired after a report result.
Root owns execution, exact-input/result retention and reader pinning.

Source inputs fixed at registration: amended declared helper SHA256
af8d1f10482b9513a20f204eee8f17afb94ee4bb549df40b5cea4bd618f859cd;
initial new-test file SHA256 f5847919a36c0541a47be701cdb938acbbf9a217fae5182d2b9664d18d82c848;
PeerLifecycle SHA256 8a57cc07bdc007fe143a5e8c51c99238732fcc4acf9f209fd4718af937f22078;
InputStream SHA256 b455205d827134830637f03457cc67e4e321721d91a7d840941fc74e1b26c88e;
Match SHA256 80c1cc2fceeb44dd4bf8c9726a8f6a77124e649a8535a9e508ea6d904ec9f238.

## Schema and semantic distinctions

Some original negative controls change just first or last on a count1 packet.
record_valid explicitly rejects unequal count1 endpoints before deterministic
pipeline inference. Those subtests establish schema rejection, not an isolated
R5 phase improvement. The original source and results remain unchanged. The
paired action-aggregate changes, both-endpoint same-kind ordinal changes, and
this added matrix's integer counter/rejection-count mutations remain structurally
well-typed; their expected rejection follows source pairing or counter state.
No claim that every negative specifically reaches the new phase is made without
its retained actual error and schema-versus-semantic adjudication.
