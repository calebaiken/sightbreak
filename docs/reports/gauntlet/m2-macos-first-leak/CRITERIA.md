# First failed native leak suite diagnostic

Preregistered against root a3b7070 before implementation. Source and pure controls
only; no local Godot, OCR, native APIs or CI dispatch.

## Actual boundaries

Run 39736389634 at 20464da passes the native menu gate. Its separate strict source
step fails at the first suite, actor: 73 checks, zero assertion failures, exit 0,
and six ObjectDB leaks. The other 11 suites are unreached. Import/bootstrap,
source/copied resources, temporary project and owned namespace cleanup pass.
The input-mode-only diagnostic correctly skips because input_mode.log is absent.
There are no actual verbose leaked-object types for this run.

Run 39732825169 at b09cfe1 remains a separate failed boundary: input_mode reaches
462 checks, zero assertion failures, exit 0 and two ObjectDB leaks after six clean
suites; five later suites are unreached. The game tree is identical at b09cfe1,
20464da and this base: fb6be859e05812d8707be1ef5c6f747d2588c1e9. Cause and possible
nondeterminism remain UNKNOWN. Counts and different suite boundaries do not prove
a common cause. Previous menu failures and the newly passed menu gate stay distinct.

The latest actor log SHA-256 is
`75f1e6946ec1e361d9ebb242b48a719fc75cb5fb4ad47472b7e4de4e400b592a`.
Raw results/isolation receipts and both leak logs are retained byte for byte in
fixtures with their run/source provenance. They are source-selection benchmarks,
not new native execution or leaked-type evidence.

## Required behavior

- Keep the existing CLI script and arguments. Select only the first failed suite
  in the original results, which must also be the terminal result. Require no
  duplicate/unknown suite identifiers, successful earlier suite receipts, exact
  integer exit 0 plus clean_log=false for the selected suite, the corresponding
  strict isolation failure, and its actual ObjectDB-leak log. Whitelist only actor
  and input_mode. Never fall through an unsupported first failure to a later one.
- Verify the selected original command is the maintained pinned-engine/headless
  suite argv for its recorded private project; verify before/after producer paths
  agree with that project and its unique original namespace. Keep original source,
  copied-resource, cleanup and current resource-hash guards. Foreign argv, paths,
  missing/changed evidence, unclean original cleanup, unsupported failures, and
  absent/malformed proof must launch no diagnostic engine process.
- Repeat exactly the selected maintained suite once with --verbose as the only
  suite-argv addition, using the existing new owned private project/user namespace.
  Imports and producer probes remain prerequisites. Preserve 240 s shared deadline,
  6 min workflow timeout, owned process groups, original evidence hashes/absence,
  raw logs, native path receipts, produced-file hashes and honest cleanup receipts.
- The original strict step stays FAILED. No warning suppression, gameplay/source
  fixture fix, invented cleanup or claim of leak resolution. A clean repeat is
  diagnostic only. Unvalidated bootstrap namespaces remain preserved on failure.
- Pure controls must cover both whitelisted suites and the previous input_mode
  behavior, actual retained receipt selection, unsupported/absent/foreign/changed/
  unclean evidence with zero launch, exact argv, first-failure ordering, deadlines,
  owned cleanup and unchanged strict failure. A fresh independent source critic
  must approve the frozen implementation before root's next ARM dispatch. Actual
  verbose object types and their cause need independent native evidence review.
