"""Exclusive offline assessment and freeze. No native/DB/network/source/key access.
Reads fixed NEUTRAL and this audit's own artifacts; writes only new output files.
"""
import datetime
import hashlib
import json
import os
import pathlib
import stat

OUT=pathlib.Path(__file__).resolve().parent
PIN="746561c7caf5a57d53fcf52fca2d018cca4b044218ac6fa4190362eea7502021"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def write(name,s):
    with (OUT/name).open("x",encoding="utf-8",newline="\n") as f:
        f.write(s)

def put(name,x):
    write(name,json.dumps(x,sort_keys=True,indent=2,ensure_ascii=True)+"\n")

def main():
    assert not (OUT/"FROZEN.json").exists(), "Frozen output cannot be overwritten"
    d=json.loads((OUT/"verifier.raw.json").read_bytes())
    assert json.loads((OUT/"execution-status.json").read_bytes())["verifier_exit_status"]==0
    assert d["manifest_sha256"]==PIN
    all_checks=d["packet_checks"]+[q for c in d["cases"] for q in c["checks"]]+[q for a in d["retained_attempts"] for b in a["aborted_cases"] for q in b["checks"]]+[q for c in d["ancillary_controls"] for q in c["checks"]]
    assert all(q["consistent"] for q in all_checks)
    root=pathlib.Path(d["input_root"])
    for h in d["input_hashes"]:
        b=(root/h["path"]).read_bytes()
        assert sha(b)==h["sha256"] and len(b)==h["bytes"], "Input changed before freeze"
    assert {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}=={h["path"] for h in d["input_hashes"]}
    comparison={"original_receipt_recovery":{"decision":"winner","sample":"sample-8e3f9bc622","scope":"Retained original-client kill after commit/before delivery at prices 400, 401, 10000000 only; not a contemporaneous randomized experiment."},"economic_integrity":{"decision":"tie","scope":"One settlement/item transfer per measured purchase; no later economic mutation in either retained group."},"broader_reliability_source_safety_release":{"decision":"uncertain","approval":False},"per_price":[{"price":p,"original_receipt_recovery_winner":"sample-8e3f9bc622","economic_integrity":"tie","broader_reliability":"uncertain"} for p in [400,401,10000000]]}
    cases=[]
    for c in d["cases"]:
        yes=c["durable_original_receipt"]
        cases.append({"case":c["case"],"price":c["price"],"integrity_judgment":"Retained records internally consistent; unsigned capture only.","economic_judgment":"One original commit, exact fee accounting and unique item; no later economic mutation.","receipt_recovery_judgment":"Original receipt recovered in fresh process." if yes else "Original-receipt recovery failed in retained scenario; account/inventory refresh only.","evidence":{k:c[k] for k in ["identities","idempotency_key","operation_id","request_hash","fee_observed","seller_net","buyer_before","buyer_after","seller_before","seller_after","capture_start_utc","capture_end_utc","timeline_record_count","commit_before_kill_margin_ns","ordering_indexes","snapshot_economic_sha256"]},"actual_recorded_exits":[{"phase":r["phase"],"pid":r["pid"],"exit":r["returncode"]} for r in c["lifecycle"]],"uncertain_transaction_retention":{"journal_before_kill":c["journals"]["before-kill"]["exists"],"journal_after_kill":c["journals"]["after-kill"]["exists"],"original_receipt_retry_count":c["same_receipt_retry_count"],"journal_after_recovery":False,"journal_after_third_process":False,"initial_vs_replay_raw_response_identical":c["initial_vs_replay_raw_response_identical"],"user_visible_uncertainty":"Not established. Stored message says Transaction confirmed before initial response delivery; may be a future success template." if yes else "Not established; pending receipt absent."},"third_process_judgment":"Fresh session, no pending receipt or economic POST, economic state unchanged; not interrupted recovery.","limits":["One trial at this price, not three repeats.","No kill of recovering process; third process is a no-pending no-op check.","Unsigned author/harness capture; no independent wire/OS authentication.","No competing owner/concurrency, actual malformed-success, low-price fee boundary, or power-loss campaign.","Probe-invoked retry observed; autonomous production recovery/source-binary binding not established."],"consistency_checks":len(c["checks"]),"inconsistent_checks":c["inconsistent_checks"]})
    classifications={
      "attempt-0049a3f2f5":("preflight_failure","Occupied native slot, recorded exit 1; prose says no DB/native created. Not a concurrency or competing-owner experiment."),
      "attempt-0664d7063a":("aborted_startup_barrier_failure","Upstream response barrier not reached, completed_run_record_count 0; aborted native exit 1. Initial SQL, fixture and three events only; no post-state/recovery."),
      "attempt-637d22fb26":("aborted_startup_barrier_failure","Upstream response barrier not reached, completed_run_record_count 0; aborted native exit 1. Initial SQL, fixture and three events only; no post-state/recovery."),
      "attempt-67c8ac3b15":("preparation_database_availability_diagnostic","Import/preparation, server-start then no-server records. DB log: recovery, ready, child exception 0xC0000142, shutdown. Not a measured transaction restart; no native exit inferred."),
      "attempt-a5efb1a60a":("preparation_only","Import/preparation output; no measured transaction outcome or process exit established."),
      "attempt-b159051dc1":("resource_preflight_failure","Out-of-memory diagnostic; tasklist returned exit 1. Not a completed measured application runtime."),
      "attempt-b1962c484d":("aborted_startup_barrier_failure","Upstream response barrier not reached, completed_run_record_count 0; aborted native exit 1. Initial SQL, fixture and three events only; no post-state/recovery."),
      "attempt-c4ee620acf":("controller_compile_failure","SystemError: built-in compile returned NULL without exception; recorded exit 1, completed_run_record_count 0. Not an application recovery failure."),
      "attempt-c9da1ca161":("author_summary_only","Three recovered=True/authoritative_pass=True lines do not add verified cases or repeats; no pairing to sample identities inferred."),
      "attempt-cb5280e303":("aborted_startup_barrier_failure","Upstream response barrier not reached, completed_run_record_count 0; aborted native exit 1. Initial SQL, fixture and three events only; no post-state/recovery."),
      "attempt-ce66957a7b":("resource_window_failure","Resource window unavailable after 20 minutes; PID/free-memory preflight text only. No measured transaction or numeric process exit invented."),
      "attempt-e4716456d0":("transcribed_cache_preflight_failure","Transcribed mismatched cache/game tree, exit 1, no DB/native measurement. Source identifiers not mapped; later success claim does not pass this attempt."),
      "attempt-f50f658b95":("startup_pipe_diagnostic","Probe active before pipe drain, exit 0 after communicate; probe ready. Not transaction/restart recovery or proof of all earlier failure causes.")}
    attempts=[]
    for a in d["retained_attempts"]:
        kind,note=classifications[a["attempt"]]
        attempts.append({"attempt":a["attempt"],"classification":kind,"judgment":note,"recorded_status":a["status"],"aborted_cases":a["aborted_cases"],"evidence_files":a["files"],"diagnostic_excerpts":a["diagnostic_excerpts"],"sample_assignment":"not inferred"})
    put("CASE_JUDGMENTS.json",{"manifest_sha256":PIN,"comparison":comparison,"cases":cases})
    put("RETAINED_ATTEMPTS.json",{"attempts":attempts,"database_resume":{"record":d["database_resume_record"],"judgment":"Status return 3/no server, then start return 0 and health response: recorded availability/setup only, not another transaction recovery or power-loss test."},"audit_process_interruptions":json.loads((OUT/"prior-audit-attempt.json").read_bytes()),"interruption_classification":"Harness disk I/O and offline checker/bootstrap syntax errors are audit tooling events, not application runtime failures. Prior artifacts retained untouched."})
    put("ANCILLARY_CONTROLS.json",{"controls":d["ancillary_controls"],"judgment":"Unchanged port-9 oracle 36/37, exit 1 remains failed. Altered reserved-DNS oracle 37/37, exit 0 is a different unmatched condition; cannot replace original failure or compare samples."})
    put("SOURCE_HASHES.json",{"scope":"All 178 neutral payloads plus pinned manifest; source means evidence inputs. Application/repository/engine source hashes not consulted or verified. Verifier source hash appears in execution status and output SHA ledger.","input_root":str(root),"manifest_sha256":PIN,"files":d["input_hashes"]})
    write("SOURCE_HASHES.sha256","".join(h["sha256"]+"  NEUTRAL/"+h["path"]+"\n" for h in d["input_hashes"]))
    rows=[]
    for c in d["cases"]:
        pids=" / ".join(str(r["pid"]) for r in c["lifecycle"])
        outcome="Original journal + exact replay; original receipt returned" if c["durable_original_receipt"] else "No journal/replay; empty result; account refresh only"
        rows.append(f"| `{c['case']}` | {c['price']:,} | {c['fee_observed']:,} | {c['seller_net']:,} | {outcome} | {pids} | 1 / 0 / 0 |")
    failure_lines="\n".join(f"- `{a['attempt']}`: **{a['classification']}**. {a['judgment']}" for a in attempts)
    n=sum(len(c["checks"]) for c in d["cases"])
    report=f"""# Frozen neutral recovery verdict

## Outcome

**Original-receipt recovery winner within the retained scenarios: `sample-8e3f9bc622`. Economic integrity: tie. Broader reliability, source safety and release readiness: uncertain. No release approval.**

At each retained price (400, 401, 10,000,000), the winning group preserves the original pending transaction across the initial native-client kill, launches a fresh authenticated process, posts the same original body/key/path, receives the semantically identical committed receipt and clears its journal. The other group has no retained pending journal, issues no original-receipt retry and returns an empty transaction result while refreshing the settled account/inventory. That is failed receipt recovery in this scenario, not double spending or a crashing recovery process.

This ranks stored outcomes, not general reliability or causal improvement. There is **one trial per price per group**, not three repeats per price. Arms are non-contemporaneous: `sample-ccaee51fd6` was captured 2026-10-19 local; `sample-8e3f9bc622` on 2026-10-22 local (2026-10-23 UTC). No identity key was requested or read, and no mapping is inferred.

## Integrity and method

- Pinned manifest SHA-256: `{PIN}`.
- All **178 payloads / 903,364 bytes** match declared SHA-256 and lengths. Exact inventory: **179 files including the separately pinned manifest**, no missing/unlisted files. All declared JSONL record counts match.
- Offline Python 3.13.15 verifier exit status 0; no inconsistent factual comparisons: **192 packet, {n} complete-case, 12 aborted-case, 2 ancillary tally/exit checks**. These are capture-consistency checks, **not invented acceptance gates or product pass counts**. Consistent records can establish a failed recovery.
- All 30 complete-case economic-state hashes and four aborted before-state hashes reproduce from retained JSON. Snapshot backend/database metadata agrees with timeline entries. All neutral inputs were re-hashed immediately before freeze.
- `SOURCE_HASHES.*` identifies neutral evidence inputs, not application source. Source code, repository hashes/identities, engine/cache binaries, executed-source bindings and private archives were not inspected or certified. README claims about those outside materials remain unverified by this audit.
- Raw verification output, verifier source, per-case judgments, distinct failures, input hashes and artifact ledger are retained alongside this report.

## Per-case judgments

All six cases have internally consistent recorded commit/kill sequences, one economic settlement and unchanged economic state after the kill, recovery and third process. PIDs/exits are **retained observations**, not processes run by this auditor. PID/exit order: killed initial client / recovery / third process.

| Neutral case | Price | Fee | Seller net | Receipt recovery outcome | Native PIDs | Exits |
|---|---:|---:|---:|---|---|---|
{chr(10).join(rows)}

The buyer starts at price + 1,600 and ends at 1,600. The seller starts at 2,000 and ends at 2,388 / 2,389 / 9,702,000 respectively in both groups. Original item, listing, actor/account, key, operation and request-hash identities remain explicit per case in `CASE_JUDGMENTS.json`; none is substituted from another trial.

## Retained transaction evidence

1. **Commit before kill, not just a status flag.** Each timeline records the original integer-price HTTP POST, upstream 200, hold before any client headers, PostgreSQL snapshot already containing settlement, kill request, native exit 1, kill acknowledgement, post-kill snapshot and discarded held response. Commit visibility precedes the kill request and acknowledgement. No original-buy response-delivered event exists; hold/kill/discard records each report zero bytes. SQL snapshot clocks, backend IDs, economic hashes and exact rows corroborate ordering within the capture.
2. **Original request/receipt lineage.** Operation ID is buyer:buy:listing:original-key. Its request hash reproduces from the raw request body and compact sorted JSON. Winning replay uses the byte-identical raw integer-valued body, same method/path/key and original pending owner/server. Initial HTTP success, operation response, replay response and native recovered result are semantically equal. Raw response property order differs on replay; that is not malformed success. Native console integral floats do not change the raw HTTP request's verified integer type.
3. **Account and actor ownership.** All three authentications match fixture buyer, login player ID, `/me`, native owner and database session owner. Three distinct token hashes bind native authentication, proxy requests and newly added sessions. Tokens are redacted, so these hashes are correlated, not re-derived from secrets. Seller, settlement actor, listing buyer, ledger players and unique item owner agree. This does not test a competing owner.
4. **Exact economics.** Relative to each case's own before state, only buyer/seller credits, one item's owner/reservation and one listing's buyer/state change; exactly two ledger rows, one settlement audit and one operation receipt are added. Other published economic rows are unchanged. Buyer debit is price, seller credit price minus fee; player and added-ledger sums decrease by exactly fee. Fees 12 / 12 / 300,000 match floor(3% of price) on these values. No fee-recipient account is captured: this is conservation with the recorded fee sink, not a verified external fee transfer. Item IDs remain unique; no new item mint, consumption or second settlement appears.
5. **Fresh processes and third-process boundary.** Three distinct native PIDs per case are non-overlapping in lifecycle records, with no other native PID reported at launch. Recovery/third process exit 0 with matching account/inventory. Winning raw journal bytes survive the kill, match their hashes, contain original owner/server/path/method/body/key without credential fields, load as pending in recovery, then disappear after receipt success. The third process has no pending receipt, economic POST or economic mutation. New login sessions are DB mutations; only the nine economic tables are unchanged.

## Limitations

- These are **unsigned author/harness captures**. Sent-byte flags, process starts/exits, SQL files and service logs corroborate one another as retained records; they are not independently signed wire/OS traces. Hashes bind this neutral derivative, not historical capture truth. No live native engine, database, service, network, source repository, parent report, private archive or identity key was accessed.
- Winning pending-transaction retention is supported; a correctly displayed **uncertain/unconfirmed user-visible state is not established**. The journal message already says `Transaction confirmed.` before initial response delivery. It may be a future success template. No rendered UI evidence resolves that; neither a UI pass nor a premature-confirmation failure gate is invented.
- Only the **initial client** is killed. Recovery is probe-invoked in retry mode and finishes normally. Third launch is a no-pending no-op check, **not** a second interrupted recovery, twice replaying the same pending receipt or proof of autonomous production recovery. No recovering-client kill, mid-replay kill, interrupted journal clear, power-loss/durable-flush or server-crash campaign is captured.
- No contemporaneous randomized order, matched resource/environment campaign or repeats per price exist. Fixture/history sizes, service logs and resource histories differ. The narrow recorded outcome can be ranked; general comparative reliability/causality cannot.
- No competing-owner/concurrent PostgreSQL buyer campaign, actual malformed-success injection, wrong-owner/wrong-server attempt or low-price zero-to-one fee-boundary trial is retained. Price 401 shows ordinary fractional 3% rounding, **not** a minimum-fee boundary. Ancillary labels do not fill missing interruption/concurrency/malformed-success/low-price coverage.
- Nine economic tables plus sessions are captured; operational rate buckets/game tickets, filesystem durability, source/binary bindings and unobserved subsystems are outside scope. Empty stderr/exit 0 do not prove universal correctness. Journal server matches the fixture's proxy endpoint; actual upstream configuration is not independently authenticated.

## Distinct retained failures and controls

Later successes do not turn these observations into passes. Opaque attempts are not assigned to sample identities.

{failure_lines}

The separate database-resume record has status return 3 (`no server running`), followed by start return 0 and a health tuple. This is recorded availability/setup only, not another transaction recovery or power-loss test.

`control-0e86e53e33` is **36/37, native exit 1**, with the unreachable-server/unconfirmed-balance error: it remains failed. `control-962ec4ee70` is **37/37, native exit 0** under an externally altered reserved `.invalid` DNS condition instead of port 9. This is a different unmatched oracle, not replacement of the original failure, not 74 independent cases and not a between-sample comparison. Neither was rerun.

The user-reported previous harness disk-I/O interruption is an **audit tooling interruption**, not a completed review/application runtime failure. An earlier timestamped offline verifier syntax-validation failure is retained and hash-referenced in `prior-audit-attempt.json`. A later assessment-bootstrap quoting error occurred before any new file was written and is recorded in `audit-tooling-notes.json`. Neither executed an application. No prior artifact was overwritten.

## Frozen meaning

The timestamped `FROZEN.json` is created after this report, judgments, verifier source/raw output, evidence hashes and `SHA256SUMS` exist. It pins the input manifest and artifact ledger, states the key was not requested/read and gives no approval. Final files are marked locally read-only and not subsequently edited by this auditor. This is **tamper-evident local freezing**, not hardware immutability, a trusted third-party timestamp or a digital capture signature. The receipt's own SHA-256 is returned separately to avoid a circular self-hash.

**Final: retained original-receipt recovery winner `sample-8e3f9bc622`; economic integrity tie; broader reliability/source safety/release uncertain. No release approval.**
"""
    write("REPORT.md",report)
    put("AUDIT_SUMMARY.json",{"comparison":comparison,"manifest_sha256":PIN,"packet_checks":len(d["packet_checks"]),"case_checks":n,"aborted_checks":12,"ancillary_checks":2,"inconsistent_checks":0,"inputs_rehashed_before_freeze":True,"neutral_payloads":178,"input_files_including_manifest":179,"retained_attempt_groups":len(attempts),"application_runtime_executed":False,"identity_key_requested_or_read":False,"approval":False})
    artifacts=[]
    for p in sorted(OUT.iterdir(),key=lambda x:x.name):
        assert p.is_file() and not p.is_symlink()
        b=p.read_bytes()
        artifacts.append({"path":p.name,"bytes":len(b),"sha256":sha(b)})
    ledger="".join(h["sha256"]+"  "+h["path"]+"\n" for h in artifacts)
    write("SHA256SUMS",ledger)
    frozen={"status":"FROZEN","frozen_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"manifest_sha256":PIN,"input_root":str(root),"artifact_ledger":"SHA256SUMS","artifact_ledger_sha256":sha(ledger.encode()),"artifact_count_excluding_ledger_receipt":len(artifacts),"artifact_hashes":artifacts,"comparison":comparison,"identity_key_requested_or_read":False,"approval":False,"method":"Exclusive creation, pinned ledger, local read-only final files; no later edits by auditor.","limits":"Unsigned local timestamp/hash receipt; tamper-evident, not hardware immutability or independent historical capture authentication. No native/DB/network/source/key access."}
    put("FROZEN.json",frozen)
    for p in OUT.iterdir():
        os.chmod(p,stat.S_IREAD)
    print(json.dumps({"output":str(OUT),"frozen_utc":frozen["frozen_utc"],"FROZEN_sha256":sha((OUT/"FROZEN.json").read_bytes()),"SHA256SUMS_sha256":frozen["artifact_ledger_sha256"],"REPORT_sha256":sha((OUT/"REPORT.md").read_bytes()),"CASE_JUDGMENTS_sha256":sha((OUT/"CASE_JUDGMENTS.json").read_bytes()),"verifier_source_sha256":sha((OUT/"verifier.py").read_bytes()),"verifier_raw_sha256":sha((OUT/"verifier.raw.json").read_bytes()),"SOURCE_HASHES_sha256":sha((OUT/"SOURCE_HASHES.json").read_bytes()),"artifact_count":len(artifacts)+2,"comparison":comparison},indent=2))

if __name__=="__main__":
    main()
