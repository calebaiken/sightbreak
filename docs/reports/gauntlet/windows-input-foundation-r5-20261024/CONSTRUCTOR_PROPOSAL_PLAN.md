# Exact old R4 control proposal before execution

Root explicitly requested a minimal constructor-only alternative for the newly
reached source-invalid ACK1/count1/seq1 control. Do not edit the original method,
assertions or helpers. Original exact eight rows are retained in constructor-conflict.
Only create one versioned dataset, bound to those exact input bytes.

Named source witness for its pipeline/lifecycle projection: C2000,A3000; first
RX8000/A9000; coalesced authority tick9999 and direct pop1 at10000; hidden RX2/A2
at10500; emitted tick11000 before pop2; coalesced pop2 at11000; tick12000. Fixed
D22000, active10500, L10500 thereafter; queue1 at11000 before pop then0; ACK1→2;
RX/A counts2, consumption count1→2. The hidden pop keeps fire/move/reload edge
unchanged so its metadata/counter can coalesce. Other old full-row fields stay
synthetic/unadjudicated: this is a named projection witness, not native provenance.

Version only necessary counter/packet/timer/queue/ACK/control fields: tick counters
in rows6/7/8 account for the prepop observer; RX/A seq2 and timestamps10500 in
rows7/8; row7/8 ages500/1500; row7 queue1; row8 consumed counter2, latest popseq2
at11000, ACK2 and actor inputseq2. Deadline values remain unchanged. Save every
recursive leaf difference, original/versioned arrays and both reader results.
Original must INVALID, proposed must UNKNOWN. No arbitrary-input projection.

For review evidence only, clone the exact existing test method AST and replace
only its pre-control constructor statements by loading this fixed versioned
fixture. Keep the original control call, every assertion, seven mutation lambdas
and schema checks AST-exact. Compile/run that one proposal method separately,
never as maintained candidate credit or production test-source replacement.
Preserve the original unchanged suite failure and old constructor output. Another
critic must approve any future constructor edit before old assertions/helpers
could change; this report makes no such approval.
