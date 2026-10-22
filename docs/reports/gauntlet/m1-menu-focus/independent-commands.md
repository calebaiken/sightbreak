# Independent menu review commands, 2026-10-22 UTC

Reviewer: `/root/menu_critic`. All product inspection and execution used isolated
detached worktrees. Commands below are the actual task commands; read/search/view
calls are described in the review. Native subprocess commands, PIDs, native actions,
relative clocks, observations, captures and cleanup exits are in each
`native-*/actions.jsonl` and `result.json`. No in-engine menu/debug commands were used.

```sh
cd /workspace/sightbreak-v1-execution
git worktree add --detach /workspace/sightbreak-menu-review 8de7331
cd /workspace/sightbreak-menu-review
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/setup python3 scripts/toolchain.py setup --targets linux
mkdir -p builds/menu-critic
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/export python3 scripts/export.py linux > builds/menu-critic/export-driver.log 2>&1
git show 561d0cb:game/scripts/main.gd > builds/menu-critic/baseline-main.gd
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/baseline ./scripts/godot.sh --headless --script res://tests/menu_focus_test.gd -- --baseline-source=/workspace/sightbreak-menu-review/builds/menu-critic/baseline-main.gd > builds/menu-critic/baseline.txt 2>&1
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/candidate ./scripts/godot.sh --headless --script res://tests/menu_focus_test.gd > builds/menu-critic/candidate.txt 2>&1
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/input ./scripts/godot.sh --headless --script res://tests/input_mode_test.gd > builds/menu-critic/input-regression.txt 2>&1
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/export python3 scripts/toolchain.py setup --targets linux > builds/menu-critic/setup-export-state.log 2>&1
mv game/tests/menu_focus_test.gd.uid builds/menu-critic/generated-menu_focus_test.gd.uid
git cherry-pick aa0b0a4
git diff 8de7331 HEAD -- game/scripts/main.gd
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/setup SIGHTBREAK_BUILDS_DIR=/workspace/sightbreak-menu-review/builds/menu-critic/clean-export python3 scripts/export.py linux > builds/menu-critic/clean-export-driver.log 2>&1
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/setup SIGHTBREAK_BUILDS_DIR=/workspace/sightbreak-menu-review/builds/menu-critic/clean-export python3 builds/menu-critic/native_menu_review.py --output builds/menu-critic/native-candidate --display :223 > builds/menu-critic/native-candidate-driver.log 2>&1
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/setup SIGHTBREAK_BUILDS_DIR=/workspace/sightbreak-menu-review/builds/menu-critic/clean-export python3 builds/menu-critic/native_menu_review.py --output builds/menu-critic/native-candidate-r2 --display :224 > builds/menu-critic/native-candidate-r2-driver.log 2>&1
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/setup SIGHTBREAK_BUILDS_DIR=/workspace/sightbreak-menu-review/builds/menu-critic/clean-export python3 builds/menu-critic/native_menu_review.py --output builds/menu-critic/native-candidate-r3 --display :226 > builds/menu-critic/native-candidate-r3-driver.log 2>&1
```

The first export failed because `export` had different template state from `setup`.
The later setup attempt failed with `ETXTBSY` while the shared editor binary was
executing; no toolchain repair was needed. Subsequent exports used the already
initialized `setup` state. Import also exposed the omitted test UID. Root supplied
UID-only `aa0b0a4`; its cherry-pick produced `6767e97`. Shipping `main.gd` was
unchanged from `8de7331`. No tracked implementation file was edited by the reviewer.

`native-candidate` used the first controller revision. It reached three Return
resumes but its held-input prerequisite timed out during the stock buy phase;
cleanup then closed Xvfb before XCloseDisplay, causing the driver's XIO exit and no
result.json. `native-candidate-r2` waits for the ordinary live phase and closes the
X11 connection before server cleanup. It passes. `native-candidate-r3` additionally
waits for two rendered frames before each screenshot, avoiding one-frame-late
navigation images under software rendering. The exact executed final controller
is retained as `native-candidate-r3/controller.py`; the final current controller
is also `native_menu_review.py`. Earlier action logs and PNG/video evidence are
preserved, but their original complete controller files were not separately saved.

```sh
cd /workspace/sightbreak-v1-execution
git worktree add --detach /workspace/sightbreak-menu-baseline 561d0cb
cd /workspace/sightbreak-menu-baseline
mkdir -p builds/menu-critic
cp /workspace/sightbreak-menu-review/builds/menu-critic/native_menu_review.py builds/menu-critic/native_menu_review.py
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/setup SIGHTBREAK_BUILDS_DIR=/workspace/sightbreak-menu-baseline/builds/menu-critic/clean-export python3 scripts/export.py linux > builds/menu-critic/export-driver.log 2>&1
cp /workspace/sightbreak-menu-review/builds/menu-critic/native_menu_review.py builds/menu-critic/native_menu_review.py
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-menu-review/builds/critic-state/setup SIGHTBREAK_BUILDS_DIR=/workspace/sightbreak-menu-baseline/builds/menu-critic/clean-export python3 builds/menu-critic/native_menu_review.py --output /workspace/sightbreak-menu-review/builds/menu-critic/native-baseline --display :225 --expected-resume no > builds/menu-critic/native-driver.log 2>&1
```

The baseline driver was the r2 controller revision (before the rendered-frame
fence). Both original baseline menu screenshots were inspected; both show the
same unselected buttons, and the observer confirms Return remained paused.

The final controller starts Xvfb at1280x720, constructs NativeUI before the game,
records raw X11 video with ffmpeg when available, launches the source-bound Linux
executable with GL compatibility and a read-only stock offline trace, and supplies
every menu/game action through XTest OS events. It uses XSetInputFocus only for
the ordinary native focus-loss/recovery case and WM_DELETE_WINDOW for clean close.
Each native attempt has its own XDG data/config/cache paths; no existing player
state, game API, match objective, save or timer was modified.
