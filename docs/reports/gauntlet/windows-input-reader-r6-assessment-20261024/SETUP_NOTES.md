# Interim setup notes

Own sparse checkout was created at exact pre-implementation registration4f0a1906,
with index read-tree before sparse patterns and explicit materialization. Other
checkouts, especially sealed R5 source/depth/report, remain unchanged.

An interface read guessed scripts/input_consumption_model.py, which was absent.
The implementation is inside scripts/analyze_input_consumption.py and its actual
diff was read in the same call. No test ran in that lookup. Any copied prototype
is explicitly unapproved working source, not a final frozen candidate.
