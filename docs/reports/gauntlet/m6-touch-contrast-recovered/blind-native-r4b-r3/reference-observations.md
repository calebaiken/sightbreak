# Shipped reference observations

All five listed images were opened using view_image. These are bounded touch/HUD references. CS2 hosts are inaccessible, so these observations establish neither CS2 parity nor gunfeel.

## Luanti 5.15 Android shadows

Local image: /workspace/reference-cache/recovered-20261023/luanti-5.15-android-shadows.jpg

Source: https://raw.githubusercontent.com/luanti-org/blog/96b71ec0fe93b5e7566de535f5fc8206b201be3e/static/blog/5.15.0/android_shadows.jpg

Retrieval metadata reports HTTP 200, 998507 bytes, SHA-256 40fe4f7831c53cbee7fa28c95d7805f18271a718751e2be77ffb39b737d21c04, matching expected Git blob e49a3f03fa2108ae8487c98d704dd5eed2781eac, fetched 2026-10-23 05:16:32 UTC.

At its wide native landscape scale, a large left circular movement guide, a vertical right-side menu/search/action stack, bottom-right shape controls, and a centered bottom inventory leave much of the middle scene exposed. Controls use a small visual vocabulary: pale outlines and very little opaque fill. Red hearts separate health from these pale controls. The selected inventory slot has a thick beveled border, visible against the thin borders of the other slots.

The high-contrast right icons read over dark foliage, while the translucent left ring is considerably less distinct over mixed water and foliage. The empty inventory cells preserve scene visibility but their fine divisions have weaker separation over detailed terrain. The bottom-right outlines are large enough to recognize as separate shapes, but shape alone does not prove a new player's understanding of their function. Their proximity to the right and bottom edges warrants a hardware reach/safe-area check.

No image series here proves held or disabled feedback.

## Luanti 5.12 touchscreen frames

Local images: luanti-5.12-touchscreen-t1.png, luanti-5.12-touchscreen-t25.png, luanti-5.12-touchscreen-t45.png in /workspace/reference-cache/recovered-20261023/.

These are the supplied still frames from the retrieved touchscreen video. Underlying source: https://raw.githubusercontent.com/luanti-org/blog/96b71ec0fe93b5e7566de535f5fc8206b201be3e/static/blog/5.12.0/touchscreen_dig_place.webm

Retrieval metadata reports HTTP 200, 1685948 bytes, SHA-256 873bb8abb1d57a437c44c7ec1f523ddbcdb57aa12c182649392ad519df133204, matching expected Git blob 00ba0e0531387dc04880ae5b2d3744da97387405, fetched 2026-10-23 05:16:32 UTC. The metadata does not independently certify frame extraction times or transforms; the supplied t1/t25/t45 names identify these frames.

The t1 settings frame uses grouped labels, rectangular value fields and a green selected Touchscreen row. The selected row is identifiable at a glance. Dense settings text, sliders, Set buttons and a narrow scroll area share limited space; the underlying play HUD shows through, adding clutter at the bottom. This frame provides settings hierarchy guidance only, not an in-play comparison.

The t25 play frame has a bottom inventory and red heart row with spare central space. A strong border distinguishes the first selected inventory slot from neighboring slots. The white right-edge icons and bottom-right outline controls are weak against bright snow in several places. Transparent presentation preserves the view but gives variable contrast across backgrounds.

The t45 play frame shows the same general inventory and health organization with a different view. White LMB and Aux1 text is readable over brown terrain, while the outlines are less secure where they cross snow. This demonstrates why a control's apparent clarity in one background should not count as general legibility. The screenshots do not establish whether the visible action label corresponds to a held state, a dynamic layout or another condition.

The small video-frame scale softens text and thin borders. It is inappropriate to judge native typography quality against the larger 5.15 still without matching scale.

## AssaultCube mines CTF SMG

Local image: /workspace/reference-cache/recovered-20261023/assaultcube-official-mines-ctf-smg.jpg

Source: https://raw.githubusercontent.com/assaultcube/assaultcube.github.io/a011672c06a2b6e1acd5739b0e4f0cbb91866a1e/htdocs/screenshots/screenshots-large/ac_mines_CTF_SMG_large01.jpg

Retrieval metadata reports HTTP 200, 79147 bytes, SHA-256 9680fb4b193b0c2f9bebb3152e28af3d8e7e8b014833a1e3de96f6f1404bea5c, Git blob 8cbdd54e125ff05a6910a28a7263f2bd6304ac60, fetched 2026-10-23 05:18:35 UTC.

The central engagement view remains mostly clear; the radar sits in the upper-right corner, health at lower left, and ammo and scoring message near lower center. White outlined/styled digits maintain separation over dark textured ground; health and ammunition have distinct nearby symbols. A yellow scoring message uses color to distinguish an event from persistent status. The weapon occupies a large lower-right area, leaving HUD information along the edges.

This is a desktop shooter HUD reference with no demonstrated touch controls, reachability or held/disabled touch feedback. Its small 640-by-400 image supports hierarchy and contrast observations, not a font-detail or mobile-size standard. Textured stylized digits and symbols are an observation, not a recommendation to reproduce them.

## Transferable bounds

Use a clear primary/secondary hierarchy, consistently grouped state information, visible selection, and enough contrast for the supplied scene. Inspect difficult bright and busy backgrounds because the Luanti frames show real contrast losses. Preserve useful scene area. None of the references proves physical-device reach, live/custom-HUD behavior, input correctness, or a complete state system.
