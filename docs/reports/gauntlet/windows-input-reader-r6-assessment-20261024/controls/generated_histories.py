#!/usr/bin/env python3
"""Independent finite source-history oracle; candidate is never expected oracle."""
import argparse,copy,gzip,hashlib,importlib.util,itertools,json,os
from pathlib import Path
import queue_oracle as qo

def header(packet):return (len(packet),packet[0][0],packet[-1][0],sum(c[1] for c in packet),sum(c[2] for c in packet))
def command(c):return {'sequence':c[0],'fire':c[1],'reload':c[2],'move':[0.,0.]}
def stage(queue,ack,packet):
 staged={seq:(fire,reload) for seq,fire,reload in packet if seq>max(ack,0)}
 if not staged:return False
 for seq,flags in staged.items():queue.setdefault(seq,flags)
 return True

def all_packets(keys,flags,lengths):
 commands=tuple((key,fire,reload) for key in keys for fire,reload in flags)
 return [p for n in lengths for p in itertools.product(commands,repeat=n)]

def oracle_profiles(family):
 keys,flags,lengths1,lengths2,between=family
 packets1=all_packets(keys,flags,lengths1);packets2=all_packets(keys,flags,lengths2)
 profiles={};source_histories=0
 for p1 in packets1:
  first={};assert stage(first,-1,p1)
  for p2 in packets2:
   queue=dict(first);ack=-1;pop=None
   if between:
    key=min(queue);fire,reload=queue.pop(key);ack=key;pop=(key,fire,reload)
   if not stage(queue,ack,p2):continue
   source_histories+=1
   prefix=(header(p1),len(first),pop,header(p2),len(queue))
   completion=tuple((k,*v) for k,v in sorted(queue.items()))
   record=profiles.setdefault(prefix,{'possible':{},'canonical':(p1,p2),'ack':ack})
   record['possible'].setdefault(completion,(p1,p2))
 return profiles,source_histories

def source_world(witness,between):
 p1,p2=witness;w=qo.SourceOracle();w.connect();w.accept([command(c) for c in p1]);w.flush()
 if between:w.pop();w.flush()
 w.accept([command(c) for c in p2]);w.flush();return w

def classify(module,rows):
 model=module.InputTransitions()
 try:
  for r in rows:model.observe(r['row'],set(map(tuple,r['owners_before'])))
 except module.UnknownTransition as e:return 'UNKNOWN',str(e)
 except (ValueError,KeyError,TypeError) as e:return 'INVALID',type(e).__name__+': '+str(e)
 return 'VALID',None

def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False)
 families={
  'two_receipts_unknown_middle':((1,2,3),((False,False),(True,False)),(1,2,3),(1,),False),
  'pop_between_receipts':((1,2,3),((False,False),(True,False)),(1,2,3),(1,),True),
  'two_receipts_fire_reload':((1,2),tuple(itertools.product((False,True),repeat=2)),(1,2),(1,2),False)}
 # All source feasibility sets are fixed independently before candidate import.
 corpus={name:oracle_profiles(family) for name,family in families.items()}
 spec=importlib.util.spec_from_file_location('held_unfrozen_history_model',a.prototype);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 summaries=[];mismatches=[];case_id=0;raw_digest=hashlib.sha256()
 path=a.output/'cases.jsonl.gz'
 with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as out:
  for name,family in families.items():
   keys,flags,_,_,between=family;profiles,source_count=corpus[name];counts={'family':name,'concrete_source_histories':source_count,'observable_prefixes':len(profiles),'cases':0,'expected_valid':0,'expected_invalid':0,'matched':0,'invalid_accepted':0,'valid_rejected':0,'valid_unknown':0,'invalid_unknown':0}
   for prefix,record in sorted(profiles.items(),key=lambda pair:json.dumps(pair[0])):
    count=prefix[-1];available=[k for k in keys if k>max(record['ack'],0)]
    for chosen in itertools.combinations(available,count):
     for controls in itertools.product(flags,repeat=count):
      completion=tuple((k,*v) for k,v in zip(chosen,controls));witness=record['possible'].get(completion);expected='VALID' if witness else 'INVALID'
      w=source_world(witness or record['canonical'],between);source_prefix=copy.deepcopy(w.truth)
      if witness:
       actual_queue=tuple((k,v['fire'],v['reload']) for k,v in sorted(w.state(9)['queue'].items()));assert actual_queue==completion
      else:
       # Only the claimed projected completion changes; the observed packet prefix is fixed.
       w.state(9)['queue']={seq:command((seq,fire,reload)) for seq,fire,reload in completion}
      while w.state(9)['queue']:w.pop();w.flush()
      actual,error=classify(module,w.rows);case_id+=1;counts['cases']+=1;counts['expected_'+expected.lower()]+=1
      if actual==expected:counts['matched']+=1
      elif expected=='INVALID' and actual=='VALID':counts['invalid_accepted']+=1
      elif expected=='VALID' and actual=='INVALID':counts['valid_rejected']+=1
      elif expected=='VALID':counts['valid_unknown']+=1
      else:counts['invalid_unknown']+=1
      result={'id':case_id,'family':name,'prefix':prefix,'claimed_completion':completion,'expected':expected,'actual':actual,'error':error,'source_witness':witness,'source_prefix_events':source_prefix,'all_oracle_completions':list(record['possible']),'projected_rows':w.rows}
      encoded=(json.dumps(result,separators=(',',':'))+'\n').encode();out.write(encoded);raw_digest.update(encoded)
      if actual!=expected:
       mismatches.append({'id':case_id,'family':name,'expected':expected,'actual':actual,'error':error})
       if len(mismatches)<=20:(a.output/('mismatch-'+str(case_id)+'.json')).write_text(json.dumps(result,indent=2)+'\n')
   summaries.append(counts);print(json.dumps(counts),flush=True)
 summary={'scope':'Independent generated persistent source-history assessment; isolated UNFROZEN InputTransitions only','prototype_sha256':hashlib.sha256(a.prototype.read_bytes()).hexdigest(),'families':summaries,'cases':case_id,'matched':case_id-len(mismatches),'mismatches':mismatches,'raw_jsonl_sha256':raw_digest.hexdigest(),'gzip_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'all_case_inputs_and_results_retained':True,'individual_mismatch_copies':min(20,len(mismatches)),'cpu_affinity':[4],'native_executed':False,'final_source_approval':False}
 (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='mismatches'},indent=2));return int(bool(mismatches))
if __name__=='__main__':raise SystemExit(main())
