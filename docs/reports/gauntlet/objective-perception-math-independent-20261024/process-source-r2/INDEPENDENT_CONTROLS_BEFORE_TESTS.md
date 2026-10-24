# Additional exact controls after source inspection, before tests

The b6 source diff preserves source_binding's six actual hashes plus Git quiet
checks. The registered hidden-physical/mode/native_log cases will run against a
new own initialized exact source view, with benign comments/mode changes only,
assume-unchanged flags recorded and restored, and no changed source executed.
Clean source_binding must pass first. Acquisition/engine is never called.

Source inspection also finds OwnedTree.observe accepts a PID from a children
snapshot without validating that its later observed PPID is that enumerated
parent. A real timing race can list an owned child, then reap/reuse its numeric
PID elsewhere before identity is sampled. Rechecking birth around pidfd then
pins the new unrelated object; it does not prove ancestry. Registered parent/
birth/no-unrelated-signal gates cover this control. A fake-only stale children
snapshot will point to an identity whose PPID is unrelated; it must not gain
owned membership or be signaled. Also inspect queued parent birth reuse before
recursing; direct Popen binding alone does not validate every descendant.

Keep positive direct-root binding with empty discovery separate from unavailable
required-interface failure. Check mandatory Popen wait/reap and forced-cleanup
acquisition failure, early observer errors/retained streams, and source-binding
worktree bytes/modes rather than Git status alone. All kernel/process operations
in these controls are fake; only local Git source metadata checks use Git tools.
No /proc probe, engine/API/helper trial or native signal is permitted.
