# Dedicated LAN sessions

SIGHTBREAK runs a native Godot ENet UDP server with ten actor slots. Guest LAN sessions are unranked practice and cannot issue online rewards. Optional account servers consume a one-use account ticket and report qualifying server results to the economy backend. Offline progression never transfers into online inventory.

Start a dedicated server from the repository root:

```sh
./scripts/godot.sh --headless -- --server --port=27020
```

On another machine, launch the game and use the multiplayer screen to join the server's LAN address and UDP port 27020. Permit that UDP port in the host's firewall. The default address is loopback `127.0.0.1` for same-machine testing. No cloud hosting is necessary. Main scene server and client both place the match at `/root/Sightbreak/Match` so RPC paths agree.

## Simulation authority

Only the server advances movement, collision, ammunition, reloads, fire cadence, hit registration, grenade damage, objective progress, purchases, scores and round timers. A peer is assigned one actor ID by the server. Clients send movement and aiming intent at 30 Hz; they never send trusted positions, damage or balances. Input validation rejects non-finite and malformed vectors, clamps movement and pitch, and limits command frequency. The actor separately enforces inventory ownership, ammunition and fire intervals. Input older than 300 ms expires to neutral controls. Purchases are limited to the preparation phase and one request every 250 ms.

The 60 Hz simulation sends compressed snapshots at 20 Hz. Remote actors move 90 % of the way toward each snapshot when it arrives and hold position between snapshots; there is no timestamped interpolation buffer yet (CLAUDE_AUDIT_0.3 M-6). Local view rotation updates immediately; local movement snaps to the server position without movement prediction. Cosmetic shot effects and grenade/smoke replicas do not apply client damage. Reliable messages carry joining, notices and purchases. Input, snapshots and shot effects use separate ENet channels. Rounds have a 15-second equipment phase, 100-second live clock, three-second plant, five-second defuse and 35-second device timer. First to seven wins; a 6–6 match draws. Squads switch sides after six rounds.

Empty slots run server bots. A disconnected player's bot inherits the actor state, preserving the ongoing round. A cryptographically generated reconnect bearer token can reclaim the actor for 60 seconds; successful reconnection rotates it. The current client retains the token in memory and attempts one automatic reconnection after a dropped established connection. Restarting the app loses it. New joins cannot steal a reserved slot. A full server rejects additional allocation. An account player can also reclaim their disconnected slot using a fresh authenticated one-use ticket; expired reservations release stale account bindings.

## Version handshake

Godot routes RPCs by method index, so a client and server whose RPC methods differ cannot exchange gameplay messages. Before this check existed, they connected and then sat in "joining" forever. Every connection now passes a version handshake in SceneMultiplayer's authentication stage, before any gameplay RPC:

- The client sends a bounded JSON hello carrying `TacticalMatch.PROTOCOL_VERSION`. The server admits it only on an exact match. Only after admission does the client send `_join_rpc`, so a rejected peer never consumes a join ticket or takes a slot.
- **Mismatched protocol.** The server replies with the reason and drops the peer about 0.5 s later. The client shows "Version mismatch: …", stops, and does not retry.
- **No hello within 5 s.** This covers 0.3.0 and earlier clients, which have no handshake, and non-SIGHTBREAK traffic. The server drops the peer at the authentication timeout. Unmodified 0.3.0 clients cannot display the new message and fall back to their own reconnect loop.
- **Server never answers within 5 s.** The client reports that the server probably runs an older release and stops.
- **Bounded waits.** Connecting, authenticating and joining together are limited to 20 s on the client.

Bump `PROTOCOL_VERSION` whenever an RPC method is added, removed, renamed or changes its arguments, or when snapshot meaning changes. Protocol 2 is the first versioned protocol; 0.3.0 had none. `scripts/test_protocol_compat.sh` runs real dedicated-server and client processes for 0.3.0, this build and a protocol-bumped copy of it, in every pairing, and writes a matrix.

## Optional account sessions

Start the local PostgreSQL/API services first, then use `scripts/serve-account-match.sh` (or set the privileged `SIGHTBREAK_SERVER_KEY` only in the dedicated server process and run `./scripts/godot.sh --headless -- --server --require-accounts --server-id=local-relay --economy-url=http://127.0.0.1:8080`). The backend must use the same key and server scope. Never put this key in the exported game or a client setting. The helper reads the ignored, permission-restricted development secret file.

The logged-in client requests `POST /auth/game-ticket` with `{server_id}`. Only its short-lived scoped ticket reaches ENet. The dedicated server consumes it at `POST /server/tickets/consume` using its private server credential, then binds the returned account ID and display name to one actor. Accounts cannot occupy two simultaneous slots. The server waits for ten distinct authenticated humans before round one; guest joins are rejected. A disconnect after match start permanently disqualifies that match from online rewards even if the player reconnects.

Qualifying results require a completed decisive match, all ten original humans, at least 300 seconds and at least 75% observed activity per player. Validated movement/aim changes, actual shots and objective interaction maintain a ten-second activity window. These are conservative farming checks, not proof of human identity or resistance to automation. The server posts five winners and five losers, activity totals and objective contributions to the transactional `/server/matches` endpoint. The backend rechecks eligibility and commits idempotently by UUID. Client statistics and offline saves cannot call the privileged result endpoint. Ties and matches involving bots are ineligible.

The server HTTP bridge permits plaintext only to exact loopback hosts, requires HTTPS elsewhere, verifies TLS normally, rejects URL credentials/query/fragment ambiguity, disables redirects and caps response size. Account tickets are still sent over unencrypted ENet on the LAN; production Internet play needs encrypted authenticated transport before release. A successful result reports `committed`; an HTTP failure reports `submission_failed` with the match ID for server review. Transport failures and HTTP 5xx responses receive up to three bounded attempts with the identical UUID and payload. A durable retry outbox/restart recovery is not yet implemented. After a completed match, new joins are rejected until every player leaves; the server then resets to a fresh guest match or an account waiting lobby. An in-flight result submission completes before that reset.

Run the integration probe with the local API already running:

```sh
python3 scripts/test_account_network.py
```

It creates one fictional account and tests real Godot → HTTP → PostgreSQL ticket consumption, guest rejection, an incompatible-protocol client presenting the ticket first (rejected, after which the same ticket still admits the real client to slot 1), authoritative names, waiting for the roster, replay rejection and account reclaim with a new ticket. It does not award rewards or claim that ten humans completed a full match. The deterministic match tests separately cover reward eligibility policy, result metadata, strict URL validation and redirect suppression.

## Automated checks

```sh
./scripts/godot.sh --headless --editor --import --quit
./scripts/godot.sh --headless --script res://tests/match_test.gd
./scripts/godot.sh --headless --script res://tests/bot_match_test.gd
./scripts/test_network.sh
```

The network test creates a real ENet server process and two client processes on UDP 27991. Both clients must receive ten actors, move through authoritative snapshots, ignore a supplied teleport field, disconnect and reclaim their original slots. This tests loopback transport and state; it is not a WAN latency or production security certification. Match tests cover holding/releasing objective actions, plant/defuse/detonation, elimination, halftime, match completion, and invalid/flooded input. The bot smoke test runs a real physics round at accelerated time and requires combat and a completed objective or round.

## Boundaries and unfinished production work

ENet guest transport is not an authenticated or encrypted Internet matchmaking service. Reconnect tokens are bearer secrets over that transport: use trusted development LANs. Account binding and a trusted result adapter are implemented behind the optional account server mode. There is no remote attestation, matchmaking, persistent ban service, replay archive, or anti-cheat guarantee. ENet/RPC protections and application input checks are foundations only; an Internet deployment also needs connection and packet quotas, encrypted game transport, abuse monitoring and independent review.

No lag-compensated rewind is implemented. Movement prediction with replay/reconciliation, timestamped snapshot buffering, adverse-network simulation and bounded server rewind remain release work. At present competitive feel is aimed at local and LAN sessions. Snapshot compression helps fit ordinary ten-actor snapshots below the MTU, but many simultaneous utilities can increase payload size; bandwidth and packet-loss profiling under ten mobile clients is unverified. Networked effects show shot and utility state; bullet impact visuals are currently local to the authority. Slot retention is in-memory and does not survive a server restart. Server failure and a failed reconnect return a clear connection status without pretending the match continued.

## Isolated reward adapter and HTTP failure fixtures

The settlement adapter is tested using ten fictional account IDs and synthetic match time/score/activity state, explicitly separate from real match play. Start a **fresh** isolated service in another terminal with `.venv/bin/python backend/bridge_fixture.py --reset --serve` after stopping any existing fixture listener on 8081, then run:

```sh
.venv/bin/python scripts/test_reward_bridge.py
python3 scripts/test_bridge_transport.py
```

The first sends the actual `TacticalMatch._ranked_payload()` through Godot's server bridge twice. It checks the actual PostgreSQL `sightbreak_bridge_test` wallets, ten unique ledger grants and ten match records, proving replay does not mint again. It only touches the explicitly named fixture database; reset it before another fresh grant run. Credentials reside in a local ignored mode-0600 fixture file and never appear in test output. The second runs a local HTTP fault server: two 503 responses followed by success must produce exactly three identical payloads; a redirect must produce one request without credential forwarding. Neither fixture establishes human activity, WAN security or a production anti-cheat score.
