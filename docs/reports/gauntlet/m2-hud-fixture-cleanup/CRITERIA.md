# HUD fixture namespace cleanup

Declared before implementation on `60db9ff884ad6989c6bfd87cf2fe3405505a9997`.
Builder `/root/branch_recon`; acceptance belongs to a separate critic.

Reference: ARM Mac [CI run 39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304).
Its actual HUD suite log reports a private inner native directory
`SIGHTBREAK_QA/hud-objective-hint-2472-215773`, distinct from the runner's owned
outer namespace. The fixture passes 33 checks but has no cleanup and leaves its
ownership marker outside the runner's cleanup scope. Raw downloaded receipts
are available at `/workspace/reviews/mac-ci-39719407304/arm-receipts`.

Required evidence:

1. Reproduce the orphan with actual native Godot: outer runner cleanup succeeds,
   inner directory/marker remains. Retain the original log and marker identity.
2. Normal success removes only this fixture's marker and now-empty leaf directory,
   restores the original native user-directory identity, and keeps all 33 HUD
   checks and progression guards intact.
3. A native controlled early source failure also cleans its owned empty fixture
   and preserves the original nonzero result.
4. Protected state or changed ownership refuses destructive cleanup and fails
   explicitly. Ordinary application profile sentinels remain byte-identical.
   Do not recursively erase unknown contents or shared parent namespaces.
5. Run actual native success and failure controls. Preserve raw outputs, producer
   paths, before/after filesystem observations, source identity and cleanup.
6. No game presentation, shipping settings, profile/economy behavior or unrelated
   changes. Linux checks do not establish Windows/macOS execution acceptance.
