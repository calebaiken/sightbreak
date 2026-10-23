# Independent source review

Reviewer: `/root/freshness_builder/freshness_source_critic`, spawned with
`fork_turns: "none"`. It received the source task below, with no builder reports
or native comparison results. The review did not edit the candidate. Verbatim
review response follows.

Prefer candidate `8e10df0` over baseline `561d0cb` for this correction. No source-level blocker found.

- `staged.is_empty()` identifies batches containing only acknowledged commands. Rejection returns before `_input_rpc` renews the silence clock, lifecycle idle clock, or qualifying activity.
- Queued duplicates remain accepted because their sequences exceed the consumed acknowledgment. Existing queue entries stay immutable; consumption still advances one command per authority step.
- Resume remains intact: disconnect clears server acknowledgment, reconnect resets client sequence, and welcome enables fresh input that can retire the matching resume alias.
- Protocol 6, prediction opt-in, owner-only acknowledgments, authoritative simulation, and live rewind settings are unchanged. Stale replays lose their ability to extend reward-qualifying activity; reward rules and backend authorization are unchanged.

I independently ran these with the pinned Godot `4.7.2.stable.official.ed1daf0bf`:

| Check | Result |
|---|---|
| Candidate input stream | 22 checks, 0 failures |
| Baseline input stream | 17 checks, 0 failures |
| Peer lifecycle | 16 checks, 0 failures |
| State privacy | 55 checks, 0 failures |
| Movement prediction | 725 checks, 0 failures; maximum error 0.075834 m |
| Resume alias | 23 checks, 0 failures |
| Lost welcome | Valid fixture; same actor restored |

All processes exited 0. Logs are outside the checkout at `/tmp/sb-source-critic-724e-*.log`. Candidate HEAD remained `8e10df0b6508964fbe67a93629b0aa8b3ac86a00`, with a clean working tree.

The largest remaining deficiency is recovery during sustained snapshot loss. The client still fills its 120-command history and stops generating commands, while no connected-state snapshot timeout initiates earlier recovery. This correction prevents stale retransmissions from postponing the existing 30-second server idle expiry; it does not shorten that interval or improve frozen-state feedback.

I inspected no builder reports or native A/B results. This verdict covers source correctness and the focused checks above; it does not establish rendered, WAN, player-experience, or full-product acceptance.

## Retained task and logs

The [source-review task](SOURCE_CRITIC_BRIEF.txt) is retained. The actual seven
reviewer logs have been copied unchanged into `source-critic/` inside
[the evidence archive](evidence.tar.gz); their original temporary paths are not
the sole copy.
