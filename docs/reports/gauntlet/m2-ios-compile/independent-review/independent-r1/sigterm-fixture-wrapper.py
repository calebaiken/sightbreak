import sys
sys.path.insert(0, '/workspace/reviews/ios-compile-critic/source571e8c7/scripts')
import qualify_ios_compile as ios
ios.platform.system=lambda:'Darwin'
ios.platform.machine=lambda:'arm64'
original=ios.bounded_command
def fixture_command(command,log,seconds,env=None):
    return original([sys.executable,'-c','import subprocess,sys,time,pathlib; subprocess.Popen([sys.executable,"-c",\'import os,pathlib,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path(\\\'/tmp/critic-ios-signal-q9pvzhkj/child.pid\\\').write_text(str(os.getpid())); time.sleep(1.2);pathlib.Path(\\\'/tmp/critic-ios-signal-q9pvzhkj/survival-marker\\\').write_text("escaped");time.sleep(10)\']);\nwhile not pathlib.Path(\'/tmp/critic-ios-signal-q9pvzhkj/child.pid\').exists():time.sleep(.01)\nprint("signal-fixture-ready",flush=True);time.sleep(10)'],log,10,env=env)
ios.bounded_command=fixture_command
sys.argv=['qualify_ios_compile.py','--output','/workspace/reviews/ios-compile-critic/evidence/independent-r1/sigterm-fixture','--builds','/tmp/critic-ios-signal-q9pvzhkj/export','--derived-data','/tmp/critic-ios-signal-q9pvzhkj/derived','--timeout','30']
raise SystemExit(ios.main())
