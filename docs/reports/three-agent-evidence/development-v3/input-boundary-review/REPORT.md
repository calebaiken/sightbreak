# Input boundary review: post-freeze source binding

## Bounded conclusion

The separately frozen neutral result now binds to exact recorded component sources:

| Neutral label | Verified source commit | Recorded fully ACKed replay return |
| --- | --- | --- |
| sample-bd249c | `f3ceaad98e089aa393c7f5fa650a52695094d979` | false, rejected counter increments |
| sample-05ec6c | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | true, no rejection increment |

The added empty-staging guard in the former source explains the narrow component distinction while preserving queued/unACKed retries. Both retain original queued movement/fire payloads and later new sequence 3. This does **not** establish a full-network win, actual Match/timer/actor behavior, PR20 integration, gameplay acceptance or release approval. The separate large-network packet key and verdict are outside this follow-up; neither was opened or changed.

The original independent component freeze remains byte-exact under `critic-neutral/`; this document is an explicitly post-freeze addendum, not a rewritten blind verdict. The main-author neutral assessment is separately preserved and is not counted as independent QA.

## Frozen-before-key boundary

Before opening/printing component source-key contents, I rehashed the independent component `FROZEN.json`, report and ledger against the supplied full pins, verified all 37 critic ledger payloads, and verified both files bound by the main-author freeze:

- Main recorded freeze: **2026-10-23 01:05:20.506667 UTC**; `MAIN_NEUTRAL_FREEZE.json` SHA256 `c2c2d24bed297c4166137166b0d13f80dbd279f2ab7b5ee438bb5d36a4a68d21`; its assessment SHA256 `19a195c9661eb958be3968162ec73df130eb04184feb9a76dd9d1e94eca42dfb` and r3 RESULTS hash both match.
- Independent critic recorded freeze: **2026-10-23 01:12:49.902292 UTC**; FROZEN `d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78`; report `cff57e331635ec0c3d2f65398f6fd4bf83ee339090211c3a2df75c19e3b0c51a`; ledger `446cbfd2dc80ab913212776b6f4024b425cb8669f55c891be03f8397f39ac2db`.
- This review's both-freezes rehash receipt records **01:18:07.597537 UTC**, followed by component source-key inspection. The exact receipt is in `review-audit/both-neutral-freezes-verified-before-key.json`.

These are **local unsigned records**, not a trusted timestamp, signed execution attestation or proof of historical human behavior. The source-key JSON itself has hashes but no trusted creation timestamp. The exact driver writes it before its import/probe loops; that is source-order evidence, not cryptographic proof of launch chronology. Source identity blinding ended only for this tiny component after the freeze boundary. Behavioral blinding was never complete: visible return values expose the behavior under comparison, and the critic already had unrelated large-packet neutral outcome context without its identity key.

## Exact source binding and engine custody checks

I verified all **12 module instances** across all six prepared projects in r1/r2/r3. For each, commit:path bytes from Git, Git blob identity (also recomputed as SHA1 over the Git blob header/content), recorded SHA256 and current retained project bytes match exactly. No parent commit, branch source, broader identity map or unprovided controller/release source was read.

| Production module | Ref(s) | Blob | SHA256 |
| --- | --- | --- | --- |
| input_stream.gd | f3ceaad… | `f0516be1ab2416d36ba3b62f37083f371364f3a4` | `b455205d827134830637f03457cc67e4e321721d91a7d840941fc74e1b26c88e` |
| input_stream.gd | 701ce2c… | `7b4cf13453a15988bb1281e49e0b6eb3835461e5` | `60d92e1cacc838867f9241379cbf3bc8b27a025fd1b91ca191effc37354d7ccc` |
| input_gate.gd | both | `bf23a5b8c6e634121fca9f5daeb2a4d731ff6538` | `4717f892f56d0f5e70aeb321454a986c714be74f150b907f77a90ed380e23c77` |

The production paths are `game/scripts/network/input_stream.gd` and `game/scripts/network/input_gate.gd`; exact bytes are included for both refs. Each attempt's retained probe/config and original driver snapshot also match its source-key hashes. R3 root `run.py` is `b1815f26b57d9169067e6e04c06a132a066deda7baf4f310be1632309f2f6162`; r3 probe is `cb03f812bc765ab996a36768915874bc8ce2c64968f15a11850c77c74cb9b563`; configuration is `5fff83ac9be6b9f4aa57d5830a7c9bb43e767028fe61cff56f08c6a041012d7e`.

The retained projects now match the recorded pre-launch hashes. The driver explicitly checks production-module and probe hashes after each completed project. It does not explicitly post-check config; this review independently checked its retained bytes against the recorded config hash. These comparisons support unchanged retained bytes, not absolute authenticated historical execution.

I independently streamhashed **180,858,888 bytes** of the actual recorded engine executable without running it: SHA256 `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`, matching all three source records. Static PE version-resource inspection gives file/product version **4.7.2.0**. The full recorded version `4.7.2.stable.official.ed1daf0bf` agrees with retained engine-log banners; the build suffix was not independently obtained by executing `--version`. The executable is excluded from publication.

The producer imports `matrix_process.run_process` and `native_log.failed` from outside the permitted producer root. Those helper sources were not provided for inspection and were not read or included. Their internals, actual OS command-line capture and root-runner exit status are not authenticated by this source binding. Producer command recipes are reconstructed from exact driver source and separately labeled; actual reviewer Python/Git read commands are recorded without pretending the recipe is an OS receipt.

## Why the source explains the two returns

Both InputStream versions stage every sanitized command whose sequence exceeds ACK. They validate/sanitize even ACKed commands before filtering them out, so an old malformed fire string is not silently exempted. They only insert a staged sequence if it is not already in the queue, preserving the first queued original payload.

The f3ceaad version then checks `staged.is_empty()` at lines 38-40, increments rejection and returns false. The 701ce2c version lacks that guard and returns true after an empty insertion loop. Thus:

- Fully ACKed sequences 1/2 at ACK2 have no staged fresh work: false only with the new guard.
- A still-queued sequence above ACK is staged even if already queued: a legitimate queued/unACKed retry remains true and cannot rewrite its first payload.
- A mixed ACKed/new batch stages sequence3, so it remains accepted.

The recorded component data independently show this distinction for identical and altered replays. Both variants have the same queue/ACK/rate transitions in this fixture; only the two replay return values and resulting rejection-counter offset differ. The narrow component signal advantage is not converted into a throughput/latency or gameplay claim.

## Match call-site inference — source only

The actual permitted path is `game/scripts/gameplay/match.gd`. Its full Git blob is **identical across both refs**, `c06f7b4177a40819fa44eee6ee678c3958fce752`. Only exact lines **986-1011** are semantically reviewed/published, with full-file hash/blob identity recorded in `SOURCE_BINDING.json`.

At 997-998, `_input_rpc` returns when `_input_stream.accept(...)` is false. That early return precedes:

- `_peer_lifecycle.active(...)` at 999;
- alias confirmation logic at 1002-1006;
- the **conditional** `_last_activity[id] = _elapsed` at 1009-1010;
- `_last_peer_input[id] = _elapsed` at 1011.

Therefore, if this RPC reaches the accept call and returns false, it skips those subsequent updates on that invocation. `_last_activity` must not be described as an unconditional update on true: its movement/look/interaction predicate still applies. Prior guards, including `_peer_lifecycle.allow_input` at 991, execute before accept; their internal side effects were not reviewed here. This is not proof that no other path can affect lifecycle/activity.

The RPC expects an unreliable-ordered compressed packet, enforces packed-size bounds and performs DEFLATE decompression before accept. The component instead directly calls `var_to_bytes` / `bytes_to_var` and `stream.accept`. **No Match instance, RPC dispatch, timer, lifecycle expiry, network socket, 300 ms silence deadline, 30 s retirement or physical actor was executed in this component.** The call-site link is source inference only.

## The actual 21 checks and 22 serialized instances

The exact r3 probe has 21 check calls. I matched the first 20 predicates independently to each sample's full raw event data. The two fully ACKed accept results at probe lines 68 and 70 are deliberately **not asserted**; checks 11/12 only assert ACK2 plus an empty queue. Consequently both can report 21/0 without equal accept-return behavior. The source comment explicitly describes the compared outcome as recorded rather than prescribed.

The 21st check (83-84) calls `stream.forget(41)` directly and asserts absence of peer41 in queues, ACKs and rates. No after-forget state event was retained, so its runtime evidence is the aggregate 21/0 plus source; it is not an independently traced cleanup event. `forget` erases three stream-owned map entries, not an actor or network session. The earlier neutral limitation “no disconnect evidence” remains correct for live disconnect/timers; this addendum adds the now-visible **component-unit forget assertion** without rewriting the old verdict.

The exact input-gate module is bound, but this probe/InputStream uses its `BOOLEAN_FIELDS` constant; `InputGate.validate` and `allow_buy` are not exercised by these calls. Backlog dropping (>6 commands), rate threshold (>90 calls), bucket rollover (>=1000 supplied ms), exact +120 acceptance and extensive malformed/type/epoch combinations are source policies, not newly proven native boundaries here. The +121 rejection and malformed-old-first packet are useful but do not prove all adjacent limits or general batch atomicity.

I rechecked all **22 serialized packet instances / seven unique byte strings** using only the bounded Python Decoder class from the frozen critic script, isolated with AST so no frozen top-level code runs or rewrites anything. All bytes fully decode, match JSON payloads and roundtrip exactly with preserved types. This is a narrow decoder for observed unflagged types, not a full protocol/compression/fuzz audit.

Both samples consume exactly sequences1/2/3 with movement +1/+1/-1 and fire true/false/true, then an empty pop. Those are payloads, not actor shots/ammo or physical movement. Both charge their rate bucket on all 11 accept attempts, including rejected attempts; final start/count is1000/11. Supplied rate times span600ms, while retained capture timestamps span only2ms per process. These clocks neither test a production inactivity origin nor establish a wall-time performance comparison.

## Failures preserved, not rerun or erased

| Attempt | Retained facts | Interpretation |
| --- | --- | --- |
| r1 (`attempt`) | Original driver snapshot/key/projects; FAILED contains `WindowsPath` has no `fileno`; no import/probe result/log receipts | Driver passed a Path instead of an open log handle and failed at the pre-import process API boundary. No import/probe execution is established. The driver's earlier `--version` preflight is separate; do not claim no native invocation of any kind historically. |
| r2 | Original driver/probe copies; import/probe receipts complete/exit0; stdout logs both zero bytes; FAILED is missing/ambiguous summary | Failed closed despite zero phase exits. A GUI/root exit0 cannot stand in for native summary evidence. No separately retained root-driver OS-exit receipt or full helper stack is available here. |
| r3 | Nonempty explicit `--log-file` engine logs for both phases/two samples; exit0 phase receipts; one summary each; separate project `probe-result.json` matches engine JSON and neutral result core | Successful retained component measurements with substantially better completion evidence. Still unsigned, not an authenticated OS execution attestation. |

No failed attempt is reclassified as an engine defect or silently dropped. The reviewer also retains an initial failed Git path lookup (assumed `game/scripts/match.gd`, exit128); a filename-only tree lookup found the permitted gameplay path, and both refs were reverified. The original critic's own count-assertion failure remains preserved in its unchanged frozen packet. No producer run or native rerun was performed during this follow-up.

## Publication, omissions and remaining gates

This publication copies **all 67 noncache producer files**, including all three attempt source keys, original failure scripts/receipts, exact modules/probes/configs, UID sidecars, r3 raw/persisted results and both main neutral-freeze files. It also preserves the complete 40-file frozen independent component packet. `ORIGINS.json` and the final ledger bind originals to copies. All 19 generated cache files (71,309 bytes) under `.godot`/`.state` are precisely indexed as omissions without inspecting/hashing their contents. The engine, unprovided helpers, full Match body outside the allowed excerpt and broader PR20/large-packet material are excluded with explicit reasons in `OMISSIONS.json`.

All payloads remain below the requested 3MiB limit. Local `.gitattributes` unsets text conversion, filter, ident and working-tree encoding; `git check-attr` confirms all four are unset for a nested binary payload. There is no staging, commit, GitHub action, network, service, database or engine run. Repository writes are exclusively this new `docs/reports/three-agent-evidence/development-v3/input-boundary-review/` subtree. Original evidence and old frozen verdicts are not modified.

The ledger covers every payload; FROZEN binds the ledger and its complete entry list, and the separate checksum binds FROZEN without a self-hash cycle. Exact whole-file-set verification after copying to the repository is externally recorded before handoff. Freeze times/hashes are local custody aids, not trusted time/authenticity claims.

**Protocol6, prediction default-off, rewind-off and all human/device/authority/privacy/full-integration gates remain.** The source-bound conclusion is limited to the two return values, their preservation controls, exact retained source identity and the static RPC early-return link. It does not independently prove PR20 integration or a full-network outcome; the separate large-packet key remains awaited and unopened here.
