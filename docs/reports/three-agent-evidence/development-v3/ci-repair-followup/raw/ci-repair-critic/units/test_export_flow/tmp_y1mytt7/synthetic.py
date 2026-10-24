import argparse, json, os, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, 'C:\\Users\\blith\\AppData\\Local\\Temp\\opencode\\sightbreak-v3\\scripts')
import export_flow

def main(supervised=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=float, required=True)
    args = parser.parse_args()
    out = export_flow.prepare_flow_output(args.output, supervised)
    state = json.loads((out / 'watchdog.json').read_text())
    initial = json.loads((out / 'results.json').read_text())
    assert state['token'] == os.environ[export_flow.TOKEN_ENV]
    assert state['status'] == initial['status'] == 'incomplete'
    assert state['passed'] is initial['passed'] is False
    (out.parent / 'worker-initial.json').write_text(json.dumps(initial))
    print('synthetic worker validated owner token', flush=True)
    options = {}
    if True:
        options = ({'creationflags': 0x200} if os.name == 'nt'
                   else {'start_new_session': True})
    child = subprocess.Popen([sys.executable, '-B', '-c', 'from pathlib import Path; import os, time; print("synthetic descendant partial output", flush=True); Path(\'C:\\\\Users\\\\blith\\\\AppData\\\\Local\\\\Temp\\\\opencode\\\\sol-ci-repair-critic-20261024T085242Z\\\\units\\\\test_export_flow\\\\tmp_y1mytt7\\\\child-started\').write_text(str(os.getpid())); time.sleep(1.1); print("ERROR: late synthetic descendant", flush=True); Path(\'C:\\\\Users\\\\blith\\\\AppData\\\\Local\\\\Temp\\\\opencode\\\\sol-ci-repair-critic-20261024T085242Z\\\\units\\\\test_export_flow\\\\tmp_y1mytt7\\\\child-finished\').write_text("finished")'], **options)
    if False:
        child.wait()
    else:
        while not Path('C:\\Users\\blith\\AppData\\Local\\Temp\\opencode\\sol-ci-repair-critic-20261024T085242Z\\units\\test_export_flow\\tmp_y1mytt7\\child-started').exists():
            time.sleep(.005)
    (out / 'results.json').write_text(json.dumps(
        {'passed': True, 'synthetic_control_not_native_evidence': True}))
    if False:
        time.sleep(30)

if __name__ == '__main__':
    raise SystemExit(export_flow.entry(main, __file__))
