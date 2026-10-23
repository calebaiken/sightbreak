"""Read-only recomputation from transferred native CI raw receipt artifacts.

This never launches Godot or supplies replacement evidence for missing PNGs.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

SOURCE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'
RULES = {'buy_seconds':15, 'round_seconds':100, 'device_seconds':35,
         'plant_seconds':3, 'defuse_seconds':5, 'win_score':7}
SUITES = ['actor','match','authority_order','state_privacy','movement_prediction',
          'peer_lifecycle','input_mode','menu_focus','offline_diagnostics','hud_objective_hint',
          'activity_provenance','bot_squad_symmetry','bot_dry_weapon','transaction_journal','gunplay_rules']
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
lines = lambda path: [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
clean = lambda text: re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', text, re.M) is None

def identity(receipt):
    source = receipt.get('source', receipt.get('authority_source', {}))
    return (source.get('source_commit') == SOURCE and source.get('source_dirty') is False
            and source.get('source_game_dirty') is False)

def exits(receipt):
    return (receipt.get('cleanup_errors') == [] and bool(receipt.get('commands'))
            and all(command.get('exit_code') == 0 for command in receipt['commands']))

def index_check(root):
    index = read(root/'qa-receipts-index.json')
    failures = []
    for entry in index['files']:
        path = root/entry['archive_path']
        if not path.is_file() or path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            failures.append(entry['path'])
    expected = {entry['archive_path'] for entry in index['files']}
    actual = {path.relative_to(root).as_posix() for path in (root/'evidence').rglob('*') if path.is_file()}
    return {'files':len(expected),'all_sizes_and_hashes_match':not failures,
            'complete_selected_file_set':actual==expected,'failures':failures}

def regressions(base):
    isolation = read(base/'regressions/isolation.json')
    results = read(base/'regressions/results.json')
    before = [item['before'] for item in results]
    after = [item['after'] for item in results]
    retained_produced=[]
    missing_produced=[]
    mismatched_produced=[]
    native_summaries={}
    hud_log=(base/'regressions/hud_objective_hint.log').read_text(errors='replace')
    hud_cleanup=[json.loads(line.split('HUD_OBJECTIVE_HINT_TEST_CLEANUP ',1)[1])
                 for line in hud_log.splitlines() if line.startswith('HUD_OBJECTIVE_HINT_TEST_CLEANUP ')]
    for item in results:
        suite=item['suite']
        native_summaries[suite]=[line for line in (base/'regressions'/(suite+'.log')).read_text(errors='replace').splitlines()
                                 if re.search(r'checks=\d+.*failures=\d+|\d+ checks, \d+ failures|\d+/\d+ passed|GUNPLAY_RULES |BOT_DRY_WEAPON_RESULT ',line)]
        for name,expected in item['produced_files_sha256'].items():
            path=base/'regressions'/(suite+'-userdata')/name
            if path.is_file():
                retained_produced.append(suite+'/'+name)
                if digest(path)!=expected:mismatched_produced.append(suite+'/'+name)
            else:
                missing_produced.append(suite+'/'+name)
    checks = {
        'fifteen_exact_maintained_suites':[item['suite'] for item in results] == SUITES,
        'all_native_exits_clean':all(item['exit']==0 and item['clean_log'] for item in results),
        'native_logs_clean':all(clean((base/'regressions'/(item['suite']+'.log')).read_text(errors='replace')) for item in results),
        'every_suite_has_native_assertion_summary':all(native_summaries.values()),
        'fresh_before_state':all(not item['profile_exists'] and not item['diagnostics_exist'] for item in before),
        'distinct_native_producer_paths':len({item['user_data_dir'] for item in before})==len(SUITES),
        'before_after_same_native_path':all(a['user_data_dir']==b['user_data_dir'] and a['custom_user_dir']==b['custom_user_dir'] for a,b in zip(before,after)),
        'native_custom_identity_selected':all(item['uses_custom_user_dir'] and item['custom_user_dir']==isolation['namespace']+'/'+suite for suite,item in zip(SUITES,before)),
        'native_path_matches_namespace':all(item['user_data_dir'].replace('\\','/').endswith('/'+item['custom_user_dir']) for item in before),
        'original_resources_unchanged':isolation['source_resources_unchanged'],
        'copied_resources_unchanged':isolation['copied_resources_unchanged'],
        'owned_cleanup_complete':isolation['temporary_project_removed'] and bool(isolation['cleanup']) and all(item['removed'] for item in isolation['cleanup']),
        'no_finalization_failure':isolation['failure'] is None and isolation['finalization_failures']==[],
        'isolation_pass_receipt':isolation['passed'],
        'retained_produced_files_match_hashes':not mismatched_produced,
        'separate_HUD_fixture_cleanup_attested':len(hud_cleanup)==1 and hud_cleanup[0]['owned'] is True and hud_cleanup[0]['removed'] is True and hud_cleanup[0]['original_user_dir_restored'] is True and hud_cleanup[0]['reason']=='' and hud_cleanup[0]['original_exit']==0 and hud_cleanup[0]['exit']==0,
    }
    return {'checks':checks,'all_checks_passed':all(checks.values()),
            'native_test_summaries':native_summaries,
            'retained_produced_files_verified':retained_produced,
            'produced_files_not_in_selected_receipts':missing_produced,
            'HUD_fixture_cleanup_native_receipts':hud_cleanup,
            'suites':[
        {'suite':item['suite'],'exit':item['exit'],'wall_seconds':item['wall_seconds'],
         'produced_files':item['produced_files_sha256'],'native_user_dir':item['before']['user_data_dir']}
        for item in results]}

def full_match(base):
    directory = base/'offline-full-match'
    receipt = read(directory/'results.json')
    events = lines(directory/'trace/events.jsonl')
    initial = events[0]
    completed = [item for item in events if item['event']=='completed']
    if len(completed)!=1:
        return {'single_completed_event':False,'receipt_passed':receipt.get('passed'),'error':receipt.get('error')}
    final = completed[0]
    summary = final['summary']
    old, after = initial['initial_profile'], final['training_after']
    reopen = lines(directory/'trace-reopened/events.jsonl')[0]['initial_profile']
    disk = read(next(directory.rglob('offline_training.json')))
    roster = summary['scoreboard']
    human = next(item for item in roster if item['local'])
    rounds = [item['round_number'] for item in events if item['event'] in ('initial','round_number')]
    seventh = next(item for item in events if item['event']=='round_number' and item['round_number']==7)
    xp = old['xp']+120+15*summary['kills']+50*summary['objectives']
    level = 1+int(math.sqrt(xp/150))
    earned = 100+75*int(summary['won'])+150*int(old['last_daily']!=after['last_daily'])+(level-old['level'])*250
    checks = {
        'clean_frozen_source':identity(receipt),'receipt_passed':receipt['passed'],
        'normal_stock_rules':initial['rules']==RULES and initial['initial_conditions']=='stock_spawns_teams_random_seeds' and initial['time_scale']==1,
        'protocol6_prediction_off':initial['protocol']==6 and initial['prediction_enabled'] is False,
        'all_natural_rounds_once':rounds==list(range(1,summary['rounds']+1)),
        'score_matches_stock_end':7<=summary['rounds']<=12 and 0<=min(summary['attack_score'],summary['defend_score'])<=max(summary['attack_score'],summary['defend_score'])<=7 and summary['attack_score']+summary['defend_score']==summary['rounds'] and (max(summary['attack_score'],summary['defend_score'])==7 or summary['rounds']==12),
        'halftime_side_swap':seventh['local_actor']['team']!=initial['local_actor']['team'],
        'ten_unique_actors_five_each_one_human':len(roster)==10 and len({item['id'] for item in roster})==10 and all(sum(item['team']==team for item in roster)==5 for team in (0,1)) and sum(item['local'] for item in roster)==1,
        'human_summary_matches_roster':all(summary[key]==human[key] for key in ('kills','assists','deaths','objectives')),
        'outcome_matches_human_side':summary['won']==(summary['attack_score']>summary['defend_score'] if human['team']==0 else summary['defend_score']>summary['attack_score']) and summary['draw']==(summary['attack_score']==summary['defend_score']),
        'one_completion_zero_dropped':final['completion_calls']==1 and final['events_dropped']==0 and not any(item['event']=='duplicate_completion' for item in events),
        'earned_xp_level_credits':after['xp']==xp and after['level']==level and after['credits']==old['credits']+earned,
        'accumulated_stats_correct':all(after[key]==old[key]+increment for key,increment in {'matches':1,'wins':int(summary['won']),'kills':summary['kills'],'deaths':summary['deaths']}.items()),
        'one_offline_history_record':after['scope']=='offline_training' and len(after['history'])==1 and after['history'][0]['credits_earned']==earned and all(after['history'][0][key]==value for key,value in summary.items()),
        'saved_reopened_exact_profile':after==disk==reopen==receipt['training_after']==receipt['reopened_initial_profile'],
        'settings_preserved':old['settings']==after['settings'],
        'all_native_exits_clean':exits(receipt),
        'native_reload_conserves_ammo':sum(receipt['fired_ammunition'])==sum(receipt['reloaded_ammunition']) and receipt['reloaded_ammunition'][0]==15,
    }
    return {'checks':checks,'all_checks_passed':all(checks.values()),'raw_events':len(events),
            'rounds':summary['rounds'],'score':[summary['attack_score'],summary['defend_score']],
            'human_stats':{key:summary[key] for key in ('kills','assists','deaths','objectives')},
            'xp_gain':after['xp']-old['xp'],'credits_gain':after['credits']-old['credits'],
            'simulation_seconds':summary['duration'],'wall_seconds':receipt['elapsed_seconds'],
            'planted_state_events':sum(item.get('objective_state')=='planted' for item in events),
            'round_end_reasons':[item['message'] for item in events if item['event']=='notification' and ' win ' in item.get('message','')],
            'executable_sha256_receipt':receipt['executable_sha256'],'native_binary_independently_downloaded':False}

def objectives(base):
    output = []
    for name,ticks in [('plant',180),('defuse',300)]:
        directory=base/('offline-'+name)
        receipt=read(directory/'results.json')
        actions=lines(directory/'actions.jsonl')
        events=lines(directory/'trace/events.jsonl')
        if not receipt.get('passed'):
            output.append({'scenario':name,'receipt_passed':False,'error':receipt.get('error'),
                           'wall_seconds':receipt.get('elapsed_seconds'),'cleanup_errors':receipt.get('cleanup_errors'),
                           'available_receipt_fields':sorted(receipt),'last_actions':actions[-8:],
                           'last_raw_events':events[-8:],
                           'scope':'Failed scenario retained exactly; passing later scenarios are evaluated separately.'})
            continue
        movement=next(item for item in actions if item['event']=='movement_completed')
        start_index=next(i for i,item in enumerate(actions) if item['event']=='movement_control')
        upper_bound=movement['seconds']-actions[start_index-1]['seconds']
        target=movement['requested']
        error=math.hypot(movement['destination'][0]-target[0],movement['destination'][2]-target[1])
        hold=receipt['objective_hold']
        edge_start,edge_end=hold['input_started'],hold['completion_notification']
        inputs=[item for item in events if item['event']=='local_interact_input' and hold['command_simulation_tick']<item['simulation_tick']<=edge_end['simulation_tick']]
        checks={
            'receipt_passed':receipt['passed'],'clean_frozen_source':identity(receipt),
            'movement_original_budget_and_tolerance':upper_bound<15 and error<.45 and movement['horizontal_speed']<=.05,
            'distinct_settled_tick_ids':len(set(movement['settled_simulation_ticks']))==2,
            'exact_hold_ticks':edge_end['simulation_tick']-edge_start['simulation_tick']==ticks and hold['simulation_ticks']==ticks,
            'raw_hold_edges_match_receipt':edge_start in events and edge_end in events,
            'single_uninterrupted_consumed_E':len(inputs)==1 and inputs[0]['held'] is True,
            'interrupted_hold_reset':receipt['partial_checks']['interrupted_E_reset'],
            'one_player_contribution':receipt['local_contribution_after']==receipt['local_contribution_before']+1,
            'normal_rules':receipt['initial']['rules']==RULES and receipt['initial']['time_scale']==1,
            'clean_exit_and_restart':exits(receipt) and receipt['progression_settings_restart_equal'],
        }
        output.append({'scenario':name,'checks':checks,'all_checks_passed':all(checks.values()),
                       'initial_conditions':receipt['initial'].get('initial_conditions'),
                       'movement_endpoint_error_m':error,'movement_wall_upper_bound_seconds':upper_bound,
                       'settled_ticks':movement['settled_simulation_ticks'],'hold_ticks':hold['simulation_ticks'],
                       'hold_simulation_seconds':hold['simulation_seconds'],'wall_seconds':receipt['elapsed_seconds'],
                       'exact_two_raw_settled_input_snapshots_retained':False})
    return output

def journey(base):
    directory=base/'offline-input'
    receipt=read(directory/'results.json')
    actions=read(directory/'actions.json')
    observations=[item for item in actions if item['event']=='offline_observation']
    if not receipt.get('passed'):
        return {'receipt_passed':False,'error':receipt.get('error'),
                'wall_seconds':receipt.get('elapsed_seconds'),'last_observation':receipt.get('last_offline_observation'),
                'completed_waits':[item.get('label') for item in actions if item['event']=='wait_completed'],
                'cleanup_errors':receipt.get('cleanup_errors')}
    focus=receipt['native_focus_recovery']
    lost,restored=focus['lost'],focus['restored_paused']
    released,moved=focus['released'],focus['fresh_press_movement']
    held=focus['held_neutral_samples']
    contexts=[focus['held_input_acknowledged'],lost,restored,*held,released,moved]
    actor=restored['local_actor']
    raw_states=[item['state'] for item in observations]
    native_for=lambda state:next(item['native_state'] for item in observations if item['state']==state)
    held_native=[native_for(state) for state in held]
    released_native,moved_native=native_for(released),native_for(moved)
    loaded=lines(directory/'restart-profile-trace/events.jsonl')[0]
    disk=read(next(directory.rglob('offline_training.json')))
    initial=lines(directory/'initial-offline-trace/events.jsonl')[0]
    movement=math.dist(released['local_actor']['position'],moved['local_actor']['position'])
    checks={
        'receipt_passed':receipt['passed'],'clean_frozen_source':identity(receipt),
        'original_300s_budget':receipt['elapsed_seconds']<300,
        'stock_initial_conditions':all(item['initial_conditions']=='stock_spawns_teams_random_seeds' and item['rules']==RULES and item['time_scale']==1 for item in (initial,loaded)),
        'settings_changed_and_loaded_exactly':disk==loaded['initial_profile'] and disk['settings']['sensitivity']!=initial['initial_profile']['settings']['sensitivity'],
        'incomplete_training_unchanged':receipt['incomplete_training_unchanged_after_reopened_exit'] and disk['matches']==initial['initial_profile']['matches'],
        'native_focus_loss_pauses':lost['ui']['focused'] is False and lost['ui']['paused'] is True,
        'restore_requires_explicit_resume':restored['ui']['focused'] is True and restored['ui']['paused'] is True and restored['ui']['mouse_mode']==0,
        'same_live_actor_round_normal_speed':all(state['phase']=='live' and state['round_number']==restored['round_number'] and state['time_scale']==1 and state['local_actor']['id']==actor['id'] and state['local_actor']['alive'] is True for state in contexts),
        'held_guard_neutral':bool(held) and all(state['ui']['paused'] is False and state['ui']['focused'] is True and state['ui']['waiting_for_input_release'] is True and state['local_input']['move']==[0,0] and all(state['local_input'][key] is False for key in ('fire','interact','reload')) and state['local_actor']['ammo']==actor['ammo'] for state in held),
        'native_W_and_LMB_still_held_during_guard':all(native['target_focused'] is True and native['lmb_down'] is True and native['keys_down']['w'] is True for native in held_native),
        'native_release_then_fresh_W':released_native['lmb_down'] is False and released_native['keys_down']['w'] is False and moved_native['target_window']==released_native['target_window'] and moved_native['keys_down']['w'] is True and moved_native['lmb_down'] is False,
        'settled_held_position_stable':len(held)>=3 and held[-2]['local_actor']['position']==held[-1]['local_actor']['position'],
        'release_ack_precedes_fresh_movement':released['ui']['waiting_for_input_release'] is False and released['local_input']['move']==[0,0] and released['local_input']['fire'] is False and moved['wall_msec']>released['wall_msec'] and moved['simulation_tick']>released['simulation_tick'] and moved['local_input']['move']!=[0,0] and movement>0,
        'focus_states_retained_in_raw_action_trace':all(state in raw_states for state in contexts if state!=focus['held_input_acknowledged']),
        'all_native_exits_clean':exits(receipt),
        'all_journey_completion_flags':all(receipt[key] is True for key in ('settings_restart_equal','natural_round_completed','purchase_and_weapon_switch','settings_loaded_into_reopened_process','explicit_resume','clean_exit')),
    }
    return {'checks':checks,'all_checks_passed':all(checks.values()),'wall_seconds':receipt['elapsed_seconds'],
            'fresh_movement_metres':movement,'held_guard_tick_ids':[state['simulation_tick'] for state in held],
            'release_tick':released['simulation_tick'],'fresh_movement_tick':moved['simulation_tick'],
            'rendered_hud_receipts':{key:receipt[key] for key in ('fired_hud','reloaded_hud','resumed_hud')},
            'settings_sensitivity_loaded':disk['settings']['sensitivity'],
            'actual_pngs_required_for_visual_review':True}

def native_input(base):
    output=[]
    for name in ['native-input','reload-release-first','reload-legacy-delayed']:
        directory=base/name
        if not (directory/'results.json').is_file():continue
        receipt=read(directory/'results.json')
        authority=read(directory/'authority.json')
        telemetry=read(directory/'authority-telemetry.json')['samples']
        player=[sample for sample in telemetry if sample.get('joined_id')==authority['joined_id'] and 'ammo' in sample]
        final=player[-1]
        checks={
            'receipt_passed':receipt['passed'],'clean_frozen_source':identity(receipt),
            'authority_summary_matches_raw':receipt['authority']==authority,
            'protocol6_prediction_off':authority['protocol']==6 and authority['prediction_default'] is False,
            'positive_consumed_ack_and_fire':max(sample.get('ack',0) for sample in player)==authority['largest_ack'] and authority['largest_ack']>0 and final['shots']==authority['shots'] and final['shots']>0,
            'depletion_recorded':min(sample['ammo'] for sample in player)==authority['lowest_ammo'] and authority['lowest_ammo']<30,
            'actual_reload_input_seen':any(sample.get('reload_input') is True for sample in player) and authority['reload_command_seen'],
            'completed_reload_conserves_total_ammo':final['ammo']==30 and final['reload_remaining']==0 and final['ammo']+final['reserve']==120-final['shots'] and authority['reload_completed'],
            'all_native_exits_clean':exits(receipt),
            'native_logs_clean':all(clean((directory/(part+'.log')).read_text(errors='replace')) for part in ('client','server')),
        }
        diagnostic=read(directory/'diagnostic-exit.json') if (directory/'diagnostic-exit.json').is_file() else None
        if diagnostic is not None:checks['diagnostic_actual_exit_zero']=diagnostic['exit_code']==0
        output.append({'scenario':name,'checks':checks,'all_checks_passed':all(checks.values()),
                       'wall_seconds':receipt['elapsed_seconds'],'shots':final['shots'],
                       'lowest_ammo':authority['lowest_ammo'],'final_ammunition':[final['ammo'],final['reserve']],
                       'raw_samples':len(telemetry),'executable_sha256_receipt':receipt['executable_sha256'],
                       'diagnostic':diagnostic,
                       'scope':'Exported client with source-engine loopback authority; movement displacement and physical input-to-photon not measured.'})
    return output

def settings_transaction(base):
    directory=base/'offline-input'
    receipt=read(directory/'results.json')
    if 'native_settings_resume' not in receipt:
        return {'transaction_receipt_available':False,'journey_passed':receipt.get('passed'),
                'error':receipt.get('error')}
    transaction=receipt['native_settings_resume']
    paused=transaction['paused_before_settings']
    after_settings=transaction['paused_after_settings']
    resumed=transaction['resumed']
    ready=transaction['capture_ready']
    after_capture=transaction['after_capture']
    primary=next(item for item in receipt['hud_analysis_pauses'] if item['capture']=='06g-switched-primary')
    hud=next(item for item in receipt['hud_analysis_pauses'] if item['capture']=='07d-explicit-resume')
    actor=paused['local_actor']
    contexts=[paused,after_settings,resumed,ready,after_capture,hud['before'],hud['paused'],hud['after_analysis']]
    actions=read(directory/'actions.json')
    ack_index=next(index for index,item in enumerate(actions) if item.get('event')=='offline_observation' and item.get('label')=='Actual living player explicitly resumes after field settings')
    fence_index=next(index for index,item in enumerate(actions) if item.get('event')=='offline_observation' and item.get('label')=='Two drawn frames after explicit native settings resume')
    down_index=max(index for index,item in enumerate(actions[:ack_index]) if item.get('event')=='key_after' and item.get('key')=='Escape' and item.get('down') is True)
    release=[item for item in actions[ack_index:fence_index+1] if item.get('event')=='key_after' and item.get('scope')=='field_settings_resume' and item.get('down') is False]
    transition_seconds=actions[fence_index]['seconds']-actions[down_index]['seconds']
    checks={
        'clean_frozen_source':identity(receipt),
        'primary_pause_retained':primary['resume_after_analysis'] is False and 'resumed' not in primary and primary['after_analysis']==paused,
        'settings_stay_paused_same_elapsed_and_health':paused['ui']['paused'] is True and after_settings['ui']['paused'] is True and paused['elapsed']==after_settings['elapsed'] and paused['local_actor']['health']==after_settings['local_actor']['health'],
        'all_original_contexts_same_living_focused_player':all(state['ui']['screen']=='game' and state['ui']['focused'] is True and state['time_scale']==1 and state['phase']==paused['phase'] and state['round_number']==paused['round_number'] and state['local_actor']['alive'] is True and state['local_actor']['health']>0 and all(state['local_actor'][field]==actor[field] for field in ['id','weapon','ammo','reserve']) for state in contexts),
        'native_resume_and_two_frame_fence':resumed['ui']['paused'] is False and ready['ui']['paused'] is False and after_capture['ui']['paused'] is False and ready['drawn_frames']>=resumed['drawn_frames']+2,
        'shared_original_10s_transition_budget':transaction['transition_watchdog_seconds']==10 and transition_seconds<=10,
        'Escape_release_before_frame_fence':len(release)==1,
        'raw_ack_and_frame_states_match_result':actions[ack_index]['state']==resumed and actions[fence_index]['state']==ready,
        'postcapture_HUD_pause_remains_same_life':hud['resume_after_analysis'] is False and 'resumed' not in hud and hud['paused']['elapsed']==hud['after_analysis']['elapsed'] and hud['paused']['local_actor']['health']==hud['after_analysis']['local_actor']['health'],
        'same_living_player_requirement_retained':transaction['same_living_player_required'] is True,
    }
    if 'resumed_hud' in receipt:
        checks['serialized_resumed_HUD_reading_living_exact_ammo']=0<receipt['resumed_hud']['health']<=100 and all(word not in receipt['resumed_hud']['status_ocr'].upper() for word in ['ELIMINATED','SPECTATING']) and receipt['resumed_hud']['ammo']==actor['ammo'] and receipt['resumed_hud']['reserve']==actor['reserve']
    return {'checks':checks,'all_checks_passed':all(checks.values()),'transition_wall_seconds':transition_seconds,
            'paused_tick':paused['simulation_tick'],'paused_elapsed':paused['elapsed'],
            'paused_health':actor['health'],'after_settings_tick':after_settings['simulation_tick'],
            'resumed_tick':resumed['simulation_tick'],'resumed_frames':resumed['drawn_frames'],
            'fenced_tick':ready['simulation_tick'],'fenced_frames':ready['drawn_frames'],
            'after_capture_tick':after_capture['simulation_tick'],
            'resumed_HUD_numeric_reading_serialized':'resumed_hud' in receipt,
            'original_resumed_PNG_requires_separate_visual_review':True,
            'scope':'Native API Escape key-up is traced; OS diagnostics sample r/d/w rather than the Escape bitmap. No exact PNG-to-tick or physical input latency claim.'}

def layouts(base):
    path=base/'layouts/results.json'
    if not path.is_file():
        return {'not_applicable':True}
    receipt=read(path)
    cases=receipt['cases']
    fences=[action for case in cases for action in case['actions'] if action['event']=='rendered_ui_fence']
    checks={
        'clean_frozen_source':identity(receipt),
        'four_requested_sizes':receipt['requested_sizes']==[[960,540],[1280,720],[1920,1080],[1280,800]],
        'four_complete_cases':len(cases)==4 and all(case['capture_generation_passed'] for case in cases),
        'original_case_and_whole_limits':receipt['elapsed_seconds']<520 and all(case['elapsed_seconds']<120 for case in cases),
        'source_unchanged':receipt['exact_source_unchanged'],
        'all_native_exits_clean':all(case.get('native_menu_exit')==0 and case.get('native_live_exit')==0 and case['cleanup_errors']==[] for case in cases),
        'two_drawn_frame_fences':bool(fences) and all(action['final_drawn_frames']>=action['first_drawn_frames']+2 for action in fences),
    }
    return {'checks':checks,'all_checks_passed':all(checks.values()),
            'capture_generation_passed':receipt['capture_generation_passed'],
            'wall_seconds':receipt['elapsed_seconds'],'fence_count':len(fences),
            'cases':[{'size':case['size'],'passed':case['capture_generation_passed'],
                      'error':case.get('error'),'wall_seconds':case['elapsed_seconds'],
                      'captures':case['captures'],'touch_toggle':case['touch_toggle'],
                      'cleanup_errors':case['cleanup_errors']} for case in cases],
            'actual_pngs_required_for_visual_review':True,
            'live_hud_classification_scope':'1280x720 touch-toggle only'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path,help='Extracted inner bounded receipts ZIP directory')
    parser.add_argument('--output',type=Path,required=True)
    arguments=parser.parse_args()
    base=arguments.root/'evidence'
    result={}
    for key,operation,target in [('raw_artifact_index',index_check,arguments.root),
                                 ('regressions',regressions,base),('full_match',full_match,base),
                                 ('objectives',objectives,base),('journey',journey,base),('layouts',layouts,base),
                                 ('native_input',native_input,base),('settings_transaction',settings_transaction,base)]:
        try:
            result[key]=operation(target)
        except Exception as error:
            result[key]={'verification_incomplete':True,'type':type(error).__name__,'error':str(error)}
    arguments.output.write_text(json.dumps(result,indent=2)+'\n')
    def summary(value):
        if isinstance(value,list):return [summary(item) for item in value]
        if 'all_checks_passed' in value:return value['all_checks_passed']
        if 'receipt_passed' in value:return value['receipt_passed']
        if 'all_sizes_and_hashes_match' in value:return value['all_sizes_and_hashes_match'] and value['complete_selected_file_set']
        return value
    print(json.dumps({key:summary(value) for key,value in result.items()}))

if __name__=='__main__':
    main()
