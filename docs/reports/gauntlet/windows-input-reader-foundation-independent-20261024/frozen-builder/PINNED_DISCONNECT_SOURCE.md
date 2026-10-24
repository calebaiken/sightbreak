# Pinned SceneMultiplayer disconnect_peer callback order

Source-only research at Godot ed1daf0bf, not a native observation or final approval. No engine/API/process/helper/CI/test invocation ran. Network source-reader commands used CPU4.

## Answer

For explicit SceneMultiplayer.disconnect_peer(id), the local SceneMultiplayer peer_disconnected signal is deliberately suppressed. It is not synchronously delivered before return, and this path does not promise a later local callback. This is stronger than simply scheduling callback delivery later.

modules/multiplayer/scene_multiplayer.cpp:429-437 checks transport status, saves signal-blocking state, sets block_signals=true, calls _del_peer synchronously, restores the prior state, then calls the transport disconnect_peer.

_del_peer:397-426 returns for already absent IDs, otherwise updates replicator/cache, removes the ID from connected_peers at425, and attempts peer_disconnected emission at426. core/object/object.cpp:1179-1182 returns immediately when _block_signals is true, so this attempted emission invokes no listener and is not queued for later delivery.

SceneMultiplayer wires the transport peer_disconnected signal to _del_peer at scene_multiplayer.cpp:204-206. ENet disconnect_peer:271-289 calls peer_disconnect and explicitly notes removal during the next poll; the omitted p_force argument uses false. Later ENet polling may emit the transport-level signal (enet_multiplayer_peer.cpp:216-223), but _del_peer:402-403 returns for the already removed SceneMultiplayer ID. This conclusion assumes no intervening re-admission/replacement of that same ID.

_admit_peer inserts the SceneMultiplayer ID and updates cache/replicator before emitting peer_connected (scene_multiplayer.cpp:388-394). Given the parent's stated Match callback sequence, a failed PeerLifecycle.connected followed by explicit SceneMultiplayer.disconnect_peer therefore cannot rely on a synchronous or guaranteed later Match peer_disconnected callback to erase PeerLifecycle state before the unconditional observer hook. The game caller itself was supplied by the parent and was not independently re-read in this follow-up.

## Exact sources

| Source | URL | SHA-256 |
|---|---|---|
| SceneMultiplayer implementation | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/modules/multiplayer/scene_multiplayer.cpp | 71d62fede101f834482346f1066023dbc126596012fcf7d2cb7689480b254494 |
| SceneMultiplayer header | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/modules/multiplayer/scene_multiplayer.h | 4b8c589bf37ae9679e8f124c811b65890e5cde7d8fc779d8faba899cb4c90247 |
| ENet transport | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/modules/enet/enet_multiplayer_peer.cpp | 972c0f8aaeffc200683a16c8d2ca1364588b77c897eb30aa6f76e715c7ed97f1 |
| Object signal implementation | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/core/object/object.cpp | d16943098177c719820de78f664d4cde3a9c4f997f25ccfa6a1f9b7e18098bd4 |
