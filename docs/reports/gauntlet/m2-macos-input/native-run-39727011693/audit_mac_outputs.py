"""Independently audit transferred ARM raw receipts; no native/OCR execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

SOURCE='e7718ee42fd67a65bcb83061c868b34bd9a2c3d2'
KEYS=('source_commit','source_game_tree','source_content_sha256','source_validation_sha256')
READ=lambda p:json.loads(p.read_text())
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
CLEAN=lambda t:re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance',t,re.M) is None

def raw_index(root):
    index=READ(root/'qa-receipts-index.json')
    bad=[]
    for entry in index['files']:
        path=root/entry['archive_path']
        if not path.is_file() or path.stat().st_size!=entry['bytes'] or SHA(path)!=entry['sha256']:bad.append(entry['path'])
    actual={p.relative_to(root).as_posix() for p in (root/'evidence').rglob('*') if p.is_file()}
    return {'files':len(index['files']),'all_sizes_and_hashes_match':not bad,
            'complete_selected_file_set':actual=={x['archive_path'] for x in index['files']},'failures':bad}

def preflight(base,identity,full):
    directory=base/'macos-input-preflight';r=READ(directory/'results.json')
    client=(directory/'client.log').read_text(errors='replace');engine=(directory/'engine.log').read_text(errors='replace')
    permissions=r['permissions'];required=('CGPreflightPostEventAccess','CGPreflightScreenCaptureAccess')
    denied=[k for k in required if permissions[k] is not True]
    before,after=r['native_user_directory_before'],r['native_user_directory_after']
    old,new=before['files'],after['files']
    effects={'created_files':sorted(new.keys()-old.keys()),'removed_files':sorted(old.keys()-new.keys()),
             'changed_files':sorted(k for k in new.keys()&old.keys() if new[k]!=old[k]),
             'created_directories':sorted(set(after['directories'])-set(before['directories'])),
             'removed_directories':sorted(set(before['directories'])-set(after['directories'])),
             'directory_created':not before['directory_exists'] and after['directory_exists']}
    windows=[w for o in r['window_observations'] for w in o['windows']]
    png=None
    if full is not None:
        path=full/'macos-input-preflight/exported-smoke.png'
        raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
        png={'sha256':SHA(path),'dimensions':list(struct.unpack('>II',raw[16:24])),'hash_matches':SHA(path)==r['capture_sha256']}
    checks={'frozen_clean_source':all(r['source'][k]==identity[k] for k in KEYS) and not r['source']['source_dirty'] and not r['source']['source_game_dirty'],
            'matching_export_identity':all(r['artifact_source'][k]==identity[k] for k in KEYS) and r['artifact_source']['export_completed'],
            'matching_executable_digest_receipts':r['executable_sha256']==r['artifact_source']['artifact']['sha256'],
            'native_arm64':r['architecture']=='arm64' and 'macOS' in r['host'],
            'all_four_permission_bools':set(permissions)=={'CGPreflightPostEventAccess','CGPreflightScreenCaptureAccess','CGPreflightListenEventAccess','AXIsProcessTrusted'} and all(isinstance(v,bool) for v in permissions.values()),
            'denied_permissions_and_status_truthful':r['blocked_apis']==denied and r['status']==('BLOCKED_EXTERNALLY' if denied else 'READY_FOR_INPUT_ATTEMPT'),
            'no_input_or_permission_request_claim':r['input_events_posted']==0 and r['permission_requests_made']==0 and r['native_input_verified'] is False,
            'exact_owned_visible_windows':bool(windows) and all(w['owner_pid']==r['client_pid'] for w in windows) and any(w['onscreen'] for w in windows),
            'normal_clean_native_exit':r['normal_exit_code']==0 and r['engine_log_clean'] and CLEAN(client) and CLEAN(engine) and 'SIGHTBREAK_MAIN_READY screen=menu' in client,
            'supported_internal_capture_scope':r['capture_scope']=='Original export viewport PNG; not an OS screenshot' and '--smoke' in r['command'] and '--log-file' in r['command'],
            'profile_entries_absent_and_unchanged':r['profile_entries_before']==r['profile_entries_after']=={'offline_training.json':False,'offline_training.json.tmp':False} and r['profile_entries_unchanged'],
            'cache_effects_recomputed':all(r['native_user_directory_side_effects'][k]==v for k,v in effects.items()),
            'owned_group_cleanup':r['cleanup']['owned_group_gone'] and r['cleanup']['pid']==r['client_pid'] and r['cleanup']['exit_code']==0,
            'source_revalidated_after':r['source_unchanged'] and 'finalization_failure' not in r,
            'original_60s_budget':r['seconds']<60}
    if png is not None:checks['original_internal_PNG_verified']=png['hash_matches'] and min(png['dimensions'])>0
    return {'checks':checks,'all_checks_passed':all(checks.values()),'status':r['status'],'permissions':permissions,
            'client_pid':r['client_pid'],'window_observations':r['window_observations'],'seconds':r['seconds'],
            'profile_entries_before':r['profile_entries_before'],'profile_entries_after':r['profile_entries_after'],
            'native_user_directory_side_effects':effects,'cleanup':r['cleanup'],'PNG':png,
            'scope':'API preflight/window/internal rendering only. Combined-session key state is not focus or delivery. Actual native user-directory files and binary bytes are not supplied by this bounded receipt artifact.'}

def ios(base,identity):
    directory=base/'ios-compile';r=READ(directory/'compile.json');source_before=READ(directory/'source-before.log');source_after=READ(directory/'source-after.log');export=READ(directory/'exported-source.json')
    build=(directory/'xcodebuild-device.log').read_text(errors='replace');unsigned=(directory/'unsigned-app.log').read_text(errors='replace')
    commands={c['label']:c for c in r['commands']};selected=r['sdk_selection'];candidate=next(c for c in selected['candidates'] if c['compatible'])
    probe=next(c for c in r['commands'] if c['label'].startswith('sdk-link-probe-') and c['exit_code']==0)
    symbols=['_CADynamicRangeAutomatic','_CADynamicRangeConstrainedHigh','_CADynamicRangeHigh','_CADynamicRangeStandard','_MTLTensorDomain']
    exported_pack=next(x for x in export['payload'] if x['path']=='ios/sightbreak.pck')
    binary=r['app']['executable']
    checks={'compile_pass_receipt':r['compile_completed'] and r['status']=='PASS',
            'native_Darwin_arm64':r['host']['system']=='Darwin' and r['host']['machine']=='arm64',
            'frozen_clean_before_after_source':source_before==source_after==r['source'] and all(source_before[k]==identity[k] for k in KEYS) and not source_before['source_dirty'] and not source_before['source_game_dirty'],
            'source_bound_export':all(export[k]==identity[k] for k in KEYS) and export['export_completed'],
            'actual_forced_five_symbol_link_probe':selected['required_symbols']==symbols and all(symbol in probe['command'] for symbol in symbols) and '-no_adhoc_codesign' in probe['command'] and candidate['probe_exit_code']==0,
            'same_process_local_developer_selected':r['developer_directory']==r['process_local_developer_dir']==candidate['developer_directory'],
            'SDK_paths_stay_in_selected_developer':all(p.startswith(r['developer_directory']+'/Platforms/iPhoneOS.platform/Developer/SDKs/') for p in (r['iphoneos_sdk'],candidate['sdk_path'])),
            'actual_compiler_linker_success_markers':bool(re.search(r'(?m)^(CompileC|SwiftCompile) ',build)) and bool(re.search(r"(?m)^Ld [^\n]+ normal(?: arm64)? \(in target 'sightbreak' from project 'sightbreak'\)\s*$",build)) and '** BUILD SUCCEEDED **' in build and '** BUILD FAILED **' not in build,
            'unsigned_actual_codesign':commands['unsigned-app']['exit_code']==1 and 'code object is not signed at all' in unsigned,
            'native_attested_arm64_device_unsigned':binary['architecture']=='arm64' and binary['format']=='Mach-O MH_EXECUTE' and binary['platform']=='iOS device' and binary['code_signature_load_command'] is False and r['app']['signature_directory'] is False and r['app']['embedded_profile'] is False,
            'native_attested_PCK_matches_export':r['app']['pck_sha256']==exported_pack['sha256'],
            'all_owned_commands_cleaned':all(not c['timed_out'] and c['cleanup_complete'] and not c['cleanup_errors'] and not c.get('unexpected_descendants') and not c['surviving_owned_processes'] for c in r['commands']),
            'actual_xcodebuild_exit_zero':commands['xcodebuild-device']['exit_code']==0,
            'original_900s_budget':r['seconds']<900}
    return {'checks':checks,'all_checks_passed':all(checks.values()),'seconds':r['seconds'],'link_wall_seconds':commands['xcodebuild-device']['seconds'],
            'Xcode':r['xcode_version'],'SDK':r['iphoneos_sdk_version'],'SDK_path_before':candidate['sdk_path'],'SDK_path_after':r['iphoneos_sdk'],
            'SDK_path_scope':'Before uses iPhoneOS.sdk; after uses iPhoneOS26.2.sdk. The native helper requires resolved-path equality on the Mac. This critic cannot independently resolve remote filesystem aliases.',
            'app_native_attestation':r['app'],
            'build_warnings':[line for line in build.splitlines() if 'warning:' in line],
            'scope':'Unsigned generic-device compile/link only. App, PCK and SDK probe bytes are not independently re-parsed from bounded receipts. No installation, runtime, simulator or physical input acceptance.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--identity',type=Path,required=True);parser.add_argument('--full',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    identity=READ(args.identity);result={}
    for label,operation in [('raw_index',lambda:raw_index(args.root)),('Mac_preflight',lambda:preflight(args.root/'evidence',identity,args.full)),('iOS_compile',lambda:ios(args.root/'evidence',identity))]:
        try:result[label]=operation()
        except Exception as error:result[label]={'verification_incomplete':True,'type':type(error).__name__,'error':str(error)}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v.get('all_checks_passed',v.get('all_sizes_and_hashes_match',v)) for k,v in result.items()}))

if __name__=='__main__':main()
