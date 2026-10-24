# Additional controls fixed before R4 implementation inspection

These supplement the frozen critic16. Each must start from a candidate-accepted
source-corrected control and preserve snapshot wall time/age, all prior counters,
source event ordering and unrelated fields. If constructing a valid pair requires
more edits, record them before interpreting the changed result. Preserve all
source/input/output bytes and independently compare old reader where meaningful.

- A directly accepted one-command packet at or below the current selected peer's
  ACK is impossible: input_stream.accept stages no new intent and returns false.
  Pair with the same projection just above ACK. Larger batches may carry old
  endpoints with hidden fresh middle content; do not impose this single-command
  rule on every endpoint of a multi-command batch.
- queue_count cannot exceed MAX_AHEAD120: accepted keys are unique sequences in
  (ACK,ACK+120], pop only deletes and advances ACK, forget/reset only clear. Pair
  a queue121 falsifier with the original valid queue and keep acceptance metadata,
  consumption and counter/clock relations otherwise unchanged.
- A receive projected from an empty commands array has count0, endpoints-1/-1 and
  zero action aggregates. A nondictionary-only array has its actual positive count
  but the same empty endpoints/actions. These are valid malformed prevalidation
  observations followed by rejection and a later valid receive. A count0 receive
  with a nonempty projected endpoint is impossible, independent of validation.
- stream_rejected is incremented once for each failed accept and retained through
  forget/reset_epoch. Its relationship with emitted/coalesced input_stream_rejected
  counters and monotonic persistence must follow real source call sites, rather
  than merely their numeric types. Do not infer a failure from a raw malformed
  packet without its corresponding rejection call/accounting.
- Latest metadata timestamp/content changes require that reason's cumulative
  counter to advance. A same-millisecond legitimate update can retain timestamp;
  a counter can advance without a direct row. Preserve old latest across epoch/
  peer/client-attempt changes because the emitter does.
