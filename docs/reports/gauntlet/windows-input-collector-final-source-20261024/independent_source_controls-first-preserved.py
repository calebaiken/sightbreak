#!/usr/bin/env python3
"""Exact source contracts and independent mutation falsifiers; no engine execution."""
import argparse
import ast
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import subprocess

TARGET = 'c32415148db1f110bbc7eadfca3793d4693429ff'
HANDOFF = 'c3c974e8235933a3f147d193e2cf5338b99be438'
ROOT = '11c5773eff6888c5157784c272aca144614338d4'
RUNTIME = 'c0738163965804297a1881905d5bb4646da40a16'
ORIGINAL = '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
PATHS = ['game/scripts/gameplay/match.gd', 'game/tests/movement_prediction_test.gd',
         'scripts/fixtures/export_integration.gd', 'scripts/verify_integration_export.py']

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])

def tree(repo, ref):
    result = {}
    for row in git(repo, 'ls-tree', '-rz', ref).split(b'\0'):
        if not row: continue
        metadata, name = row.split(b'\t', 1)
        if name.startswith(b'docs/'): continue
        mode, kind, blob = metadata.decode().split()
        result[name.decode()] = {'mode': mode, 'kind': kind, 'blob': blob}
    return result

def sha(value): return hashlib.sha256(value).hexdigest()

def erase(value):
    output, inside = [], False
    for line in value.splitlines(keepends=True):
        if b'# BEGIN INPUT OBSERVATION' in line:
            assert not inside
            inside = True
        elif b'# END INPUT OBSERVATION' in line:
            assert inside
            inside = False
        elif not inside and b'# INPUT_OBSERVATION_HOOK' not in line:
            output.append(line)
    assert not inside
    return b''.join(output)

def functions(value):
    result = {}
    for match in re.finditer(r'^(?:static )?func (_native_input_\w+)\([^\n]+\n', value, re.M):
        end = re.search(r'^(?:static )?func |^# END INPUT OBSERVATION METHODS', value[match.end():], re.M)
        result[match[1]] = value[match.end():match.end()+end.start()]
    return result

def method_contract(value):
    methods = functions(value)
    assert len(methods) == 5
    gate = methods['_native_input_allowed']
    assert 'if not debug or not "--native-input-observation" in args' in gate
    assert 'bool(settings.get("require_accounts", false))' in gate
    assert 'not str(settings.get("join_ticket", "")).is_empty()' in gate
    assert 'not in ["127.0.0.1", "::1"]' in gate
    assert 'settings.get("_native_input_fixture") is bool and settings._native_input_fixture' in gate
    config = methods['_native_input_configure']
    assert '_native_input_allowed(settings, OS.get_cmdline_user_args(), OS.is_debug_build())' in config
    controls = methods['_native_input_controls']
    assert set(re.findall(r'"(\w+)"\s*:', controls)) == {'sequence', 'fire', 'reload', 'move'}
    assert 'data.get("sequence") is int else -1' in controls
    assert 'data.get("fire") is bool and data.fire' in controls
    assert 'data.get("reload") is bool and data.reload' in controls
    assert 'move.is_finite() else [0.0, 0.0]' in controls
    packet = methods['_native_input_packet']
    assert 'commands.slice(0, SBInputStream.MAX_BATCH)' in packet
    assert set(re.findall(r'"(\w+)"\s*:', packet)) == {'epoch', 'count', 'first', 'last', 'fire', 'reload', 'moving'}
    observer = methods['_native_input_observe']
    assert observer.lstrip().startswith('if _native_input_observation.is_empty(): return\n')
    assert 'if int(diagnostic.count) >= 1024: return' in observer
    assert observer.index('>= 1024: return') < observer.index('Time.get_ticks_msec()')
    assert '"observation_limit" if int(diagnostic.count) == 1023 else reason' in observer
    assert 'now - int(diagnostic.last_emit) < 1000' in observer
    assert 'if reason == "snapshot_applied":\n\t\t\tfor value: Variant in data.get("actors", []):' in observer
    assert 'int(value.get("id", 0)) == local_id' in observer
    assert 'actors.get(int(diagnostic.last_actor)) if _authority else local_actor()' in observer
    assert observer.count('print(') == 1
    assert 'print("SIGHTBREAK_INPUT_OBSERVATION " + JSON.stringify(record))' in observer
    all_methods = '\n'.join(methods.values())
    # Contextual lexical checks are a falsifier, not a language-wide effects proof.
    prohibited = [r'\.rpc(?:_id)?\(', r'@rpc', r'FileAccess\.', r'HTTP',
                  r'Input\.(?:parse_input_event|action_press|action_release)',
                  r'_input_stream\.(?:accept|pop|forget|reset)',
                  r'_prediction\.(?:predict|packet|reconcile|reset)',
                  r'_peer_lifecycle\.(?:active|allow_input|admitted|forget|reject|connected)',
                  r'^\s*(?:_local_input|connection_state|_snapshot_generation|_simulation_tick)\s*=',
                  r'^\s*(?:actor|actors|options|_peer_actors|_last_input_sequence)[.\[]']
    for pattern in prohibited:
        assert not re.search(pattern, all_methods, re.M), pattern
    assert not re.search(r'"(?:token|join_ticket|reconnect_token|account|name|look|position|health)"\s*:', all_methods)
    assert observer.count('data.get("actors", [])') == 1
    return methods

def flag_contract(value):
    module = ast.parse(value)
    declaration = next(n for n in ast.walk(module) if isinstance(n, ast.Expr)
                       and isinstance(n.value, ast.Call)
                       and any(isinstance(a, ast.Constant) and a.value == '--observe-input-consumption' for a in n.value.args))
    branches = sorted([n for n in ast.walk(module) if isinstance(n, ast.If)
                       and isinstance(n.test, ast.Attribute) and n.test.attr == 'observe_input_consumption'], key=lambda n:n.lineno)
    assert len(branches) == 3
    import argparse
    cases = []
    for enabled in (False, True):
        parser = argparse.ArgumentParser()
        exec(compile(ast.Module(body=[declaration], type_ignores=[]), 'actual-flag', 'exec'), {'parser':parser})
        args = parser.parse_args(['--observe-input-consumption'] if enabled else [])
        assert args.observe_input_consumption is enabled
        env = {'args':args, 'result':{}, 'client_command':['game','--quit-after','10'],
               'server_command':['godot','--','--output=fresh']}
        exec(compile(ast.Module(body=branches, type_ignores=[]), 'actual-branches','exec'),env)
        assert env['client_command'] == ['game','--quit-after','10'] + (['--','--native-input-observation'] if enabled else [])
        assert env['server_command'] == ['godot','--','--output=fresh'] + (['--native-input-observation'] if enabled else [])
        assert bool(env['result']) == enabled
        cases.append({'enabled':enabled, 'client':env['client_command'], 'server':env['server_command'], 'result':env['result']})
    return cases

def gate_cases(gate):
    # Restricted translation of the ACTUAL three-line source predicate. This is a
    # finite source-expression model, not GDScript execution or type/API proof.
    lines = [line.strip() for line in gate.splitlines() if line.strip()]
    assert len(lines) == 3
    expressions = []
    for line in lines:
        value = line[3:].split(': return false')[0] if line.startswith('if ') else line[7:]
        value = value.replace('false','False')
        value = value.replace('not str(settings.get("join_ticket", "")).is_empty()', 'bool(str(settings.get("join_ticket", "")))')
        value = value.replace('settings.get("_native_input_fixture") is bool', 'type(settings.get("_native_input_fixture")) is bool')
        value = value.replace('settings._native_input_fixture', 'settings.get("_native_input_fixture")')
        expressions.append(compile(value, 'actual-gate-predicate', 'eval'))
    cases = []
    for debug, requested, mode, address, account, ticket, fixture in itertools.product(
            (False,True),(False,True),('offline','client','server'),('127.0.0.1','::1','localhost','192.0.2.1'),
            (False,True),('','fictional'),(None,False,True,1,'true')):
        settings = dict(mode=mode,address=address,require_accounts=account,join_ticket=ticket)
        if fixture is not None: settings['_native_input_fixture']=fixture
        env = dict(settings=settings,args=['--native-input-observation'] if requested else [],debug=debug)
        actual = not eval(expressions[0], {}, env) and not eval(expressions[1], {}, env) and bool(eval(expressions[2], {}, env))
        expected = debug and requested and not account and not ticket and address in ('127.0.0.1','::1') and (mode=='client' or mode=='server' and fixture is True)
        assert actual == expected
        cases.append({'debug':debug,'requested':requested,'settings':settings,'allowed':actual})
    return cases

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); assert sorted(os.sched_getaffinity(0)) == [4]
    before, after, reference = tree(args.repo,ROOT), tree(args.repo,TARGET), tree(args.repo,RUNTIME)
    changed=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p))
    assert len(before)==len(after)==507 and changed==sorted(PATHS)
    assert tree(args.repo,HANDOFF)==after
    assert tree(args.repo,'HEAD')==after
    expected=dict(before)
    for path in PATHS: expected[path]=reference[path]
    assert expected==after
    bindings={};payloads={}
    for path in PATHS:
        actual=(args.repo/path).read_bytes()
        frozen=git(args.repo,'show',TARGET+':'+path)
        original=git(args.repo,'show',ROOT+':'+path)
        assert actual==frozen and erase(actual)==original==git(args.repo,'show',ORIGINAL+':'+path)
        bindings[path]={'candidate_sha256':sha(actual),'recovered_sha256':sha(erase(actual)),'original_sha256':sha(original),'exact_erasure':True}
        payloads[path]=actual.decode()
    assert not git(args.repo,'diff',TARGET,'--',':!docs').strip()
    assert not git(args.repo,'diff','--cached',TARGET,'--',':!docs').strip()
    for path in ('scripts/analyze_input_consumption.py','scripts/test_input_consumption_observation.py'):
        assert path not in after and not (args.repo/path).exists()
    methods=method_contract(payloads[PATHS[0]])
    cases=gate_cases(methods['_native_input_allowed'])
    flags=flag_contract(payloads[PATHS[3]])
    mutations=[]
    def reject(name,original,old,new,validator):
        assert old in original
        altered=original.replace(old,new,1)
        try: validator(altered)
        except (AssertionError,StopIteration): mutations.append({'name':name,'rejected':True});return
        raise AssertionError('Mutation escaped independent contract: '+name)
    runtime=payloads[PATHS[0]];controller=payloads[PATHS[3]]
    for name,old,new in [
        ('release gate removed','if not debug or not','if not'),
        ('guest gate removed','bool(settings.get("require_accounts", false))','false'),
        ('loopback expanded','["127.0.0.1", "::1"]','["127.0.0.1", "::1", "192.0.2.1"]'),
        ('fixture type check removed','settings.get("_native_input_fixture") is bool and ','true and '),
        ('cap expanded','>= 1024: return','>= 2048: return'),
        ('batch projection unbounded','commands.slice(0, SBInputStream.MAX_BATCH)','commands'),
        ('private aim projected','return {"sequence":','return {"look": data.get("look"), "sequence":'),
        ('protected input mutated','var diagnostic: Dictionary = _native_input_observation','_local_input = {}\n\tvar diagnostic: Dictionary = _native_input_observation'),
        ('network publication inserted','print("SIGHTBREAK_INPUT_OBSERVATION','_input_rpc.rpc_id(1, data)\n\tprint("SIGHTBREAK_INPUT_OBSERVATION'),
        ('client actor privacy widened','if _authority else local_actor()','if true else local_actor()'),
        ('schema rejection actor traversal','if reason == "snapshot_applied":','if reason == "snapshot_schema_rejected":')]:
        reject(name,runtime,old,new,method_contract)
    reject('flag becomes default on',controller,"action='store_true'","action='store_true', default=True",flag_contract)
    reject('client omits user delimiter',controller,"['--', '--native-input-observation']","['--native-input-observation']",flag_contract)
    def recovers(value):assert erase(value.encode()) == git(args.repo,'show',ROOT+':'+PATHS[3])
    reject('original timeout relaxed',controller,'default=180','default=240',recovers)
    checks=payloads[PATHS[1]].split('# BEGIN INPUT OBSERVATION TESTS')[1].split('# END INPUT OBSERVATION TESTS')[0]
    assert len(re.findall(r'^\s*check\(',checks,re.M))==13
    assert 'res://tests/movement_prediction_test.gd' in (args.repo/'scripts/validate.sh').read_text()
    report={'passed':True,'source':TARGET,'comparison_root':ROOT,'runtime_reference':RUNTIME,'handoff':HANDOFF,
            'cpu_affinity':sorted(os.sched_getaffinity(0)),'initialized_head':git(args.repo,'rev-parse','HEAD').decode().strip(),
            'shallow':git(args.repo,'rev-parse','--is-shallow-repository').decode().strip(),
            'reachable_commits':int(git(args.repo,'rev-list','--count','HEAD')),
            'non_doc_paths':len(after),'changed_non_doc_paths':changed,'full_union':after,'erasure_bindings':bindings,
            'source_expression_gate_cases':len(cases),'gate_cases':cases,'actual_flag_ast_cases':flags,
            'independent_mutations':mutations,'reachable_new_godot_checks':17,'new_godot_checks_executed':False,
            'limits':'Static contracts, Python command AST and restricted finite source-expression model only. No GDScript/native/API, runtime/overhead/completeness/physical latency/reader acceptance.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('gate_cases','full_union')},indent=2))

if __name__=='__main__':main()
