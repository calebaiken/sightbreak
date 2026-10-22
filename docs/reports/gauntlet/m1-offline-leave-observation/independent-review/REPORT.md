# Independent LEAVE observer review

2026-10-22. Accept the bounded observer correction at `85d6101bb049d41368cac2921c6479afe420a242` and the focused Linux native LEAVE transaction. The actual Windows full journey remains required. This review does not close G1, G7, G11 or G12.

## Failure and comparison

The original Windows run [39723283770](https://github.com/calebaiken/sightbreak/actions/runs/39723283770), frozen `dc2a198`, failed `Native UI text not found: LEAVE` at 87.375 driver seconds. I opened its unchanged [final native image](original-windows/ocr-current.png): FIELD MENU and LEAVE MATCH are readable, with the training pause visible. Its SHA-256 is `e62116a4c42c7b09ca947a7eb1cb3551865c4d6f4ffecff36066f8e7d4bee635`. The original Windows OCR exited zero, but its stdout was absent; the exact Windows token stream remains unknown.

The retained [baseline Linux replay](baseline-replay/results.json) applies the original production transform to those same pixels and produces LEAYE MATCH, so the original exact-LEAVE lookup fails. This establishes an observer weakness on identical pixels, without establishing the missing Windows tokenization.

I independently reran the final production transform with Tesseract and `OMP_THREAD_LIMIT=1`. The [three retained cases](independent-pixel/results.json) pass: the original final Windows frame yields exact FIELD MENU and LEAVE MATCH; an actual settings frame yields neither; the explicitly altered removed-MATCH frame preserves FIELD MENU and rejects the incomplete control. Raw PNGs, transforms and TSVs are retained. This is Linux saved-image evidence.

The builder's broader 9/11 versus 11/11 result compares the old and new transforms under the **same new strict caption predicate**. It does not replay the original click authorization on every negative: the old single-token lookup could accept LEAVE when MATCH was removed. I raised this distinction before acceptance. The replay at `4a9ee7b` and maintained-test source `fc4e609` have identical full Python ASTs; only comments and whitespace differ. The final `85d6101` adds stdout retention without changing that transform or caption predicate.

## Source and native evidence

No blocking source defect found. Grayscale enlargement precedes the unchanged threshold of 145. The complete LEAVE MATCH and FIELD MENU captions must each occupy a unique complete OCR line. Missing, reordered, misread, extra or ambiguous text fails. The LEAVE path checks the same living actor, round, weapon, ammunition, focus and simulation speed before and after OCR, and requires the ordinary field pause. It retains the real native click and return wait. Product game files are unchanged by this correction.

I independently ran the five maintained caption tests; all pass. I also exercised the actual stdout-retention closure with a fake subprocess: success, nonzero exit, timeout with partial bytes and 2 MiB plus one byte. Byte counts, hashes, completeness and failure outcomes were correct. The ceiling bounds the retained file; subprocess stdout still uses a pipe. The existing QA packer selects these nested `.log` files and keeps its 30 MiB archive ceiling.

The [Linux native receipt](native/results.json) is bound to clean `85d6101`, validation SHA `e4e266c124671e79da69c2d7418c73ca6a750d96779c86b904ce3293bddea6bc` and game-content SHA `f8a849b90df3ff214037cace7bc32c0c7b5e184911558b424b0a6c0f798db781`. I rehashed the 84,222,840-byte ELF: `92d892f76bd400896b326062ef8f0a0d7981c783798563be8ad07e1bb5aab7e1`, matching the export and execution receipts. The executable remains in the builder's `builds/leave-native-r1/linux/` directory; it is not duplicated here.

The probe executes the production settings/resume/LEAVE block verbatim in a first stock match with the sidearm. The archived driver, production block and transformed-controller hashes independently match its receipt. Settings preserve 100 health and 15/60 ammunition; the explicit resume is acknowledged and advances two drawn frames. The final [native field-menu image](native/ocr-current.png) clearly contains the intended control. All seven raw stdout files match their byte counts and SHA-256, have exit zero, and are complete and untruncated. The final TSV yields a unique LEAVE MATCH box centered at reference coordinate (639, 384).

The actual LEAVE click occurs at 59.712 seconds; the return wait completes at 60.729 seconds. I opened [08-return-menu.png](native/08-return-menu.png) and confirmed the main menu. The probe finishes in 61.955 seconds with client and Xvfb exit zero and no cleanup errors. The 300-second flow limit, 20-second OCR ceiling, 10-second resume budget and 30-second return wait remain intact. These llvmpipe timings are execution evidence only.

## Remaining gap

The largest gap is a fresh exact-source Windows **full** offline journey, retaining per-invocation raw OCR stdout. The Linux probe omits purchases, second-round setup, restart and focus recovery, and explicitly records those limits. The original Windows failure remains failed. Full maintained validation of the final integrated source is owned by the coordinator and was not run in this critic lane. No native renderer or additional OCR ran after the builder released the shared slot.

Recheck the retained bytes, native transaction receipts and exact captions without starting OCR or Godot:

```sh
python3 docs/reports/gauntlet/m1-offline-leave-observation/independent-review/verify_receipts.py
```
