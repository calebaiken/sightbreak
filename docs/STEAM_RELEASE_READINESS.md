# Steam release readiness

**Development preparation only — 2026-10-20.** No Steam application, SDK integration, upload, purchase, live service or store publication is included. No release or Steam Deck certification is claimed. Export/build verification and native gameplay evidence belong in [builds](builds.md) and the [desktop QA report](reports/DESKTOP_ALPHA_REPORT.md); export success alone does not establish playability.

## 1. Current development status

The 2026-10-21 [desktop playability continuation, draft PR #23](https://github.com/calebaiken/sightbreak/pull/23)
is stacked on desktop PR #22. Input-policy/objective-HUD corrections, native
Windows/Linux match and offline-training restart evidence, macOS diagnostics and
remaining failed gates are in the [playability report](reports/DESKTOP_PLAYABILITY_REPORT.md).
A scripted offline match cannot authorize online rewards, certify physical
performance or satisfy Steam release review. No Steam SDK/authentication or
publication work is added; the official-Steamworks retrieval limitation below
remains unchanged.

This milestone starts from PR #16 `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`, whose game/backend/server trees match frozen V2 `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`. Historical V2 results are not new desktop/V3 results. PR #17 has no verified V3 candidate; recovery, trade-read, input-freshness and prediction-diagnostic PRs #18–#21 retain separate integration gates. Newer bot/art inputs remain blocked by the recorded contract/visual findings.

Implemented foundations include native offline 5v5, authoritative LAN matches, settings/training persistence and a separate PostgreSQL account/economy backend. Protocol 6 remains the current runtime contract. Prediction stays disabled by default; live hit-history rewind stays disabled. Public matchmaking, secure public transport, production operations and commercial quality acceptance remain incomplete.

## 2. Documentation evidence and limits

Official Steamworks and Godot website retrieval was attempted on 2026-10-20. This host's policy denied the HTTPS tunnels with **403 Forbidden**; the available research connector required unavailable OAuth. **Current Steamworks documentation retrieval is UNVERIFIED.** Steamworks links below are official review targets, not a claim that their current contents were fetched. Before an actual upload, a release engineer must retrieve them through an authorized connection, record the retrieval date and reconcile the plan with the partner application's current configuration. No payment amount, waiting period or deadline is certified here.

Official Godot documentation **was retrieved from the godotengine GitHub repository**, frozen at [`0914a4d43fdce90c21a57374322559baacddf80c`](https://github.com/godotengine/godot-docs/tree/0914a4d43fdce90c21a57374322559baacddf80c). Preset capabilities were also checked against the pinned [Godot 4.7.2 macOS exporter](https://github.com/godotengine/godot/blob/4.7.2-stable/platform/macos/export/export_plugin.cpp) and [Windows exporter](https://github.com/godotengine/godot/blob/4.7.2-stable/platform/windows/export/export_plugin.cpp). Documentation master is guidance; the pinned engine and actual artifact inspection govern this build.

## 3. Native desktop requirements and build readiness

| Target | Required product payload | Required release evidence |
| --- | --- | --- |
| Windows 10/11 x86_64 | Native PE executable, game name/icon/version resources, complete Godot resources and notices | Native startup and rendered input flow, clean restart/persistence, permissions, window/focus/DPI tests; physical GPU/frame pacing remains separate |
| Linux x86_64 | Native ELF executable, embedded or accompanying PCK, executable permissions and notices | Native rendered gameplay, extracted-package launch, X11 and Wayland tests on supported sessions; distro/driver coverage |
| macOS Intel + Apple Silicon | Universal 2 `.app`, Info.plist, icon, resources, executable modes and signatures | Bundle inspection plus native execution on both architectures; Gatekeeper, notarization and controller/focus tests |

The pinned macOS exporter supports `binary_format/architecture="universal"`. Its default deployment floors are macOS 11.00 for x86_64 and 13.00 for arm64; do not advertise older support without checking the actual binary and testing. The macOS desktop app is distinct from the preserved unsigned **iOS Xcode project**. Windows/macOS execution is not established by this document.

Build only the chosen target using the [platform commands](builds.md). Freeze and commit runtime **and validation tooling** before qualification. Retain exact source SHA/game tree, physical shipped-source bytes, engine identity, per-file hashes/modes, export receipts and archive checksums. Verify the extracted distributable; exclude tests, caches, developer state, credentials and account journals. A changed/stale/incomplete artifact requires a new export, not a rewritten receipt. Signing/notarization and platform filesystems can change bytes; repeatable input provenance does not promise binary equality.

For macOS development, built-in ad-hoc signing is available without credentials. Distribution requires an owner's Developer ID certificate, signing identity and a secure signing process. The official Godot docs describe Xcode `codesign` plus `notarytool`, or `rcodesign`; disable the debugging entitlement, notarize and staple the ticket. Verify signatures and Gatekeeper acceptance on a Mac after download. Ad-hoc signing is not Developer ID/notarization. Keep credentials out of presets/repository/artifacts. ZIP preserves executable modes across a Windows export host; a raw `.app` copied from Windows may lose them. Every bundled native SDK library must contain the required architectures and be signed as part of the final bundle.

## 4. SteamPipe depots and launch configuration design

Use three OS-specific depots for the initial desktop release. Symbolic names are placeholders, **not assigned IDs**. Keep all compatible clients/server on the same qualified source/protocol family. Mobile exports never enter desktop depots.

| Symbolic depot | OS restriction | Install-relative launch entry |
| --- | --- | --- |
| `WINDOWS_DEPOT_ID` | Windows, 64-bit | `windows/SIGHTBREAK.exe` |
| `LINUX_DEPOT_ID` | Linux, 64-bit | `linux/sightbreak.x86_64` |
| `MACOS_DEPOT_ID` | macOS | `macos/SIGHTBREAK.app` (bundle launch; confirm partner UI representation) |

Create OS launch configurations restricted to the matching depot/platform, with the required working directory and no developer/test flags. Preserve the app bundle hierarchy on macOS and executable flags on Linux/macOS. Stage **verified package contents only**, rather than mapping the whole repository or the entire `builds/` directory. Do not include console-only harnesses, import/export logs, privileged server scripts, user data or Steam login material. Validate install/update/uninstall, launch from the Steam client and launch after a clean download on each OS.

A future local SteamPipe template may use `APP_ID`, `WINDOWS_DEPOT_ID`, `LINUX_DEPOT_ID`, `MACOS_DEPOT_ID`, a narrow `ContentRoot`, explicit `FileMapping` rules and a separate build-output directory. Render real IDs only after the owner has provisioned the application and reviewed the plan. Default builds must not automatically publish to the public branch. No upload-ready configuration or fabricated App ID is shipped here.

Official review targets: [SteamPipe uploading](https://partner.steamgames.com/doc/sdk/uploading), [depots](https://partner.steamgames.com/doc/store/application/depots), [platform launch configuration](https://partner.steamgames.com/doc/store/application/platforms).

## 5. Internal testing and beta workflow

1. Qualify a clean source commit locally/CI: package integrity, native startup, exported offline movement/aim/fire/reload/buy/objectives, UI at multiple resolutions, restart/persistence, protocol rejection and real peers. Record unavailable cases as UNVERIFIED. Preserve failed attempts.
2. Once separately authorized, upload the verified staged bytes to a private internal branch. Record Steam BuildID, depot manifest IDs, source commit, local checksums and signing receipts together. Restrict partner permissions; never store Steam credentials in the repository or artifacts.
3. Download through Steam on clean Windows/Linux/macOS systems and repeat the executable flow. Match client/server versions; do not use a branch switch to bypass protocol/admission checks. Test update rollback and save compatibility before inviting players.
4. Use a separate closed beta branch, controlled access and a feedback/support channel after internal gates pass. Review Steam Playtest as an optional distribution mechanism. Keep a previous qualified build available for rollback. A rollback does not erase failed evidence or authorize a destructive save/backend migration.
5. Promote to public only after explicit release approval, store/build review and all release gates. This milestone performs none of these distribution actions.

Review [build branches](https://partner.steamgames.com/doc/store/application/branches) and [Steam Playtest](https://partner.steamgames.com/doc/features/playtest).

## 6. SDK, authentication and networking architecture

The game currently needs no Steam SDK to run offline. Evaluate an SDK/GDExtension adapter separately, including license/provenance, pinned Godot compatibility, Windows/Linux x86_64 libraries, both macOS slices, lifecycle cleanup, overlay/focus behavior and signed bundle integration. The GodotSteam project is a third-party option, not an existing integration or a Valve/Godot acceptance guarantee. Keep offline startup functional when Steam is absent.

**Proposed account path, not implemented:** the client obtains a Steam authentication ticket for the intended backend audience; the SIGHTBREAK backend validates it with Valve through the appropriate trusted API and checks the expected App ID, returned identity, entitlement and applicable account restrictions. Use the authenticated response, never a submitted SteamID/profile/name or an unverified decoded ticket. Publisher/API credentials remain server-only. A native game-server ticket/session path is an alternative that requires successful authentication callbacks before binding; do not silently combine the two ticket types.

Link the verified external identity to a SIGHTBREAK account using explicit account-owner confirmation and fresh authentication for both sides. Enforce one external identity per intended account mapping, avoid account takeover through display names, and define unlink/relink/revocation and recovery rules. Store full Steam identifiers losslessly. Protect ticket/session exchange against replay and expire/revoke bindings as appropriate. Family-sharing/ownership policy requires an explicit product decision, not assumptions from a client flag.

After verification, retain the existing SIGHTBREAK flow: authenticated backend session → short-lived, one-use, server-scoped game ticket → trusted server inspection/consumption → reserved unique account/actor binding. Steam login cannot skip capacity/lifecycle rules. Steam ownership cannot authorize match rewards: the server still computes eligibility/activity/results and the backend commits idempotently. Transaction ownership, revisions, expected-price consent, reservations and immutable receipt identity stay tied to the SIGHTBREAK account. Offline training never becomes online value.

Steam identity does not encrypt the current ENet transport. Review SteamNetworkingSockets/Steam Datagram Relay as a separate transport project with authorization, privacy, reconnect, fairness, abuse and cross-platform regression gates. Local ENet interoperability is not production Internet security. No protocol change, prediction activation, live rewind or identity/economy replacement is authorized by this design.

Review [Steam authentication](https://partner.steamgames.com/doc/features/auth) and [Steam Datagram Relay](https://partner.steamgames.com/doc/features/multiplayer/steamdatagramrelay), then reconcile with the actual [SIGHTBREAK runtime](../game/scripts/gameplay/match.gd), [account service](../backend) and [network contracts](network.md). Older network documentation contains historical protocol references; current source is protocol 6.

## 7. Optional achievements, cloud saves and controller support

Achievements require trusted definitions and idempotent unlock conditions. Cosmetic rewards and Credits remain backend-authoritative; an achievement callback cannot mint inventory. Cloud saves may eventually synchronize approved settings/training files with schema/version/conflict handling. Exclude tokens, credentials, account journals, result outboxes and authoritative economy state; protect against stale restores reissuing transactions. Online inventory remains on the account service.

Godot already provides controller input; Steam Input can supply mappings or a later action-based integration. Verify menu navigation, prompts, deadzones, rumble, hot-plug, focus loss, text entry and gameplay without a mouse before claiming full controller support. Official Godot guidance documents SDL3 desktop input and `input_devices/joypads/ignore_joypad_on_unfocused_application`; physical controller coverage remains required. Do not permit simultaneous synthesized/controller input to duplicate gameplay actions.

Steam Deck work follows native Linux qualification: controller-only completion, readable 1280×800 UI, on-screen keyboard, suspend/resume, compatible dependencies, default settings and sustained device frame/thermal tests. Only Valve's relevant review process can establish Deck Verified status. Review [Steam Input](https://partner.steamgames.com/doc/features/steam_controller), [Deck compatibility](https://partner.steamgames.com/doc/steamdeck/compat), [Steam Cloud](https://partner.steamgames.com/doc/features/cloud) and [achievements](https://partner.steamgames.com/doc/features/achievements).

## 8. Store and onboarding prerequisites

The owner must complete Steamworks legal/entity, banking/tax and identity requirements and explicitly approve any Steam Direct credit purchase. No application credit is purchased here. Verify current timing/review requirements in [onboarding](https://partner.steamgames.com/doc/gettingstarted/onboarding).

Prepare original game-specific capsule/library assets, icons, supported-language descriptions, accurate feature/platform requirements, genuine current-build gameplay screenshots and a representative trailer. Do not use personal Crimson Archive branding as an assumed game identity. List development limitations honestly, disclose required account/online features and collect actual minimum/recommended hardware measurements. Review ratings/content disclosures, rights/licenses, accessibility and any applicable generated-content disclosures. Do not advertise absent multiplayer/controller/progression features. Complete Valve's store and build reviews before release: [store assets](https://partner.steamgames.com/doc/store/assets), [trailers](https://partner.steamgames.com/doc/store/trailer), [review process](https://partner.steamgames.com/doc/store/review_process).

## 9. Privacy, moderation, security and support

Before public beta: document account/Steam linking data, tickets, game telemetry, logs, retention/deletion/export and user consent; minimize personal data and redact bearer credentials. Publish owner-approved privacy/support/account-recovery policies. Establish reporting, blocking, moderation/ban appeals and incident response appropriate to online play. Validate backups/restores, result recovery, rate limits, abuse monitoring and production TLS/transport. Keep database and privileged server credentials isolated. No production security acceptance follows from a local process campaign.

Preserve earned Credits, cases, keys, item ownership, trading and marketplace rules. **No real-money cases, premium currency, cash-out, cryptocurrency, paid item transfers or Steam Community Market integration.** Selling the standalone game is a separate owner decision; no price or monetization model is assumed.

## 10. Release blockers and follow-up milestones

| Gate | Required closure |
| --- | --- |
| Current Steamworks requirements | Authorized retrieval/review of official docs and actual partner configuration; identity/legal/store setup remains outside this milestone |
| Desktop execution | Native Windows/Linux/macOS artifacts and gameplay evidence; both Mac architectures, extracted-package permission tests, focus/window/DPI and controller coverage |
| Integrity/regression | Clean exact-source artifacts, signing provenance, full affected gameplay/network/economy gates; qualify PRs #18–#21 independently before integration |
| Commercial game quality | Independent evidence for **8.5/10 in every applicable category**, human full matches/gunplay/listening/accessibility, corrected AI/art findings and measured hardware performance |
| Public online operation | Secure transport, admission/reward/transaction abuse review, real account-user matches, moderation/support/privacy/backup/incident readiness |
| macOS distribution | Developer ID signing, notarization, stapling, downloaded-app Gatekeeper tests; iOS signing/device work stays a separate preserved project |
| Steam/Deck | Actual partner build/store review and separately authorized beta; Steam Deck physical tests and Valve review, never inferred from a Linux export |

The next milestones are: (1) close native desktop playability and package evidence gaps; (2) integrate independently validated systems changes and resolve the highest-impact AI/art defects with real before/after captures; (3) prepare a separately authorized closed Steam beta after security, store and support gates. This document is a preparation package, not release acceptance.
