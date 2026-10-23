# Retained inspection and packaging mistakes

The first exploratory read command, tool chunk `560fc7`, printed the original
overall receipt and then tried to read `failure.json`. That file is absent:
normal failure publication succeeded through `overall.json`, so a separate
publication-error fallback file was never created. The read command exits 1
with `FileNotFoundError`; this is an inspection assumption, not an acquisition
or auditor pass. No original file changed. Subsequent reads use the actual file
set and preserve the absence of fallback publication.

The early failure-input commit `05881df9` retained copied originals but omitted
four `.log` copies because Git ignored their names. All four original copies
remained on disk with their first hashes. Commit `587b0c74` explicitly force-adds
the exact accepted-block stdout/stderr, client and Xvfb logs, preserving the
initial omission and correction. No raw byte was replaced or normalized.

The first full payload and actual auditors both pass with empty stderr. Auditor
exit 0 verifies the retained FAILED acquisition; it does not change that verdict.
