# Independent saved-process reconstruction

Separate critic `/root/collector_native_preflight_critic_20261024/movement_reachability`
read saved process evidence only on CPU4. It launched no engine, live observer
or signals and changed no raw files.

| PID/start ticks | Observed role | Sample lines | Elapsed seconds |
| --- | --- | --- | --- |
| 6283/1732134 | Python movement runner | 1–140 | 0.718379–14.829013 |
| 6284/1732144 | Pinned engine version | 2 | 0.820209 |
| 6287/1732153 | Bootstrap native producer | 3–5 | 0.921392–1.123841 |
| 6297/1732185 | Private import | 6–69 | 1.224963–7.615231 |
| 6534/1732824 | Before-suite native producer | 70–71 | 7.716629–7.819189 |
| 6544/1732846 | Movement suite | 72–135 | 7.920590–14.321813 |
| 6554/1733499 | After-suite native producer | 136–138 | 14.422960–14.626303 |

All six Godot commands use the pinned executable and the same private project
where applicable. No command contains the collector-enabling flag. Every child
has PPID/PGID/SID6283; runner PPID6238 and PGID/SID6283. Every sampled native
thread mask is exactly[0,1]:1,392 observations,48 distinct TIDs, maximum13
simultaneous sampled threads. These are eligibility masks, not CPU consumption.

The140 running rows have139 adjacent gaps: minimum0.101040142s,
median0.101301380s, maximum0.105988338s at lines128→129. Each identity's observed
presence is contiguous. The first sample occurs0.718379s after wrapper start;
the maximum-gap statistic excludes this leading interval.

Runner is live at line139/14.727973s, zombie at line140/14.829013s, then absent
in the empty cleanup-start row141/14.830067s. Every child disappears by the next
sample after its last appearance. Exit is recorded at14.830052s,405.169948s
before420; total wrapper wall15.012425s. No cleanup signal is recorded.

There is one empty cleanup sample, rather than sustained five-second observation.
The five seconds is a cleanup ceiling. Finite samples cannot exclude brief
processes/threads, escaped descendants outside discovery, or affinity changes
between samples. Supervisor6238/start1732055 has one CPU4 snapshot only. No
sampled affinity, group/session, deadline or observed-remnant violation appears.
