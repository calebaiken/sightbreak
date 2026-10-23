# Independent source and conditional recipe verdict

ACCEPT exact candidate `216d39ada8f9d11e2d8544d01fde42da49607b14` for source and the conditional first-use r2 acquisition recipe. The candidate wins over actual failed source `f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9`: it removes the direct Variant-return inference at the compiler-reported declaration while retaining the same runtime Dictionary guard, keys Array, comparator, traversal, serialization and fingerprints. This is a labeled source comparison. Native compilation of the candidate is UNOBSERVED.

The single largest gap is actual pinned-engine compilation/import. The old attempt remains FAIL at strict import, with outer exit 1, import child exit 0, zero export and zero native conditions. No runtime, cadence, performance, cause or release-gate conclusion follows from this review. Root must separately release the lane before any execution.

The fresh reviewer preregistration was committed and pushed as `a1c45578` before candidate handoff/diff/test inspection. Its parent is the exact candidate. Builder registration `86d5e62cb4f9f5127856cb06d78e937072e6c604` precedes implementation `2e9ed451b43280815324100171c51580c7f4ec98`. The installed original gauntlet/no-ai-slop/eval and mission instructions were read. No nested agent ran.

## Source identity and meaning

The complete executable/configuration delta is three lines:

- Fixture line 107 changes `var keys := value.keys()` to `var keys: Array = value.keys()`.
- The supervisor pins the resulting fixture SHA-256 `bac96e5c3aa9e63dfe0aa41522076cb6352293a3d5d9e70657a19cdfa4d52b92`.
- The fixed output changes from `builds/linux-profile-acquisition-r1` to `builds/linux-profile-acquisition-r2`.

`Dictionary.keys()` supplies the Array in the existing `TYPE_DICTIONARY` branch. The explicit unparameterized Array adds no element conversion or filtering. The comparator and its supported key variants remain byte identical. Every other `:=` site was inspected; none directly infers from the untyped canonical `value`. Inspection of those sites does not certify the whole fixture parses.

Every other tracked path outside the new correction report directory matches the failed source. This includes the controller/evaluator, scene, tests, payload reader, pins, original offline controller, measurements, prior reports and mission files. The shipping game tree is unchanged at `55691684d31d44f1680141954bbe530443de9d1f`. All 20 candidate manifest artifact identities match their exact Git-bound bytes. The builder worktree remains clean at the candidate SHA.

## Independent pure verification

| Check | Result |
| --- | --- |
| Existing acquisition suites | 31 methods, zero failures/errors/skips |
| Existing fixture/controller/evaluator suite | 22 methods, zero failures/errors/skips |
| Independent source and preservation checks | 81 passing predicates |
| Owned-worktree source mutations | 18 rejected by the unmodified saved source audit |
| Real main admission controls | Six unsafe/reused output states rejected before execution |

The [acquisition output](acquisition.txt) and [fixture output](fixture.txt) come from independent runs of the maintained suites. Those suites cover synthetic payloads, original falsifiers, publication mutations, source/read boundaries, cadence mathematics, deadlines and fake-process ownership. No test was changed or added to portray a string check as compilation.

The [independent verifier](verify_source.py) checks the exact complete before/after fixture and wrapper bytes, all remaining tracked paths, the source ledger and the preserved original records. It runs the unmodified builder audit with only its generated receipt redirected into this review directory. The audit rejects changed key typing, comparator and hash; stale/arbitrary/reused output pins; extended whole/phase/condition bounds; CPU, LP or display changes; packaging changes; sampling/controller/scene/game changes; and altered fixed pins. Each mutation is restored byte for byte in the reviewer worktree. Neither original nor builder worktree is mutated.

The six admission controls exercise existing empty, partial and claimed output directories, a directory symlink, a dangling symlink and a symlinked parent. Each returns failure without calling execution or changing the existing files. The maintained flow controls separately verify the fixed one-pass phase order and stop at the first failed phase. No continuation option or fallback was introduced.

The first reviewer control run failed because the harness compared the native critic's shortened outer-record labels to their original prefixed filenames. [Its original error](controls-first.stderr.txt) is retained. The mapping was corrected without changing expected bytes or any candidate code. The next run passed 79 checks; the final run added direct original-source verification and passed 81. The preregistration's mistaken wording `display range 99..127` is retained and explicitly corrected in [the amendment](PREREGISTRATION-AMENDMENT.md) to the sole fixed display `:99127`.

## Preserved failed evidence and conditional recipe

All 224 original raw files, totaling 178,615,722 bytes, and all three original external wrapper records rehash identically to the actual-output critic's registry. All 430 original game/script files match both their recorded SHA-256 identities and exact failed-source Git bytes. These finite observations were repeated after the controls. Original source HEAD and clean tracked status remain unchanged; no perpetual immutability is claimed.

The old import stderr still contains exactly the two strict compiler/load errors, including `Cannot infer the type of "keys"` at line 107. The candidate's unchanged strict matcher rejects both. The old actual-output review `5cbbcd3c0e58a2b381c762d11cdbc0fe92936a5e` and all earlier reports remain unchanged. The builder's missing sparse-game fixture failure and first source-audit allowlist failure are retained, with their original failing outputs/notes. None is counted as a passing run.

The conditional recipe is acceptable only as one fresh first use of the builder's exact clean candidate SHA. At this review observation its r2 output/claim and all `.local/linux-profile-acquisition-r2-*` records are absent. Keep those identities fresh; preserve any failed claim/output/streams/outer receipt and do not continue manually. Substitute the reviewed full candidate SHA for the handoff placeholder. This approval grants no execution or lane release.

The supervisor preserves the original 1320-second whole cap, phase caps `60/45/15/120/30/120/60/30/750/60`, five-second owned cleanup and ten-second failure publication. The controller retains each strict 180-second condition bound, OFF/ON/ON/OFF, 32 warm and 64 measured intervals. CPU `0,1`, LP2, display `:99127`, pinned Godot 4.7.2/editor/templates, and the reviewed external text-script/export amendment remain exact. There is one fixed output and one exclusive `attempt.claim`; unavailable admission rejects without alternate affinity or display.

No Godot, engine/import/compiler/export/native condition, generated UID, Xvfb, profiler, OCR, CI or service was run by this reviewer. Text export/resources, runtime fingerprints/pixels, runtime cleanup, host interference, cadence and the H1 outcome remain unqualified. The next authorized step is root's decision on a separately released single native attempt.
