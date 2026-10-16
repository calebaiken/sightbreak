from pathlib import Path
import subprocess, re, json
r=Path('/workspace/reviews/stabilization-v2-20261016/audio')
src=Path('/workspace/sightbreak-three-agent/game/tests/reload_sequence_test.gd').read_text()
funcs=['_identity','_paths','_grip','_sync','_reduced_motion','_visibility','_authority','_casings','_edges']
results=[]
for f in funcs:
 s=src
 for other in funcs:
  if other!=f:s=s.replace('\tawait '+other+'()','\t# excluded '+other)
 s=s.replace('\t_measure_well()','\t_measure_well()\n\tfor event in SBReloadAudio._streams:\n\t\tfor wav in SBReloadAudio._streams[event]: print("STREAM_ID ",event," ",wav.get_instance_id())')
 p=r/('cause-sequence-'+f+'.gd');p.write_text(s)
 log=r/('cause-sequence-'+f+'.txt')
 with log.open('w') as out:
  run=subprocess.run(['/workspace/sightbreak-three-agent/scripts/godot.sh','--headless','--verbose','--script',str(p)],stdout=out,stderr=subprocess.STDOUT,timeout=180)
 data=log.read_text()
 leak=re.search(r'(\d+) ObjectDB instances were leaked',data)
 result={'part':f,'exit':run.returncode,'leaks':int(leak[1]) if leak else 0,'errors':data.count('SCRIPT ERROR:')}
 results.append(result);print(result,flush=True)
(r/'cause-sequence-split.json').write_text(json.dumps(results,indent=2))
