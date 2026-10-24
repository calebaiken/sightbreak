# Actual CS2 references and the unchanged quality bar

Retrieved and visually inspected on **2026-10-19**. These are actual Valve-published CS2 render/gallery JPEGs, not AI illustrations or Sightbreak assets. The publisher pages are the [official CS2 feature page](https://www.counter-strike.net/cs2) and [Steam listing](https://store.steampowered.com/app/730/CounterStrike_2/). A retrieval date or HTTP `Last-Modified` value is not an individual capture date. The pictures are linked to their publisher rather than redistributed as game assets.

| Actual image | Visible reference, not a requirement to copy CS2 |
| --- | --- |
| [Nuke, Bombsite A][nuke] | Large red-banded silo landmarks, roof/crane structure, distinct grating/paint/concrete, service conduits and readable A wayfinding. Direct industrial-composition reference. |
| [Overpass, Back Long][overpass] | Curving paved route, layered masonry/railings, foliage and distinct directional tree shadows. |
| [Dust II, Mid Doors][dust2] | Detailed shaded foreground doors frame a sunlit route; surface scale/variation and architectural depth remain legible. |
| [First-person rifle][rifle] | Receiver/attachment forms and glove construction remain distinct in the foreground. This still establishes no reload-animation quality. |
| [Operators][operators] | Five distinct clothing/equipment silhouettes and layered fabric forms. Promotional gallery still, not observed match behavior. |
| [Smoke][smoke] | An irregular diffuse cloud occupies a lane, with a visible opponent and nearby fire. This still establishes no cloud dynamics or gameplay response. |

## Retrieved-byte identity

All six requests returned HTTP 200 and `image/jpeg`. Original bytes and a retrieval manifest are retained outside the checkout under `sightbreak-v3-evidence/cs2-references-20261019/`. This table supports independent re-download checks without interpreting a CDN timestamp as a capture date.

| Image | UTC retrieval time on 2026-10-19 | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Nuke | 19:05:36.383631 | 2632974 | `c310fe7e74343c4e810f9ccb041bc3305e310f28c20c56d3503d6d03e3b45330` |
| Overpass | 19:05:36.599481 | 4378688 | `f3d31fe6093927d99f8e4d21d60be3d630461bdca335a5a44d3ad612dd45fe7e` |
| Dust II | 19:05:36.749916 | 2483567 | `6a856f9314f841ea888ce173193dd02f3a5d89548deb0cb47e77cfa532b2a90a` |
| Rifle | 19:05:37.418815 | 309414 | `f8e7411cecd0dfe4b300865174ae2bd7a28ced935db5aa61784933b4dce97db5` |
| Operators | 19:05:37.486009 | 501241 | `2cab42e06f2878d31cd0bec1c1262d7b06c44a37822b453b553c4ed0ddd8ecba` |
| Smoke | 19:05:38.157432 | 459987 | `efa4a751b0f9998eedaed934649d0233663782c8fb45a1411af56f840f8cfd62` |

## Repository-backed assessment rule

The rubric is [QA-0.3.md, explicit visual rubric](../../QA-0.3.md#explicit-visual-rubric); the acceptance rule remains [SPECIFICATION.md, section 17 QA requirements](../../../SPECIFICATION.md#17-qa-requirements). Source reference: documentation `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`, not a newly scored V3 candidate.

Seven equally weighted categories: **geometry/composition; materials/surfaces; lighting/atmosphere; models/animation presentation; combat/cosmetic effects; identity/consistency; competitive readability**. Common anchors: **5** recognizable development blockout; **7** coherent but visibly simplified alpha; **8.5** consistently polished, convincing mobile art direction with minor defects; **10** exceptional executed quality. Every applicable category must meet 8.5; an aggregate cannot waive a weak category. Untested criteria remain unverified.

Historical 0.3 scores (8.1/7.9/7.7/7.8/7.6/8.6/8.7; rounded mean 8.1) and V2's scoped weapon/reload estimate (5.5–6) are **not new V3 scores**. Tests, triangle counts, asset counts and code changes do not mechanically raise a visual score. Still images cannot establish animation, audio, touch feel, sustained performance or enjoyment.

For the next comparison, judge randomized unlabelled native outputs before reading the mapping or owner quality claims; retain the blind verdict, then unblind and bind observations to exact source/image hashes. Check normal/calm/reduced-current reload sequences, shade and finish separation, and retain both regressions and wins. Preserve Sightbreak's own graphite/crimson/muted-gold identity; commercial-reference clarity is not permission to copy CS2 art. Native desktop graphics are not Android/iOS device evidence, and no human/device gate is waived.

[nuke]: https://cdn.akamai.steamstatic.com/apps/csgo/images/csgo_react/cs2/maps/nuke_default_s2.jpg
[overpass]: https://cdn.akamai.steamstatic.com/apps/csgo/images/csgo_react/cs2/maps/overpass_back_long_s2.jpg
[dust2]: https://cdn.akamai.steamstatic.com/apps/csgo/images/csgo_react/cs2/maps/dust2_double_doors_s2.jpg
[rifle]: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/730/ss_0f8cf82d019c614760fd20801f2bb4001da7ea77.jpg
[operators]: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/730/9c8b8fd6ebb2c84a1c38541369e6c05db7f1fbe0/ss_9c8b8fd6ebb2c84a1c38541369e6c05db7f1fbe0.jpg
[smoke]: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/730/ss_ef98db5d5a4d877531a5567df082b0fb62d75c80.jpg
