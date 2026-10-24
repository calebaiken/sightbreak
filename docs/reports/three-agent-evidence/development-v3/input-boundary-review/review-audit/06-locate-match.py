import pathlib,sys,subprocess,json,hashlib,datetime,time
sys.stdout.reconfigure(encoding='utf-8')
out=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-sourcebinding-20261023T011730421928Z')
(out/'06-locate-match.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
argv=['git','-C',r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3','ls-tree','-r','--name-only','f3ceaad98e089aa393c7f5fa650a52695094d979','--','game/scripts']
t=time.perf_counter();p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
commands=json.loads((out/'actual-git-commands.json').read_bytes())
commands.append({'argv':argv,'started_utc_local':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.perf_counter()-t,'exit':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr':p.stderr.decode(),'scope':'Filename lookup only; only match.gd path selected, no neighboring contents read.'})
(out/'actual-git-commands.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
assert p.returncode==0
paths=[line for line in p.stdout.decode().splitlines() if pathlib.PurePosixPath(line).name=='match.gd'];assert len(paths)==1,paths
(out/'match-location.json').write_text(json.dumps({'path':paths[0],'initial_lookup_failure':'Assumed game/scripts/match.gd absent; failed git show exit128 preserved in actual commands. Filename-only lookup identified permitted Match target.'},indent=2)+'\n',encoding='utf-8')
source=(out/'05-verify-binding.py').read_text(encoding='utf-8')
source=source.replace("(OUT/'05-verify-binding.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')","(OUT/'07-verify-binding-corrected.py').write_text(pathlib.Path(__file__).read_text(encoding='utf-8'),encoding='utf-8')")
source=source.replace('commands=[]',"commands=json.loads((OUT/'actual-git-commands.json').read_bytes())")
source=source.replace("path='game/scripts/match.gd'","path="+repr(paths[0]))
target=out/'07-verify-binding-corrected.py';target.write_text(source,encoding='utf-8')
print('PERMITTED_MATCH_PATH',paths[0])
subprocess.run([sys.executable,'-I',str(target)],check=True)