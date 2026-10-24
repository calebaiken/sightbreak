# Additional coupled source cases before execution

Use the frozen builder's run_case only as an injected source fixture driver, not
its expected verdict. Root supplies and records independent obligations. Its
actual PipeRetention, WindowsJob.close_held and execute_prepared bodies run with
fake process/clock/kernel functions; real effects stay prohibited by guarded_runner.

1. Two failed sink closes + one failed pipe close + unexpected child handles300/301
   with held1300 failing: attempt both sinks/pipes/job handles, retain1300 and audit
   IDs100/200/300/301, return failed with finish metadata; no later sibling skipped.
2. Prior coherent audit then query failure + before/after state errors + stdout
   pipe failure: retain the pre-failure audit and attempt all resources, return
   failed/structured. Cleanup may remain failed; it never reconstructs old audit.
3. Terminal audit snapshot failure after an earlier success snapshot + pipe-close
   error: retain the already obtained audit, preserve typed snapshot/close errors,
   return failed/structured with finish metadata. No false successful closure.

Also inspect the normal original benchmark's actual pipe attempt counts: each
Popen pipe aliases streams.pipes and must be closed once, not twice. These cases
are additional pure source combinations, not native faults or capability proof.
Use identical data/expected obligations for repeat view. No variant tuning after
outcomes; preserve failures and interface/setup errors as their own records.
