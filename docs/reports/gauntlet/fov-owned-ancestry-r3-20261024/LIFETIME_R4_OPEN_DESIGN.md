# Lifetime design issue found before implementation

The pinned Linux v6.6 `fork.c` retained by independent review `85cba435`, lines
2075–2091, returns `EPOLLIN | EPOLLRDNORM` only when the whole thread group exits.
This supports the proposed held-lifetime check; it is not an actual-host probe.

Do not simply exclude every ready pidfd from `live()` and declare cleanup fixed.
The existing `reap_descendants()` iterates `live()` to find adopted zombies. Such
a change could omit required reaping and leave an owned zombie unaccounted.
Conversely, numeric PID/start-tick matching must not certify that an exited held
descriptor refers to a replacement zombie. Existing cleanup semantics need an
explicit lifetime-bound exited/reaped state as well as a live state.

One possible mechanism is descriptor-bound `waitid(P_PIDFD, ...)`, with its own
supported-source, availability, status and fake-model contract. It is not part
of the currently proposed one-method protection extension and is not authorized
for implementation by that proposal. Another design is acceptable if it proves
both safe ancestry and complete owned-zombie accounting without numeric aliasing.
Do not widen the erasure guard or change protected cleanup to hide this gap.

The existing critic must adjudicate the exact required scope before code. No
process/poll/wait/pidfd experiment or native retry occurred. Keep the rejected
candidate frozen; current Linux acquisition remains blocked independently by the
missing child-list interface and inherited physical-source binding.
