"""Audit retained native Windows OCR bytes/captions without executing OCR."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re

READ=lambda p:json.loads(p.read_text())
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def caption_boxes(text,caption):
    grouped={}
    for row in csv.DictReader(io.StringIO(text),delimiter='\t'):
        if not row.get('text','').strip():continue
        identity=tuple(row.get(k) for k in ('page_num','block_num','par_num','line_num'))
        if any(v in (None,'') for v in identity):continue
        grouped.setdefault(identity,[]).append(row)
    boxes=[]
    for rows in grouped.values():
        rows.sort(key=lambda r:int(r['left']))
        if [r['text'].upper() for r in rows]!=caption.split():continue
        left=min(int(r['left'])//2 for r in rows);top=min(int(r['top'])//2 for r in rows)
        right=max(int(r['left'])//2+int(r['width'])//2 for r in rows)
        bottom=max(int(r['top'])//2+int(r['height'])//2 for r in rows)
        boxes.append({'left':left,'top':top,'width':right-left,'height':bottom-top,'caption':caption})
    return boxes

def audit(root):
    directory=root/'evidence/offline-input';receipt=READ(directory/'results.json');commands=READ(directory/'ocr-commands.json');actions=READ(directory/'actions.json')
    raw=[]
    for index,entry in enumerate(commands,1):
        path=directory/entry['stdout_path'];data=path.read_bytes()
        raw.append({'call':index,'label':entry['label'],'stdout_path':entry['stdout_path'],
                    'bytes':len(data),'sha256':SHA(path),'hash_matches':SHA(path)==entry['stdout_sha256'],
                    'byte_counts_match':len(data)==entry['stdout_total_bytes']==entry['stdout_retained_bytes'],
                    'complete_untruncated':entry['stdout_complete'] is True and entry['stdout_truncated'] is False,
                    'exit_code':entry['exit_code'],'timed_out':entry.get('timed_out',False),
                    'started_seconds':entry['started_seconds'],'finished_seconds':entry['finished_seconds'],
                    'command':entry['command']})
    leaves=[a for a in actions if a['event']=='click_text' and a.get('caption')=='LEAVE MATCH']
    if not leaves:
        hud=[]
        for capture in ('05-after-fire','06-after-reload','06e-purchased-smg','06f-switched-sidearm','06g-switched-primary','07d-explicit-resume'):
            health=next((e for e in commands if e['label']==capture+':(0, 630, 450, 720)'),None)
            ammo=next((e for e in commands if e['label']==capture+':(980, 648, 1280, 680)'),None)
            item={'capture':capture,'both_original_stdout_calls_available':bool(health and ammo)}
            if health and ammo:
                health_text=(directory/health['stdout_path']).read_text()
                ammo_text=(directory/ammo['stdout_path']).read_text()
                h=re.search(r'(?<!\d)(\d{1,3})\s*[^A-Z0-9]*HEALTH',health_text.upper())
                a=re.search(r'(\d+)\s*/\s*(\d+)',ammo_text)
                item['parsed_original_stdout']={'health':int(h[1]) if h else None,'ammo':int(a[1]) if a else None,'reserve':int(a[2]) if a else None,'health_text':health_text,'ammo_text':ammo_text}
            hud.append(item)
        checks={'all_per_call_original_stdout_bytes_match':all(e['hash_matches'] and e['byte_counts_match'] and e['complete_untruncated'] for e in raw),
                'all_OCR_exits_zero_without_timeout':all(e['exit_code']==0 and e['timed_out'] is False for e in raw),
                'unique_retained_file_per_call':len({e['stdout_path'] for e in raw})==len(raw),
                'sidecar_matches_native_result_commands':commands==receipt['ocr_commands'],
                'whole_ordinary_journey_passed':False,'strict_actual_LEAVE_and_heading_captions':False,
                'actual_LEAVE_return_and_capture_within_original_30s':False,
                'numeric_HUD_readings_recomputed_from_original_stdout':False}
        return {'checks':checks,'all_checks_passed':False,'calls':raw,'LEAVE_call':None,'LEAVE_unreached':True,
                'original_error':receipt.get('error'),'HUD_original_stdout_recomputation':hud,
                'missing_success_only_numeric_result_fields':[key for key in ('fired_hud','reloaded_hud','resumed_hud') if key not in receipt],
                'scope':'Earlier native failure precedes LEAVE and resumed-HUD OCR. Reached stdout originals are audited; missing calls and success-only comparisons remain unavailable, not invented or passed. No OCR is run.'}
    leave=leaves[0]
    candidates=[(i,e) for i,e in enumerate(commands) if e['label']=='current-native-ui' and e['finished_seconds']<=leave['seconds']]
    index,entry=max(candidates,key=lambda pair:pair[1]['finished_seconds'])
    text=(directory/entry['stdout_path']).read_bytes().decode('utf-8',errors='replace');heading=caption_boxes(text,'FIELD MENU');control=caption_boxes(text,'LEAVE MATCH')
    return_wait=next(a for a in actions if a['event']=='wait_completed' and a.get('label')=='Return from offline match' and a['seconds']>leave['seconds'])
    captures=[a for a in actions if a['event']=='capture_end' and a.get('capture')=='08-return-menu' and a['seconds']>return_wait['seconds']]
    pauses=receipt['hud_analysis_pauses'];last=next(p for p in pauses if p['capture']=='07d-explicit-resume')
    actor=last['before']['local_actor'];states=[last[k] for k in ('before','paused','after_analysis')]
    hud=[]
    for capture,key in [('05-after-fire','fired_hud'),('06-after-reload','reloaded_hud'),('07d-explicit-resume','resumed_hud')]:
        health_entry=next(e for e in commands if e['label']==capture+':(0, 630, 450, 720)')
        ammo_entry=next(e for e in commands if e['label']==capture+':(980, 648, 1280, 680)')
        health_text=(directory/health_entry['stdout_path']).read_bytes().decode('utf-8',errors='replace')
        ammo_text=(directory/ammo_entry['stdout_path']).read_bytes().decode('utf-8',errors='replace')
        health=re.search(r'(?<!\d)(\d{1,3})\s*[^A-Z0-9]*HEALTH',health_text.upper())
        ammo=re.search(r'(\d+)\s*/\s*(\d+)',ammo_text)
        parsed={'health':int(health[1]),'ammo':int(ammo[1]),'reserve':int(ammo[2]),'status_ocr':health_text,'ammo_ocr':ammo_text}
        hud.append({'capture':capture,'parsed_original_stdout':parsed,'native_numeric_receipt_available':key in receipt,'matches_receipt':parsed==receipt.get(key),
                    'living_reading':0<parsed['health']<=100 and all(word not in health_text.upper() for word in ('ELIMINATED','SPECTATING'))})
    checks={'all_per_call_original_stdout_bytes_match':all(e['hash_matches'] and e['byte_counts_match'] and e['complete_untruncated'] for e in raw),
            'all_OCR_exits_zero_without_timeout':all(e['exit_code']==0 and e['timed_out'] is False for e in raw),
            'unique_retained_file_per_call':len({e['stdout_path'] for e in raw})==len(raw),
            'sidecar_matches_native_result_commands':commands==receipt['ocr_commands'],
            'whole_ordinary_journey_passed':receipt['passed'] is True and receipt['elapsed_seconds']<300,
            'strict_actual_LEAVE_and_heading_captions':len(control)==len(heading)==1 and leave.get('heading')=='FIELD MENU',
            'actual_LEAVE_return_and_capture_within_original_30s':0<return_wait['seconds']-leave['seconds']<30 and len(captures)==1,
            'actual_living_same_player_HUD_pause_context':all(s['local_actor']['alive'] is True and s['local_actor']['health']>0 and s['ui']['focused'] is True and s['time_scale']==1 and all(s['local_actor'][k]==actor[k] for k in ('id','weapon','ammo','reserve')) for s in states),
            'HUD_pause_stays_frozen_through_analysis':last['paused']['elapsed']==last['after_analysis']['elapsed'] and last['paused']['local_actor']['health']==last['after_analysis']['local_actor']['health'],
            'pause_retained_for_LEAVE':last['resume_after_analysis'] is False and 'resumed' not in last}
    checks['numeric_HUD_readings_recomputed_from_original_stdout']=all(h['matches_receipt'] and h['living_reading'] for h in hud)
    return {'checks':checks,'all_checks_passed':all(checks.values()),'calls':raw,'LEAVE_call':index+1,'LEAVE_stdout_path':entry['stdout_path'],
            'FIELD_MENU_boxes':heading,'LEAVE_MATCH_boxes':control,'LEAVE_action':leave,'return_wait':return_wait,
            'actual_return_capture_actions':captures,'LEAVE_return_wall_seconds':return_wait['seconds']-leave['seconds'],
            'HUD_original_stdout_recomputation':hud,
            'scope':'Original native stdout/caption and journey evidence only. Individual LEAVE before/after guard reads execute in the frozen controller but are not separately serialized; original per-call input PNGs are not all retained. No new OCR is run.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=audit(args.root);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'all_checks_passed':result['all_checks_passed'],'calls':len(result['calls']),'LEAVE_call':result['LEAVE_call']}))
