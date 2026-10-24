# Input boundary — main-author neutral assessment

This assessment precedes opening this component attempt's private source mapping.
It is a main-author assessment, not an independent review of my own fixture.
The compared behavior makes source identity inferable; opaque labels are not a
claim of perfect behavioral blinding.

## Narrow preferred outcome

Prefer **sample-bd249c** for rejecting fully ACKed replays without rejecting
still-unconsumed retries. Both samples complete 21 common checks, zero failures,
with actual probe exit 0. The common checks do not prescribe the answer for the
two fully ACKed replay events, so their equal assertion totals are not a tie on
that observed contract.

- Fresh commands 1 and 2, identical queued retries, altered queued retries and
  a partially ACKed batch are accepted in both samples. Altered retries do not
  overwrite the original queued movement or fire values.
- After consumption reaches ACK 2 and an empty queue, sample-bd249c rejects
  both identical and altered fully ACKed replays and increments rejection count;
  sample-05ec6c returns true for both while queuing no new command.
- Both accept a mixed stale/new batch, retain new command 3 through a queued
  retry, consume its original left-movement/fire payload exactly once and then
  return an empty pop. Both reject old epoch, beyond-window input and a malformed
  stale command mixed with new intent without mutating queued intent.

## What this does not establish

The engine runs the production InputStream and input gate modules through a
serialized dictionary boundary. It does not execute Match._input_rpc, lifecycle
timers, actor firing, UDP, physical movement or stock-client reconnect. Supplied
rate-clock values are fixture-controlled; capture_monotonic_ms is an actual
capture timestamp, not a production inactivity origin. Both variants charge
their rate bucket for the recorded replay attempts.

Imports completed before probes. Engine file logs and independently persisted
probe-result.json must agree on the completion summary; empty Windows GUI stdout
alone was not accepted as evidence. Earlier driver/API and missing-summary
attempts remain failed, not discarded or reclassified as runtime defects.

This is not a latency, FPS, full-network, gameplay-accuracy or release claim.
Protocol 6, prediction default-off, rewind-off and all human/device gates remain.
