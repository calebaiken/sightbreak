# R2 acquisition source review: ACCEPT

Accept exact `6276f0b799fde78811075af1fc37434ea4d0aec8` for the declared
source and pure/mock scope. The reviewed wrapper SHA-256 is
`78ce6ba388e49b1e633612e17a1dd33c07efc23a49d47a9e0dbdd54af7e038a3`.
This does not release runtime or accept a future acquisition result. Root
must release candidate and regressions separately. Rejected `c7145cd` and
independent rejection `b8ccf8f` remain rejected.

The three retained falsifiers now reject. The original six-test source is
byte-identical and independently replayed with no edits: 239 seconds plus
a two-second overall write returns failure; a 121-second phase receipt under
the 120-second cap fails; an explicit squad failure beside success fails.
The clean four-stage candidate and ten-stage regression controls still pass.
The candidate authority audit precedes its after producer. Fixed native argv,
suite order, one shared import, per-suite private-state environments and the
separate 240/480-second whole limits remain unchanged.

All 49 methods pass with no skips: 25 retained builder methods, ten R2
publication methods, six unchanged original independent methods, and eight
new independent methods. Raw streams and replay JSON are retained. The added
independent controls establish these mocked boundaries:

* Four individually small I/O costs crossing either original whole cap fail,
  including a late final journal readback. Clean publication confirms both
  required artifacts under a positive alarm and the unchanged deadline.
* A late journal write demotes the earlier tentative receipt and the journal.
  Failure-only emergency publication cannot resume a native command or
  promote an already failed budget back to success.
* An unrecoverable readback followed by failed demotion returns failure with
  `publication_confirmed=false`. The original readback error stays primary.
  A prior strict native failure also survives failed recovery publication.
* A final private-state verification error rejects a previously clean
  four-native-stage candidate. Contradictory, extra and malformed squad result
  inventories and cross-suite explicit failure prefixes reject.

Source inspection confirms that phase stream/classification work and required
receipt writes/readbacks use the smaller original phase/whole deadline.
Successful final source/state checks and required overall receipt/journal
publication use the original whole deadline. Publication checks monotonic
time after each I/O and the readback set. Emergency publication is terminal,
failure-only and uses one non-resetting five-second allowance. The original
five-second scoped cleanup allowance is unchanged. No native recovery,
adaptive retry, suppressed warning or relaxed success count was added.

One evidence limitation is deliberate and independently exercised: a stored
tentative `passed=true` receipt and journal can remain if readback and failure
demotion both fail. Those files alone cannot establish success. Stored
`publication_confirmed=false` and `wall_seconds_before_publication` describe
their snapshot. Actual acceptance must retain and require the wrapper's final
terminal summary with `passed=true`, `publication_confirmed=true`, both
confirmed readbacks and zero wrapper exit, together with the phase/source
evidence. The final returned duration follows required publication/readbacks;
it is not substituted by the stored pre-publication snapshot. An absent or
failed terminal result stays failed even if tentative files say true.

Provenance passes 45 hashes: 22 R2 manifest entries and the accepted candidate's
23 entries. Accepted candidate manifest bytes and `game`/`scripts` tree IDs
equal exact `1b7ebc71290e6c4c23017f7a2d8539d7c5eec149`. Seven reviewed source
files match target Git blobs and the local review copy. Five retained rejected
artifacts decompress or compare byte-for-byte to their original `c7145cd` or
`b8ccf8f` objects. The new wrapper bytes are retained as deterministic gzip.
`source-binding.json` records these checks; no game/test-policy source changed.

The earlier source guarantees remain supported within their declared scope:
same-HEAD/block claim rejection; mechanical original Git/SHA-256 project copy;
source and staged manifests; separate original equality versus the permitted
generated UID addition; fixed prepared non-cache source set; native producer
identity/leftover predicates; strict complete stdout/stderr leak scanning;
and stop-on-failure before later native calls. The candidate pure authority
diagnostic cannot upgrade a strict failed acquisition. Successful mocked
producer receipts demonstrate controller predicates, not actual userdata.

The largest remaining gap is actual native behavior. There were zero engine
invocations, imports, GDScript compiles, actual native signals, services, CI,
OCR or nested agents in this review. Native producer defaults, parser/import
readiness, generated UID behavior, real private userdata, signal delivery,
shutdown and the original audio-object leaks remain unobserved. Process
cleanup only covers observed stable identities, ancestry and anchored session
members; an unobserved escaping/reparented descendant can still evade polling.
No arbitrary descendant cleanup, bot selection result, exported gameplay,
full-match, balance, tactical-quality or release gate is accepted here.

Root may use this source verdict when deciding whether to release one bounded
candidate attempt. Any actual result, including warnings, missing stages or
failed publication, requires a fresh independent actual-output review.
