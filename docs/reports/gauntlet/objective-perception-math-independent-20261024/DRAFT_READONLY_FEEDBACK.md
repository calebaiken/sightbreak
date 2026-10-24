# Mutable draft inspection before final freeze and all tests

Builder invited read-only inspection of its untracked draft after prereg27afc162
and case amendmenta54b650c. Reviewer read scripts/acquire_fov_math_reference.py,
fov_math_reference.py,test_fov_math_reference.py and the tiny project/reference.gd.
No tests, generator, native process or mutable component-C source were executed.
This observation is not a frozen-source verdict; final hashes remain required.

Concrete admission issues returned to builder:

1. Stream retention initialized after post-spawn identity/executable checks;
   early failures could lose both pipes. Error-finally closed streams before
   cleanup/drain, leaving unretained bytes/unknown EOF with no explicit incomplete
   failure-coverage status. Retain immediately and drain within the same5s cleanup,
   recording caps/truncation/EOF separately from complete raw coverage.
2. Source-binding Git subprocess calls had no remaining-whole-deadline timeout.
   Native budget checks after a blocking child do not themselves bound that child.
3. Output validation checked bit/decimal and predicates from reported native dot,
   while general Python/model differences merely became unresolved. Add required
   analytical exact-axis/zero/equality/recent controls, plus coordinated dot+bits+
   predicate and toward+bits negative controls, without forcing general native/
   model equivalence or adding broad numerical tolerance.
4. Corpus includes150 opposite-team pairs with explicit alive/dead metadata plus
   one synthetic yaw mutation. Do not describe all151 as living native captures.

Builder acknowledged all four points before final source freeze and is correcting
the proposal. Final review will challenge the frozen implementation and fresh
pure/admission controls; agreement is not approval. Native math precision, libm,
serialization and actual completion remain unknown, with no execution released.
