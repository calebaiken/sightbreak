# Cleanup review corrections

The independent critic found two native counterexamples in b899972: a dangling
leaf link survived cleanup while the receipt said `removed: true`, and a linked
shared `SIGHTBREAK_QA` parent was followed despite the documented refusal rule.
Original outputs remain in the independent review evidence.

Before revision testing, require:

- Report removal only after successful owned-leaf removal and an entry-aware
  absence check. A dangling link refusal must report `removed: false`.
- Refuse a linked shared namespace before creating the private leaf or marker;
  restore the caller's native directory and preserve the link and target bytes.
- Recheck that shared namespace before controlled cleanup. Keep protected-file,
  marker, leaf-link and original nonzero-exit behavior intact.
- Rerun the actual native ordinary HUD suite and independent edge controls.
  Obtain independent re-review before root integration.

The fixture owns its unique leaf, not the shared parent or the operating system's
data directory. Checks cover cooperative local tests; they do not promise atomic
protection against concurrent filesystem replacement or cleanup after SIGKILL.
