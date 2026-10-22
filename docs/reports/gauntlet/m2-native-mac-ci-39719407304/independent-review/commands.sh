#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# In a fresh review checkout. Existing extracted evidence is deliberately refused.
python3 unpack_evidence.py
python3 audit_receipts.py arm-receipts --identity source/independent-source-identity.json > arm-receipt-audit-reopened.json
python3 audit_native_mac.py arm-receipts/evidence arm-qa > arm-native-audit-reopened.json
if [ -d intel-receipts ]; then
  python3 audit_receipts.py intel-receipts --identity source/independent-source-identity.json > intel-receipt-audit-reopened.json
  python3 audit_native_mac.py intel-receipts/evidence intel-qa > intel-native-audit-reopened.json
fi
