#!/usr/bin/env python3
"""Read-only exact-source collector facts; does not certify coverage or gameplay."""
import argparse, collections, csv, hashlib, json, math
from pathlib import Path

MARKER=b"SIGHTBREAK_INPUT_OBSERVATION "
TOP=set("schema scope role reason index wall_unix_msec wall_msec process_frames physics_frames drawn_frames connection_state transport_status transport_id local_id local_attempt peer bound_actor last_bound_actor peer_bound generation joined input_age_msec deadline_remaining_msec simulation_tick authority_epoch stream_ack queue_count stream_rejected stream_skipped prediction_epoch prediction_sequence pending_count pending_oldest_sequence pending_newest_sequence snapshot snapshot_age_msec local_input physical counters latest actor".split())
CONTROL=set("sequence fire reload move".split())
PACKET=set("epoch count first last fire reload moving wall_msec".split())
HEADER=set("tick epoch own_ack".split())
ACTOR=set("id alive ammo reserve reload input".split())
PHYSICAL=set("r lmb physical_mouse_fire application_focused paused waiting_for_input_release".split())
COMMON={"ready"}
AUTH=COMMON|set("authority_tick input_consumed peer_connected peer_bound peer_expired peer_disconnected input_gate_rejected input_decode_rejected input_received input_stream_rejected input_accepted".split())
CLIENT=COMMON|set("client_attempt client_connected client_connection_failed client_disconnected client_tick input_send_called welcome_received snapshot_schema_rejected snapshot_order_rejected snapshot_applied".split())
PACKETS={"input_send_called","input_received","input_accepted","input_stream_rejected"}
HEADERS={"snapshot_applied","snapshot_schema_rejected","snapshot_order_rejected","welcome_received"}
INT_TOP=TOP-set("scope role reason connection_state peer_bound joined snapshot local_input physical counters latest actor".split())

def isint(v): return type(v) is int

def finite(v): return type(v) in (int,float) and math.isfinite(v)

class Audit:
    def __init__(self): self.counts=collections.Counter(); self.failures=[]
    def check(self,key,ok,where,detail=None):
        self.counts[(key,"PASS" if ok else "FAIL")]+=1
        if not ok: self.failures.append({"predicate":key,"where":where,"detail":detail})
    def controls(self,v,where):
        self.check("control_exact_keys",isinstance(v,dict) and set(v)==CONTROL,where)
        if not isinstance(v,dict): return
        self.check("control_sequence_integer",isint(v.get("sequence")),where)
        self.check("control_buttons_boolean",all(type(v.get(x)) is bool for x in ("fire","reload")),where)
        move=v.get("move")
        self.check("control_move_two_finite_numbers",isinstance(move,list) and len(move)==2 and all(finite(x) for x in move),where)
    def record(self,r,where):
        self.check("top_exact_keys",isinstance(r,dict) and set(r)==TOP,where,{"missing":sorted(TOP-set(r)) if isinstance(r,dict) else sorted(TOP),"unknown":sorted(set(r)-TOP) if isinstance(r,dict) else []})
        if not isinstance(r,dict): return
        self.check("integer_top_fields",all(isint(r.get(k)) for k in INT_TOP),where)
        self.check("schema_scope",r.get("schema")==1 and r.get("scope")=="debug_guest_loopback_input_observation",where)
        role=r.get("role"); reasons=AUTH if role=="authority" else CLIENT if role=="client" else set()
        self.check("role_literal",role in ("authority","client"),where)
        self.check("reason_role_source",r.get("reason") in reasons or (r.get("reason")=="observation_limit" and r.get("index")==1024),where,r.get("reason"))
        self.check("index_source_cap",isint(r.get("index")) and 1<=r["index"]<=1024,where)
        self.check("top_boolean_fields",all(type(r.get(k)) is bool for k in ("peer_bound","joined")),where)
        self.check("connection_state_literal",r.get("connection_state") in ("offline","hosting","connecting","joining","authenticating","connected","reconnecting","failed"),where)
        self.check("binding_boolean_source",r.get("peer_bound")== (r.get("bound_actor",0)>0),where)
        self.controls(r.get("local_input"),where+".local_input")
        phys=r.get("physical")
        self.check("physical_projection",isinstance(phys,dict) and {"r","lmb"}<=set(phys)<=PHYSICAL and all(type(x) is bool for x in phys.values()),where)
        actor=r.get("actor")
        self.check("actor_projection_keys",isinstance(actor,dict) and (not actor or set(actor)==ACTOR),where)
        if isinstance(actor,dict) and actor:
            self.check("actor_value_types",all(isint(actor.get(k)) for k in ("id","ammo","reserve")) and type(actor.get("alive")) is bool and finite(actor.get("reload")),where)
            self.controls(actor.get("input"),where+".actor.input")
            expected=r.get("last_bound_actor") if role=="authority" else r.get("local_id")
            self.check("actor_selected_source",actor.get("id")==expected,where,{"actor":actor.get("id"),"expected":expected})
        counters=r.get("counters")
        self.check("counter_role_keys_values",isinstance(counters,dict) and set(counters)<=reasons and all(isint(v) and v>0 for v in counters.values()),where)
        if isinstance(counters,dict) and r.get("reason")!="observation_limit":
            self.check("printed_reason_has_hook_counter",counters.get(r.get("reason"),0)>0,where)
        snapshot=r.get("snapshot")
        self.check("snapshot_projection",isinstance(snapshot,dict) and (not snapshot or set(snapshot)==HEADER|{"wall_msec"}) and all(isint(v) for v in snapshot.values()),where)
        latest=r.get("latest")
        latest_allowed=(PACKETS|HEADERS|{"input_consumed"})&reasons
        self.check("latest_role_slots",isinstance(latest,dict) and set(latest)<=latest_allowed,where)
        if not isinstance(latest,dict): return
        for k,v in latest.items():
            at=where+".latest."+k
            keys=PACKET if k in PACKETS else HEADER|{"wall_msec"} if k in HEADERS else CONTROL|set("peer actor generation wall_msec".split())
            self.check("latest_exact_projection",isinstance(v,dict) and set(v)==keys,at)
            if not isinstance(v,dict): continue
            integer_keys=keys-CONTROL if k=="input_consumed" else keys
            self.check("latest_integer_metadata",all(isint(v.get(x)) for x in integer_keys),at)
            self.check("latest_not_future",isint(v.get("wall_msec")) and v["wall_msec"]<=r.get("wall_msec",-1),at)
            if k=="input_consumed": self.controls({x:v.get(x) for x in CONTROL},at)
            elif k in PACKETS:
                self.check("packet_count_projection",all(isint(v.get(x)) and v[x]>=0 for x in ("count","fire","reload","moving")) and all(v.get(x,0)<=min(v.get("count",0),12) for x in ("fire","reload","moving")),at)
                # first/last are original array endpoints. No ordering predicate.
        applied=latest.get("snapshot_applied")
        if isinstance(applied,dict):
            self.check("snapshot_last_applied_header",snapshot=={x:applied.get(x) for x in HEADER|{"wall_msec"}},where)
            self.check("snapshot_age_source",r.get("snapshot_age_msec")==r.get("wall_msec",0)-applied.get("wall_msec",0),where)
        else: self.check("snapshot_uninitialized_source",snapshot=={} and r.get("snapshot_age_msec")==-1,where)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("raw_root",type=Path); ap.add_argument("--out",type=Path,default=Path(__file__).parent); args=ap.parse_args()
    raw=args.raw_root.resolve(); out=args.out.resolve(); audit=Audit(); inventories=[]; streams=[]; allrows=[]; parse_failures=[]; exact_lines=collections.defaultdict(list)
    files=sorted(p for p in raw.rglob("*") if p.is_file() and (p.suffix.lower() in (".log",".stdout",".stderr",".txt") or "stdout" in p.name.lower() or "stderr" in p.name.lower()))
    for path in files:
        content=path.read_bytes(); rel=str(path.relative_to(raw)); rows=[]; occurrences=0
        for line_no,line in enumerate(content.splitlines(),1):
            if MARKER not in line: continue
            occurrences+=1; where=f"{rel}:{line_no}"
            if not line.startswith(MARKER):
                audit.check("observation_prefix_at_line_start",False,where,{"line_sha256":hashlib.sha256(line).hexdigest()}); continue
            try:
                r=json.loads(line[len(MARKER):].decode("utf-8"),parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            except (ValueError,UnicodeError) as e:
                parse_failures.append({"file":rel,"line":line_no,"error":str(e),"line_sha256":hashlib.sha256(line).hexdigest()}); continue
            audit.record(r,where)
            if not isinstance(r,dict): continue
            record={"file":rel,"line":line_no,"ordinal":len(rows)+1,"data":r}; rows.append(record); allrows.append(record)
            exact_lines[hashlib.sha256(line).hexdigest()].append(where)
        inventories.append({"file":rel,"bytes":len(content),"sha256":hashlib.sha256(content).hexdigest(),"line_count":len(content.splitlines()),"ends_newline":not content or content.endswith(b"\n"),"marker_occurrences":occurrences,"decoded_rows":len(rows)})
        if not rows: continue
        auxiliary="/app_userdata/" in rel.replace("\\","/")
        if auxiliary:
            streams.append({"file":rel,"kind":"auxiliary_shared_userdata_sink","row_count":len(rows),"role_counts":dict(collections.Counter(x["data"].get("role") for x in rows)),"ordering":"NOT ASSERTED; sink can contain copied/interleaved/truncated output from multiple processes"})
            continue
        episodes=[]; current=[]
        for rec in rows:
            if current and rec["data"].get("index",0)<=current[-1]["data"].get("index",0):
                episodes.append(current); current=[]
            current.append(rec)
        if current: episodes.append(current)
        for enum,episode in enumerate(episodes,1):
            first=episode[0]; last=episode[-1]; fd=first["data"]; ld=last["data"]; gaps=[]; transitions=[]
            for prev,nxt in zip(episode,episode[1:]):
                a=prev["data"]; b=nxt["data"]; where=f"{rel}:{nxt['line']}"
                audit.check("per_episode_contiguous_output_indexes",b.get("index")==a.get("index",0)+1,where)
                audit.check("per_episode_role_stable",b.get("role")==a.get("role"),where)
                for key in ("wall_msec","process_frames","physics_frames","drawn_frames"):
                    audit.check("per_episode_monotone_"+key,b.get(key,-1)>=a.get(key,-1),where)
                for key,v in a.get("counters",{}).items():
                    audit.check("per_episode_counters_monotone",b.get("counters",{}).get(key,0)>=v,where,{"counter":key})
                gap=b.get("wall_msec",0)-a.get("wall_msec",0)
                gaps.append({"msec":gap,"before_line":prev["line"],"after_line":nxt["line"],"before_index":a.get("index"),"after_index":b.get("index")})
                identity=("local_attempt","peer","bound_actor","generation","authority_epoch","prediction_epoch","connection_state","transport_id")
                changes={k:[a.get(k),b.get(k)] for k in identity if a.get(k)!=b.get(k)}
                if changes: transitions.append({"line":nxt["line"],"index":b.get("index"),"wall_msec":b.get("wall_msec"),"reason":b.get("reason"),"changes":changes})
            age_stats={}
            for slot in sorted({k for rec in episode for k in rec["data"].get("latest",{})}):
                vals=[(rec["data"]["wall_msec"]-rec["data"]["latest"][slot]["wall_msec"],rec["line"],rec["data"]["index"]) for rec in episode if slot in rec["data"].get("latest",{})]
                age,line,index=max(vals)
                age_stats[slot]={"largest_observed_age_msec":age,"line":line,"index":index,"last_slot":ld.get("latest",{}).get(slot)}
            identity_segments=[]
            segment=[]
            for rec in episode:
                r=rec["data"]
                key=(r.get("local_attempt"),) if r.get("role")=="client" else (r.get("peer"),r.get("generation"))
                if segment and key!=segment[-1][0]:
                    identity_segments.append(segment); segment=[]
                segment.append((key,rec))
            if segment: identity_segments.append(segment)
            segment_summaries=[]
            for group in identity_segments:
                begin=group[0][1]; end=group[-1][1]
                adjacent=[{"msec":b[1]["data"]["wall_msec"]-a[1]["data"]["wall_msec"],"before_line":a[1]["line"],"after_line":b[1]["line"]} for a,b in zip(group,group[1:])]
                segment_summaries.append({"identity":list(group[0][0]),"row_count":len(group),"first_line":begin["line"],"last_line":end["line"],"first_index":begin["data"].get("index"),"last_index":end["data"].get("index"),"first_wall_msec":begin["data"].get("wall_msec"),"last_wall_msec":end["data"].get("wall_msec"),"largest_adjacent_gap":max(adjacent,key=lambda x:x["msec"]) if adjacent else None,"boundary_limit":"Client attempt hook precedes reset; server disconnect hook precedes unbind. Identity change alone does not timestamp delivery or action effects."})
            clock_offsets=[r["data"]["wall_unix_msec"]-r["data"]["wall_msec"] for r in episode]
            stale_identity=[]
            for rec in episode:
                r=rec["data"]; consumed=r.get("latest",{}).get("input_consumed")
                if consumed and (consumed.get("peer")!=r.get("peer") or consumed.get("generation")!=r.get("generation") or consumed.get("actor")!=r.get("bound_actor")):
                    stale_identity.append({"line":rec["line"],"index":r.get("index"),"row_peer":r.get("peer"),"row_generation":r.get("generation"),"row_bound_actor":r.get("bound_actor"),"slot_peer":consumed.get("peer"),"slot_generation":consumed.get("generation"),"slot_actor":consumed.get("actor"),"slot_age_msec":r["wall_msec"]-consumed["wall_msec"]})
            streams.append({"identity_segments":segment_summaries,"latest_consumed_identity_differs_from_row":stale_identity,"unix_minus_monotonic_offset_msec":{"minimum":min(clock_offsets),"maximum":max(clock_offsets),"meaning":"uncalibrated process clock offset; no cross-role latency inference"},"file":rel,"episode":enum,"row_count":len(episode),"role":fd.get("role"),"first_line":first["line"],"last_line":last["line"],"first":fd,"last":ld,"reason_counts":dict(collections.Counter(r["data"].get("reason") for r in episode)),"largest_adjacent_gap":max(gaps,key=lambda x:x["msec"]) if gaps else None,"observed_span_msec":ld.get("wall_msec",0)-fd.get("wall_msec",0),"process_origin_to_first_msec":fd.get("wall_msec"),"trailing_unobserved_interval":"UNKNOWN pending independently bound process termination; no collector terminal seal", "configuration_boundary":"initial index1" if fd.get("index")==1 and enum==1 else "RESET/INITIAL OFFSET REQUIRES SOURCE/LIFECYCLE CORROBORATION", "cap_reached":ld.get("index")==1024,"transitions":transitions,"latest_age":age_stats})
    summary={"raw_root":str(raw),"scope":"Exact source-hook facts and projection checks only; no completeness/overall/gameplay verdict", "log_inventory":inventories,"decoded_rows_including_artifact_replicas":len(allrows),"streams":streams,"parse_failures":parse_failures,"duplicate_line_fingerprints":[{"sha256":h,"locations":locs} for h,locs in exact_lines.items() if len(locs)>1],"predicates":[{"predicate":k,"status":s,"count":v} for (k,s),v in sorted(audit.counts.items())],"predicate_failures":audit.failures,"limitations":["Replica files do not add independent events","Monotonic clocks are process local; no global total order or wall-clock transport latency is inferred","Counters establish named source-hook calls only; latest slots may coalesce or remain stale","No terminal seal and output cap prevent completeness inference","No release/remote/account negative execution inferred from source gating","Leading wall_msec is process clock origin to first row, not independently observed process launch time"]}
    out.mkdir(parents=True,exist_ok=True); (out/"collector-facts.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    columns="file line ordinal role reason index wall_unix_msec wall_msec process_frames physics_frames drawn_frames local_attempt transport_id connection_state peer bound_actor last_bound_actor peer_bound generation joined authority_epoch prediction_epoch simulation_tick stream_ack queue_count pending_count pending_oldest_sequence pending_newest_sequence snapshot_age_msec snapshot_tick snapshot_epoch snapshot_ack local_fire local_reload physical_r physical_lmb actor_id actor_ammo actor_reserve actor_reload actor_fire actor_reload_input latest_send_msec latest_send_first latest_send_last latest_send_fire latest_send_reload latest_received_msec latest_received_first latest_received_last latest_received_fire latest_received_reload latest_accepted_msec latest_consumed_msec latest_consumed_sequence latest_consumed_peer latest_consumed_actor latest_consumed_generation latest_consumed_fire latest_consumed_reload".split()
    with (out/"collector-rows.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=columns); writer.writeheader()
        for rec in allrows:
            r=rec["data"]; d={k:r.get(k) for k in columns}; d.update({k:rec[k] for k in ("file","line","ordinal")})
            for key,slot in (("snapshot_tick","tick"),("snapshot_epoch","epoch"),("snapshot_ack","own_ack")): d[key]=r.get("snapshot",{}).get(slot)
            for key,slot in (("local_fire","fire"),("local_reload","reload")): d[key]=r.get("local_input",{}).get(slot)
            for key,slot in (("physical_r","r"),("physical_lmb","lmb")): d[key]=r.get("physical",{}).get(slot)
            for key,slot in (("actor_id","id"),("actor_ammo","ammo"),("actor_reserve","reserve"),("actor_reload","reload")): d[key]=r.get("actor",{}).get(slot)
            for key,slot in (("actor_fire","fire"),("actor_reload_input","reload")): d[key]=r.get("actor",{}).get("input",{}).get(slot)
            for prefix,slot in (("send","input_send_called"),("received","input_received"),("accepted","input_accepted"),("consumed","input_consumed")):
                latest=r.get("latest",{}).get(slot,{})
                for key in ("wall_msec","first","last","fire","reload","sequence","peer","actor","generation"):
                    col="latest_"+prefix+"_"+("msec" if key=="wall_msec" else key)
                    if col in columns:d[col]=latest.get(key)
            writer.writerow(d)
    print(json.dumps({"files":len(files),"streams":len(streams),"decoded_rows_including_replicas":len(allrows),"parse_failures":len(parse_failures),"predicate_passes":sum(v for (k,s),v in audit.counts.items() if s=="PASS"),"predicate_failures":len(audit.failures)}))

if __name__=="__main__": main()
