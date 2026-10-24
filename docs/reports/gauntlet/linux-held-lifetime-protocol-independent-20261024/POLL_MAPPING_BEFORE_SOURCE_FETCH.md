# Required matching poll mapping, additive source-only scope

Root requests the same bounded CPython mapping for select.poll(0), since the
waitid source already shows interpreter-level EINTR handling. Fetch only:
https://raw.githubusercontent.com/python/cpython/v3.12.14/Modules/selectmodule.c

Pin complete bytes/hash and inspect poll register/result/timeout0/EINTR handling.
No select import probe, poll object, registration or poll/wait/process API executes.
The admissible proposed contract is one Python call per reconciliation, no
wrapper-level retry/fallback, and existing observed-success deadline checks after
return. This fetch cannot prove hard preemption or build/kernel availability.
