#!/usr/bin/env python3
import hashlib, json, os, pathlib, subprocess, sys, time
R = pathlib.Path('/workspace/reviews/authority-order-critic')
K = ['game/scripts/gameplay/actor.gd','game/scripts/gameplay/match.gd','game/tests/authority_order_test.gd','scripts/validate.sh','game/scripts/network/movement_step.gd','game/scripts/network/state_privacy.gd','game/scripts/network/hit_history.gd']
def run(side, label, args):
    env = dict(os.environ, SIGHTBREAK_TOOLS_DIR='/workspace/tools', SIGHTBREAK_STATE_DIR=str(R / 'state' / side / label))
    cmd = ['./scripts/godot.sh', *args]
    begin = time.time()
    with (R / f'{side}-{label}.log').open('w') as out:
        result = subprocess.run(cmd, cwd=R/side, env=env, stdout=out, stderr=subprocess.STDOUT, timeout=540)
    receipt = {'side':side, 'label':label,'command':cmd,'cwd':str(R/side),'state':env['SIGHTBREAK_STATE_DIR'],'exit_code':result.returncode,'elapsed_seconds':time.time()-begin,'log_sha256':hashlib.sha256((R/f'{side}-{label}.log').read_bytes()).hexdigest()}
    (R/f'{side}-{label}.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt), flush=True)
    return result.returncode
if __name__ == '__main__':
    mode = sys.argv[1]
    side = sys.argv[2]
    if mode == 'initial':
        run(side,'import',['--headless','--editor','--import','--quit'])
        run(side,'oracle',['--headless','--script','res://tests/authority_order_test.gd'])
    elif mode == 'regressions':
        for label in ['actor','hit_feedback','weapon_integrity','hit_history','match','state_privacy','movement_prediction','input_lifecycle','input_stream','bot_ai_regression','bot_lifecycle']:
            run(side,label,['--headless','--script',f'res://tests/{label}_test.gd'])
    elif mode == 'benchmark':
        run(side,'benchmark_original',['--headless','--script','res://tests/authority_order_test.gd','--','--benchmark'])
    elif mode == 'instrumented':
        run(side,'old_benchmark_instrumented',['--headless','--script','res://tests/critic_old_benchmark_instrumented.gd','--','--benchmark'])
    elif mode == 'reviewed':
        run(side,'reviewed_oracle',['--headless','--script','res://tests/authority_order_test.gd'])
        run(side,'reviewed_benchmark_growth',['--headless','--script','res://tests/critic_reviewed_benchmark.gd','--','--benchmark-only'])
    elif mode.startswith('negative'):
        run(side,'critic_' + mode,['--headless','--script','res://tests/critic_authority_negative.gd'])
