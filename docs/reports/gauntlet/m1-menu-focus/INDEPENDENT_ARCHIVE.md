# Independent menu evidence archive

The independent reviewer chose the candidate for the bounded field-menu keyboard
focus correction. The original [review](independent-review.md),
[brief](independent-critic-brief.txt) and [commands](independent-commands.md) are
verbatim copies. Their historical absolute workspace paths remain unchanged.
This file supplies the current archive paths and preservation notes separately.

[The compressed archive](independent-evidence.tar.gz) contains 123 files and
29,926,833 payload bytes. Its compressed size is 26,310,169 bytes (25.1 MiB), below
the archival limits of 32 MiB compressed and 64 MiB of file contents. PNGs and
videos retain their original bytes. Sorted archive entries use zero timestamps,
UID/GID zero and mode 0644; this changes filesystem metadata only.

The [archive manifest](independent-evidence-manifest.json) records every member's
path, size and SHA256. [Outer checksums](archive-sha256.txt) cover the archive and
its accompanying records. Verify and extract from this directory:

```sh
sha256sum -c archive-sha256.txt
mkdir -p /tmp/sightbreak-menu-evidence
tar -xzf independent-evidence.tar.gz -C /tmp/sightbreak-menu-evidence
cd /tmp/sightbreak-menu-evidence/menu-critic
sha256sum -c sha256.txt
```

The inner historical manifest has 117 entries; all are retained and verified.
The current manifest adds that manifest itself, the original critic brief and
four native Godot logs omitted by the earlier manifest's blanket state exclusion.
Those logs are at `native-*/state/data/godot/app_userdata/SIGHTBREAK/logs/godot.log`.
All other state files were font, Mesa or shader caches and are excluded.

| Historical location in the original review | Location inside the extracted archive |
| --- | --- |
| `builds/menu-critic/REVIEW.md` | `menu-critic/REVIEW.md` |
| `builds/menu-critic/COMMANDS.md` | `menu-critic/COMMANDS.md` |
| Original root `builds/mission-m1/menu-critic-brief.txt` | `menu-critic/critic-brief.txt` |
| `native-baseline` | `menu-critic/native-baseline` |
| Failed first native candidate | `menu-critic/native-candidate` |
| Passing second and final candidates | `menu-critic/native-candidate-r2`, `menu-critic/native-candidate-r3` |
| Failed setup/export logs | `menu-critic/setup-export-state.log`, `menu-critic/export-driver.log`, `menu-critic/failed-first-export` |
| Successful export receipts | `menu-critic/baseline-export-receipts`, `menu-critic/clean-export/linux` |

All four attempts retain original screenshots and videos, OS actions, native
logs and one-way observer events/status. Passing attempts also retain their
result files. The first failed attempt never wrote result.json because its
cleanup closed Xvfb before XCloseDisplay; its failure, actions and raw media are
preserved. Earlier complete controller revisions were not separately saved.
The original commands already disclose that limit; no controller was recreated
and presented as a historical original. The final executed controller is
`menu-critic/native-candidate-r3/controller.py`.

[Excluded artifact records](excluded-artifacts.json) identify the compiled
baseline and candidate ELF paths, sizes and SHA256 values, the shared engine
path/hash, the generated launcher and cache roots. No compiled app/engine,
downloaded template archive, key or cache is included. The two Godot license
files are plain text and remain so the original historical manifest stays
fully checkable.

Both source-bound receipts name clean sources. Baseline is
`561d0cbba651514bfac96c50437a849d65843545`; its ELF SHA256 is
`3a0d35a55d6ddc1cb461b1bb1087b2f562ada61ae82b4355d189151e6020cc4f`.
The final native menu candidate is
`6767e977ee886fe534350c43c35691e2dc7d9421`; its ELF SHA256 is
`8680ef47aab4e024eee0d5581e804fd4e08a76aa61a2cc2456df83c27f3c836b`.
Its shipping fix is 8de7331 plus the test UID only. Root's UID repair is aa0b0a4.
`source-reproduction.json` retains the exact UID diff and detached candidate's
commit object, tree and parent so that review source identity can be restored
if its worktree is removed. The pinned editor/template retrieval is defined by
the exact source's `scripts/toolchain.py`; no downloaded toolchain is committed.

To replay the controller, restore the payload at
`<matching-source-worktree>/builds/menu-critic` because its root lookup expects
that path. Use fresh outputs and the matching source-bound export receipt.
The recorded absolute commands require path adjustment for another machine.
The archived source identities and expected ELF hashes support reproduction;
this preservation step did not run another export or certify bit-for-bit
rebuild determinism.

This branch starts at 6a0d8d5 and changes only documentation/evidence. The archived
menu proof remains on its original 561d0cb/6767e97 sources. Root separately reports
that integrated validate.sh passes at 6a0d8d5 with intentional skips, and is running
other frozen M1 scenarios. Those results are outside this independent menu
review. Desktop CI [39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860)
has a reported source-suite isolation failure; this archive makes no overall CI
pass claim. Controller hardware, other UI journeys, full-match/objective results,
visual quality and release readiness retain their existing unverified status.
