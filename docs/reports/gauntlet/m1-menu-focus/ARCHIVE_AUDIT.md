# Independent archive audit

Reviewer: `/root/menu_critic/archive_audit`, separate from the archivist.
Date: 2026-10-22. Read-only verification; no game execution or file changes.
No defect found.

The auditor verified 123 regular, sorted, safe archive members against the current
manifest and original source bytes, including every size and SHA256. All 117
historical hashes and the eight outer checksums present at audit time passed.
Review, commands and brief copies matched their originals inside and outside the
archive. The archival audit record is added as the ninth outer checksum afterward.

The archive SHA256 is
`df918e51da299842a76c0ff3bdb4ca2253971e77d437ce69033cd5e8bd6970d5`.
Its compressed size is 26,310,169 bytes and payload size is 29,926,833 bytes, within
the 32 MiB/64 MiB caps. Four raw Godot state logs are present; no other state file
is included. The auditor found no symlink, hardlink, special file, unsafe path,
compiled binary magic, generated launcher, template payload, cache, private key
or token. Retained Godot license/copyright files are plain UTF-8 text.

The source reproduction commit object hashes to exact 6767e97 and matches the
original object; its UID diff, tree and game tree agree. Excluded app/editor/
launcher bytes and hashes match the exclusion receipts. RESULTS.md and
INDEPENDENT_ARCHIVE.md retain the menu review's bounded mechanical/input scope,
leave physical/full-game/release gaps open and disclose the reported CI failure.
This audit verifies preservation and scope; it adds no player-experience acceptance.
