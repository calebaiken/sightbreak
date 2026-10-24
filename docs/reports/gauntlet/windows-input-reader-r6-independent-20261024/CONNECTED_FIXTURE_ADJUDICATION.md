# Read-only fresh-connected fixture adjudication

At root's request, independently inspected the retained declared_rows helper
without changing R6 product/tests or old fixtures. Its first authority
peer_connected row declares peer9/generation1 but input_age_msec=-1 and
deadline_remaining_msec=-1 because its helper conditions both on bound status.
This is schema-positive historical data, not a source-faithful fresh connection.

Match._peer_connected calls PeerLifecycle.connected before the observation hook.
For this first successful connection, connected initializes generation,
last_input=connect_now and deadline=connect_now+JOIN_MSEC(20000), with joinedfalse.
The observation samples the lifecycle regardless bound_actor. Therefore at a
later sample input_age>=0 and deadline_remaining=20000-input_age. Remaining time
can be negative if scheduling delays the hook; do not infer a universal positive
deadline merely from the peer_connected reason. A same-millisecond witness has
age0/deadline20000, the minimum declared-helper correction for that one row.

Later bound/received/tick helper ages/deadlines also need their own state/time
model before a broader lifecycle validator can treat them as source positives.
A fixed deadline must age with time; admitted/accepted activity changes last_input
but does not extend the join deadline. Preserve every original helper/assertion
and preregister any future full-helper correction. A necessary expiry-predicate
component can be independently tested without claiming all row lifecycle fields
are modeled. This review's v3 Emitter already computes lifecycle clock fields
for both unbound and bound live states; original v1/v2 placeholders remain raw.
