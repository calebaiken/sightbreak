# Exact additional R4 precedence cases before execution

Use the exact R3 source-supported anonymous-accept UNKNOWN control, byte-copied
from sealed2945287b, as the common parent. Preserve that fixture and all8 original
single-field negatives unchanged, with their original expected statuses.

Add independent final-row variants expected INVALID: wall_unix_msec regresses;
input_received counter becomes3 while accepted stays2/rejected0; accepted counter
becomes3 while receive stays2/rejected0; stream_rejected becomes1 with no rejection
call; one new rejection counter/latest and RX3/A2 but stream_rejected2 exceeds one
call; same rejection call but stream_rejected0 fails to increase; latest received
fire0 differs from the sole latest accepted fire1 while exactly one RX/A and no
rejection occurred in the interval. Hidden rejection metadata uses the same source
packet projection/time10500; schema must be checked for every row before reader.

These source contradictions test guards still below lifecycle UNKNOWN. Retain
prior d2cab results as a comparison, not an oracle replacing source reasoning.
No fixture repair/normalization. If a proposed probe fails schema, preserve it as
a test-construction failure and do not count it as a candidate failure.
