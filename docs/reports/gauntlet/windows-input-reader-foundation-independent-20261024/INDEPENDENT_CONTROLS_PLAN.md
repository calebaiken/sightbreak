# Independent source-model controls, before execution

Target exact728/19b869 model and frozen04d30 constructor proposal. Do not modify
old reader/helper/tests. No final native/whole-fixture validation is attempted.

Compare model outputs to independently declared source equations/operation cuts:
- Successful connection C0/1/2000 with capture delays0/1/19999/20000/20001/100000.
  Expect generation1, joinedfalse, L=C,D=C+20000 and sticky actor0; a delayed
  hook can have negative remaining time while age+remaining is still20000.
- C0/2000, admission offsets0/1/19999, later bound captures0/1/20000/30000ms.
  Admission exactly at20000/20001 is denied. Deadline never renews on admission.
- Gate at29999, active at29999/30000/30001, capture at operation+0/1/30000.
  Only active before30000 refreshes L; callback capture time is separate.
- Joined/unjoined reject R0/1/29999, repeated rejectR+1, attempted activityR+2,
  capture/service predicate atR+499/500/501. Reject is absorbing and freezes L;
  original joined-idle predicate may expire before the rejected deadline.
- Concrete interleaved identities9/10, delayed bound/connect hooks, pre-forget
  disconnect, absent-after-forget projection, reconnect generation3, positive
  gate selection and sticky last actor. Compare ten explicit projection rows.
  Duplicate/full-connect transport callback acceptance is not adjudicated.

Independently reconstruct the old authority array by changing only the six timer
row pairs already preregistered. Compare the complete resulting dictionaries to
the proposed versioned array/model output; every other field and the original
client/authority objects must remain exact. Eight proposed negatives are source-
invariant adjudications in this fresh-successful context, not blanket rejection
of every peer_connected failure/duplicate/full hook. Keep their old-reader false
complete results as a pre-edit benchmark. No input normalizing validator is allowed.

Run the18 builder methods as attributed model evidence, then independent controls;
retain each source case/expected/actual/errors. All54 builder witnesses are one-way
only, not closed reconstruction. Validate original12 snapshots/105 methods and
all517 protected non-document paths against actual frozen2d Git identities.
