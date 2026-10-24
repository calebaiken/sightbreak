# Collector attempts

This note transcribes the first collector's tool output, not a native engine log.
The initial selection exceeded its 4 MiB cap: `5167006 > 4194304`, exit 1.
The refusal happened before creating the publication directory or copying files.
The selection contained a generated 3,269,740-byte Godot editor documentation
cache under the UID fixture's `.local` directory. The collector now excludes
`.local` alongside other generated cache roots and lists omissions explicitly.
The original cache and external attempts are untouched. No tests or native
programs were rerun to make this publication.
