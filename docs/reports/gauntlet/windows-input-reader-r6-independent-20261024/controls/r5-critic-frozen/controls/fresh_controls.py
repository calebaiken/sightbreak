#!/usr/bin/env python3
"""Independent coalesced/local-source falsifiers; no engine simulation or native."""
import argparse,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reader',type=Path);a=p.parse_args()
root=a.source.resolve();a.output.mkdir(parents=True,exist_ok=False);assert sorted(os.sched_getaffinity(0))==[4]
sys.path.insert(0,str(root/'scripts'))
import test_input_consumption_observation as f
reader_path=a.reader or root/'scripts/analyze_input_consumption.py'
spec=importlib.util.spec_from_file_location('independent_r5_reader',reader_path);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
results=[]
def clone(v):return copy.deepcopy(v)
def base():return f.declared_rows('client'),f.declared_rows('authority')
def packet(now,seq=2,count=1,last=None,epoch=1):return {'epoch':epoch,'count':count,'first':seq,'last':seq if last is None else last,'fire':1,'reload':0,'moving':0,'wall_msec':now}
def append(rows,reason='authority_tick',**changes):
 row=clone(rows[-1]);row['reason']=reason;row['index']+=1;row['wall_msec']+=1000;row['wall_unix_msec']+=1000;row['process_frames']+=1;row['physics_frames']+=2;row['drawn_frames']+=1
 if reason=='authority_tick':row['simulation_tick']+=1
 row['counters'][reason]=row['counters'].get(reason,0)+1;row.update(changes);rows.append(row);return row
def hidden(seq=2,count=1,last=None,epoch=1,offset=1000):
 c,s=base();previous=s[-1]['wall_msec'];row=append(s,queue_count=1)
 for stage in ('input_received','input_accepted'):
  row['counters'][stage]+=1;row['latest'][stage]=packet(previous+offset,seq,count,last,epoch)
 return c,s

def run(name,pair,expected,source_basis,paired=None):
 c,s=pair;raw_c=f.text(c);raw_s=f.text(s);case=a.output/name;case.mkdir()
 (case/'client.txt').write_text(raw_c);(case/'authority.txt').write_text(raw_s)
 report=reader.analyze(raw_c,raw_s);actual=report['diagnostic_complete']
 item={'name':name,'expected':expected,'actual':actual,'met_expectation':expected==actual,'paired_control':paired,'source_basis':source_basis,'inputs':{'client_sha256':hashlib.sha256(raw_c.encode()).hexdigest(),'authority_sha256':hashlib.sha256(raw_s.encode()).hexdigest()},'result':report}
 (case/'RESULT.json').write_text(json.dumps(item,indent=2)+'\n');results.append(item)

run('admitted_declared_pipeline',base(),True,'Retained schema-positive fixture; no engine-model claim.')
run('coalesced_single_fresh',hidden(),True,'ACK1, fresh2 can be staged; identical fire/reload/moving edge fields permit coalescing.')
for name,kwargs in [('coalesced_single_already_acknowledged',{'seq':1}),('coalesced_single_above_window',{'seq':122}),('coalesced_accepted_wrong_epoch',{'epoch':2}),('coalesced_accepted_over_batch_cap',{'count':13})]:
 run(name,hidden(**kwargs),False,'InputStream14-47 requires correct epoch, count<=12, every sequence<=ACK+120 and at least one sequence>ACK, including hidden accept calls.','coalesced_single_fresh')
run('coalesced_stale_endpoints_hidden_fresh_middle',hidden(seq=1,count=3,last=1),True,'Possible commands[stale1,false;fresh2,true;stale1,false] expose1/1,count3,fire1; middle fresh sequence is unobserved.')
for queue in (2,120):
 c,s=base();s[4]['queue_count']=queue
 run('direct_single_command_inflates_queue_'+str(queue),(c,s),False,'A synchronous count1 accept after the direct receive observed queue0 can add at most one unique pending command.','admitted_declared_pipeline')
for name,updates in [('ack_advances_without_consumption',{'stream_ack':2}),('ack_zero_without_consumption',{'stream_ack':0}),('ack_clears_without_reset',{'stream_ack':-1}),('queue_appears_without_acceptance',{'queue_count':1})]:
 c,s=base();append(s,**updates)
 run(name,(c,s),False,'Same live binding/epoch, unchanged accept/consume counters/latest: pop alone updates ACK, accept alone adds queued commands; forget/reset would need an observed lifecycle/epoch boundary.','unchanged_tick')
c,s=base();append(s);run('unchanged_tick',(c,s),True,'Unchanged ACK/queue/latest with another ordinary authority tick is possible.')
for name,kind in [('cached_snapshot_disappears','clear'),('cached_snapshot_restamped','time'),('cached_snapshot_header_changes','header')]:
 c,s=base();row=c[-1]
 if kind=='clear':row.update(snapshot={},snapshot_age_msec=-1)
 elif kind=='time':row['snapshot']['wall_msec']+=1000;row['snapshot_age_msec']-=1000
 else:row['snapshot']['own_ack']+=1
 run(name,(c,s),False,'Match1283-1289 writes cached snapshot and latest from the same header at a counted snapshot_applied call; unchanged count/latest cannot clear, restamp or alter the cached copy.','admitted_declared_pipeline')
c,s=base();c[0]['snapshot']={'tick':50,'epoch':1,'own_ack':1,'wall_msec':1000};c[0]['snapshot_age_msec']=0
run('cache_precedes_first_applied_counter',(c,s),False,'The cache starts empty and is written only after the snapshot_applied counter increment.','admitted_declared_pipeline')
for first_time,expected in [(3999,False),(4500,True)]:
 c,s=base()
 for row in c[4:]:
  row['snapshot']['wall_msec']=first_time;row['snapshot_age_msec']=row['wall_msec']-first_time;row['latest']['snapshot_applied']['wall_msec']=first_time
 run('first_snapshot_time_'+str(first_time),(c,s),expected,'Welcome4000 precedes apply_snapshot; first counted call lies within[4000,5000], then its cache persists.','admitted_declared_pipeline')

def rejection_lifetime():
 c,s=base();row=append(s,stream_rejected=2)
 row['counters']['input_received']+=2;row['counters']['input_stream_rejected']=2
 for stage in ('input_received','input_stream_rejected'):row['latest'][stage]=packet(row['wall_msec'],seq=-9,epoch=-1)
 return c,s
run('two_coalesced_rejections_same_stream',rejection_lifetime(),True,'Two malformed receives each increment stream state and observer counter; neither changes queue/ACK.')

def after_disconnect():
 c,s=rejection_lifetime();append(s,'peer_disconnected');actor=clone(s[-1]['actor']);actor['input']=f.control()
 row=append(s,authority_epoch=3,stream_ack=-1,queue_count=0,bound_actor=0,peer_bound=False,joined=False,generation=-1,actor=actor)
 return c,s
for state,expected,name in [(0,True,'full_stream_replacement_reset'),(2,True,'epoch_change_retains_old_stream_state'),(1,False,'partial_rejected_state_survives_replacement')]:
 c,s=after_disconnect();s[-1]['stream_rejected']=state
 run(name,(c,s),expected,'Without new rejects, old rejected2 either survives no replacement or a new SBInputStream resets it to0; no source operation decrements2 to1.','full_stream_replacement_reset')
c,s=rejection_lifetime();append(s,authority_epoch=2,stream_ack=-1,queue_count=0,stream_rejected=0)
run('live_binding_cannot_reset_rejected_state',(c,s),False,'Stream replacement requires zero bound peers; live binding plus epoch advance cannot clear rejected count.','two_coalesced_rejections_same_stream')
c,s=after_disconnect();s[-1].update(authority_epoch=1,stream_rejected=0)
run('zero_peers_without_epoch_cannot_reset',(c,s),False,'A replacement advances authority_epoch; without that change rejected state cannot drop.','full_stream_replacement_reset')
for offset,expected in [(-1,False),(0,True),(500,True),(1001,False)]:
 run('coalesced_latest_time_offset_'+str(offset),hidden(offset=offset),expected,'New latest call must lie between prior emitted wall11000 and current12000, inclusive.','coalesced_single_fresh')
# Every named negative must change a real input from its named admitted control.
by_name={r['name']:r for r in results}
for r in results:
 if not r['expected'] and r['paired_control']:
  assert r['inputs']!=by_name[r['paired_control']]['inputs'],r['name']
summary={'candidate':'7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508','source_root':str(root),'reader_path':str(reader_path),'reader_sha256':hashlib.sha256(reader_path.read_bytes()).hexdigest(),'cpu_affinity':sorted(os.sched_getaffinity(0)),'cases':len(results),'passed':sum(r['met_expectation'] for r in results),'false_accepts':[r['name'] for r in results if not r['expected'] and r['actual']],'false_rejects':[r['name'] for r in results if r['expected'] and not r['actual']],'results':[{k:v for k,v in r.items() if k!='result'} for r in results],'native_executed':False}
(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2));raise SystemExit(any(not r['met_expectation'] for r in results))
