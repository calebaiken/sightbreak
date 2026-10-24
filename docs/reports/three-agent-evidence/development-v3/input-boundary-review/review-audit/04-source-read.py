import pathlib,sys,json,difflib
sys.stdout.reconfigure(encoding='utf-8')
p=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022')
out=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-sourcebinding-20261023T011730421928Z')
(out/'04-source-read.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
for rel in ['run.py','probe.gd','attempt-r3/private/sample-bd249c/input_stream.gd','attempt-r3/private/sample-05ec6c/input_stream.gd','attempt-r3/private/sample-bd249c/input_gate.gd','attempt-r3/private/sample-bd249c/project.godot','attempt/FAILED.json','attempt-r2/FAILED.json','MAIN_NEUTRAL_COMPONENT_VERDICT.md']:
 print('\nFILE',rel)
 for i,line in enumerate((p/rel).read_text(encoding='utf-8').splitlines(),1):print(f'{i}: {line}')
for old,new in [('attempt/private/driver-before-api-fix.py','attempt-r2/private/driver-before-log-fix.py'),('attempt-r2/private/driver-before-log-fix.py','run.py'),('attempt-r2/private/probe-before-file-result.gd','probe.gd')]:
 print('RETAINED_ATTEMPT_DIFF',old,new)
 print(''.join(difflib.unified_diff((p/old).read_text().splitlines(keepends=True),(p/new).read_text().splitlines(keepends=True),fromfile=old,tofile=new)))