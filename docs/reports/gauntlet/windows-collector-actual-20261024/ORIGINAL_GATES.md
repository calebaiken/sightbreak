# Original source inventory, before the Windows attempt

A narrow delegated read-only source inventory used CPU4, launched no engine,
and changed no files. Relevant controller/helper/game-test/profile/workflow
bytes at documentation-only HEAD728906f9 equal exact c3241514. These are
expectations and source predicates, not observed execution.

| Suite in original runner order | Expected checks |
| --- | ---: |
| actor | 73 |
| match | 75 |
| authority_order | 178 |
| state_privacy | 55 |
| movement_prediction | 742 |
| peer_lifecycle | 16 |
| input_mode (headless) | 462 |
| menu_focus | 30 |
| offline_diagnostics | 60 |
| hud_objective_hint | 1,535 |
| activity_provenance | 32 |
| bot_squad_symmetry | 2,722 |
| bot_dry_weapon | 590 |
| bot_exhausted_primary | 20,116 |
| transaction_journal | 41 |
| gunplay_rules | 2,840 |
| Total | 29,567 |

`scripts/run_native_regressions.py:23` fixes this16-suite order. The runner
requires exit0, strict-clean complete logs, isolation, resource invariance and
cleanup; it does not invent an assertion-count acceptance gate. Any actual
count deviation needs investigation. Movement source adds17 admission/projection/
disabled-state checks to the prior725.

`desktop-alpha.yml:148` fixes ordinary `--visit-armory --timeout240`;
`verify_integration_export.py:615` defaults to keyboard reload, legacy schedule,
zero synthetic delay. `export_integration.gd:136` requires joined_id>0, shots>0,
lowest_ammo<30, largest_ack>10, reload_seen/completed and a native reload command
unless explicit authority diagnostic. Completion at112 requires countdown<=0
and ammo30. Controller864/870 retain10/5-second reload waits;878/880 retain30/10
normal client/server close limits. At882–906 both exits0, protocol6, prediction
false, strict logs, current source/manifest, no owned descendants and the whole
deadline remain required. Motion itself does not measure displacement.

`desktop-alpha.yml:165` fixes living300. `verify_offline_export.py:610` starts
same live sidearm15/60 context, real depletion/reserve conservation and fresh
render/OCR agreement. Reload648–711 retains5-second start/15-second completion,
actual observed countdown allowance and ammo conservation. Next BUY716–725
retains160 seconds, same-actor/source/PID/trace/profile phase-capture barriers.
Second-LIVE and route731–761 share35 seconds. `native_settings_route.py:9`
fixes cover(-7.8,-21), stock start(-4.4,-21);39–80 require same live standard
attacker/round/deaths, SMG30/120, neutral actions, no release guard, focused/
unpaused controls, monotone clocks and corridor x[-8.5,-3.9], y[-.1,.1],
z[-21.75,-20.25]. Initial spawn89–94 is within.25m and speed<=.05m/s.

Living765–788 switches sidearm15 then SMG30/120 and persists changed sensitivity.
791–803 retains same live transaction, unchanged paused elapsed/health/weapon/
ammo/reserve/time_scale1. Explicit Escape resume807–840 and fresh rendering
share10 seconds.841–848 requires exact LEAVE MATCH inside FIELD MENU and menu
return<=30 seconds.864–887 requires disk equality after restart and runtime
initial_profile==saved in a new default stock process; living round1 BUY capture
shares30 seconds.

Focus891–1017 first acknowledges heldW+LMB<=10s; minimize must become unfocused/
paused<=10s. Restore/observed focus each<=10s, stays paused and mouse_mode0.
Explicit resume while physically held<=10s must remain neutral with same actor,
weapon/ammo/yaw/pitch. Inertia settles within one simulation second and two fresh
stable-position samples. Physical release<=10s clears waiting_for_input_release.
`native_focus_fence.py:76` keeps same live actor/round/deaths, living health,
unit speed, game/no scoreboard and monotone counters.123–167 requires freshW
within10 seconds with consumed nonzero move, advancing tick and displacement;
there is no life retry. Controller1019–1034 retains both clean ordinary exits,
unchanged incomplete-match profile, source/manifest, no descendants and whole
deadline.

Objectives each180 seconds (`desktop-alpha.yml:168/171`) preserve normal rules
buy15/round100/device35/plant3/defuse5/win7 (`verify_offline_match.py:37`).
Objectives use only declared layout/seed42; full-match is unseeded. Initial
689–698 requires fresh zero progress and ten living100HP actors.350–369 retains
out-of-rangeE .6s with no contribution, interruptedE progress.1<=p<.8 within3s,
then reset0/interactfalse<=2s with no state/contribution change.385–423 requires
live<=45s, legitimate smoke, ordinary bot plant for defuse, displacement>4.2m
plant/>2m defuse, plant site distance<3.8m and defuse device radius<=2.8m.

Objective427–488 requires final neutral state, uninterrupted native E, exactly
one contribution, hold start<=3s and watchdog9s plant/15s defuse.
`verify_hold_edges:58` requires exactly one completion notification and one held
consumedE edge through completion, original3/5 simulation seconds/ticks with
one60Hz-tick tolerance. Funds add ordinary300 capped9000, plus2700 win/1900 loss
where same transition occurs.494–512 requires same living planted-role
DEFEND THE DEVICE capture<=15s; genuine natural resolution<=50s with notice,
next BUY<=12s. Living-through-resolution is not required.703–726 retains clean
normal exit/reopen and unchanged default profile/settings; this fixture does not
qualify earned runtime reopen by itself.

Full-match1,800 seconds (`desktop-alpha.yml:174`) forbids --seed at103–104;
669–672 supplies scenario/seed flags only to objectives.514–551 requires stock
sidearm15/60, real move/aim<=3s/displacement>=.3m, actual depletion<=3s/reserve60,
R start<=3s/completion<=5s and conservation.554–602 requires natural stock7..12
rounds, sumscore==rounds, maxscore7 or round12, ten unique actors/teams5each/one
local, summary statistics match actual local row, won/draw match team/score,
every round recorded, natural halftime at7 changes local team, one completion
and zero duplicate/lost events.

Full-match604–615 computes XP=old+120+15*kills+50*objectives;
level=1+floor(sqrt(XP/150)); earned=100+75*won+150*freshdaily+250*levelgain.
Stored credits add exactly earned; matches/history each1 and cumulative stats
agree.620–638 retains real Escape summary dismissal<=8s, heldTab roster<=8s,
release<=5s and3-second no-duplicate dwell.703–748 requires exact saved/runtime
training equality, unchanged dwell/restart and distinct default reopened stock
BUY process with initial_profile==saved/completion_calls0; its incomplete match
must leave disk unchanged.750–766 retains source/manifest, strict logs, clean
ordinary exits/no descendants/deadline. `profile.gd:65` records local training;
`main.gd:1838` calls it only offline; guest loopback fixture earns no rewards.

Original PNGs require direct visual inspection. Hosted native data does not
qualify physical input feel, device performance or human judgment.
