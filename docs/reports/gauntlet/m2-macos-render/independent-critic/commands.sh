#!/bin/bash
# Run from the reviewed checkout. No renderer is started by these commands.
cd /workspace/sightbreak-macos-render
python3 scripts/test_macos_render_diagnostic.py -v
python3 /workspace/reviews/macos-diagnostic-critic/audit_evidence.py
python3 /workspace/reviews/macos-diagnostic-critic/audit_fixture.py
python3 /workspace/reviews/macos-diagnostic-critic/process_controls.py
# The retained original failed Mac evidence and Linux controls were extracted
# with Python zipfile/tarfile. See raw/original-summary.json and linux-controls/.
