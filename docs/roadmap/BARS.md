# Quality bars

Registry of references used by the gauntlet loop. A bar must be **named**, **fetchable** from the working container and **comparable** side by side. Record every fetch attempt. Never commit third-party game footage or screenshots; keep URL, date and SHA-256 here instead.

## Fetchability, checked 2026-10-21

The container reaches GitHub (`github.com`, `raw.githubusercontent.com`) through an allow-listed proxy. These hosts were denied (`CONNECT` answered 403):

| Host | Needed for |
| --- | --- |
| `store.steampowered.com` | CS2 store media list (trailers, screenshots) |
| `cdn.akamai.steamstatic.com`, `shared.akamai.steamstatic.com`, `cdn.cloudflare.steamstatic.com`, `steamcdn-a.akamaihd.net` | CS2 screenshots and trailer files |
| `www.youtube.com`, `i.ytimg.com` | Gameplay footage |
| `counter-strike.net`, `www.counter-strike.net` | Official CS2 pages |
| `upload.wikimedia.org` | Reference images |
| `partner.steamgames.com` | Steamworks documentation (see STEAM_RELEASE_READINESS.md) |

To unblock, the owner edits the cloud environment's network access (environment menu in the session title bar, then Edit) and allows these hosts. Docs: https://code.claude.com/docs/en/cloud-environments#network-access.

## Bars

| ID | Bar | Piece it judges | Status | Notes |
| --- | --- | --- | --- | --- |
| B1 | Counter-Strike 2 official trailer and store screenshots, first-person rifle fire and reload | Viewmodel pose, reload readability, muzzle effects, HUD clarity | BLOCKED EXTERNALLY | Hosts above denied. Earlier Claude sessions hit the same block (`tools/art/REFERENCES.md`). |
| B2 | Counter-Strike 2 published weapon data (cycle time, magazine, reload time, recoil/spread parameters) | Plausible ranges for fire rate, magazine and reload duration | NOT USABLE YET | 2026-10-21: `raw.githubusercontent.com` serves SteamDatabase `GameTracking-CS2` (`game/csgo/pak01_dir/scripts/items/items_game.txt`, 8,117,698 bytes, SHA-256 `f427df5f23edcd80e9ed16fa65519d3f2ea33166ff02574069b4a8bfa596de39`). It defines attribute names (`cycletime`, `spread`, `recoil_magnitude`) but a grep finds no per-weapon values. Numbers likely live in compiled weapon data elsewhere in that repo; the `github.com` web and API routes for the repo returned 403, so the tree cannot be listed. Use only as a plausibility range if values are found, never as balance values to copy. |
| B3 | The previous verified SIGHTBREAK build (`codex/desktop-playability-p1` at `db3981e`) | Any change that claims improvement | FETCHABLE | Proves improvement and catches regressions. Does not prove parity with a shipped title. Say so in the report. |
| B4 | Accessibility rules: WCAG 2.2 contrast (4.5:1 body text, 3:1 large text and UI components) | HUD and menu text and controls | FETCHABLE (computed locally) | Measure from captured pixels; no network needed. |
| B5 | Measured frame time and input latency on the same fixed scene | Performance claims | FETCHABLE | Software rendering only. Relative numbers; never device FPS. |

Add rows as bars are proven fetchable. Change a status only after a real fetch attempt, and keep the date.
