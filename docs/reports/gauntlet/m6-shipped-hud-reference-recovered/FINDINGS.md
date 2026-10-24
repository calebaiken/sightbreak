# Retrieved touch and HUD references, 2026-10-23

Fresh official media is available for touch-control visibility and FPS HUD
placement. I inspected two original images and three decoded clip frames.
The useful touch material comes from official Luanti release announcements;
the FPS HUD comes from the official AssaultCube gallery. These support the
specific observations below. They do not qualify CS2 parity or declare an
accessibility pass.

This is new evidence. The interrupted session's unpublished Red Eclipse report
and images were not recovered, and none of its observations are reused here.
All third-party pixels remain outside Git in
`/workspace/reference-cache/recovered-20261023`. The repository contains only
provenance, findings and comparison criteria. Exact original URLs, Git blobs,
retrieval times, SHA-256 hashes and frame commands are in
[PROVENANCE.json](PROVENANCE.json).

## Sources actually viewed

| Source and official provenance | Original pixels | Useful observation | Limit |
| --- | --- | --- | --- |
| [Luanti 5.15 Android image in its release announcement](https://github.com/luanti-org/blog/blob/96b71ec0fe93b5e7566de535f5fc8206b201be3e/_posts/2026-01-24-5.15.0-released.md) | `luanti-5.15-android-shadows.jpg`, 2340 × 1080 | Translucent outlined joystick at lower left; large white menu/search/action icons at right; Aux1 label; health above a separate bottom hotbar. The same frame contains bright sky, dark foliage and grass. | The caption identifies Android. It does not identify the exact capture binary, game package, device or physical size. Luanti is a released game platform; this is release-announcement media, not a verified tactical-FPS capture. |
| [Luanti 5.12 touchscreen clip in its release announcement](https://github.com/luanti-org/blog/blob/96b71ec0fe93b5e7566de535f5fc8206b201be3e/_posts/2025-05-24-5.12.0-released.md) | `luanti-5.12-touchscreen-dig-place.webm`, 938 × 420, 52.625 s; inspected frames at 1, 25 and 45 s | At 25 s, white outlined controls fade into bright snow. At 45 s, right-side action labels and outlined lower buttons stand out more against brown ground. This supplies a concrete adverse-underlay example. | The 1 s frame is a settings menu and is excluded from gameplay comparison. The clip is lossy and low resolution. No contrast ratio, interaction accuracy or motion quality is inferred from these stills. |
| [AssaultCube official media page](https://github.com/assaultcube/assaultcube.github.io/blob/a011672c06a2b6e1acd5739b0e4f0cbb91866a1e/htdocs/media.html) | `assaultcube-official-mines-ctf-smg.jpg`, 640 × 400 | Actual first-person firing scene: health/name at bottom left, ammo at lower center, minimap top right, small status pictograms on dark plates. Most of the central aiming region remains free of HUD. | It has no touch controls. Exact capture version/device is unspecified. Its small, older gallery format cannot establish current typography quality, touch reach or tactical-FPS parity. |

Original assets are pinned to Luanti blog commit
`96b71ec0fe93b5e7566de535f5fc8206b201be3e` and AssaultCube website commit
`a011672c06a2b6e1acd5739b0e4f0cbb91866a1e`. Their bytes match the Git blob IDs
returned by the official repositories. The three downloaded assets total
2,763,602 bytes. No thumbnail, generated reference or reconstructed image is
presented as an original screenshot.

## How the M6 critic can use them

Use the Luanti Android image and gameplay frames to inspect whether SIGHTBREAK's
controls remain distinct over bright, dark and busy scenery, whether the
joystick silhouette remains visible, and whether edge controls avoid the
central aiming region and existing HUD. The snow frame is a useful failure
example; copying its white-on-bright treatment would preserve that weakness.
The AssaultCube image can inform separation of health, ammo, radar and the aim
region. Its arrangement and artwork are not a template to copy.

No SIGHTBREAK native candidate was opened in this research lane, so there is no
actual side-by-side winner. The references have different aspect ratios,
resolutions, scenes and control sets. Whole-screen rescaling cannot establish
equal physical readability. A later critic should name the limited question
being compared and keep original pixels and source attribution available.
It must not convert these observations into a claim of CS2, touch, gameplay or
human usability parity.

The strongest pass/fail bar remains the project's existing WCAG criteria and a
matched SIGHTBREAK native baseline: text contrast at least 4.5:1, large text and
non-text UI components at least 3:1, measured against the actual composited
backdrop. Use the same source-bound frame, viewport, text scale, control state
and gameplay conditions for baseline/candidate comparison. Preserve objective
prompts, HUD information and control bounds. Reference screenshots alone cannot
prove a contrast ratio, touch target size, thumb reach or input correctness.

## Access boundary

Current `/etc/codex/network-policy.json` is restricted. The current supported
environment status reports that policy enforced and observations current.
GitHub, its API and raw file host are allowed. The named CS2 media destinations,
including Steam store/static hosts, YouTube thumbnails/video and
counter-strike.net, are absent from the allowlist. No request was sent to those
denied destinations, and no redirect was followed. The earlier recorded 403s
remain historical evidence; this report does not claim a new 403 measurement.
No official CS2 reference asset was obtained, so G18 remains blocked.

All asset downloads preserved the inherited proxy and TLS verification, refused
redirects and completed with HTTP 200. Still frames were decoded from the
already downloaded official clip; there was no recording, OCR, engine, export,
service or native gameplay run. A mistaken `htdocs/screenshots.html` lookup
returned 404 before the inspected tree identified the real `htdocs/media.html`
page. SuperTuxKart and Red Eclipse metadata were also examined, but no pixels
from them were downloaded or judged.

The remaining gap is a genuinely comparable shipped tactical-FPS touch/HUD
reference and source-bound SIGHTBREAK candidate output. These contextual
references improve the review questions; they do not close that gate.
