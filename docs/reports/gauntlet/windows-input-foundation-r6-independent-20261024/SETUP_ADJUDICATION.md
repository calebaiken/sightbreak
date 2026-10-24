# Retain initial setup failures before corrected execution

Frozen63112ce3 first own-models run exited1 on a SyntaxError before any candidate import: the final summary print lacked one closing parenthesis. Preserve controls/models.py and its exact GUARD/stdout/stderr. Create models_r2.py changing only that parenthesis; no source model/case/predicate change. This is a review harness error, not a candidate failure or a completed model pass.

The copied sealed R5 control exited1 before candidate import because runpy did not place the sibling script directory on sys.path and the original independent_models dependency was not on PYTHONPATH. Preserve its raw GUARD/stdout/stderr and unchanged script. Correct only invocation PYTHONPATH to include the immutable sealed R5 controls directory as well as candidate scripts; use fresh output/guard paths. This grants no case/expectation/reader edit.

Both outer guards record zero forbidden operation attempts. Other independently launched pure checks keep their own results; no failed setup is counted passing, overwritten, silently omitted or used to change a candidate expectation. Commit this adjudication and corrected source before execution.
