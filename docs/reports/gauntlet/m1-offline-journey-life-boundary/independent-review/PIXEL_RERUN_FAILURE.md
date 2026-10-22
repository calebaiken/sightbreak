The first independent saved-pixel run completed 10 checks on the baseline and
5c11a5b readers. Three real positive Windows frames passed per reader; the
actual main-menu and eliminated frames failed per reader. Both reader ASTs are
identical. The completed result is retained in `windows-recomputed.json`.

After adding the unchanged reader from 171169e to the script, a second invocation
failed before writing a replacement result. Tesseract's PSM 7 subprocess timed
out after the unchanged 20-second limit while processing a 5c11a5b frame. The
native builder probe overlapped this saved-pixel work and separately timed out
in its first PSM 6 health read before the changed settings block. Its receipt
reports 72.11193678899872 seconds and empty cleanup errors. The shared resource
cause is uncertain; neither timeout establishes a gameplay-context failure.
No native renderer was launched by this critic. Further critic OCR was stopped
while the builder retried its same-source probe.

The independent invocation failed with:

```text
subprocess.TimeoutExpired: Command '['tesseract', 'stdin', 'stdout', '--psm', '7']' timed out after 20 seconds
```
