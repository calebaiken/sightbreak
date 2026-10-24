# Additional normal game-lifetime source inspection

Root requested this read-only inspection while its sole admitted verbose Windows
run 40083894472 is active. This addendum does not inspect or reconstruct that run.
It changes only this task's existing report folder. No production changes,
tests, native processes, export, CI, waits/drains, or Mac review were attempted.

Game tree is byte-identical at c3241514, frozen diagnostic source 7101350e and
current handoff HEAD a936ae96: Git game-tree identity
`bca627d5dc8e4482b63e263020a6382f2d36f33c`. The accompanying identity JSON binds
22 inspected source files to their original bytes. All shell work used CPU4.
A search used a guessed bot_controller.gd path and returned exit2; rg --files
identified the actual bot_ai.gd. No missing file was treated as inspected.

## Supported ownership facts

Main owns OfflineProfile and the optional SBOfflineDiagnostics through fields
(main.gd34–35,107). OfflineProfile extends RefCounted and stores only a duplicated
profile dictionary (profile.gd1–17). Match is a Node3D (match.gd1–2), parented to
Main at main.gd837. It owns eight explicitly instantiated RefCounted helper
objects through fields: input gate55, privacy56, snapshot buffer57, hit history59,
input stream61, prediction62, reconnect policy75 and peer lifecycle90. Its RNG104
is another RefCounted engine object. These field instances exist even when the
selected mode is ordinary offline; their existence identifies no exit leak.

The inspected helper state has no explicit retained Match/actor member:
input_gate.gd5–7 stores dictionaries/counter, reconnect_policy.gd7–9 numeric
state, peer_lifecycle.gd8–15 numeric/Boolean peer records, and state_privacy.gd12
only a ray counter. Function arguments in state_privacy.gd34–51 are transient
parameters. snapshot_buffer.gd37–47 stores IDs and vector/numeric poses;
hit_history.gd29–37 copies transform/shape/team/liveness values;
input_stream.gd49–65 constructs validated primitive/vector command records;
movement_prediction.gd32–40 appends command dictionaries and positions. These
source schemas support no explicit helper-to-Match reference cycle.

Bot state initialization copies actor.position, never the actor reference
(bot_ai.gd113–135); team state141–157 contains scalar dictionaries; target updates
at573–575 store actor ID, position and elapsed time. Match/actor variables passed
through perception methods remain local in the inspected paths. No retained
bot-state actor object or helper self-reference was found.

The procedural SBWeaponModel is RefCounted (weapon_model.gd1–2). Its _pack method
creates a local model and plain Node3D root at153–155, builds/packs the hierarchy,
and pack_children explicitly frees that source root at183–188. build instantiates
a cached PackedScene, reparents its children into the supplied parent, then frees
the emptied temporary root at105–119. Actor packed bodies use the same temporary
root/reparent/free pattern at actor.gd360–369. _authored_nodes saves meshes and
transforms rather than source Nodes and frees the source scene at
weapon_model.gd580–594. A material/mesh retained by a PackedScene is a source
ownership path, not evidence of a circular owner or native exit leak.

Static resource caches remain visible in actor195–196/350,
weapon_model93/96/508/544, viewmodel_shading194–199, reload_audio24,
utility16–18, cosmetic_material87–88 and design_tokens52. Material values point
to shaders/textures (for example viewmodel_shading232–236), and heading_font
points to ThemeDB.fallback_font (design_tokens100–106). No explicit reverse
reference from those resource objects to their owning script/helper is set by
the inspected code. Cache existence or cache object count does not identify the
three previously reported leaks. LEAVE does not clear those static caches
(main.gd1855–1867), so established caches also exist at the initial client's later
menu shutdown; cache presence alone does not explain the distinction.

CombatEffects is parented to its world when created (combat_effects.gd12–18).
Its MultiMesh pools store mesh Resources and scalar slot dictionaries, with the
MultiMeshInstance parented to the pool node at67–91. Actor shot/hurt/reload
players are children (actor.gd233–245) and are stopped during actor tree exit
(566–572). These ordinary scene ownership paths are not leak attribution.

UI control signals hold callbacks while their controls exist. For example,
setting_slider captures a format Callable and a value Label at main.gd680–690;
clear_ui removes/queues its child trees at239–243. This is a callback lifetime
path; inspected source does not show that Callable capturing itself. No pending
ordinary offline await was found in the earlier scan.

OfflineDiagnostics has primitive dictionaries/fields (offline_diagnostics.gd10–25)
and signal closures capture observer/game at258–261. Its _snapshot result is
scalar observation data: the rejected self-referential snapshot hypothesis is
excluded. The signal connections identify callbacks attached while Match/actor
Nodes live. They do not establish an ownership cycle or a leaked RefCounted
instance. No new instrumentation is proposed.

## Living-match close versus LEAVE/menu

The existing initial producer invokes LEAVE and waits for menu before close;
reopened close follows the fresh focus-test movement inside the living Match.
Base controller lines845–850 and1011–1022 show that difference. LEAVE calls
OfflineDiagnostics.finish, detaches Match, queues it for deletion, clears the
Main match field, then shows menu (main.gd1855–1867). Offline Match tree exit
contains no helper-specific reset; its only explicit _exit_tree work is for
non-offline multiplayer mode (match.gd176–179). Thus LEAVE offers an earlier
scene/resource release point. That is a lifetime timing distinction only;
it neither proves deferred deletion is faulty nor supports adding a delay.

## Findings held for actual object identity

One conditional source lead is bidirectional script use: actor.gd14 preloads
Utility, while utility.gd303 calls SBActor._synthesize_sound. This establishes
usage in both directions, not a compiled-resource ownership cycle. It warrants
further inspection only if actual leaked identities implicate script resources.
No API/lifetime change is supported by this relationship alone.

No explicit retaining cycle was established in this bounded inspection. Remaining
possibilities include ordinary scene destruction, script/static resource teardown,
callback release, or an engine-owned object lifetime, but source alone does not
rank or select any of them. Native verbose output can narrow native class and
instance identity; a generic RefCounted class alone may still not identify which
script helper owns it. Native IDs/refcounts provide no allocation stack or
retaining-owner chain. The prior three-object count cannot assign ownership.

Wait for the admitted run's original verbose output and independent actual review.
Any later targeted investigation must start from those observed identities and
retain the unchanged normal-close benchmark. This addendum authorizes no fix,
new native run, retry, teardown workaround or acceptance change.
