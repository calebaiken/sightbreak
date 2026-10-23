"""Port prior independent, read-only receipt auditors to this exact candidate."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
OLD = 'docs/reports/gauntlet/windows-0527715-39741504894/'
SOURCE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'
FILES = ['verify_receipts.py', 'audit_full_qa.py', 'audit_gunplay.py', 'audit_journey_ocr.py',
         'audit_native_commands.py', 'audit_objective_stages.py', 'audit_phase_captures.py',
         'audit_raw_sources_logs.py', 'audit_windows_source.py', 'audit_export_identity.py',
         'safe_extract.py', 'recompute_source.py']
manifest = []
for name in FILES:
    original = subprocess.check_output(['git', 'show', SOURCE + ':' + OLD + name])
    value = original.decode()
    transforms = []
    def replace(old, new):
        global value
        if old not in value:
            raise ValueError('Missing exact port edit in ' + name + ': ' + repr(old))
        value = value.replace(old, new)
        transforms.append({'old': old, 'new': new})
    if '05277154c6b8c92b80fd7c25e8365de9efdc4fae' in value:
        replace('05277154c6b8c92b80fd7c25e8365de9efdc4fae', SOURCE)
    if '39741504894' in value:
        replace('39741504894', '39907358390')
    if name in ('verify_receipts.py', 'audit_native_commands.py'):
        replace("'transaction_journal',", "'bot_dry_weapon','transaction_journal',")
        replace('fourteen', 'fifteen')
    if name == 'verify_receipts.py':
        replace('|GUNPLAY_RULES ', '|GUNPLAY_RULES |BOT_DRY_WEAPON_RESULT ')
    if name == 'audit_native_commands.py':
        replace('2722, 41, 2840', '2722, 590, 41, 2840')
        replace("if suite == 'gunplay_rules' else", "if suite == 'gunplay_rules' else ['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/bot_dry_weapon_test.gd'] if suite == 'bot_dry_weapon' else")
        replace("        if suite == 'transaction_journal':", "        if suite == 'bot_dry_weapon':\n            native = [json.loads(line.removeprefix('BOT_DRY_WEAPON_RESULT ')) for line in log.splitlines() if line.startswith('BOT_DRY_WEAPON_RESULT ')]\n            counts = [(r['checks'], r['failures']) for r in native]\n        if suite == 'transaction_journal':")
        replace('distinct_29_native_producers', 'distinct_31_native_producers')
        replace("== 29", "== 31")
    raw = value.encode()
    (ROOT / name).write_bytes(raw)
    manifest.append({'name': name, 'original_git_path': OLD + name,
                     'original_sha256': hashlib.sha256(original).hexdigest(),
                     'ported_sha256': hashlib.sha256(raw).hexdigest(), 'edits': transforms})
name = 'recompute_dry_observable.py'
path = 'docs/reports/gauntlet/m5-dry-weapon-recovered-independent/recompute_observable.py'
raw = subprocess.check_output(['git', 'show', SOURCE + ':' + path])
(ROOT / name).write_bytes(raw)
manifest.append({'name': name, 'original_git_path': path, 'original_sha256': hashlib.sha256(raw).hexdigest(),
                 'ported_sha256': hashlib.sha256(raw).hexdigest(), 'edits': []})
(ROOT / 'auditor-port-provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'ported_read_only_auditors': len(manifest)}))
