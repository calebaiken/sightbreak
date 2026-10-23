# Independent live process observations

Read-only observer began at 09:59:43.434950Z before the 10:00:08 controller
launch. It ran on CPU4 with one-second metadata scans and its own 3,600-second
observation cap, which did not control or bound the original pipeline. It
stopped on the existence of lane-end.json at 10:33:22.841824Z, after 1,919 scans
and 2,019.407 seconds. No image, log or quality output was read by the observer.

The immutable 9,564,827-byte JSONL has SHA-256
`4f804f7931763aad7b879285a35d43a1c4641edd3ea84ae0f6420b95bfe8ca46`.
It retains live `getpgid`, `getsid`, `/proc` group/session/start ticks, commands,
affinity and only the named display/thread/private-state environment selectors.
It also retains outer controller/shell identities and group/session members.

Nine of the eleven recorded owned processes were observed alive: both imports,
Xvfb, shared backgrounds, both controls producers, baseline input_mode, candidate
touch and candidate input_mode. Each observed native producer had live PGID and
SID equal to its recorded PID and actual affinity CPU0-3. Xvfb had its own live
group/session and inherited CPU0-4, consistent with the unchanged controller's
display launch. The short version and baseline touch processes ended between
scans; their live identities cannot be invented. Their original command/result
receipts remain separate evidence.

Full process-group cleanup FAILS its preregistered terminal absence condition.
At the observer's terminal scan, PID136526 was sleeping with PPID1 and group/
session136513, the background producer's actual observed group/session. Its
start tick2199755 follows the background leader's2199750. By the separate
10:40:34.970411Z check it was a zombie with the same start/group/session and
affinity CPU0-3. The later exact comm/stat/status read identifies `dbus-launch`.
No reviewer signal was sent. The 10:44:17 independent terminal scan still found
that zombie, with no unreadable `/proc` records and no :131 socket/lock.

All controller leaders were recorded absent and the display was removed. Those
facts do not erase the observed descendant. The controller only signals groups
while their recorded leaders remain running, so successful leader cleanup and
archival assertions cannot prove complete descendant absence. A zombie performs
no continuing application work, but the required group-absence observation is
false. These separate states remain in the original evidence and this review.
