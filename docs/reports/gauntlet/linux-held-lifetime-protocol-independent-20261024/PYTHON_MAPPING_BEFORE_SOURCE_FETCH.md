# Required static Python mapping only

Interpreter metadata is CPython3.12.14; this is no host wait/poll capability proof.
Fetch only the corresponding public tagged source files needed for the protocol:

- https://raw.githubusercontent.com/python/cpython/v3.12.14/Modules/posixmodule.c
- https://raw.githubusercontent.com/python/cpython/v3.12.14/Doc/library/os.rst

Preserve response/status/hash even on failure. Read source for waitid availability,
P_PIDFD/options export, None/si_pid-zero mapping, struct result/status fields,
exception and EINTR retry mapping. No source module or process API is executed.
No host proc, poll, wait, pidfd or subprocess experiment. A release tag/source
mapping is conditional evidence; deployed build/headers/kernel support remain
separate prerequisites. No extra Linux or process research is introduced.
