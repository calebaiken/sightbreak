#!/usr/bin/env python3
"""Derive bounded actual stage links from original canonical collector logs."""
import argparse,collections,hashlib,json
from pathlib import Path
MARKER=b"SIGHTBREAK_INPUT_OBSERVATION "
FIELDS="epoch count first last fire reload moving".split()
def digest(p):return {"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("raw_root",type=Path);ap.add_argument("full_root",type=Path);ap.add_argument("--out",type=Path,default=Path(__file__).parent);a=ap.parse_args();base=a.raw_root;out=a.out;ordinary=base/"native-input"
 rows={};canon={};files={}
 for name in ["client.log","server.log"]:
  p=ordinary/name;files["native-input/"+name]=digest(p);found=[]
  for line_no,line in enumerate(p.read_bytes().splitlines(),1):
   if line.startswith(MARKER):
    r=json.loads(line[len(MARKER):]);item={"file":"native-input/"+name,"line":line_no,"data":r};found.append(item);canon[line]=item
  rows[name]=found
 stage={}
 for filename,slot in [("client.log","input_send_called"),("server.log","input_received"),("server.log","input_accepted")]:
  stage[slot]=[r for r in rows[filename] if r["data"]["reason"]==slot]
 links=[]
 for i,(send,recv,accept) in enumerate(zip(stage["input_send_called"],stage["input_received"],stage["input_accepted"]),1):
  projected=[{k:r["data"]["latest"][slot][k] for k in FIELDS} for r,slot in [(send,"input_send_called"),(recv,"input_received"),(accept,"input_accepted")]]
  links.append({"ordinal":i,"same_projection":projected[0]==projected[1]==projected[2],"projection":projected[0],"send":send,"received":recv,"accepted":accept,"claim_limit":"Current source-hook rows share a summary in the only observed attempt/peer/epoch; bodies and transport latency are not reconstructed."})
 control_edges=[];previous=None
 for item in rows["client.log"]:
  r=item["data"];sig=[r["local_input"][k] for k in ["fire","reload"]]+[r["physical"][k] for k in ["lmb","r"]]
  if sig!=previous:control_edges.append(item)
  previous=sig
 effect=[];shots=[]
 for no,line in enumerate((ordinary/"server.log").read_text().splitlines(),1):
  if line.startswith("EXPORT_UI_TIMING "):
   r=json.loads(line.split(" ",1)[1]);effect.append({"file":"native-input/server.log","line":no,"data":r})
  elif line.startswith("EXPORT_UI_SHOT ") or line.startswith("EXPORT_UI_RELOAD_"):
   shots.append({"file":"native-input/server.log","line":no,"text":line})
 commands=json.loads((ordinary/"commands.json").read_text());actions=json.loads((ordinary/"actions.json").read_text())
 action_rows=[{"file":"native-input/actions.json","array_index_1based":i,"data":r} for i,r in enumerate(actions,1) if r.get("event")=="before_firing" or r.get("event") in ["button_before","button_after"] or r.get("key")=="r" or r.get("event") in ["capture_begin","capture_end"] or "reload" in r.get("label","").lower()]
 for name in ["commands.json","actions.json","results.json","authority.json","authority-telemetry.json","join-snapshot.json"]:files["native-input/"+name]=digest(ordinary/name)
 replica=[]
 for p in sorted((ordinary/"state").rglob("*.log")):
  copies=[];fragments=[];unmatched=[]
  for no,line in enumerate(p.read_bytes().splitlines(),1):
   if line.startswith(MARKER):
    if line in canon:copies.append({"sink_line":no,"canonical_file":canon[line]["file"],"canonical_line":canon[line]["line"],"canonical_index":canon[line]["data"]["index"]})
    else:unmatched.append({"line":no,"sha256":hashlib.sha256(line).hexdigest()})
   elif b'"scope":"debug_guest_loopback_input_observation"' in line:
    origins=[{"file":v["file"],"line":v["line"],"index":v["data"]["index"],"missing_leading_bytes":len(k)-len(line)} for k,v in canon.items() if k.endswith(line)]
    fragments.append({"line":no,"bytes":len(line),"sha256":hashlib.sha256(line).hexdigest(),"canonical_suffix_matches":origins})
  replica.append({"file":str(p.relative_to(base)),**digest(p),"copied_rows":copies,"unmatched_prefixed_rows":unmatched,"markerless_fragments":fragments})
 logs=[]
 for p in sorted(base.rglob("*")):
  if p.is_file() and (p.suffix.lower() in [".log",".txt",".stdout",".stderr"] or "stdout" in p.name.lower() or "stderr" in p.name.lower()):logs.append({"file":str(p.relative_to(base)),"marker_count":p.read_bytes().count(MARKER),**digest(p)})
 argv=[]
 def walk(v,where,file):
  if isinstance(v,dict):
   for k,x in v.items():
    if k in ["command","argv"] and isinstance(x,list) and all(isinstance(s,str) for s in x):argv.append({"file":file,"json_pointer":where+"/"+k,"args":x,"observation_flag": "--native-input-observation" in x})
    else:walk(x,where+"/"+k,file)
  elif isinstance(v,list):
   for i,x in enumerate(v):walk(x,where+"/"+str(i),file)
 for p in sorted(base.rglob("*.json")):
  try:v=json.loads(p.read_text())
  except (ValueError,UnicodeError):continue
  walk(v,"",str(p.relative_to(base)))
 imgs=[{"file":"native-input/"+p.name,**digest(p)} for p in sorted((a.full_root/"native-input").glob("*.png"))]
 report={"identity":{"run":40080238905,"job":120832097220,"candidate":"c32415148db1f110bbc7eadfca3793d4693429ff"},"canonical_records":sum(len(v) for v in rows.values()),"canonical_unique_line_count":len(canon),"raw_file_bindings":files,"commands":commands,"current_packet_summary_links":links,"current_stage_counts":{k:len(v) for k,v in stage.items()},"client_current_control_edges":control_edges,"authority_current_consumed_edges":[r for r in rows["server.log"] if r["data"]["reason"]=="input_consumed"],"authority_effect_markers":shots,"authority_effect_timing_rows":effect,"controller_action_rows":action_rows,"auxiliary_sinks":replica,"all_retained_logs":logs,"command_occurrences":argv,"images":imgs,"limits":["Collector keys/types/role predicates are in collector-facts.json","All current-stage matches use projected summaries, never reconstructed packet bodies","System clocks are uncalibrated; no cross-process latency or global order is claimed","No terminal seal, coalescing and bounded print cap prevent complete-event-coverage inference","Observed absence of flag/emission in retained lanes is not negative execution of release/remote/account paths"]}
 (out/"stage-facts.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"canonical_rows":report["canonical_records"],"unique":len(canon),"current_stage_counts":report["current_stage_counts"],"matched_packet_summaries":sum(x["same_projection"] for x in links),"command_occurrences":len(argv),"flagged_command_occurrences":sum(x["observation_flag"] for x in argv),"auxiliary_rows":sum(len(x["copied_rows"]) for x in replica),"auxiliary_markerless_fragments":sum(len(x["markerless_fragments"]) for x in replica)}))
if __name__=="__main__":main()
