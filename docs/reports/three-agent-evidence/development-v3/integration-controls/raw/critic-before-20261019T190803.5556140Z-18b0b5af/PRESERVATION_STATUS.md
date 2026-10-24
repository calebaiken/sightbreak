# Preservation status

**Completed retrospectively. No controls rerun. No live source reads, source edits, fixes, or commits.**

- Original review: saved in `REVIEW.md`.
- Actual original command text: four command files plus `commands/execution-metadata.json`.
- Original tool-visible output: four transcribed output files; both the failed HUD harness and its corrected run are retained.
- Immutable baseline recovery: **18 of 18** exact Git blobs recovered and their Git blob IDs verified.
- Derived reviewed source: **19 files**, reconstructed only from those blobs, the retained pre-fix diff, and retained new-workflow text.
- All **seven changed tracked files** match the new-blob hash prefixes recorded in the original pre-fix diff. Full derived Git blob IDs and SHA-256 hashes are in `sources/source-evidence.json`.
- Original working-tree byte hashes, exact original execution timestamps, temporary fixture outputs/ZIPs/logs, and a real frozen-source receipt: **unavailable / not originally collected**. No substitutes are represented as original evidence.
- Original native Python crash: preserved as observed, including explicit exit `-1073741819` / `0xC0000005`; no clean unit-process pass is claimed.
- Integrity: `SHA256SUMS.txt` is created at preservation time for the saved files, excluding itself. It is not a contemporaneous execution receipt.

## Full derived blob IDs for the reviewed scope

These identify **reconstructed Git-normalized bytes**, not original working-tree byte captures:

| Path | Derived Git blob SHA-1 |
| --- | --- |
| `.github/workflows/engineering.yml` | `bfe82ec8077ad14a6544f3b80d54c37b701d2787` |
| `.github/workflows/v3-development.yml` | `d4da48ca5e7f2ef4ea48d1075756de66adbdff55` |
| `game/export_presets.cfg` | `468a8a1bea62779ae2c53d11ac2a332cccc718b4` |
| `scripts/build_manifest.py` | `b1a034a325d6f2e0b2da83d424e6cddb9d9c0837` |
| `scripts/test_build_manifest.py` | `dd87fd9d4d468c8d2fc3d8181b44dd3b17f16241` |
| `scripts/verify_builds.py` | `273b6bb1983ebdc494680c21ef9722a9bb42a9c8` |
| `scripts/verify_integration_export.py` | `23d89d49b4ea59b47bfacc4fa96c0cafad6456bf` |
| `scripts/verify_offline_export.py` | `988f96278a5462aa2dff1bd64a7da5561110cb7e` |
