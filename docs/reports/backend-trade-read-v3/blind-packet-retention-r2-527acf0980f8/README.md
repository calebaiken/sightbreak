# Anonymous trade-read evidence: retained-artifact round

Use **only this directory** for this round. Save the earlier round's verdict
before opening this packet. Two opaque labels, **M** and **V**, were assigned by
a new random shuffle after measurement; neither label denotes a preferred
implementation. The controller holds source identities and input checksums in a
separate key. Save this round's verdict before requesting that key.

Start with `METHOD.md` and `REVIEW_QUESTIONS.md`. Each label directory contains
`measurement.json` and every referenced response/table artifact. There are seven
workloads per label, two warm-ups and ten timed responses per workload:
**168 received responses, 140 timing samples, and 336 full-table snapshots**.

- `responses/` holds exact received body bytes, deduplicated by content within
  each workload. Every warm-up and timed response points to its raw-body hash.
- `canonical-responses/` holds canonicalized **actual** received payloads and
  hashes. `expected-response.json` is a separate fixture expectation.
- `state/before/` and `state/after/` hold **full canonical row arrays** for every
  authoritative table, including empty arrays. These are not hash-only records.
  Each table has a row count and hash; the aggregate state hash is recomputable
  from all twelve table files. There is no separate aggregate-body file.
- `equivalence.json` is symmetric derived metadata. Check it against the bodies
  and rows rather than accepting its booleans as proof.
- `SHA256SUMS.txt` covers all other packet files. Run
  `python -B verify_packet.py` with Python 3.12+ for file, arithmetic, actual-body
  and full-row verification. The verifier is standard-library-only and accesses
  neither an application nor a database. Do not use Python's `-O` mode because
  the supplied verifier uses assertions.

The packet contains no source/checkout labels, commits, original run headers or
database identifiers. Source-bound provenance is held outside it. Original
fixture-row timestamps are preserved for honest full-row hashing; they can
reveal chronology. Recognizable query-count signatures can also link anonymous
variants across rounds. New labels do not erase those behavioral clues.

These artifacts permit independent recomputation of the retained body/row
claims. They are not independent instrumentation of the original execution, a
source authorization audit, or broad monetary-contract acceptance. The earlier
round's digests were **expected-fixture hashes**; judge these new actual-body
artifacts on their own evidence.
