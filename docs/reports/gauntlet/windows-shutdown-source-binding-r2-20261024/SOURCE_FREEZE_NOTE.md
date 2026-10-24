The first source commit964a891d contains the physical verifier. A sparse-path
refusal left the new test file outside that commit; it remains intact and is
added in the next additive freeze. No history was rewritten and no preflight/native
execution ran from the incomplete test commit. Pure-r1 passes36 before the freeze;
independent source review must bind actual code/test blobs and scope.
