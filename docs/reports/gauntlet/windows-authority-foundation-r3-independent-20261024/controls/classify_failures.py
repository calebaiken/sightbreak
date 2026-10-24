#!/usr/bin/env python3
"""Classify retained failures without rewriting or replaying their rows."""
import json
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parents[1]
items=json.loads((P/'literal-traced-v2/FAILURES.json').read_text())
for i,x in enumerate(items):
 t=x['test'];x['ordinal']=i
 if 'test_input_consumption_foundation_model.' in t:
  x['classification']='historical-preedit-model-layer';x['finding']='Frozen pre-edit expectations deliberately refer to old reader/helper; exact registered baseline18 adapter passes separately, no candidate credit.'
 elif 'test_input_consumption_expiry.' in t:
  x['classification']='historical-expiry-layer';x['finding']='Exactly named method requires old helper or missing-foundation UNKNOWN semantics; two-method hash-bound old snapshot run passes, no candidate credit.'
 elif 'retired_generation_cannot_consume' in t:
  x['classification']='negative-message-layer';x['finding']='Input remains INVALID; earlier source contradiction changes error substring. No assertion change adjudicated.'
 else:
  x['classification']='derived-constructor-source-classification-incomplete';x['finding']='Retained literal failure. Named timer contradictions are documented in REVIEW.md, but no blanket repair, expectation transfer or full fixture/source adjudication is granted.'
summary=dict(events=len(items),failure_events=sum(x['kind']=='failure' for x in items),errors=sum(x['kind']=='error' for x in items),categories=dict(Counter(x['classification'] for x in items)),all_original_test_tracebacks_retained=True,candidate_failures_not_reclassified_as_pass=True,events_detail=items)
(P/'FAILURE_CLASSIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='events_detail'},indent=2))
