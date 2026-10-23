# Bounded layout OCR resource candidate

Status: candidate for independent review. Native CI timeout correction is
UNVERIFIED. Baseline source is `7d46d2e`; the benchmark script was frozen at
`b2aed69` before the observer changed. No shipping game files changed.

The candidate sets `OMP_THREAD_LIMIT=1` only in each Tesseract child's copied
environment. Original PSM 11 TSV, full-frame preprocessing, footer analysis,
words, exclusions, current-frame capture, source/ELF checks, native actions,
drawn-frame fences and timeouts stay unchanged. The parent and Godot environment
are not edited. Each attempted OCR command now retains its supplied timeout,
wall duration and thread policy, including an exception receipt on failure.

## Measured comparison

After the account-match builder explicitly released the CPU/native lane at
04:37:47 UTC, one serial OCR child ran at a time. Two alternating-order rounds
compared inherited OpenMP behavior and the one-thread child on all 22 original
native fixtures, full-frame and footer analysis separately. All 176 actual calls
completed; all 88 paired analysis and TSV hashes are identical, with the same
word lists and expected HUD classifications. Original fixture hashes still match.

| Saved-image child measure | Inherited OpenMP | Child limit 1 |
| --- | ---: | ---: |
| Calls | 88 | 88 |
| Total child CPU seconds | 47.861085 | 22.521193 |
| Total child wall seconds | 22.926853 | 22.577192 |
| Maximum child wall seconds | 0.561861 | 0.546480 |
| Maximum observed child threads | 4 | 1 |

Child CPU use falls by 52.94%; aggregate wall time falls by about 1.53%.
These saved-pixel measurements support a bounded CPU reduction. They do not
establish that the original native CI deadlines now pass. The host has a
four-CPU cgroup quota, not a physical-device performance benchmark.

`thread-comparison/` retains the complete report, every raw TSV/stderr and raw
run log. Reproduce after reserving the shared CPU lane:

```sh
python3 docs/reports/gauntlet/native-layout-timeout/measure_tesseract_threads.py \
  --output .local/fresh-thread-comparison --rounds 2
```

## Repeated startup investigation

The failed 0ca CI receipts contain 30 repeated completed startup OCR calls after
first occurrences, across the four cases. Their original PNG hashes exactly
match the retained prior native `menu-ready-1` originals for each size. Those
prior images are available; the new CI final menu/settings images remain
unavailable. This does not turn the old captures into new CI image evidence.

Twenty-four additional actual Tesseract calls compare these exact retained
startup bytes under both thread policies. Each size produces byte-identical
TSVs on every trial. Inherited median child wall durations are 0.2195, 0.1788,
0.2368 and 0.1723 seconds for 960×540, 1280×720, 1920×1080 and 1280×800.
The one-thread values are similar. A cache could avoid roughly one to two
seconds of such child work per case on this saved-image host. That estimate
is not a native deadline result. No cache was added: the current candidate
contains only the measured thread policy and failed-attempt receipts.
`startup-repetition/` retains the raw trials and exact prior/native-CI hash link.

## Candidate controls and remaining gate

The actual production helper passes eight saved-image tests in 14.299 seconds:
all original recognition/negative controls and a real deliberately tiny-budget
Tesseract timeout. The timeout propagates, its exact supplied budget/error is
recorded and the parent thread setting remains unchanged. The ordinary test
OCR limit stays five seconds. Raw output and 46 classification TSVs are retained
in `candidate-controls/`. Existing observation tests pass four Linux controls
with three Windows-only skips; all 24 build/log controls pass. Compilation and
whitespace checks pass. These source/observer tests do not qualify other hosts.

The original failed CI result JSON files are retained byte for byte as lossless
gzip, with original hashes in `native-ci-39719407304/index.json`. The 960×540 and
1920×1080 menu predicates recognized their required words late, then failed the
post-condition wall-budget check. They do not establish missing text.
The original settings timeout and all forced-cleanup receipts remain failures.

Biggest remaining deficiency: no exact-source native four-size rerun proves
that the combined CI failure is resolved, and that failed run's final PNGs could
not be independently inspected. Root must run the original Linux gate on a
clean reviewed source and retain the newly added per-size bounded image archives.
No full layout, visual quality, hardware performance or RC acceptance follows
from this candidate.
