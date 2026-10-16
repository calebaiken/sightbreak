import subprocess,pathlib,re,json,time,concurrent.futures
p=pathlib.Path('/workspace/reviews/stabilization-v2-20261016/audio')
repo='/workspace/sightbreak-three-agent'
src=subprocess.check_output(['git','-C',repo,'show','HEAD:game/tests/reload_sequence_test.gd'],text=True)
print(src[src.index('print("RELOAD_SEQUENCE_TEST'):src.index('## A second magazine')],flush=True)
# Baseline test quit lacked owner cleanup; release the entire existing test world, then drain only.
needle='\tquit(1 if not failures.is_empty() else 0)'
assert src.count(needle)==1
src=src.replace(needle,'\tworld.queue_free()\n\tawait process_frame\n\tawait create_timer(0.5).timeout\n'+needle)
probe=p/'cause-sequence-drainalone.gd';probe.write_text(src)
def run(i,loaded=False):
 log=p/('cause-sequence-drainalone-%s-%s.txt'%('loaded' if loaded else 'isolated',i))
 with log.open('w') as f:
  r=subprocess.run([repo+'/scripts/godot.sh','--headless','--verbose','--script',str(probe)],stdout=f,stderr=subprocess.STDOUT,timeout=240)
 data=log.read_text();m=re.search(r'(\d+) ObjectDB instances were leaked',data)
 result={'mode':'loaded' if loaded else 'isolated','i':i,'exit':r.returncode,'leaks':int(m[1]) if m else 0,'script_errors':data.count('SCRIPT ERROR:')};print(result,flush=True);return result
results=[run(i) for i in range(3)]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results.extend(pool.map(lambda i:run(i,True),range(3)))
(p/'cause-sequence-drainalone-results.json').write_text(json.dumps(results,indent=2))
