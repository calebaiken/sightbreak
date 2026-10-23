# Strict native log guard integration result

Ready for fresh independent source review. Implementation is frozen at
`64a7afbad452d9559a39844bde7f25026029c97b`, based on root
`358b240ebadb8f32b581922ab99baec11ff9ed81`. Preregistration `23e91c30`
precedes the implementation and retained red check.

`scripts/native_log.py` equals the independently accepted blob at
`aae1f0a5e963a01dceb4aed1d9c3b0c40520c76f` byte for byte: 390 bytes,
SHA-256 `8684252c3ec4ca466fe24a31f938a7614b8ce993c91041b0a2c42d2d483f94e1`.
The exact old root matcher returns false on the complete original native log;
the retained baseline control exits 1 on that assertion. The corrected matcher
returns true. This is a stricter failure classification of preserved output.

The complete original corpus is force-tracked at
`scripts/fixtures/native_log/input-mode.log`: 2,000,315 bytes, SHA-256
`a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218`,
Git blob `29fe318726e0519bc43130d289692e72e4be232b`. Its 353 orphan rows and
positive summary retain all original bytes at lines 6,939–7,292. Their combined
29,016 bytes hash to
`0b763d8e87812ec6ea07183bd17f3566072fdb6b9811c62f26be5d5527475350`.
Fixture provenance maps the full corpus, diagnostic range, original source,
manifest/receipt hashes, pinned engine/version/binary hash, native-format source,
original independent actual archive and accepted matcher/review. The fixture
attributes preserve log bytes with Windows `core.autocrlf=true`.

The five standalone stdlib methods pass. They bind the entire original corpus,
reject each of 353 original orphans individually in LF/CRLF/unterminated forms,
reject a positive summary without orphan details, allow quoted/embedded/split
records and zero summaries, and retain legacy error/leak rejection. The test
loads only its module and checked-out fixtures. It invokes no Git or audio code.

Build-manifest controls pass 24 methods; QA-receipt packaging passes eight.
`bash -n scripts/validate.sh` passes. The first manifest run retains two setup
errors because the sparse checkout omitted `game/export_presets.cfg`; restoring
that exact tracked file resolves both without a source edit. Original failed
output and the passing rerun have separate receipts.

An exact depth-one checkout of `64a7afba` independently repeats all 37 pure
methods with zero failures or skips. It has one reachable commit, no remote,
no report directory and no audio lifecycle modules. With `core.autocrlf=true`,
the corpus still has its exact original hash. The checkout remains clean.
See `shallow-verification.json` and the three retained test outputs. This is
builder verification; a separate critic must judge the integration.

Only one pure test command is added to each of `scripts/validate.sh` and
`desktop-alpha.yml`, beside packaging controls. Removing those exact additions
reconstructs the root files byte for byte, preserving every existing workflow
matrix, condition, native step and budget. The game tree remains root
`55691684d31d44f1680141954bbe530443de9d1f`. Source hashes are recorded in
`source-binding.json`; original raw/receipt hashes remain unchanged.

No audio analyzer, acquisition wrapper, observer, probe or corresponding test
module is integrated. No engine/import/export/UID/native/CI/OCR/service/heavy
aggregate or nested agent operation ran. Historical native output and results
remain unchanged. No leak repair, owner/cause, server drain, audio quality,
gameplay or release gate is qualified. Root retains canonical mission updates
and integration ownership.
