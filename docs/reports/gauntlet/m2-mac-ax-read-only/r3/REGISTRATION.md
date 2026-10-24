# R3 untitled AXButton registration

Registered before implementation on own branch `codex/m2-mac-ax-untitled-r3`,
based on exact diagnostic source `d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53`.
The empty sparse worktree index was populated from HEAD before checkout; its
initial status was clean. Root, contributor and previous builder worktrees stay
owned by their authors. This is source-only work pending independent review.

## Actual failure and inspected bar

ARM run `39939989024`, job `120368768573`, fails with trusted/query prerequisites
true and a partial three-node traversal: AXWindow, AXGroup, then AXButton.
The button's AXTitle read returns `-25212`. Original observation SHA-256 is
`f795b8f263668b7e4e6960969fd9f23dc57fbbf97c7b88e541999f75919c8be8`;
original QA artifact `12495925886` SHA-256 is
`09486d7f72e8ca3290ff4a8d395447668f7a7f11bc762c5c635494f6f2208273`.
Independent critic `/root/mac_ax_native_fresh_critic` supplied those references.
The node has no retained subrole. Its identity and any later Deploy exposure
remain unknown because traversal aborted. Original OCR confidence 0.5, zero
CGEvents/prompts and ordinary close 0 remain their observed separate scopes.

The fetched bar is Apple's AXError/AXUIElement SDK contract, Godot's pinned
Button documentation/implementation, and its pinned AccessKit macOS title
implementation. [API_RESEARCH.json](API_RESEARCH.json) retains immutable URLs,
full fetched byte hashes and line-numbered excerpts. Apple developer URLs were
denied with HTTP tunnel 403; the Apple declarations were retrieved through the
immutable SDK mirror already used by the original research. They distinguish
`kAXErrorNoValue = -25212` (the attribute does not have a value) from unsupported
attributes and failed messaging. Godot documents empty button text and AccessKit
returns an optional title. These facts permit an untitled button; they do not
identify the actual failing node or prove later native traversal will succeed.

## Minimal amendment

Only an AXTitle Copy returning exactly `-25212`, with a NULL output pointer and
a freshly checked AXButton role, may yield an empty title. Empty title already
normalizes to an empty string and cannot match the unchanged exact Deploy label.
Required window titles and all other attributes remain required. Success/NULL,
error/non-NULL, unsupported/cannot-complete/disabled/invalid errors, exceptions,
late returns, malformed strings, foreign owners and secure/text-entry roles
remain failures. A contradictory non-NULL Copy output remains owned and released.
No catch-all exception recovery, skipped subtree, synthesized label, alternative
attribute, new API, new permission request or event is introduced.

The existing complete traversal, exact unique role/label/enabled/frame/owner
selection, original OCR receipt and 0.8 gameplay gate remain unchanged. All
five-second/0.25-second, node/depth/byte/snapshot budgets remain exact. Controller,
AppKit helper, workflow, product, launch arguments and original source-preservation
fixtures stay byte-identical to d6cb78aa. No native, engine/import, OCR executable,
CI dispatch, service, integration or self-approval is authorized by this report.

## Measurable controls declared before code edits

1. A checked-in fake-native control must reproduce the exact original rejection
   at d6cb78aa and accept only the defined no-value/null/button case after repair.
2. The actual NativeAX adapter over fake C boundaries must still reject other
   errors, pointer contradictions, success/NULL, non-button no-value reads,
   role changes, late calls and changed owner/window geometry. Non-NULL Copy
   references must release exactly once on every error path.
3. The real bounded traversal must pass an untitled sibling before a nested
   exact Deploy button without pruning that sibling's children. Empty-title-only,
   wrong/duplicate/disabled/outside Deploy controls must reject selection. A later
   traversal error must retain the partial tree and fail the observation.
4. Retain and execute all R1/R2 maintained source and boundary controls, including
   counted Unicode/NUL rejection, original 0.8 OCR rejection and source preservation.
5. Freeze candidate source, then run the same pure commands from a fresh depth-one
   sparse checkout with exactly one reachable commit, no history dependency and
   clean final status. Pure checks are pinned to CPU 4. Keep all failed receipts.

Builder test results support a source-review handoff only. A fresh independent
critic and root decide any later diagnostic release; actual gameplay, full Mac
stability and all broader mission gates remain open.
