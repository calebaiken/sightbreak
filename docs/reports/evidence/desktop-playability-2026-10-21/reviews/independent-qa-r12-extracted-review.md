# Independent review — extracted S12 Linux runtime and 960×540 layout

The actual extracted S12 package has independently supported launcher and defuse successes. The plant attempt **failed**, so the extracted objective aggregate remains failed. A separate new 960×540 capture case completes and its five original images support readable, contained default desktop UI. No local game or engine process was launched by this reviewer.

Source is clean `e3c1194a9c7bb2ff8a5e3b81ab122513dce4a32c`, game tree `45b6c6ea9d3244700e324e90d6df4778ee28d18e`, runtime content `0c471fb5c52826aa0391db7d4514429d08dc683f53d96e89f9176557d8a6f7ed`, validation `2f5ea31bacef994fd0a14b981e5b6abfca8e83a78da050c29d76c43a2fdc09fc`. Tested Godot is `4.7.2.stable.official.ed1daf0bf`, host Linux x86_64 with Xvfb/llvmpipe and dummy audio. Source/ELF identity agrees across both native receipts and the independently verified S12 package manifest. Actual extracted ELF SHA256 remains `fa05beef74745ddfe34145ac5beb7cac7f14f49e3205bf61cfe7b9fee69b729f`.

## Actual extracted execution

The real `/workspace/playability-evidence/packages-r12/extracted/linux/sightbreak.sh` launcher reaches the graphical main menu and exits 0 in 8.099 seconds. Raw `extracted-native-r12/launcher-menu.png` visibly shows that menu. The launcher and ELF both retain executable permissions.

The defuse controller uses the declared initial-spawn/side/seed fixture (seed 42), not stock full-match starting conditions. Ten living actors begin with stock sidearms; ordinary bot behavior, timers and objective rules remain present. Initial carrier is bot actor 2, and the ordinary device-armed event precedes every local E edge. The actual player moves 3.151081 m to approach the device.

An earlier eligible E hold is interrupted at tick 1410, and the independent input-edge event records progress reset to 0. The final E edge is tick 1434 / elapsed 23.9 s; the defuse notification is tick 1734 / elapsed 28.9 s. There is no intervening release: **300 ticks and 5 simulation seconds**, independently recomputed from input and notification clocks, rather than inferred from normalized progress. The measured command-to-observed-completion wall time is 8.709 s on this software-rendered host; this is not a claim of 5 real-time seconds on physical hardware.

Raw `05-objective-hold.png` visibly shows live defense, a planted device timer, living health 100 and E-hold progress. Raw `06-player-objective-completed.png` visibly shows DEVICE / DEFUSED, the ordinary defense round win, health 100 and funds 3800. Contribution moves 0→1; funds 800→3800 comprise the 300 objective reward plus the ordinary round award. Post phase and natural round-2 buy follow. Both actual application processes and Xvfb exit 0 with cleanup empty; complete defuse controller wall duration is 61.426 s. This is a one-round objective scenario, not earned full-match training qualification.

The extracted plant attempt remains **FAIL** at 48.091 s with `Legitimate native movement did not reach the requested floor position`. It reached the declared match but failed approach; it does not provide a plant completion. The raw failed trajectory and original controller exit 1 remain retained. The parent command aggregate must not be described as passed merely because defuse succeeded.

## New 960×540 original-image review

Five original 960×540 PNGs were independently viewed: main menu, active HUD, Tab roster, Field Menu and Field Settings. Text and controls are readable at their recorded native size; all ten roster rows fit. Health/ammo and navigation controls fit inside the frame. No clipping was observed in the currently visible settings fields; additional settings below the scroll area were not exhaustively reviewed.

The controller completes in 31.379 s, both graphical app roots and Xvfb exit 0, cleanup is empty and exact-source identity stays unchanged. The actual extracted ELF is the package-qualified one above. This new S12 observation closes the earlier S10 960 menu-only coverage gap for these five UI views. The earlier S10 failure remains preserved.

The live layout command uses `--demo` solely to enter the ordinary rendered layout; this does not constitute offline menu-to-match interaction, objective or full-match acceptance. This case does not certify scale changes, the entire scrollable settings surface, physical input feel or an 8.5/10 human quality score. Weapon, smoke and character art quality still require separate improvement and human review; the large polygonal smoke surface in the held-objective capture is visibly unfinished.

## Evidence and integrity

`independent-qa-r12-extracted-recomputed.json` records the original capture hashes and passing read-only audit assertions while explicitly preserving the underlying failed native aggregate. Native originals remain under `extracted-native-r12/` and `extracted-layout-960-r12/`.

The separate complete S12 package audit remains `packages-r12/results.json`: all five delivered archives pass exact source/hash/byte/mode/resource checks; modified byte, missing launcher, removed executable bit, developer file and changed receipt copies are all rejected. These strict negative controls were not weakened or rerun to erase earlier failures. Other OS qualification and S12 CI outcomes retain their own separate source-bound statuses.
