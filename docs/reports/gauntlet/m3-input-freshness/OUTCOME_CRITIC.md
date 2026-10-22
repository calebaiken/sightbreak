Choose **A** for the declared native input-freshness criteria. Its raw authority rows meet both distinguishing requirements in prediction-off and prediction-on modes. B fails both. This is a functional verdict for these supplied cases, with no conclusion about graphical presentation, player feel, scale, or release readiness.

| Recomputed outcome | A, prediction off / on | B, prediction off / on |
|---|---|---|
| Snapshot gap, authority displacement during 3.8–4.8 s | 0 / 0 m | 1.020009756 / 1.003009319 m |
| Snapshot gap, maximum absolute authority velocity during 3.8–4.8 s | 0 / 0 m/s | 1.019999981 / 1.019999981 m/s |
| Snapshot gap, stop after last advancing consumed ACK | 0.316 / 0.333 s | No stop before snapshot resumption in either mode |
| Snapshot gap, maximum client pending history | 120 / 120 commands | 120 / 120 commands |
| Stale replay, first authority row with peer retired | 32.040 / 32.032 s | Still bound at 34.009 / 34.010 s |
| Stale replay, final binding / lifecycle / input queue / pending join counts | 0 / 0 / 0 / 0 in both modes | 1 / 1 / 1 / 0 in both modes |

For the snapshot cases, I selected raw authority rows with `3.8 <= t <= 4.8`, computed absolute endpoint displacement and maximum absolute `vx`, and located the last ACK advance before 4.8 s and the first subsequent row below 0.001 m/s before 5 s. A's last ACK advances were at 2.985/2.947 s, followed by stops at 3.301/3.280 s. Both meet the 0.350 s bound. B has no qualifying stop before resumption. Client rows independently establish the 120-command bound; A first reaches it at 2.937/2.880 s and B at 2.940/2.898 s.

Stale replay corroborates the difference beyond the summary metrics: A stops at 2.375/2.367 s after its ACK stops advancing, rejects 900 packets per mode, and retires the peer within the declared 31.5–32.5 s window. B's ACK remains fixed while its recorded input freshness timestamps keep advancing, its authority continues rightward at approximately 1.02 m/s, and its binding, lifecycle entry, and input queue remain present at the end. I checked the retirement transition in the authority rows and the cleanup counts in the raw server receipt; per-table cleanup is reported only as final counters, not a time series.

Both labels preserve the declared ordinary and recovery behavior. Across all twelve steady, input-gap, and recovered snapshot cases, authority rows show exactly two shot increments, ammunition 15 to 13, and an actual `fire_held` false-to-true transition at each shot. The snapshot timeout does not invent a release or extra shot in these records. Every authority row in these twelve cases retains its peer. All 7.0–7.8 s recovery samples have `vx = -1.019999981 m/s`, meeting the fresh-leftward criterion. Neither label shows a regression on these declared controls.

Checks actually performed:

- Verified SHA-256 for all 81 manifest entries, including the criteria. The directory contains exactly those files plus `MANIFEST.json`: sixteen expected scenario/mode cases, each with both raw JSON receipts, both logs, and metrics.
- Parsed every JSON receipt and inspected all 32 native logs. Every log identifies official Godot `4.7.2.stable.official.ed1daf0bf`, contains its role's intentional barrier retry and completion markers, and contains no error/warning output. Every server logs readiness. All metrics report both processes exiting with status 0.
- Checked protocol 6, zero recorded privacy violations, zero hit-history frames, prediction agreement, and barrier retry counters in both raw roles. Read retry counts are 15 except two A clients with 16; publish retries are 0.
- Evaluated all 13,937 authority rows and all 13,937 client rows. Raw timestamps are strictly increasing, values are finite, and runs cover the declared 8 or 34 seconds. The largest observed sample interval is 34 ms.
- Performed 384 assertions against recomputed metrics, raw history maxima, ACK and stop timing, shot/ammo edges, binding continuity, timestamps, finite values, and mode fields. All passed. The recomputed numerical metric fields matched the supplied summaries; the verdict does not depend on their precomputed pass flags.

The **single largest remaining deficiency is repeatability evidence for A's stopping bound**. There is only one supplied trial per scenario/mode, and the prediction-on snapshot stop at 0.333 s leaves roughly 17 ms before the declared limit. The records prove that this run passed; they do not establish that the same bound holds across repeated shared-host scheduling variation. Repeated native trials focused on this threshold would address that uncertainty directly.

No artifact-integrity failure or observed correctness/regression issue blocks the narrow choice of A. Evidence limits remain: private-field absence is supported by the probe's zero-violation counters, not an independently supplied packet capture; cleanup tables are supported by final receipt counters. The blind package does not contain the source or driver needed to audit those instruments.

I inspected only the blind directory and did not seek label mappings or source identities. Blinding is partial: launch commands were removed, but outcome fields can reveal behavioral differences. Matching a supplied manifest establishes internal integrity, not independently authenticated provenance. The omitted commands and withheld originals mean I cannot independently establish the claimed identical driver/fixture, source launch equivalence, or that no trial was omitted. The official engine version is directly corroborated by every log. These are single-client headless, sequential, same-host observations; there is no basis here for WAN, ten-client, physical-device, visual, or tactile claims. None of those limits reverses the measured distinction between A and B.
