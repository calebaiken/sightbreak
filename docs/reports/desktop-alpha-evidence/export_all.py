import subprocess,json,pathlib,os,time
out=pathlib.Path(os.environ['SIGHTBREAK_BUILDS_DIR']);out.mkdir(parents=True,exist_ok=True)
records=[]
for target in ['linux','windows','macos','android','ios']:
 command=['python3','scripts/export.py',target];start=time.monotonic()
 with (out/(target+'-driver.log')).open('w') as stream:r=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=660)
 records.append({'target':target,'command':command,'exit_code':r.returncode,'seconds':time.monotonic()-start});print(records[-1],flush=True)
 (out/'export-results.json').write_text(json.dumps(records,indent=2)+'\n')
