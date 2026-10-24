# Retained audit mismatch, before audit correction

The first raw parity audit failed on the versioned seq21/22 corrected authority
input. The frozen builder replay iterates a Python set of CONTROL_KEYS when
rebuilding actor.input, so two independent processes can serialize those object
keys in different orders. Original copied inputs and outcomes are unchanged;
the separate generated corrected case has identical parsed objects and verdicts.

Preserve the failed audit script/stderr. Its correction permits semantic JSON
comparison only for that specifically versioned authority.log, records its
serialization difference explicitly, and still requires exact byte parity for
all other cases/results. Both original serialized inputs remain tracked.
No candidate expectation or source guard changes; no repeated acceptance claim
from this audit correction. If another difference appears, retain and adjudicate
it separately rather than broadening the exception.
