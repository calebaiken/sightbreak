# Live process inspection corrections

The first independent process inspection stopped before writing a receipt:
`FileNotFoundError` for `/proc/98374/task/98374/children`. The exact owned driver
exists, with PID/Tgid/NSpid 98374 and one thread, but this environment omits that
optional proc file. The inspector now falls back to `ps -o pid= --ppid 98374`,
retaining only children of the explicitly supplied fake-run driver.

The next inspection stopped at its cwd assertion. Native PID 99164 executes in
`/workspace/sightbreak-account-activity/game`, while the inspector initially
required the repository root. The wrapper's game cwd is valid. The corrected
inspector accepts only that root and its game directory.

The third inspection succeeded. It retained eleven actual pinned-engine child
identities and hashes and the server's owned UDP socket inode in
`live-processes.json`. The actual game socket is wildcard IPv6 on port 37622.
These were independent observer-tool failures, not native gameplay failures.
No game, backend, worker or builder-harness source changed for these corrections.
