# Independent S12 delivered-package qualification

All five original S12 archives pass independent extraction and inspection at frozen commit `e3c1194a9c7bb2ff8a5e3b81ab122513dce4a32c`. The external filesystem-only checker exited 0. Original archives, manifests, source receipts and source helpers remained unchanged. No engine or native executable was launched by this reviewer.

Frozen game tree: `45b6c6ea9d3244700e324e90d6df4778ee28d18e`. Runtime content SHA256: `0c471fb5c52826aa0391db7d4514429d08dc683f53d96e89f9176557d8a6f7ed`. Validation SHA256: `2f5ea31bacef994fd0a14b981e5b6abfca8e83a78da050c29d76c43a2fdc09fc`. Manifest SHA256: `8a1301cb37b2c0db1136653d631d27e8cbe4b556e7dbcd97d288a7b2f538f5d1`.

Each archive is bound to committed Git objects and the original seven successful export/inspect/package command receipts. Checks cover full entry inventory, safe paths/types, byte lengths and SHA256, exact payload archive_mode permissions, original source-receipt bytes/mode, notices, native headers/metadata/icons, included resource inventories and exclusion of developer tests. The 77 delivered entries contain 72 payload files and five source receipts; source receipt mode 0600 is preserved rather than replaced with an assumed 0644.

| Target | Entries / payload files | Inspected format | ZIP SHA256 |
| --- | --- | --- | --- |
| linux | 5 / 4 | x86_64 ELF/embedded PCK | `a867001007b865fdb0c2cc091d0eb2e21c329eed512c9ad8a3da8f2b00575d70` |
| windows | 5 / 4 | AMD64 PE/icon/version/embedded PCK | `6b402c3fbda241b17d3e8412973f0e0edfbaeb552400077e96684960fdd1ae5f` |
| macos | 11 / 10 | Universal2 Mach-O/metadata/icon/PCK | `d4353e2d33c8fb63a4a4872b3f1a85e904e85292ecd7800758448bcf155f7e9a` |
| android | 5 / 4 | APK assets and arm64/x86_64 native libraries | `d011d44680267728469fa057669f12e57499aba4843c77a555eec2cc90bb3809` |
| ios | 51 / 50 | Unsigned iOS Xcode project/PCK/catalogs | `af0baaa9dec4f0e13cf4ca344c1b8417c61541af0f102a62dac23ee5e62557d9` |

All five mutated copies were rejected: changed executable bytes, missing launcher, removed executable permission, added developer-only file and changed source receipt. Those negative copies and reasons are retained under `packages-r12/`. Desktop packages each contain 132 accepted PCK resources. Android inspection preserves the root-run exact-source SDK v2/v3 signature receipt and independently checks its delivered bytes/resources; this reviewer did not repeat SDK execution. Android physical execution and iOS Xcode build/device execution remain UNVERIFIED. The iOS delivery is an unsigned Xcode project, not a macOS application.

The actual extracted Linux executable is `/workspace/playability-evidence/packages-r12/extracted/linux/sightbreak.x86_64`; the launcher is `/workspace/playability-evidence/packages-r12/extracted/linux/sightbreak.sh`. Both have mode 0755. Executable SHA256 is `fa05beef74745ddfe34145ac5beb7cac7f14f49e3205bf61cfe7b9fee69b729f`. They are available for separately coordinated native execution. Windows and macOS runtime functionality is not established by this archive-only qualification.

Results: `packages-r12/results.json`. Raw checker output: `package-qualification-r12.log`. Checker source: `qualify_packages.py` (SHA256 `8a42987471f0d4fa592d40e36ee3fcc30e2fe6d73fe3ae86ec9272868ad858bd`). The original S7 external-checker permission-assumption failure remains retained separately; this result does not erase earlier failure evidence.
