"""Read-only critic controls using real local PCK data and owned process fixtures.

No test in this file is an Apple compiler result. All native headers and Apple
host values used by fixtures are synthetic, and scratch payloads are deleted.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path('/workspace/reviews/ios-compile-critic/source571e8c7')
OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
import qualify_ios_compile as ios
import package_qa_receipts as qa

SOURCE = Path('/workspace/sightbreak-v1-mobile6a/builds/mobile-preservation')
PCK = SOURCE/'ios/sightbreak.pck'
SOURCE_RECORD = json.loads((SOURCE/'ios/source.json').read_text())
results = []

def note(name, detail=None):
    results.append({'case':name,'passed':True,'detail':detail})
    (OUT/'independent-results.json').write_text(json.dumps({'scope':'Linux fixtures and implementation readiness only, not Apple compiler evidence','cases':results},indent=2)+'\n')
    print('PASS',name,flush=True)

def rejects(name, operation):
    try:
        operation()
    except (RuntimeError,ValueError,KeyError,FileNotFoundError) as error:
        note(name,str(error))
        return
    raise AssertionError('Invalid fixture accepted: '+name)

def executable(*,cpu=0x0100000c,device_platform=2,signed=False):
    command = struct.pack('<6I',0x32,24,device_platform,0x000f0000,0x00120000,0)
    if signed:command+=struct.pack('<4I',0x1d,16,0,0)
    return struct.pack('<8I',0xfeedfacf,cpu,0,2,1+int(signed),len(command),0,0)+command

@contextmanager
def app_fixture():
    with tempfile.TemporaryDirectory(prefix='critic-ios-app-') as tmp:
        root=Path(tmp);export=root/'export';(export/'ios').mkdir(parents=True)
        shutil.copyfile(PCK,export/'ios/sightbreak.pck')
        app=root/'sightbreak.app';app.mkdir()
        shutil.copyfile(PCK,app/'sightbreak.pck')
        (app/'sightbreak').write_bytes(executable())
        info={'CFBundleIdentifier':'com.sightbreak.game','CFBundleShortVersionString':'0.3.3','CFBundleVersion':'6','CFBundleExecutable':'sightbreak','DTPlatformName':'iphoneos','CFBundleSupportedPlatforms':['iPhoneOS']}
        (app/'Info.plist').write_bytes(plistlib.dumps(info))
        yield root,app,export,info,copy.deepcopy(SOURCE_RECORD)

with app_fixture() as (_,app,export,_,record):
    accepted=ios.inspect_app(app,export,record)
    assert accepted['pck_resources']==132
    note('accept unsigned ARM64 device fixture carrying actual source-bound 132-resource PCK',accepted)

for name,change in [
    ('reject ARM64 simulator Mach-O',lambda app,info:(app/'sightbreak').write_bytes(executable(device_platform=7))),
    ('reject x86_64 Mach-O even with device plist',lambda app,info:(app/'sightbreak').write_bytes(executable(cpu=0x01000007))),
    ('reject inline LC_CODE_SIGNATURE with zero data size',lambda app,info:(app/'sightbreak').write_bytes(executable(signed=True))),
    ('reject embedded provisioning profile',lambda app,info:(app/'embedded.mobileprovision').write_bytes(b'fixture')),
    ('reject nested signature directory',lambda app,info:(app/'Resources/_CodeSignature').mkdir(parents=True)),
    ('reject symlink executable',lambda app,info:((app/'sightbreak').rename(app/'fixture-bin'),(app/'sightbreak').symlink_to('fixture-bin'))),
]:
    with app_fixture() as (_,app,export,info,record):
        change(app,info)
        rejects(name,lambda:ios.inspect_app(app,export,record))

for key,value in [('CFBundleIdentifier','wrong.bundle'),('CFBundleShortVersionString','9.9.9'),('CFBundleVersion','7'),('DTPlatformName','iphonesimulator'),('CFBundleSupportedPlatforms',['iPhoneSimulator']),('CFBundleExecutable','other')]:
    with app_fixture() as (_,app,export,info,record):
        info[key]=value;(app/'Info.plist').write_bytes(plistlib.dumps(info))
        rejects('reject changed app '+key,lambda:ios.inspect_app(app,export,record))

with app_fixture() as (_,app,export,_,record):
    pack=app/'sightbreak.pck'
    with pack.open('r+b') as stream:
        stream.seek(160);old=stream.read(1);stream.seek(160);stream.write(bytes([old[0]^1]))
    rejects('reject same-size one-byte built PCK tamper',lambda:ios.inspect_app(app,export,record))
with app_fixture() as (_,app,export,_,record):
    pack=export/'ios/sightbreak.pck'
    with pack.open('r+b') as stream:
        stream.seek(160);old=stream.read(1);stream.seek(160);stream.write(bytes([old[0]^1]))
    rejects('reject same-size exported PCK tamper',lambda:ios.inspect_app(app,export,record))
with app_fixture() as (_,app,export,_,record):
    record['payload'] += [copy.deepcopy(next(p for p in record['payload'] if p['path']=='ios/sightbreak.pck'))]
    rejects('reject duplicate manifest PCK provenance',lambda:ios.inspect_app(app,export,record))

def live(pid):
    result=subprocess.run(['ps','-o','stat=','-p',str(pid)],capture_output=True,text=True,timeout=2)
    return bool(result.stdout.strip()) and not result.stdout.strip().startswith('Z')

def wait_dead(pid):
    deadline=time.monotonic()+2
    while time.monotonic()<deadline and live(pid):time.sleep(0.02)
    return not live(pid)

def cleanup(pid):
    if live(pid):
        try:os.kill(pid,signal.SIGKILL)
        except ProcessLookupError:pass

def child_code(pidfile,marker,close_output=False):
    return ('import os,pathlib,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); '
            +("os.close(1);os.close(2); " if close_output else '')
            +'pathlib.Path('+repr(str(pidfile))+').write_text(str(os.getpid())); '
            +'time.sleep(1.2);pathlib.Path('+repr(str(marker))+').write_text("escaped");time.sleep(10)')

process_records=[]
for scenario in ('timed-out leader with TERM-resistant child','leader exits0 with child stdout closed'):
    with tempfile.TemporaryDirectory(prefix='critic-ios-process-') as tmp:
        root=Path(tmp);pidfile=root/'child.pid';marker=root/'survival-marker'
        child=child_code(pidfile,marker,scenario.startswith('leader'))
        parent='import subprocess,sys,time,pathlib; subprocess.Popen([sys.executable,"-c",'+repr(child)+']);\nwhile not pathlib.Path('+repr(str(pidfile))+').exists():time.sleep(.01)\n'
        if scenario.startswith('timed'):parent+='print("parent-ready",flush=True);time.sleep(10)'
        try:
            record=ios.bounded_command([sys.executable,'-c',parent],OUT/('timeout-child.log' if scenario.startswith('timed') else 'zero-exit-child.log'),.25 if scenario.startswith('timed') else 2)
            child_pid=int(pidfile.read_text())
            assert record['cleanup_complete'],record
            assert record['timed_out']==scenario.startswith('timed'),record
            if scenario.startswith('leader'):assert record['unexpected_descendants'],record
            assert wait_dead(child_pid)
            time.sleep(1.25)
            assert not marker.exists()
            process_records.append({'scenario':scenario,'result':record,'child_stopped':True,'marker_absent':True})
            note(scenario,record)
        finally:
            if pidfile.exists():cleanup(int(pidfile.read_text()))

# Cleanup failures must not be qualified even if the leader eventually dies.
with tempfile.TemporaryDirectory(prefix='critic-ios-kill-failure-') as tmp:
    pidfile=Path(tmp)/'leader.pid'
    command=[sys.executable,'-c','import os,pathlib,time;pathlib.Path('+repr(str(pidfile))+').write_text(str(os.getpid()));time.sleep(10)']
    try:
        with patch.object(ios.os,'killpg',side_effect=PermissionError('critic injected killpg denial')):
            record=ios.bounded_command(command,OUT/'killpg-denied.log',.1)
        assert record['timed_out'] and not record['cleanup_complete'] and record['cleanup_errors'],record
        process_records.append({'scenario':'killpg denied','result':record})
        note('killpg failure retains timeout and failed cleanup',record)
    finally:
        if pidfile.exists():cleanup(int(pidfile.read_text()))

# Exercise the real CLI's SIGTERM handler plus real bounded-command finally block.
# Apple host values are explicitly synthetic; export/compiler commands never run.
with tempfile.TemporaryDirectory(prefix='critic-ios-signal-') as tmp:
    root=Path(tmp);pidfile=root/'child.pid';marker=root/'survival-marker';output=OUT/'sigterm-fixture'
    child=child_code(pidfile,marker)
    parent='import subprocess,sys,time,pathlib; subprocess.Popen([sys.executable,"-c",'+repr(child)+']);\nwhile not pathlib.Path('+repr(str(pidfile))+').exists():time.sleep(.01)\nprint("signal-fixture-ready",flush=True);time.sleep(10)'
    wrapper="""import sys
sys.path.insert(0, {scripts!r})
import qualify_ios_compile as ios
ios.platform.system=lambda:'Darwin'
ios.platform.machine=lambda:'arm64'
original=ios.bounded_command
def fixture_command(command,log,seconds,env=None):
    return original([sys.executable,'-c',{parent!r}],log,10,env=env)
ios.bounded_command=fixture_command
sys.argv=['qualify_ios_compile.py','--output',{output!r},'--builds',{export!r},'--derived-data',{derived!r},'--timeout','30']
raise SystemExit(ios.main())
""".format(scripts=str(ROOT/'scripts'),parent=parent,output=str(output),export=str(root/'export'),derived=str(root/'derived'))
    (OUT/'sigterm-fixture-wrapper.py').write_text(wrapper)
    with (OUT/'sigterm-cli.log').open('w') as stream:
        worker=subprocess.Popen([sys.executable,'-c',wrapper],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        try:
            deadline=time.monotonic()+3
            while time.monotonic()<deadline and not pidfile.exists():time.sleep(.02)
            assert pidfile.exists(),'cancellation fixture never became ready'
            os.kill(worker.pid,signal.SIGTERM)
            status=worker.wait(timeout=8)
            report=json.loads((output/'compile.json').read_text())
            assert status==1 and report['status']=='FAILED' and not report['compile_completed'],report
            assert 'Interrupted by signal 15' in report['failure'],report
            assert wait_dead(int(pidfile.read_text()))
            time.sleep(1.25);assert not marker.exists()
            note('real CLI SIGTERM unwinds owned descendant and preserves FAILED receipt',{'exit_code':status,'report':report,'child_stopped':True,'marker_absent':True})
        finally:
            if worker.poll() is None:os.killpg(worker.pid,signal.SIGKILL);worker.wait(timeout=3)
            if pidfile.exists():cleanup(int(pidfile.read_text()))

# Full helper rejects this actual Linux host and writes its failure receipt.
native_output=OUT/'actual-linux-rejection'
argv=[sys.executable,str(ROOT/'scripts/qualify_ios_compile.py'),'--output',str(native_output),'--builds',str(OUT/'unused-linux-export'),'--derived-data',str(OUT/'unused-linux-derived'),'--timeout','30']
result=subprocess.run(argv,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=10)
(OUT/'actual-linux-rejection.log').write_text(result.stdout+result.stderr)
report=json.loads((native_output/'compile.json').read_text())
assert result.returncode==1 and report['status']=='FAILED' and not report['compile_completed'] and report['commands']==[]
note('actual Linux helper exits1 with failure receipt, no export or Apple command',{'argv':argv,'exit_code':result.returncode,'report':report})

# Exercise actual source snapshot machinery on a tiny disposable Git fixture.
with tempfile.TemporaryDirectory(prefix='critic-ios-source-') as tmp:
    root=Path(tmp);(root/'game').mkdir();(root/'scripts').mkdir()
    for name in ('project.godot','export_presets.cfg'):shutil.copyfile(ROOT/'game'/name,root/'game'/name)
    (root/'scripts/probe.py').write_text('print("fixture")\n')
    subprocess.run(['git','init','-q'],cwd=root,check=True)
    subprocess.run(['git','add','.'],cwd=root,check=True)
    subprocess.run(['git','-c','user.name=Review Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],cwd=root,check=True)
    with patch.object(ios.manifest,'ROOT',root):
        clean=ios.manifest.source();ios.manifest.clean(clean)
        (root/'untracked.txt').write_text('fixture dirty source')
        rejects('untracked source dirt rejected by actual manifest machinery',lambda:ios.manifest.clean(ios.manifest.source()))
        (root/'untracked.txt').unlink()
        (root/'scripts/probe.py').write_text('print("changed fixture")\n')
        changed=ios.manifest.source()
        assert changed['source_validation_sha256']!=clean['source_validation_sha256']
        rejects('validation script dirt rejected by actual manifest machinery',lambda:ios.manifest.clean(changed))
        note('validation script content change alters source validation hash')

# The native payload directories are siblings of QA. The real packer must omit
# even native files injected under the selected receipt tree.
with tempfile.TemporaryDirectory(prefix='critic-ios-qa-') as tmp:
    root=Path(tmp);source=root/'desktop-playability';receipts=source/'ios-compile';receipts.mkdir(parents=True)
    (receipts/'compile.json').write_text('{"fixture":true}\n');(receipts/'xcodebuild.log').write_text('fixture log\n')
    (receipts/'libgodot.a').write_bytes(b'native fixture');(receipts/'sightbreak.pck').write_bytes(b'native fixture')
    (source/'Export.app').mkdir();(source/'Export.app/Info.plist').write_bytes(b'native fixture')
    sibling=root/'ios-device-derived';sibling.mkdir();(sibling/'libgodot.a').write_bytes(b'native fixture')
    receipt=qa.package(source,root/'qa-receipts.zip')
    import zipfile
    with zipfile.ZipFile(root/'qa-receipts.zip') as z:names=z.namelist()
    assert set(names)=={'evidence/ios-compile/compile.json','evidence/ios-compile/xcodebuild.log','qa-receipts-index.json'},names
    note('actual QA packer includes only logs and JSON, excludes injected and sibling native payloads',{'receipt':receipt,'entries':names})

(OUT/'process-control-receipts.json').write_text(json.dumps(process_records,indent=2)+'\n')
after=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
assert not after,after
note('review source remains clean at exact ac3cfde',subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
