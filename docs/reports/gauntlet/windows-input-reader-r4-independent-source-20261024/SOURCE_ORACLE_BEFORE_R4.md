# Source rules recorded before reading R4 implementation

All source below is fetched at reader base342c3641ab2fccd1fc875c84188a8395a9b93a96.
This is static inspection only; final R4 handoff and execution remain pending.

- match.gd1266–1322 increments counters and updates latest before deciding whether
  to emit. latest is initialized once in _native_input_configure, then retained.
  Lifecycle events always emit. Other control events may coalesce based on fields
  excluding peer identity, generation, packet endpoints and full packet movement.
  A counter increase need not have a direct row for every receive or acceptance.
- The direct event increments its own counter; direct tracked latest has timestamp
  now. Latest metadata persists until that same reason executes again; generation,
  epoch or connection changes do not clear it. Repeated stage counts, missing
  latest, changed metadata without a counter increase and future timestamps are
  deterministic source contradictions. Multiple events can share one millisecond.
- match.gd1053–1078 has a synchronous receive→stream rejection or acceptance body.
  Receive precedes validation, so malformed packet header projections are valid
  observations. With R=input_received, A=input_accepted,J=input_stream_rejected,
  direct receive rows require R=A+J+1; other emitted rows require R=A+J. The accepted
  and received packet projections are from exactly the same data in this body,
  excluding their separately sampled wall timestamps.
- match.gd1249–1264 projects incoming array count but visits at most MAX_BATCH12.
  Nondictionary entries are skipped. A single-command projection has equal first
  and last even for negative/invalid sequence; an empty or nondictionary-only
  projection has endpoints-1 and zero aggregate actions. For multi-command
  malformed payloads first is reassigned while negative, so it is not necessarily
  the first raw array element. Incoming endpoints are not sorted minima/maxima.
- input_stream.gd14–47 accepts only epoch-correct batches1–12 with sanitized
  dictionary commands and at least one sequence greater than current ACK. Thus
  direct acceptance has a nonempty queue. A count1 accepted endpoint must exceed
  current stream ACK; retransmitted acknowledged commands in larger batches may
  coexist with some fresh command. Packet projection does not expose batch middle
  sequences or immutable queued values, so full content equality is unprovable.
- input_stream.gd65–84 pops the oldest after optional bounded backlog discard,
  erases it and sets ACK to exactly the returned sequence. match.gd263–280 copies
  that returned clean command into the bound actor immediately before consumption
  observation. Direct consumed projection, actor input and ACK must match; later
  actor input may change through normal source actions.
- peer_lifecycle.gd12–17 cannot connect an already live peer. Generations increase
  globally, and peer bindings cannot be invented without a preceding connection.
  _peer_disconnected observes before forget and can recur for a forgotten peer;
  do not impose a false exactly-one-disconnect rule. Prior peer A's accepted work
  cannot prove peer B received anything unless cumulative counters permit hidden
  B work. Direct B receive/accept rows are not required if legitimate coalescing
  and counter/latest transitions support hidden B events.

Fresh independent falsifiers will preserve snapshot freshness and all unrelated
source invariants, with a valid control paired before mutating only the targeted
rule. Where existing fixture simplifications remain, they must be stated and
must not be used as sole evidence of a source-invalid history.
