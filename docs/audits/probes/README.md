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

## Re-run on `claude/independent-audit-visual-v04`

Same probes, same host, after the fixes. `verification_probe.gd` replaces the F-HEAD section of `audit_probe.gd`, which hard-codes the 0.3 headshot rule and so cannot measure the new authoritative path (`SBActor.trace_shot`):

```sh
./scripts/godot.sh --headless --script "$PWD/docs/audits/probes/verification_probe.gd"
```

```
AUDIT fire_interval.smg = designed=0.0850s effective=0.0851s rate_designed=11.76/s rate_effective=11.76/s delta=-0.1%
AUDIT fire_interval.rifle = designed=0.1050s effective=0.1051s rate_designed=9.52/s rate_effective=9.52/s delta=-0.1%
AUDIT marksman_second_shot.normal = 0.833s after first (designed interval 0.82s)
AUDIT marksman_second_shot.quickswitch = 0.833s after first (designed interval 0.82s)
AUDIT spread_identical_for_same_actor_id_after_round_reset = false
AUDIT spread_differs_for_other_actor_id = true
AUDIT smoke_on_container.cloud_center = (-7.0, 4.7, -11.0)
AUDIT smoke_on_container.center_inside_container_volume = false
AUDIT inventory.after_halftime = ["sidearm"] credits=1200 team=1 weapon=sidearm
AUDIT round_start_cost = 0.9 ms for _begin_round() with 9 bot purchases
AUDIT snapshot_bytes = raw=6540 deflate=735 per_second_per_client=14700
AUDIT snapshot_exposes_enemy_positions_and_carrier = true
AUDIT bot_navigation = 110.2 us/call, waypoints=176 obstacles=25, 10 bots @ 8.33 Hz = 9.2 ms per second of play
AUDIT weapon_model_build = 0.06 ms per first-person rifle build; meshes shared between builds=true
AUDIT actor_construction = 0.68 ms per actor (body batching + first-person gun)
AUDIT cosmetic_shader_shared_between_calls = true
AUDIT arena_batches = multimesh_batches=9 shadow_casting_batches=4 instances=1472 instances_thinner_than_5cm=590 ground_decal_boxes=176 label3d=40
AUDIT input_gate_drops_newer_bunched_packet = true
VERIFY headshot_area.standing = counted_cells=577 visible_head_cells=599 counted_outside_visible=0 body_cells=3038 (ratio counted/visible=0.96)
VERIFY headshot_area.crouched = counted_cells=852 visible_head_cells=863 counted_outside_visible=0 body_cells=620 (ratio counted/visible=0.99)
B-MARKET active_listings=501 mythic_active=1 filtered_result_count=1 (expected 1); unauthenticated request took 29.9 ms
B-KEY non_ascii_server_key_status=403 (expected 403)
B-ENUM median_ms existing_user_wrong_password=154.3 unknown_user=150.0
```

Still open, as the output shows: snapshots expose opponents (M-4), the input gate drops a newer bunched packet (L-4), and bot navigation cost is unchanged (L-10). The standing head grid counts 22 fewer cells than the drawn silhouette: 20 are the chin rows at 1.37–1.38 m, where the torso volume's top edge is nearer to the shooter and the hit counts as a body hit; the other 2 are exact tangent points at the head's widest edge.
