"""Compare frozen current source to accepted component and old Windows controls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

SOURCE='05277154c6b8c92b80fd7c25e8365de9efdc4fae'
RECOVERY='79e076ed83651aea3ff8e439a64c0f979d35ecf2'
PREVIOUS='3b5cf7640e256dff404b401bf2b27ffaff157bdd'


def audit(repo, identity):
    git=lambda *args:subprocess.check_output(['git',*args],cwd=repo)
    checks={}
    for path in ('game/scripts/ui/economy_ui.gd','game/scripts/ui/transaction_journal.gd',
                 'game/tests/transaction_journal_test.gd','game/tests/gunplay_rules_probe.gd'):
        checks['accepted_component_bytes:'+path]=git('show',SOURCE+':'+path)==git('show',RECOVERY+':'+path)
    for path in ('scripts/verify_offline_export.py','scripts/verify_offline_match.py',
                 'scripts/verify_integration_export.py','scripts/native_log.py'):
        checks['prior_Windows_control_bytes:'+path]=git('show',SOURCE+':'+path)==git('show',PREVIOUS+':'+path)
    checks['accepted_recovery_game_tree']=identity['source_game_tree']=='1f3616afdfaaed0fb7c9ffbd0aa8e4947f7d2a48'
    checks['accepted_recovery_shipping_digest']=identity['source_content_sha256']=='6bebcf50351c29d4c9959bfe4b33418f8f7b4a2e963e65336f361e99891f07b5'
    runner=git('show',SOURCE+':scripts/run_native_regressions.py')
    runner_hash=hashlib.sha256(runner).hexdigest()
    checks['accepted_registration_runner']=runner_hash=='4d13e981f9a16581ba8247028dc3688f06db814e357b1a0b346257b13e93f5af'
    validation=git('show',SOURCE+':scripts/validate.sh').decode()
    checks['validator_includes_journal_and_Dummy_gunplay']=all(s in validation for s in
        ('transaction_journal_test.gd','--audio-driver Dummy --script res://tests/gunplay_rules_probe.gd'))
    return {'checks':checks,'all_checks_passed':all(checks.values()),'source_commit':SOURCE,
            'source_game_tree':identity['source_game_tree'],'shipping_sha256':identity['source_content_sha256'],
            'LF_validation_sha256':identity['source_validation_sha256'],'runner_sha256':runner_hash,
            'scope':'Frozen Git bytes only; older Windows and fixture results cannot substitute for current native execution.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('repo',type=Path);p.add_argument('identity',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=audit(a.repo,json.loads(a.identity.read_text()));a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
