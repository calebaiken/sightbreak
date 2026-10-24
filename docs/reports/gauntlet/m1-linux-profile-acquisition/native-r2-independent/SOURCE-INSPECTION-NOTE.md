A read-only schema probe initially assumed `original-before.json` was an object.
It is the original 430-entry list. The probe printed that list, then exited 1
with `AttributeError: 'list' object has no attribute 'items'`. The tool output was
truncated and was not saved as a raw audit result. This was a schema-inspection
error, not a native run or a passing preservation check. The saved source
admission reads the original list directly and records its actual comparison.
