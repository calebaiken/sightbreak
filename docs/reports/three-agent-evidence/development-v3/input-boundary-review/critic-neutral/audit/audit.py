import pathlib,sys,json,hashlib,struct,re,collections,datetime,math
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-neutral-20261023T010534385344Z')
P=ROOT/'packet';A=ROOT/'audit';A.mkdir(exist_ok=False)
(A/'audit.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(name,obj):
 path=A/name;path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def diff(a,b,path=''):
 out=[]
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append({'path':path+'/'+k,'bd249c':a.get(k),'05ec6c':b.get(k),'missing':True})
   else:out.extend(diff(a[k],b[k],path+'/'+k))
 elif isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b):out.append({'path':path,'lengths':[len(a),len(b)]})
  for i,(x,y) in enumerate(zip(a,b)):out.extend(diff(x,y,path+'/'+str(i)))
 elif type(a)!=type(b) or a!=b:out.append({'path':path,'bd249c':a,'05ec6c':b})
 return out
class Decoder:
 def __init__(self,data):self.data=data;self.pos=0;self.nodes=[]
 def take(self,n):
  start=self.pos;end=start+n
  if n<0 or end>len(self.data):raise ValueError('truncated variant')
  self.pos=end;return self.data[start:end]
 def u32(self):return struct.unpack('<I',self.take(4))[0]
 def read(self,path='$',depth=0):
  assert depth<20
  start=self.pos;header=self.u32();typ=header&0xffff;flags=header>>16
  assert flags==0, ('unhandled flags',header)
  node={'offset':start,'type_id':typ,'header_hex':struct.pack('<I',header).hex(),'path':path}
  if typ==1:
   word=self.u32();assert word in (0,1);value=bool(word);kind='bool';tree=(typ,value)
  elif typ==2:value=struct.unpack('<i',self.take(4))[0];kind='int32';tree=(typ,value)
  elif typ==4:
   size=self.u32();data=self.take(size);pad=self.take((-size)%4);assert not any(pad)
   value=data.decode('utf-8');kind='string';tree=(typ,value)
  elif typ==5:
   value=list(struct.unpack('<ff',self.take(8)));kind='Vector2_float32';tree=(typ,value)
  elif typ==27:
   count=self.u32();assert count<100 and count&0x80000000==0
   value={};children=[];kind='dictionary'
   for i in range(count):
    k,kt=self.read(path+'/key['+str(i)+']',depth+1);assert isinstance(k,str) and k not in value
    v,vt=self.read(path+'/'+k,depth+1);value[k]=v;children.append((kt,vt))
   tree=(typ,children)
  elif typ==28:
   count=self.u32();assert count<100 and count&0x80000000==0
   value=[];children=[];kind='array'
   for i in range(count):v,t=self.read(path+'/'+str(i),depth+1);value.append(v);children.append(t)
   tree=(typ,children)
  else:raise ValueError(('unhandled variant type',typ,start))
  node.update({'end_offset':self.pos,'kind':kind})
  if typ not in (27,28):node['value']=value
  self.nodes.append(node)
  return value,tree
 def encode(self,tree):
  typ,value=tree;header=struct.pack('<I',typ)
  if typ==1:return header+struct.pack('<I',int(value))
  if typ==2:return header+struct.pack('<i',value)
  if typ==4:
   b=value.encode('utf-8');return header+struct.pack('<I',len(b))+b+bytes((-len(b))%4)
  if typ==5:return header+struct.pack('<ff',*value)
  if typ==27:return header+struct.pack('<I',len(value))+b''.join(self.encode(k)+self.encode(v) for k,v in value)
  if typ==28:return header+struct.pack('<I',len(value))+b''.join(self.encode(v) for v in value)
  raise ValueError(typ)
intake=load(ROOT/'intake-inventory.json')
for e in intake['files']:
 b=(P/e['path']).read_bytes();assert len(b)==e['bytes'] and sha(b)==e['sha256']
packets={};samples={};checks=[]
def verify(name,condition,detail=None):
 checks.append({'name':name,'verified':bool(condition),'detail':detail})
for label in ['sample-bd249c','sample-05ec6c']:
 base=P/label;r=load(base/'result.json');events=r['events']
 engine=(base/'probe.engine.log').read_text(encoding='utf-8');imports=(base/'import.engine.log').read_text(encoding='utf-8')
 lines=[line for line in engine.splitlines() if line.startswith('INPUT_BOUNDARY_RESULT ')]
 verify(label+'/one_engine_result_line',len(lines)==1)
 rawresult=json.loads(lines[0][len('INPUT_BOUNDARY_RESULT '):])
 verify(label+'/engine_result_equals_saved_result_core',rawresult=={k:v for k,v in r.items() if k not in ['label','actual_exit']})
 receipts={name:load(base/name) for name in ['import.process.json','probe.process.json']}
 verify(label+'/recorded_process_receipts_complete_exit_zero',all(v=={'complete':True,'exit':0,'errors':[]} for v in receipts.values()))
 verify(label+'/result_actual_exit_matches_probe_receipt',r['actual_exit']==receipts['probe.process.json']['exit'])
 errorlines=[line for text in [engine,imports] for line in text.splitlines() if re.search(r'SCRIPT ERROR|(?:^|\s)ERROR:|Parse Error|FATAL|crash|backtrace',line,re.I)]
 verify(label+'/no_unexpected_native_error_lines',not errorlines)
 verify(label+'/event_count_15',len(events)==15)
 derived=[];popped=[];previous=None;rate_attempts=0
 for index,e in enumerate(events):
  name=label+'/'+e['event'];before=e['before'];after=e['after'];op=e['operation']
  verify(name+'/before_equals_previous_after',previous is None or before==previous)
  verify(name+'/ack_never_decreases',after['ack']>=before['ack'])
  verify(name+'/state_has_only_component_fields',set(before)==set(after)=={'ack','queue','rate','rejected'})
  d={'event_index':index,'event':e['event'],'operation':op,'before':before,'after':after,'raw_event':e,'delta':{'ack':after['ack']-before['ack'],'rejected':after['rejected']-before['rejected'],'queue_keys_added':sorted(set(after['queue'])-set(before['queue']),key=int),'queue_keys_removed':sorted(set(before['queue'])-set(after['queue']),key=int),'queue_existing_values_changed':[key for key in set(before['queue'])&set(after['queue']) if before['queue'][key]!=after['queue'][key]],'rate_count':after['rate'].get('count',0)-before['rate'].get('count',0)}}
  if op=='accept':
   rate_attempts+=1;data=bytes.fromhex(e['packet_variant_bytes_hex']);decoder=Decoder(data);payload,tree=decoder.read()
   verify(name+'/variant_exactly_consumed',decoder.pos==len(data))
   verify(name+'/variant_semantics_match_packet_json',payload==e['packet'])
   verify(name+'/variant_type_preserving_roundtrip',decoder.encode(tree)==data)
   h=sha(data)
   if h not in packets:
    packets[h]={'sha256':h,'bytes':len(data),'hex':data.hex(),'decoded':payload,'variant_nodes':sorted(decoder.nodes,key=lambda n:n['offset']),'uses':[]}
    binary=A/'packets'/(h+'.bin');binary.parent.mkdir(exist_ok=True);binary.write_bytes(data)
   packets[h]['uses'].append({'sample':label,'event':e['event']})
   classes=[]
   for command in payload['commands']:
    seq=command['sequence'];kind='fully_acked' if seq<=before['ack'] else 'queued_unacked' if str(seq) in before['queue'] else 'new_unacked'
    classes.append({'sequence':seq,'classification':kind,'move':command['move'],'fire':command['fire'],'fire_is_bool':type(command['fire']) is bool,'queued_payload_matches_incoming_explicit_fields':None if str(seq) not in before['queue'] else all(before['queue'][str(seq)].get(k)==v for k,v in command.items())})
   d['packet_analysis']={'sha256':h,'bytes':len(data),'decoded':payload,'commands':classes,'all_sequences_le_ack':all(c['sequence']<=before['ack'] for c in payload['commands']),'epoch':payload['epoch'],'sequence_distance_from_ack':[c['sequence']-before['ack'] for c in payload['commands']],'supplied_rate_clock_ms':e['supplied_rate_clock_ms'],'capture_monotonic_ms':e['capture_monotonic_ms'],'accepted_result':e['accepted']}
   verify(name+'/accept_does_not_advance_ack',after['ack']==before['ack'])
   verify(name+'/rate_charged_once_each_attempt',after['rate']=={'start':1000,'count':rate_attempts})
   verify(name+'/rejected_counter_delta_matches_false_result',after['rejected']-before['rejected']==int(not e['accepted']))
   if e['event'] in ['identical_queued_retry','altered_queued_retry','partially_acked_retry','new_intent_queued_retry']:
    verify(name+'/queued_unacked_retry_accepted',e['accepted'] is True)
    verify(name+'/queued_retry_does_not_mutate_queue',before['queue']==after['queue'])
   if e['event'] in ['fully_acked_identical_replay','fully_acked_altered_replay']:
    verify(name+'/actually_fully_acked_not_queued_unacked',d['packet_analysis']['all_sequences_le_ack'] and before['queue']=={})
    verify(name+'/replay_does_not_repopulate_queue_or_advance_ack',after['queue']=={} and after['ack']==2)
   if e['event'] in ['old_epoch','beyond_ahead_limit','malformed_acked_command_with_new_intent']:
    verify(name+'/invalid_control_rejected_no_queue_ack_mutation',e['accepted'] is False and before['queue']==after['queue']=={} and before['ack']==after['ack']==3)
  elif op=='pop':
   verify(name+'/pop_leaves_rate_and_rejected_unchanged',before['rate']==after['rate'] and before['rejected']==after['rejected'])
   if e['popped']:
    value=e['popped'];seq=value['sequence'];key=str(seq);popped.append(value)
    verify(name+'/popped_payload_is_original_queued_value',key in before['queue'] and value==before['queue'][key])
    verify(name+'/exactly_one_queue_element_removed',after['queue']=={k:v for k,v in before['queue'].items() if k!=key})
    verify(name+'/ack_advances_to_popped_sequence',after['ack']==seq and after['ack']>before['ack'])
   else:verify(name+'/empty_pop_state_no_change',before==after and before['queue']=={})
  else:raise ValueError(op)
  previous=after;derived.append(d)
 verify(label+'/original_consumption_sequence',[(v['sequence'],v['move'],v['fire']) for v in popped]==[(1,[1.0,0.0],True),(2,[1.0,0.0],False),(3,[-1.0,0.0],True)])
 verify(label+'/only_three_nonempty_pops',len(popped)==3)
 clocks=[e['capture_monotonic_ms'] for e in events];supplied=[e['supplied_rate_clock_ms'] for e in events if e['operation']=='accept']
 verify(label+'/capture_clock_nondecreasing',all(y>=x for x,y in zip(clocks,clocks[1:])))
 verify(label+'/supplied_rate_clock_nondecreasing',all(y>=x for x,y in zip(supplied,supplied[1:])))
 rises=[];held=False
 for v in popped:
  if v['fire'] and not held:rises.append(v['sequence'])
  held=v['fire']
 samples[label]={'raw_result':r,'engine_result_core':rawresult,'raw_engine_log':engine,'raw_import_engine_log':imports,'empty_process_stdout_logs':{name:(base/name).read_text() for name in ['probe.log','import.log']},'process_receipts':receipts,'native_error_lines':errorlines,'execution_authenticated':False,'source_identity_unknown':True,'events':derived,'component_summary':{'accept_attempts':rate_attempts,'accepted_true':sum(e.get('accepted') is True for e in events),'accepted_false':sum(e.get('accepted') is False for e in events),'pop_attempts':sum(e['operation']=='pop' for e in events),'nonempty_pops':len(popped),'popped_original_payloads':popped,'fire_payload_values':[v['fire'] for v in popped],'hypothetical_rising_edges_if_simple_latch_consumed_once':rises,'hypothetical_edges_are_not_actor_shots':True,'final_component_state':previous,'capture_clock_min_max_ms':[min(clocks),max(clocks)],'capture_clock_span_ms':max(clocks)-min(clocks),'supplied_rate_clock_min_max_ms':[min(supplied),max(supplied)],'supplied_rate_clock_span_ms':max(supplied)-min(supplied),'rate_bucket_start':previous['rate']['start'],'rate_bucket_final_count':previous['rate']['count'],'disconnect_evidence_present':False,'live_activity_clock_evidence_present':False,'reported_checks':r['checks'],'reported_failures':r['failures'],'reported_counts_independently_reproduced_as_original_assertions':False}}
 save(label+'-evidence.json',samples[label])
left=samples['sample-bd249c'];right=samples['sample-05ec6c'];eventdiffs=[]
for i,(a,b) in enumerate(zip(left['raw_result']['events'],right['raw_result']['events'])):
 verify('cross/event_order/'+str(i),a['event']==b['event'] and a['operation']==b['operation'])
 if a['operation']=='accept':verify('cross/serialized_packets_match/'+a['event'],a['packet_variant_bytes_hex']==b['packet_variant_bytes_hex'])
 stripped=lambda e:{k:v for k,v in e.items() if k!='capture_monotonic_ms'}
 eventdiffs.append({'event_index':i,'event':a['event'],'capture_monotonic_ms':[a['capture_monotonic_ms'],b['capture_monotonic_ms']],'behavior_differences':diff(stripped(a),stripped(b)),'queue_ack_rate_equivalent':all(a[when][k]==b[when][k] for when in ['before','after'] for k in ['ack','queue','rate'])})
comparison={'schema':1,'scope':'Independent source-identity-blinded component evidence critique only, not Match/lifecycle/timer/UDP/actor behavior','samples':['sample-bd249c','sample-05ec6c'],'behaviorally_equivalent':False,'component_freshness_signal_advantage':'sample-bd249c','global_network_or_release_winner':None,'distinctive_events':[{'event':a['event'],'before_ack':a['before']['ack'],'packet_sequences':[v['sequence'] for v in a['packet']['commands']],'accepted':[a['accepted'],b['accepted']],'rejected_delta':[a['after']['rejected']-a['before']['rejected'],b['after']['rejected']-b['before']['rejected']]} for a,b in zip(left['raw_result']['events'],right['raw_result']['events']) if a.get('accepted')!=b.get('accepted')],'event_comparison':eventdiffs,'component_summaries':{k:v['component_summary'] for k,v in samples.items()},'unique_variant_packets':len(packets),'serialized_packet_instances_decoded':sum(len(p['uses']) for p in packets.values()),'source_identity_blinding':'Keys/source modules/parent driver/main verdict/owner claims were not inspected; neutral labels only. Prior large-packet review exists but no identity mapping was opened or used.','behavioral_blinding':'Not behavior-blind: raw acceptance/rejection outputs reveal the behavior under test; neutral source identities do not hide behavioral differences. No source guesses or correspondence to prior labels are made.','authenticity':'Unsigned local historical receipts/logs, no external supplied hash pin, binary custody/signature/path/PID/command/duration not established. Complete/exit0/banner/result agreement are internal corroboration, not authenticated native execution.','large_packet_freeze':'No file from the previous large-packet freeze was opened or modified in this follow-up.'}
save('comparison.json',comparison)
save('packet-decodes.json',{'format':'Narrow independent offline Godot Variant parser: little-endian unflagged bool/int32/string/Vector2 float32/dictionary/array only; validates padding, duplicates, full consumption and exact type-preserving byte roundtrip. Serialized component boundary evidence, not captured UDP datagrams.','packets':list(packets.values())})
save('independent-checks.json',{'note':'Independent state/byte-consistency checks, not a rerun/reconstruction of the probe authors 21 hidden assertions.','total':len(checks),'verified':sum(c['verified'] for c in checks),'failed':[c for c in checks if not c['verified']],'checks':checks})
print('SUMMARY',json.dumps({k:v for k,v in comparison.items() if k not in ['event_comparison','component_summaries']},indent=2))
print('COMPONENT_SUMMARIES',json.dumps(comparison['component_summaries'],indent=2))
print('PACKETS',json.dumps([{'sha256':h,'bytes':p['bytes'],'uses':len(p['uses']),'packet':p['decoded']} for h,p in packets.items()],indent=2))
print('INDEPENDENT_CHECKS',len(checks),'FAILED',json.dumps([c for c in checks if not c['verified']]))
print('DIFFERENCE_PATHS',json.dumps(eventdiffs,indent=2))
print('AUDIT_PATH',A)