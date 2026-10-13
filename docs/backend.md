# Persistent economy service

The native game talks JSON/HTTP to an independent FastAPI service backed only by PostgreSQL. Local/offline progress has no import endpoint. New accounts start at zero Credits and with no items. All Credits are earned; no payment, redemption, withdrawal, premium-currency, or external-market integration exists.

## Reproducible local start

Requires Python 3.12+, uv, and Docker. From the repository root:

```sh
UV_CACHE_DIR=/workspace/.cache/uv UV_PROJECT_ENVIRONMENT="$PWD/.venv" uv sync --project backend --frozen
backend/dev-db.sh
.venv/bin/python backend/migrate.py
backend/dev-api.sh
```

The default URL is `http://127.0.0.1:8080`; `/health` verifies a PostgreSQL connection. OpenAPI documentation is available at `/docs`. The database container binds only `127.0.0.1:55432` and uses an explicitly public **local-development-only** password and named Docker volume. Stop with `docker stop sightbreak-postgres`; restart with the script. The PostgreSQL 17 image is pinned by verified digest in `backend/dev-db.sh`. The uv lockfile pins and hashes all Python dependencies. The `/workspace` cache location above can be replaced with a writable local path on other systems.

For an existing PostgreSQL deployment, set `DATABASE_URL` before migration and launch. Keep DB credentials and `SIGHTBREAK_SERVER_KEY` on the server, never inside the game or export. Non-PostgreSQL connection strings fail immediately. Do not deploy the development password or superuser role. Outside loopback, TLS termination and firewall restrictions are mandatory deployment work; this repository does not provide a production deployment.

Schema versions 1, 2 and 3 are applied explicitly by `backend/migrate.py`; `schema_migrations` records the applied revision. Its SQL migration adds immutable ledger/audit triggers and a partial uniqueness constraint for active listings. Migration 2 adds the game ticket table; migration 3 adds persistent cosmetic loadout slots. Neither recreates existing account/economy records. Future schema changes need forward versioned migrations, not automatic destructive recreation. API startup never mutates schema.

## Client contract

JSON requests reject extra fields. UUIDs are strings. Errors are non-2xx with `{ "detail": "message" }` or Pydantic validation details. Authenticated requests use `Authorization: Bearer TOKEN`. Tokens expire after 24 hours, are generated with a cryptographic RNG and stored only as SHA-256 hashes. Passwords use Argon2id. Logout immediately revokes the token. Store session tokens in device secure storage or memory; never log them.

| Method / route | Request / response |
| --- | --- |
| POST `/auth/register` | `{username,password,display_name}` → `{token,player_id,expires_at}`; password 12–128 characters; username 3–32 alphanumeric/underscore |
| POST `/auth/login` | `{username,password}` → same session response |
| POST `/auth/logout` | Auth; revokes current session and any unconsumed game tickets tied to it |
| POST `/auth/game-ticket` | Auth; `{server_id}` → 201 `{ticket,server_id,expires_at}`; opaque, single-use, 60-second join credential |
| POST `/server/tickets/consume` | Trusted server key; `{ticket,server_id}` → `{player_id,display_name}` |
| GET `/me` | `{player_id,display_name,xp,level,credits}` |
| GET `/inventory` | `{items:[Item]}` excluding consumed case/key instances |
| GET `/loadout` | `{slots:{rifle:Item}}`, or `{slots:{}}` when unequipped |
| PUT `/loadout` | `{slot:"rifle",item_id:UUID-or-null}` → current slots; null unequips |
| GET `/catalog` | `{definitions:[Definition],case_tables:{version,probabilities,key_definition_id},prices:{case,key},market_fee_basis_points}` |
| POST `/store/buy` | `{definition_id,idempotency_key}` → `{item,credits}`; only cases/keys are sold |
| POST `/cases/open` | `{case_id,key_id,idempotency_key}` → `{item,table_version,roll}`; committed before response/reveal |
| GET `/market` | Optional collection, rarity, max_price, weapon, finish query filters → `{listings:[{id,seller_id,price,item}]}`; up to 500 active rows |
| POST `/market/list` | `{item_id,price}` → `{id,seller_id,price,item}` |
| POST `/market/{id}/buy` | `{idempotency_key}` → `{item,credits,fee}` |
| POST `/market/{id}/cancel` | `{}` → `{state:"cancelled"}` |
| GET `/trades` | `{trades:[Trade]}` visible to the authenticated participant |
| POST `/trades` | `{partner_id}` → Trade |
| PUT `/trades/{id}/offer` | `{item_ids,revision}` → Trade with revision incremented and confirmations cleared |
| POST `/trades/{id}/confirm` | `{revision}` → Trade; settles only when both confirm same revision |
| POST `/trades/{id}/cancel` | `{}` → Trade, releases reservations |
| GET `/history` | Up to 100 recent ledger entries and match reward records |

`idempotency_key` must be a freshly generated UUID for a new operation. Retain it across retries. Retrying returns the original committed response; reuse for a different payload is rejected. The key is scoped to authenticated player and operation/target. Listing creation is safely protected against duplication by its item reservation, but its creation route is not a response-replay API.

Item: `{id,definition_id,rarity,pattern_seed,wear,variant,collection,kind,name,reserved,trade_eligible,marketplace_eligible,acquired_at}`. `wear` is 0–1. No cosmetic modifies combat statistics. Eligibility booleans describe current availability. Case/key definitions include a `price`. Skin definitions include `weapon` and `finish`. Catalog IDs include `key`, `obsidian_case`, `crimson_archive_case`, `spectral_circuit_case`, `blacksite_case`, and six skin definitions per collection. Only weapon skins, cases and keys are supplied in this initial catalog; other cosmetic categories remain roadmap work.

Trade: `{id,a,b,revision,offers:{player_id:[item_id]},offer_items:{player_id:[Item]},confirmations:[player_id],state}` where state is `open`, `completed` or `cancelled`. Both sides must inspect the same revision. Any offer edit clears both confirmations. A completed-confirm retry does not transfer again. Gifts with one empty side are allowed; wholly empty exchanges are rejected. Players can cancel their own open trade. Reservations remain until cancel/settlement; expiration UX is future work.

## Trusted match rewards

`POST /server/matches` requires `X-Server-Key` matching `SIGHTBREAK_SERVER_KEY` (minimum 32 characters). If the environment variable is absent, reward submission is disabled. It is never exposed to the client. Provision a cryptographically generated secret securely to the economy service and trusted dedicated game server only.

```json
{
  "match_id": "server-generated-UUID",
  "mode": "ranked_5v5",
  "started_at": "2026-10-13T12:00:00+00:00",
  "ended_at": "2026-10-13T12:20:00+00:00",
  "participants": [
    {"player_id":"authenticated-account-UUID","won":true,"active_seconds":1100,"objective_contributions":2,"abandoned":false}
  ]
}
```

The example participant is repeated with **ten distinct authenticated human account IDs**, exactly five winners. Matches require 300–7200 seconds, recent timestamps and no overlapping rewards for an account. Each participant must meet 75% activity and not abandon to earn; at most twelve matches pay each day. UUID replay returns the original rewards and changed results are rejected. The service calculates all Credit and XP amounts itself. A first eligible daily match and level changes award bonuses in the same transaction. Result response is `{match_id,rewards:[{player_id,credits,xp,won,eligible,started_at,ended_at}]}`.

**Integration boundary:** short-lived game tickets bind an authenticated economy account to a dedicated game connection. The server consumes the ticket over HTTP before admitting the player; the account bearer token never travels in ENet. Guest LAN/bot matches cannot create tradable value. This service trusts a provisioned dedicated server to attest activity, identities, objective counts, timestamps and the match UUID. It does not establish those gameplay facts from client claims. Production requires protected server enrollment/rotation, encrypted ticket transport and independent anti-farming telemetry. A compromised trusted server can invent eligible matches; duration/caps are defense layers, not a complete cheat defense.

## Transactions and threat boundaries

Every value mutation executes under one PostgreSQL transaction advisory lock. This deliberately serializes the initial economy service, including across multiple API workers, eliminating lock-order ambiguity for wallet/item/trade mutations. Failed validation or disconnect before commit rolls back the whole operation. After a successful commit, idempotency allows safe retrieval following a lost response. Unique item IDs, reservations, nonnegative-wallet constraints, a partial listing index, persisted operation responses and append-only ledger/audit triggers provide additional checks. Direct application writes that bypass this service are unsupported.

Cases use `secrets.randbelow(10000)` against integer weights summing to exactly 10000. Pattern/wear seeds are server-generated. Audit records store the rolled value, version, consumed items and awarded item. Probabilities do not depend on engagement/account state. This is an auditable CSPRNG draw, not a client-verifiable randomness commitment scheme.

The initial rate limiter stores per-minute source-IP buckets in PostgreSQL, ignores untrusted forwarded headers and survives process restarts. Auth: 15/minute; economic writes: 60/minute; trades: 20/minute plus a 30-second new-trade cooldown; server results: 120/minute. Shared NAT clients share limits. Production needs an edge limiter, request-size/time limits, carefully configured proxy identity, account-based limits and bucket/session cleanup. Global serialization limits throughput and needs measured replacement before high traffic. Reads and health checks are not currently rate limited.

## PostgreSQL adversarial tests

Use a disposable database whose name ends `_test`. The test harness refuses other names and truncates its test tables.

```sh
docker exec sightbreak-postgres createdb -U sightbreak sightbreak_test
DATABASE_URL=postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/sightbreak_test \
  PYTHONPATH=backend .venv/bin/pytest backend/tests -q
```

Fixtures mint fictional test values through internal database code; there is no HTTP fixture/grant endpoint. Tests cover concurrent competing buyers, double-spend, replay and changed replay payload, single case consumption, unowned items, duplicate trade items, market reservations, stale confirmations, atomic trade ownership changes, forged rewards, bot-size rejection, AFK rejection, database append-only rules, exception rollback, session expiry/revocation, password/token storage and persisted rate limits. They do not prove internet deployment safety or mobile integration. Latest actual results are recorded in the QA report.

## Backup, recovery and release work

Before changing schemas, take a consistent PostgreSQL dump and save it outside the live volume with controlled access. Example local development backup and separate restore rehearsal:

```sh
docker exec sightbreak-postgres pg_dump -U sightbreak -Fc sightbreak > /tmp/sightbreak-backup.dump
docker exec sightbreak-postgres createdb -U sightbreak sightbreak_restore
cat /tmp/sightbreak-backup.dump | docker exec -i sightbreak-postgres pg_restore -U sightbreak -d sightbreak_restore
```

Reconcile each wallet to the sum of its ledger, verify one owner per unconsumed item and valid reservations, then exercise reads on the restored database before switching traffic. Establish encrypted off-host backups, retention, point-in-time recovery and tested RPO/RTO before production. This local sample does not establish a production backup service.

Unresolved release requirements include restricted application DB roles (no DDL/TRUNCATE, no update/delete access to immutable history), TLS/secret rotation, authentication recovery/abuse controls, independent penetration review, full authenticated 10-human reward-flow verification, load/concurrency benchmarking at scale, rate-limit cleanup, pagination beyond initial limits, challenge and achievement definitions/rewards, career aggregates, additional cosmetic loadout categories and account moderation. Do not call this a production-ready economy or mark these untested controls as passed.

Validation performed in this cloud workspace: 18 PostgreSQL integration tests passed; live `/health` returned PostgreSQL ready. A local dump/restore rehearsal into a separate database restored schema version 1 with zero wallet/ledger discrepancies; the source had no live player economy data, so this does not validate recovery at production scale.


## Account-bound local dedicated server

`backend/dev-api.sh` creates a random local server key only when no external `SIGHTBREAK_SERVER_KEY` is supplied. It stores that development key in ignored `.local/secrets/server.key` with permissions 0600 (directory 0700), loads it into the API process environment and never prints it. `SIGHTBREAK_SERVER_ID` defaults to `local-relay`. The dedicated server must load the same key externally. `scripts/serve-account-match.sh` provides the corresponding account-required game launch. The key is never a game project asset or client setting. Preserve external environment values when deploying under a real secret manager.

A signed-in native client requests `/auth/game-ticket` over its economy HTTPRequest connection, then sends only the returned short-lived ticket in the ENet join request. `/server/tickets/consume` validates the trusted-server credential, exact server identity, ticket expiry, single-use status, parent session validity and account state in one transaction. Only a successful response supplies the trusted player ID to the game. Ticket plaintext is not stored; the database stores its SHA-256 hash. Logout or parent-session expiry before consumption invalidates outstanding tickets. Concurrent consumes admit at most one connection. A consumed ticket is not reusable after disconnect; reconnect needs a fresh ticket.

The development secret authorizes just `SIGHTBREAK_SERVER_ID`; a production multi-server registry, per-server credential rotation and TLS remain release requirements. Local loopback HTTP is for development only. Remote bearer/ticket HTTP requests must use HTTPS with verification enabled; ENet itself is not an authenticated encrypted transport and requires a secure transport strategy before internet-ranked play. Revoking an economy session after a ticket has already been consumed does not automatically eject its active game peer; cross-service session revocation is future work.

Latest ticket validation: 23 PostgreSQL tests passed, including concurrent consume, replay, mismatched server credential/ticket scopes, missing/wrong server key, expiry, session logout/expiry and inactive accounts. Migration 2 was applied to the existing local development database without resetting player records. Full gameplay integration validation is recorded separately by the game/network tests.


## Persistent rifle cosmetic loadout

`PUT /loadout` accepts an owned, unconsumed, unreserved weapon skin whose catalog weapon matches the rifle slot. Non-owned items, cases/keys, reserved items and unsupported slots are rejected. An explicit null item ID unequips. Marketplace settlement and completed trades delete the original owner's equipped record in the same transaction as ownership transfer. Receiving a skin does not automatically equip it. Reads additionally filter ownership/consumption so stale records cannot authorize using another player's cosmetic. A skin already equipped may remain visible while listed/reserved until ownership transfers; reserving an item does not change gameplay statistics.

The native client applies the stored pattern/finish metadata to its visual rifle presentation. Cosmetic records never modify damage, recoil, movement or any other competitive statistic. The initial catalog contains rifle skins only; broader item types and multiplayer replication of visual loadouts remain future work.

Schema migration 3 was applied additively to the existing database and rerun successfully. Latest backend result: **27 PostgreSQL integration tests passed**, including compatibility/ownership equip validation, explicit unequip, reservation rejection, unsupported slots, market/trade automatic unequip and defensive stale-owner filtering.

## Isolated Godot-to-economy reward bridge validation

`backend/bridge_fixture.py` prepares the dedicated `sightbreak_bridge_test` PostgreSQL database and ten fictional zero-value accounts. It writes a random service key and account IDs to ignored `.local/bridge-fixture.json` with mode 0600 and never prints credentials. It cannot target the live development database. Start the isolated API with:

```sh
backend/dev-db.sh
.venv/bin/python backend/bridge_fixture.py --serve
```

This binds port 8081, leaving the normal API on 8080. Game adapter validation can submit synthetic authoritative results only to this isolated fixture. Stop the isolated API before `--reset --serve`; reset refuses while port 8081 is listening and only truncates the explicitly named fixture database. Repeated submissions of a successful match must use identical payloads/UUIDs to verify replay; a new overlapping fixture match is deliberately rejected. The fixture is development test data, not a reward-grant endpoint or live wallet seed.
