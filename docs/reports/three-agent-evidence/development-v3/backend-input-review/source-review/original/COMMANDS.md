# Commands and execution limits

All repository reads used `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3` as the working directory. No working-tree source, dirty integration code, reports, private/blind material, GitHub, or other agents' files were opened. No application, PostgreSQL, native test, benchmark, export, or network call was executed. No repository edit, commit, or post was made.

## Exact successful collection

`collect_review_sources.ps1` is the source-collection script actually executed. It reads immutable objects through `git show`, `git rev-parse`, and a scoped `git diff`; it does not execute application source. Its complete successful Git argv, result code, output byte length, and SHA-256 are in `git-commands.json`.

Invocation:

```powershell
& 'C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-source-critic-20261019T194154Z\collect_review_sources.ps1'
```

The canonical combined diff command recorded by that collector is:

```powershell
git --no-pager diff --no-ext-diff --no-textconv --no-renames --unified=3 d2439acdd5f73df7bae5ada62ee1e3dec2cf30db 4a8e9ea73aa8b286d9f1751b0a6b485479737294 -- backend/app.py backend/tests/test_trade_reads.py scripts/benchmark_trade_reads.py
```

Combined authorized diff SHA-256:

`0d3736d44d7261f440df67763dc85dfd61f1bc61c31f8b2b2cfb02295749133f`

App-only diff was also captured without newline transformations:

```powershell
git diff --no-ext-diff --no-textconv --no-renames --unified=3 --output=C:/Users/blith/AppData/Local/Temp/opencode/sol-backend-source-critic-20261019T194154Z/pr16-to-candidate-app.diff d2439acdd5f73df7bae5ada62ee1e3dec2cf30db 4a8e9ea73aa8b286d9f1751b0a6b485479737294 -- backend/app.py
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-source-critic-20261019T194154Z\pr16-to-candidate-app.diff'
```

App-only diff SHA-256:

`c07b93646c716416f8751cf0229fa6d145d683043741a8b207a309f7e578b2e3`

## Initial discovery commands

- `git rev-parse --verify 4a8e9ea73aa8b286d9f1751b0a6b485479737294` resolved.
- An initial literal interpretation of `PR16d243...` attempted `git rev-parse --verify 16d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`; it failed because that string is 42 hex characters. Candidate-parent metadata established the intended baseline as PR 16 / `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`.
- `git rev-parse --verify 701ce2c` resolved to `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.
- `git show -s --format="%H%n%P%n%s" 4a8e9ea73aa8b286d9f1751b0a6b485479737294` established its PR16 parent.
- `git diff --name-status d2439acdd5f73df7bae5ada62ee1e3dec2cf30db 4a8e9ea73aa8b286d9f1751b0a6b485479737294 -- backend` identified the app change and added trade-read tests.
- `git diff-tree --no-commit-id --name-status -r 4a8e9ea73aa8b286d9f1751b0a6b485479737294` identified the new workload script. The listed documentation/report file was not opened or reviewed.
- Before capture, the same pinned app diff, new tests, and workload were read with `git diff` / `git show`. Relevant app-helper/model definitions were read only from candidate Git objects. The collector saved line-numbered versions and hashes.

## Host startup and interpreter failures

Initial parallel PowerShell startups failed with `System.OutOfMemoryException` / exit 35. A later shell startup failed to load CoreCLR with `0x800705AF` / exit 137. Subsequent calls were serial. These are tool/host limitations, not backend measurements or source findings.

`py -0p` subsequently reported Python 3.14 and a CPython 3.13.15 registration pointing at:

`C:\Users\blith\AppData\Local\Temp\opencode\laya-python-runtimes\cpython-3.13.15-windows-x86_64-none\python.exe`

That executable and its parent runtime directory were absent. The following launch attempts failed before running any Python code:

```powershell
& 'C:\Users\blith\AppData\Local\Temp\opencode\laya-python-runtimes\cpython-3.13.15-windows-x86_64-none\python.exe' -I 'C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-source-critic-20261019T194154Z\collect_review_sources.py'
py -V:Astral/CPython3.13.15 -I -c "import sys; print(sys.version); print(sys.executable)"
```

The first returned command-not-found; the second returned `The system cannot find the file specified`. A limited standard-runtime directory check found no alternative 3.13. No runtime was installed, downloaded, or substituted. `collect_review_sources.py` is therefore an **unused/unexecuted collector**, not evidence of a Python run.

## Reproduction controls: saved, NOT executed

`isolated_assurance_controls.py` contains small stdlib-only controls for the query-budget false-pass and harness fixture shadowing. It refuses all interpreters except CPython 3.13. It reads only the pinned authorized Git objects, imports no application or native dependencies, and uses tiny temporary fixture files only in this external review directory. It does not execute the workload or access a database.

When an existing authorized CPython 3.13 executable is available, run:

```powershell
& '<existing-CPython-3.13-python.exe>' -I 'C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-source-critic-20261019T194154Z\isolated_assurance_controls.py'
```

No control-output artifact is present because these controls were **not run**. The source review distinguishes static deductions from executed results. No pytest pass, database result, concurrency experiment, memory benchmark, or performance verdict is claimed.
