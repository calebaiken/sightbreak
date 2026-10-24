The first inline source audit stopped at its tracked-path allowlist. It expected
only the two code paths but compared against the original base, so it also saw
the already committed preregistration. No source-preservation receipt was written.
The tool output was:

```text
Traceback (most recent call last):
  File "<stdin>", line 23, in <module>
AssertionError
```

The corrected saved `audit_source.py` allows additions only under this new report
directory and requires every other changed tracked path to be the two exact code
files. It checks their complete expected before/after bytes. This is a source
delta audit, not a GDScript compiler or runtime test. No product code changed for
the audit correction.
