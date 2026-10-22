#!/bin/bash
cd /workspace/reviews/macos-diagnostic-evidence-worktree
python3 /workspace/reviews/macos-diagnostic-critic/followup/check_fallback.py
python3 scripts/test_package_qa_receipts.py -v
git show --format=fuller --no-ext-diff 3bfc29b
