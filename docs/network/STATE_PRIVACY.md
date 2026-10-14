# Recipient state authorization

Protocol 3 replaces shared network snapshots with a recipient-specific projection. Both the reliable welcome and recurring snapshots use the server's peer-to-actor binding. The complete `_snapshot()` overload remains for authority/offline tests and must never be sent to a peer.

| Information | Authorization |
| --- | --- |
| IDs, names, teams, alive flag, kills/deaths/assists, objective contribution totals | Public roster/scoreboard; not removed when geometry is hidden |
| Own pose, health, match funds, ammunition, inventory, recoil and utility counts | Owning player |
| Teammate pose, health and match funds | Same team; inventories/ammunition remain private |
| Enemy pose, velocity, facing, equipped weapon and crouch | Only within the authorized viewpoint's conservative potentially visible region |
| Enemy health, funds, inventory, ammunition, recoil/reload timers and utility counts | Never replicated |
| Carried objective identity | Attack team only |
| Dropped objective position | Attack team or visible to permitted viewpoint |
| Planted objective | Public gameplay event |
| Interaction progress | Acting recipient only |
| Backend account IDs, ticket/reconnect maps, keys, wallet balances | Never included; match funds are distinct from earned account Credits |

## Visibility and deliberate limits

`SBStatePrivacy` checks static-world rays against body samples, including feet, head and a 0.40 m corner margin. It uses 360-degree relevance so turning does not wait for an update. A moving observer may inspect an additional unobstructed point up to 0.65 m ahead (100 ms candidate horizon). It does not extend either endpoint through cover. No remembered-visibility grace sends continuing hidden coordinates.

The margin intentionally discloses a narrow region before a perfect visual line opens. This trades some near-corner secrecy for competitive readability. Dynamic asset changes, very narrow apertures, extreme latency and complex geometry still require further fixtures. This is runtime conservative sampling, not a complete precomputed PVS or perfect wallhack prevention.

Smoke privacy uses only the central rendered ellipsoid, shrunk by 0.30 m, with an entry-facing threshold of 0.65. The bot's larger spherical concealment test cannot be used: native evidence shows it would erase visible players at the translucent rim. Growth, fade, outer lobes and uncertain edges remain disclosed. This protects the confidently opaque center; it **does not fully prevent modified clients seeing through all smoke**. Replica age prevents a newly relevant mature cloud from replaying its birth animation. No shader or asset has been changed.

Dead players inherit the first living teammate's bounded spectator camera. A team with no living observer receives no enemy positions. The camera and authority share collision-clamped placement. Team changes and reconnects recompute permissions; cached geometry, position and private state are revoked on the client. A modified client can always remember previously disclosed positions.

## Other channels

Hidden gunfire within the existing 65 m audio range uses an unattributed event with a one-meter-quantized origin and weapon sound. This necessarily allows sound-based inference; it does not reveal a persistent actor ID or hidden movement stream. Visible shots carry an audio fallback because events and snapshots can arrive in either order. Impacts require a visible world point. Utility trajectories require visibility; explosions are audible events; silent smoke is relevant through its conservative visible bounds. No utility owner ID is sent.

Public eliminations and objective completion remain public. Carrier recovery/drop notices are restricted to attackers. Snapshot decompression is bounded; an explicit schema rejects malformed dictionaries before any client mutation. The server retains every actor for hit detection, so filtering never changes authoritative damage.

## Evidence

`game/tests/state_privacy_test.gd`: permissions, wall concealment, visibility restoration, peeking, smoke core/rim transitions, objective privacy, team switch, dead observation, revocation and malformed packets. `network_probe.gd` inspects received dictionaries in two real ENet clients, including reconnect. Independent reviewer probes exposed and prompted corrections for low openings, relevance restoration, malformed crouch and smoke-rim invisibility. See the QA report for the current test results and limitations.
