# Old timing test requires pre-edit adjudication

Read after preregistration `41c2dbe2`, before implementation. Original
`test_source_git_children_receive_only_remaining_whole_deadline` mocks every
binary Git result as empty and every text result as the expected commit. It
requires a successful binding and exactly four Git calls. This tests the old
four-query implementation, not a physical-source corpus with tree/blob evidence.

A complete binder must not accept that empty mock as proof of required files.
Do not preserve its pass by bypassing physical validation or redirecting the old
test to an obsolete function. The prior promise of no constructor amendment was
premature: this precise test needs independent pre-edit adjudication.

Proposed change for review: retain the original source/assertions and literal
old-test result, then version its fake Git construction with an explicit small
tree and matching blobs/physical files. Continue requiring every Git subprocess
timeout to be positive, at most the remaining whole budget and nonincreasing;
require no late subprocess. Replace only the implementation-specific count of
four with the count derived from that frozen fixture and declared Git query
design. No process/native/math/canonical assertion changes. This is a proposal,
not authority to edit the old method or its protection hash.

The original test module is protected by `44154d83...`. Any permitted adaptation
must be exact and additive, preserving the original bytes/hashes and all outside
methods. Until adjudication, no binding implementation or old-test edits occur.
