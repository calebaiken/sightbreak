"""Real Windows CPython-only verifier regression; no engine/export is launched."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch


def run_control(verifier, output):
    output.mkdir()
    ready, ack, returned = (output / name for name in ('ready.json', 'observed', 'returned'))
    child = ("import os,pathlib,sys,time; p=pathlib.Path(sys.argv[1]); "
             "print('DESCENDANT_READY pid='+str(os.getpid()),flush=True); "
             "deadline=time.monotonic()+8\n"
             "while not p.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
             "print('ERROR: verifier descendant late control',flush=True); sys.exit(23)")
    root = ("import json,os,pathlib,subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-B','-c',sys.argv[1],sys.argv[4]],close_fds=True); "
            "pathlib.Path(sys.argv[2]).write_text(json.dumps({'root':os.getpid(),'child':p.pid})); "
            "deadline=time.monotonic()+8\n"
            "while not pathlib.Path(sys.argv[3]).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
            "print('ROOT_EXIT_ZERO',flush=True); os._exit(0)")
    observed = {}

    def observe():
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        api.WaitForSingleObject.restype = wintypes.DWORD
        api.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        api.GetExitCodeProcess.restype = wintypes.BOOL
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.CloseHandle.restype = wintypes.BOOL
        handles = {}
        try:
            deadline = time.monotonic() + 10
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(.01)
            pids = json.loads(ready.read_text())
            observed['pids'] = pids
            for name, pid in pids.items():
                handle = api.OpenProcess(0x1000 | 0x100000, False, pid)
                if not handle:
                    raise ctypes.WinError(ctypes.get_last_error())
                handles[name] = handle
            ack.touch()
            for name in ('root', 'child'):
                if api.WaitForSingleObject(handles[name], 12000) != 0:
                    raise RuntimeError(name + ' did not exit in bounded control')
                code = wintypes.DWORD()
                if not api.GetExitCodeProcess(handles[name], ctypes.byref(code)):
                    raise ctypes.WinError(ctypes.get_last_error())
                observed[name + '_exit'] = code.value
        except Exception as error:
            observed['error'] = repr(error)
        finally:
            for handle in handles.values():
                api.CloseHandle(handle)

    observer = threading.Thread(target=observe, daemon=True)
    observer.start()
    command = [sys.executable, '-B', '-c', root, child, str(ready), str(ack), str(returned)]
    attempt = verifier.VerificationAttempt(output / 'attempt', 'REAL CPython-only descendant control; synthetic source identity, not a game/export pass')
    current = {'source_commit': 'control-only', 'source_game_tree': 'not-game',
               'source_content_sha256': hashlib.sha256((root + child).encode()).hexdigest(),
               'source_validation_sha256': hashlib.sha256(Path(verifier.__file__).read_bytes()).hexdigest(),
               'source_game_dirty': False, 'source_dirty': False}
    with patch.object(verifier, 'source', return_value=current):
        code = attempt.execute(lambda run: run.run('descendant', command, timeout=12))
    raw = attempt.output / 'descendant.log'
    (output / 'returned.log').write_bytes(raw.read_bytes())
    returned.touch()
    observer.join(timeout=15)
    (output / 'settled.log').write_bytes(raw.read_bytes())
    result = {'verifier_exit': code, 'passed': attempt.report['passed'], 'observed': observed,
              'observer_finished': not observer.is_alive(), 'command_exit': attempt.report['processes'][0]['exit'],
              'returned_log': (output / 'returned.log').read_text(encoding='utf-8', errors='replace'),
              'settled_log': (output / 'settled.log').read_text(encoding='utf-8', errors='replace')}
    (output / 'control.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', choices=('before', 'after'), required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.checkout / 'scripts'))
    import verify_builds
    result = run_control(verify_builds, args.output)
    if args.phase == 'before':
        matched = (result['verifier_exit'] == 0 and result['passed'] is True
                   and result['observed'].get('root_exit') == 0 and result['observed'].get('child_exit') == 23
                   and 'ERROR:' not in result['returned_log'] and 'ERROR:' in result['settled_log'])
    else:
        matched = (result['verifier_exit'] == 1 and result['passed'] is False
                   and result['observed'].get('root_exit') == 0 and result['observed'].get('child_exit') == 1
                   and result['command_exit'] == 0 and 'HARNESS_ERROR' in result['returned_log'])
    print(json.dumps({'phase': args.phase, 'expected_control_matched': matched, **result}, indent=2))
    raise SystemExit(0 if matched and result['observer_finished'] and 'error' not in result['observed'] else 1)
