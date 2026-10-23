# Sightbreak V3 final CI integration critic

## Outcome and review boundary

Two process-containment findings are verified below. Neither reproduces an ordinary-path Linux CI launch failure or a false-green matrix/campaign. This is a narrow source/mock review, **not acceptance and not a V3 native/CI pass**.

- Workspace: `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3`.
- Initial branch: `integration/sightbreak-v3-validation`.
- Initial HEAD: `bd12301ac69ac2952f65d70133b6c6b7020db534`.
- Primary reviewed sources: `.github/workflows/v3-development.yml`, `.github/workflows/engineering.yml`, `scripts/matrix_process.py`, `scripts/godot_process.py`, `scripts/validate_matrix.py`, and `scripts/run_network_campaign.py`; relevant setup, protocol-history, and export-launch contracts were checked read-only.
- The six primary files and the two files cited by these findings were byte-identical between the initial and closing hashes. `scripts/build_manifest.py` changed concurrently; its closing bytes are **not** represented as the reviewed initial revision. See `source-stability.json` and the two hash inventories. No finding below depends on its changed code.
- No repository source edits, commits, staging, resets, posts, fetches, engine/editor launches, campaign/export launches, databases or services were performed by this critic. The other agents' `verify_builds` and `reload_negative_controls` implementation/test topics were not inspected or executed.
- All executed Python was the approved CPython 3.13.15 at `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe` with `-B`. Linux behavior below is mocked; the sole real tree was two serial CPython processes, with the grandchild naturally finishing after two seconds. No broad process cleanup was used.

## F1 — P2: Linux crash fallback loses detached descendants after the owning supervisor dies

**Locations:** `scripts/matrix_process.py:113-122`, `scripts/matrix_process.py:159-180`, `scripts/matrix_process.py:203-209`, `scripts/matrix_process.py:242-250`.

Only the subprocess running `supervise()` becomes the Linux child subreaper. Unlike the Windows branch's parent-held Job Object, its caller retains no independent Linux descendant owner. If that supervisor dies before its cleanup/receipt completes, an already detached (`setsid`) descendant is reparented away from the dead supervisor. The fallback starts its discovery at the dead supervisor's PID. Once that `/proc/.../children` entry is absent, it only signals the old supervisor's process group; a descendant in another group is undiscoverable through that path.

**Reproduction:** `critic_controls.py`, function `linux_dead_supervisor()`; outputs `control-linux-dead-supervisor.json` and `linux-dead-supervisor.log`.

The pure mock supplies the post-death kernel state: supervisor PID/group `41000` has exited with `-9` and has no `/proc` entry or live process group; its detached descendant PID/group `41001` remains alive and has been reparented. Actual `run_process()` and fallback code execute against mocked process operations. Observed:

```json
{
  "returned_exit": 1,
  "raw_log_has_harness_error": true,
  "inspected_pids": [41000],
  "attempted_group_signals": [[41000, 0], [41000, 9]],
  "detached_pid": 41001,
  "detached_child_alive": true
}
```

**Impact/qualification:** This path correctly fails the evidence gate; it is **not** a false pass. It does not establish bounded cleanup after supervisor death, however: remaining native children could retain ports, resources or inherited log handles while later checks continue. This matters for fatal-signal/OOM behavior, not a demonstrated normal-path three-job Linux failure. No actual Linux process escape was launched in this review.

## F2 — P2: Windows tree helper reports successful cleanup after the root exits without containing its surviving child

**Locations:** `scripts/godot_process.py:96-111`, `scripts/godot_process.py:138-145`; the taskkill race is at `scripts/godot_process.py:106-109`.

If the root already exited, `terminate_process_tree()` skips `taskkill`, waits only on the root, and returns success. `cleanup_processes()` consequently returns no failures even if the root's child remains alive. There is a second instance of the same uncertainty: a nonzero `taskkill` result is ignored if a subsequent root poll says the root has exited.

**Reproduction:** `critic_controls.py`, functions `windows_dead_root()` and `windows_taskkill_race()`; outputs `control-windows-exited-root.json`, `control-windows-taskkill-race.json`, the marker files and `windows-root.log`.

The real approved-CPython parent spawns one approved-CPython child, waits for its startup marker, and exits normally. The critic opens a **synchronize-only** handle to that child, calls the actual `cleanup_processes()` on the exited parent, and checks the child handle before/after cleanup. Observed:

```json
{
  "root_exit": 0,
  "alive_before_cleanup": true,
  "alive_after_successful_cleanup": true,
  "cleanup_errors": [],
  "taskkill_call_count": 0,
  "grandchild_naturally_finished_and_handle_signalled": true
}
```

The pure race control separately supplies `taskkill.returncode == 128` and root poll results `[null, 0]`; cleanup again returns `[]`.

**Impact/qualification:** A successful return from this helper alone is not verified Windows descendant cleanup. This finding does **not** bypass the separate parent-held Windows Job Object in `matrix_process.run_process()`, and is not a Linux CI blocker. No real taskkill or process termination was issued by these controls.

## Evidence and reproduction command

The control program is exclusive-output by design. To repeat, copy `critic_controls.py` into a **new empty approved external directory**, then run the copied file with:

```powershell
& 'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe' -B '<new-empty-external-directory>\critic_controls.py'
```

Saved evidence in this directory:

- `commands.json`, `ancestry-commands.json`, `git-01.log` through `git-12.log`, and `git-final-status.log`: exact read-only Git commands/results. Both hard-coded protocol fixture commits were verified as ancestors of the initial HEAD; no missing-ancestry finding is claimed.
- `control-command.json`, `control-exit.json`, `controls.stdout.log`, `controls.stderr.log`: actual approved interpreter command and serial control run, exit `0`.
- `critic_controls.py` and the per-control JSON/raw logs: standalone reproduction and observed outcomes.
- `source-hashes-before.json`, `source-hashes-after.json`, `source-stability.json`, `additional-contract-source-hashes.json`: exact source SHA-256/byte counts and concurrency qualification.
- `syntax-only.json`: successful `ast.parse` of seven scoped Python/helper files. This is syntax-only, not a runtime test.

Actual Linux execution, setup downloads, native resource pressure, the three workflow jobs, and physical-device behavior remain unverified by this critic. No acceptance conclusion should be inferred from the absence of a further source/mock finding.
