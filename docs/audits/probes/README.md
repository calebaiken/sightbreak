# Audit reproduction probes (baseline `e67f2c8`)

Read-only probes used for `../CLAUDE_AUDIT_0.3.md`. They exercise the real code paths and print `AUDIT`, `SLOT_PROBE` or `B-` lines. They are evidence of the **audited** behavior: after fixes land, several numbers intentionally change.

```sh
# Gameplay, rendering-structure and timing probe (headless is sufficient)
./scripts/godot.sh --headless --script "$PWD/docs/audits/probes/audit_probe.gd"

# ENet idle-connection probe: start a dedicated server first
./scripts/godot.sh --headless -- --server --port=27993 &
./scripts/godot.sh --headless --script "$PWD/docs/audits/probes/slot_probe.gd" -- 27993 30

# Backend probe: disposable database whose name ends in _test
DATABASE_URL=postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/sightbreak_audit_test \
  PYTHONPATH=backend:backend/tests .venv/bin/python docs/audits/probes/backend_probe.py
```

Baseline output recorded on the audit host:

```
AUDIT fire_interval.smg = designed=0.0850s effective=0.1000s rate_designed=11.76/s rate_effective=10.00/s delta=-15.0%
AUDIT fire_interval.rifle = designed=0.1050s effective=0.1167s rate_designed=9.52/s rate_effective=8.57/s delta=-10.0%
AUDIT marksman_second_shot.normal = 0.833s after first (designed interval 0.82s)
AUDIT marksman_second_shot.quickswitch = 0.367s after first (designed interval 0.82s)
AUDIT spread_identical_for_same_actor_id_after_round_reset = true
AUDIT spread_differs_for_other_actor_id = true
AUDIT headshot_area.standing = counted_cells=1398 visible_head_cells=599 counted_outside_visible=799 (ratio counted/visible=2.33)
AUDIT headshot_area.crouched = counted_cells=1774 visible_head_cells=863 counted_outside_visible=1070 (ratio counted/visible=2.06)
AUDIT smoke_on_container.cloud_center = (-7.0, 1.6, -11.0)
AUDIT smoke_on_container.center_inside_container_volume = true
AUDIT inventory.after_halftime = ["sidearm", "rifle"] credits=1200 team=1 weapon=rifle
AUDIT round_start_cost = 228.9 ms for _begin_round() with 9 bot purchases
AUDIT snapshot_bytes = raw=6484 deflate=732 per_second_per_client=14640
AUDIT bot_navigation = 105.4 us/call, waypoints=176 obstacles=25, 10 bots @ 8.33 Hz = 8.8 ms per second of play
AUDIT weapon_model_build = 27.09 ms per first-person rifle build; meshes shared between builds=false
AUDIT actor_construction = 45.14 ms per actor (body batching + first-person gun)
AUDIT cosmetic_shader_shared_between_calls = false
AUDIT arena_batches = multimesh_batches=75 shadow_casting_batches=75 instances=1460 instances_thinner_than_5cm=578 ground_decal_boxes=176 label3d=40
AUDIT input_gate_drops_newer_bunched_packet = true
SLOT_PROBE idle_connections_established=30
SLOT_PROBE legitimate_11th_client_connected=true status=2
B-MARKET active_listings=501 mythic_active=1 filtered_result_count=0 (expected 1); unauthenticated request took 247.3 ms
B-KEY non_ascii_server_key_status=500 (expected 403)
B-ENUM median_ms existing_user_wrong_password=83.9 unknown_user=12.0
```
