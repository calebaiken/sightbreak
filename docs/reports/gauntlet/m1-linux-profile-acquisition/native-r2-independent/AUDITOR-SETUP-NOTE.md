The first independent auditor run is retained in `audit-first.stdout` and
`audit-first.stderr`. It exited 1 because it assumed the complete import cache
would still equal the terminal cache after the later export. The original
registration allows generated root `.godot` cache files; it requires the declared
staged source and UID identities to stay exact.

The corrected auditor retains every observed cache difference between the
original inventories, requires identical closed path sets, checks all 131 declared
source identities and the generated fixture UID at each reached inventory, and
requires all remaining differences to be inside the declared root cache. It
does not rewrite or rebaseline either original inventory, any cache or a native
receipt. The initial failed auditor run is not counted as a passing audit.

The original import cache version is represented by its immutable inventory
hash; its earlier bytes were overwritten during the registered export and were
not separately retained. The terminal cache bytes are retained. The auditor
does not claim independent historical byte readback for that earlier version.

A second failed auditor run is retained in `audit-second.stdout` and
`audit-second.stderr`. It required an independent live observation of the short
version process. The 100 ms observer missed that 0.134-second command. Import and
export were independently observed with actual CPU/LP/environment readbacks.
The final auditor records the missed version command as an explicit evidence gap
and checks its recorded identity/logs/cleanup and later absence. It certifies
the retained FAILED acquisition, not complete live observation or native success.
