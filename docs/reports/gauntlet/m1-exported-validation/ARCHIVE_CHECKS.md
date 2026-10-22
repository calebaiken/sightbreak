# Preservation checks

The archivist's read-only [verifier](verify_archive.py) checks all 445 member
paths, sizes and hashes; all 346 entries in the critic's original manifest;
the ten externally referenced baseline members; and all 418 retained raw snapshot
hashes. It checks source/ELF receipt consistency, synthetic profile scope,
verbatim report copies, bounds and excluded-content rules. The
[saved result](archive-validation.json) records 61 plant-r1, 188 plant-r2 and 169
defuse-r1 snapshots, 154 PNGs, 100 TSVs, one MP4 and two anonymous synthetic profiles.
The outer `sha256sum -c sha256.txt` check also passes. These are preservation
checks and execute no game or test controller.

`/root/native_validation_critic` separately confirmed its local report was final,
checked all three outside report/brief copies against the originals, spot-checked
that all 445 archive member paths are safe and confirmed the retained scope:
bounded objective/X11 PASS, complete layout FAIL and the 1.5-second queued-input
limitation. Its main report SHA256 is
`98e369638d7666231d34127b30b71172aeb003c3a24ce849fff48b460ef17dd7`.
That spot-check did not repeat the all-member hash audit; the verifier and saved
result provide that audit. Its separate CI review is outside this archive.

Re-run from this directory:

```sh
sha256sum -c sha256.txt
python3 verify_archive.py
```

The existing baseline archive must remain at its documented sibling location.
No implementation, mission worklog, progress or next-session file changed, and
no gameplay execution or wider gate acceptance occurred during preservation.
