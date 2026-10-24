# Independent R6 fixture construction adjudications

These conclusions follow from unchanged source and exact historical inputs.
No original108/30 input, expectation, outcome, source file or R5 artifact was
edited. historical-fixtures/ retains the selected exact old input/result and
old state-test source, with hashes. Builder subsequently registered0719aafb
before proposed construction changes. This adjudication approves only their
source basis, not R6 correctness, a complete new fixture or native behavior.

## Prior consumption_outside_accepted_batch positive is impossible

The preserved normalized case has peer71/generation1/epoch7 throughout. Its
first direct count1 receive/accept exposes sequence21, queue0 then queue1. A
coalesced second count1 acceptance exposes22; cumulative received/accepted are2.
Its first consumed call claims22/ACK22/queue0, skipped0; the next authority tick
then reports ACK21 while latest consumed remains22 and its count remains1.

InputStream stores both unacknowledged unique keys. Pop sorts and selects the
minimum; a size2 queue does not meet the >6 backlog threshold. With no reset,
forget, earlier pop or skips, [21,22] must pop21, leaving22. The later ACK22→21
regression is a second independent contradiction. The historical True expectation
and passing old outcomes must stay visible as an obsolete positive.

A narrow DISTINCT source-feasible replacement preserves its intended lesson:
keep the latest accepted22 and A2/R2, but consume the still-queued21 with matching
actor input/ACK21 and queue1 retaining22. Carry consumed21, actor21, ACK21 and
queue1 into the terminal tick. This proves a popped command need not belong to
the latest projected acceptance, without inventing packet identity. Alternatively,
add a real earlier pop21 before a later pop22 and update every affected counter,
queue, ACK and carried metadata. Do not patch only one field to force the old
expectation to pass or replace the historical bytes in place.

## Queued-duplicate positive has a one-field construction error

In test_queued_duplicate_accepts_without_queue_growth_or_command_replacement,
original[:5] already contains the first accepted sequence1/queue1. The inserted
duplicate receives copied original queue0, although no pop/skip/reset occurs
between them. Receive observes the queue before the later accept and removes
nothing. That duplicate receive must report queue1.

Minimum correction is duplicate[0]['queue_count']=1 before restamp. The duplicate
accepted row remains queue1. Its incoming fireFalse cannot replace the first
queued fireTrue because InputStream43-45 inserts only previously absent keys.
Keep consumed fireTrue and every existing assertion/mutation unchanged. Preserve
old test source and the first focused failure, and version construction changes
before assertions; never repair mutated input in the analyzer.

## Snapshot clarification carried forward

The prior R4 snapshot adjudication was delivered by collaboration messages;
there was no separate adjudication document. The guessed missing filename was
only a lookup failure, already retained in the R5 review. Exact source is
642dd0e0:test_input_consumption_lifecycle.py restamp/failed-attempt construction
and declared_rows in test_input_consumption_observation.py. The source sequence
has welcome6000 with count0/cache{}, then first counted snapshot-bearing tick7000.
Timestamp6000 is valid after the welcome within the inclusive interval. New
cache/latest must persist thereafter; a genuine previously positive cache on a
later welcome must not be restamped. R5 independent bindings reproduced this
transition and all inherited assertions; no R5 approval is attributed to that
read-only message adjudication.
