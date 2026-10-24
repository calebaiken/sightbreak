"""Read-only raw objective/full-match audit for the single admitted Windows run.

No Godot import, execution, OCR, workflow, input, cleanup or completeness reader.
Receipt passed/partial flags are facts only and never supply a predicate result.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

SOURCE = 'c32415148db1f110bbc7eadfca3793d4693429ff'
RUN = 40080238905
JOB = 120832097220
RULES = {'buy_seconds': 15, 'round_seconds': 100, 'device_seconds': 35,
         'plant_seconds': 3, 'defuse_seconds': 5, 'win_score': 7}
LOG_FAILURE = re.compile(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance'
                         r'|^Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\r?$'
                         r'|^StringName: [1-9][0-9]* unclaimed string names at exit\.\r?$', re.M)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Case:
    def __init__(self, base, scenario):
        self.directory = base / ('offline-' + scenario)
        self.scenario = scenario
        self.receipt = read(self.directory / 'results.json')
        self.actions = lines(self.directory / 'actions.jsonl')
        self.events = lines(self.directory / 'trace/events.jsonl')
        self.initial = self.events[0]
        self.rows = []
        self.facts = {'receipt_passed': self.receipt.get('passed'), 'receipt_error': self.receipt.get('error'),
                      'receipt_partial_checks': self.receipt.get('partial_checks'),
                      'raw_actions': len(self.actions), 'raw_events': len(self.events),
                      'elapsed_seconds': self.receipt.get('elapsed_seconds'),
                      'initial': self.initial, 'commands': self.receipt.get('commands')}

    def row(self, name, predicate, anchor):
        try:
            value = predicate()
            if type(value) is not bool:
                raise TypeError('Predicate did not return bool')
            result = {'name': name, 'status': 'SATISFIED' if value else 'NOT_SATISFIED', 'source_anchor': anchor}
        except (KeyError, IndexError, StopIteration, TypeError, ValueError, FileNotFoundError) as error:
            result = {'name': name, 'status': 'UNAVAILABLE', 'source_anchor': anchor,
                      'reason': type(error).__name__ + ': ' + str(error)}
        self.rows.append(result)

    def action(self, event, field, value):
        found = [(index + 1, item) for index, item in enumerate(self.actions)
                 if item.get('event') == event and item.get(field) == value]
        if len(found) != 1:
            raise ValueError('Expected one action ' + event + '/' + str(value) + '; found ' + str(len(found)))
        return {'line': found[0][0], **found[0][1]}

    def observed(self, label):
        return self.action('observed', 'label', label)

    def capture(self, name):
        return self.action('capture_end', 'capture', name)

    def common(self, timeout):
        r, i = self.receipt, self.initial
        self.row('exact_clean_c324_source_receipt', lambda: r['source']['source_commit'] == SOURCE
                 and r['source']['source_dirty'] is False and r['source']['source_game_dirty'] is False,
                 'verify_offline_match.py:641–649,750')
        self.row('export_manifest_and_executable_hash_receipts_agree', lambda:
                 all(r['artifact_source'][key] == r['source'][key] for key in r['source'])
                 and r['artifact_source']['target'] == 'windows'
                 and r['artifact_source']['artifact']['sha256'] == r['executable_sha256'],
                 'verify_offline_match.py:642–648; this compares receipts, not independently downloaded executable bytes')
        self.row('original_windows_scenario_and_configured_budget', lambda: r['target'] == 'windows'
                 and r['scenario'] == self.scenario and r['timeout_seconds'] == timeout,
                 'desktop-alpha.yml:168–174; verify_offline_match.py:90,127')
        self.facts['final_receipt_elapsed_below_configured_budget'] = 0 < r.get('elapsed_seconds', 0) < timeout
        self.facts['deadline_limit'] = 'Final elapsed includes cleanup/finalization; it is not the timestamp of the source remaining() checkpoint before success.'
        self.row('initial_raw_event_equals_controller_initial', lambda: i == r['initial'] and i['event'] == 'initial',
                 'verify_offline_match.py:687–699')
        self.row('normal_rules_protocol_prediction_speed', lambda: i['rules'] == RULES and i['time_scale'] == 1
                 and i['protocol'] == 6 and i['prediction_enabled'] is False, 'verify_offline_match.py:690–693')
        self.row('genuine_empty_isolated_offline_training', lambda: i['initial_profile']['scope'] == 'offline_training'
                 and i['initial_profile']['matches'] == i['initial_profile']['xp'] == i['initial_profile']['credits'] == 0
                 and i['initial_profile']['history'] == [], 'verify_offline_match.py:694–696')
        self.row('ten_living_stock_health_initial_actors', lambda: len(i['actors']) == 10
                 and all(a['alive'] is True and a['health'] == 100 for a in i['actors']), 'verify_offline_match.py:697–698')
        self.row('both_normal_root_exits_zero', lambda: r['initial_exit'] == r['reopened_exit'] == 0
                 and len(r['commands']) == 2 and all(c['exit_code'] == 0 for c in r['commands']),
                 'verify_offline_match.py:711–714,745–748')
        self.row('original_native_error_resource_leak_regex_clear', lambda: all(
                 LOG_FAILURE.search((self.directory / (n + '.log')).read_text(errors='replace')) is None
                 for n in ('client', 'reopened')), 'native_log.py:5–10; verify_offline_match.py:713,747')
        warnings = {n: [line for line in (self.directory / (n + '.log')).read_text(errors='replace').splitlines()
                        if re.search(r'^WARNING:', line)] for n in ('client', 'reopened')}
        self.facts['native_warning_lines'] = warnings
        self.row('preregistered_zero_warning_requirement', lambda: not any(warnings.values()),
                 'PREREGISTRATION.md:195; separate from native_log.py error regex')
        self.row('no_reported_cleanup_errors', lambda: r['cleanup_errors'] == [], 'verify_offline_match.py:804')
        self.facts['profile_files'] = [str(p.relative_to(self.directory)) for p in self.directory.rglob('offline_training.json')]
        self.facts['source_receipt'] = r.get('source')
        self.facts['artifact_source_receipt'] = r.get('artifact_source')
        self.facts['executable_sha256_receipt'] = r.get('executable_sha256')
        self.facts['native_binary_independently_downloaded'] = False

    def output(self):
        selected = [p for p in self.directory.rglob('*') if p.is_file()
                    and (p.suffix in ('.json', '.jsonl', '.log') or p.name == 'offline_training.json')]
        return {'scenario': self.scenario, 'facts': self.facts, 'predicates': self.rows,
                'predicate_status_counts': {s: sum(row['status'] == s for row in self.rows)
                                            for s in ('SATISFIED', 'NOT_SATISFIED', 'UNAVAILABLE')},
                'selected_file_sha256': {str(p.relative_to(self.directory)): sha(p) for p in sorted(selected)}}


def objective(base, scenario):
    c = Case(base, scenario)
    c.common(180)
    r, i, ev = c.receipt, c.initial, c.events
    required = 3 if scenario == 'plant' else 5
    c.row('declared_initial_layout_and_seed42', lambda: i['initial_conditions'] == 'declared_initial_spawns_side_and_seeds_only'
          and any('--offline-scenario=' + scenario in x for x in r['commands'][0]['command'])
          and '--offline-seed=42' in r['commands'][0]['command'], 'verify_offline_match.py:669–672,689–691')
    c.row('out_of_range_rejection_observed', lambda: c.action('invalid_interaction_rejected', 'event', 'invalid_interaction_rejected')['observed']['interaction_progress'] == 0,
          'verify_offline_match.py:350–358')
    c.row('out_of_range_rejection_preserves_zero_local_contribution', lambda:
          c.action('invalid_interaction_rejected', 'event', 'invalid_interaction_rejected')['observed']['local_contribution']
          == i['local_contribution'] == 0, 'verify_offline_match.py:350–358')
    c.row('interrupted_hold_progress_then_zero_same_contribution', lambda:
          .1 <= c.observed('Real E interaction progress')['observed']['interaction_progress'] < .8
          and c.observed('Released E clears interaction progress')['observed']['interaction_progress'] == 0
          and c.observed('Released E clears interaction progress')['observed']['local_contribution']
          == c.observed('Real E interaction progress')['observed']['local_contribution'], 'verify_offline_match.py:360–369')
    def legitimate_approach():
        entered = c.capture('03b-legitimate-objective-approach')['observed']
        recent = [e for e in ev if e['simulation_tick'] <= entered['simulation_tick'] and 'objective_position' in e]
        position = entered['local_actor']['position']
        distance = math.hypot(position[0] - r['approach_origin'][0], position[2] - r['approach_origin'][2])
        c.facts['approach_raw_capture_state'] = entered
        return (distance > (4.2 if scenario == 'plant' else 2)
                and (math.hypot(position[0] + 15, position[2] - 10) < 3.8 if scenario == 'plant'
                     else math.dist(position, recent[-1]['objective_position']) <= 2.8))
    c.row('legitimate_authoritative_approach', legitimate_approach, 'verify_offline_match.py:415–423')
    c.row('original_objective_role_and_independent_attacker_carrier', lambda:
          (i['local_actor']['team'] == 0 and i['objective_carrier'] == i['local_actor']['id'] if scenario == 'plant'
           else i['local_actor']['team'] == 1 and i['objective_carrier'] != i['local_actor']['id']
           and next(a for a in i['actors'] if a['id'] == i['objective_carrier'])['team'] == 0),
          'verify_offline_match.py:388–409')
    try:
        command = c.action('objective_hold_command', 'event', 'objective_hold_command')
        c.row('known_zero_eligible_living_final_hold_start', lambda:
              command['observed']['phase'] == 'live' and command['observed']['round_number'] == i['round_number']
              and command['observed']['objective_state'] == ('carried' if scenario == 'plant' else 'planted')
              and command['observed']['interaction_progress'] == 0
              and command['observed']['local_actor']['id'] == i['local_actor']['id']
              and command['observed']['local_actor']['alive'] is True
              and 0 < command['observed']['local_actor']['health'] <= 100,
              'verify_offline_match.py:425–428')
        prior_tick = command['simulation_tick']
        message = 'Relay device armed' if scenario == 'plant' else 'Relay device defused'
        completions = [x for x in ev if x.get('event') == 'notification' and message in x.get('message', '') and x['simulation_tick'] > prior_tick]
        terminal = completions[0] if len(completions) == 1 else {}
        inputs = [x for x in ev if x.get('event') == 'local_interact_input' and prior_tick < x['simulation_tick'] <= terminal.get('simulation_tick', prior_tick)]
        start = inputs[0] if len(inputs) == 1 else {}
        c.facts['final_hold'] = {'command_action': command, 'raw_completion_notifications': completions,
                                 'raw_consumed_interaction_edges': inputs,
                                 'simulation_seconds': terminal.get('elapsed', 0) - start.get('elapsed', 0),
                                 'simulation_ticks': terminal.get('simulation_tick', 0) - start.get('simulation_tick', 0),
                                 'required_simulation_seconds': required, 'one_tick_tolerance': 1 / 60}
        c.row('exactly_one_authoritative_completion_and_held_E_edge', lambda: len(completions) == len(inputs) == 1 and start['held'] is True,
              'verify_offline_match.py:58–68')
        c.row('original_authoritative_hold_duration_with_one_tick_tolerance', lambda:
              terminal['elapsed'] - start['elapsed'] + 1 / 60 + 1e-6 >= required
              and terminal['simulation_tick'] - start['simulation_tick'] + 1 + 1e-6 >= required * 60
              and terminal['elapsed'] - command['elapsed'] + 1 / 60 + 1e-6 >= required,
              'verify_offline_match.py:70–78')
        c.row('raw_consumed_edges_equal_controller_hold_receipt', lambda:
              start == r['objective_hold']['input_started'] and terminal == r['objective_hold']['completion_notification'],
              'verify_offline_match.py:473–479')
        completed = c.observed('Player-driven ' + scenario + ' completes')
        before, after = command['observed'], completed['observed']
        # Scores are omitted from action projections: use the full raw transition publication.
        matching = [x for x in ev if 'attack_score' in x and 'defend_score' in x
                    and terminal['simulation_tick'] <= x.get('simulation_tick', -1) <= after['simulation_tick']
                    and x.get('local_contribution') == after['local_contribution']]
        full_after = matching[-1]
        earlier = [x for x in ev if 'attack_score' in x and 'defend_score' in x
                   and x.get('simulation_tick', -1) <= prior_tick]
        full_before = earlier[-1]
        round_won = (full_after['attack_score'] > full_before['attack_score'] if after['local_actor']['team'] == 0
                     else full_after['defend_score'] > full_before['defend_score'])
        expected = min(9000, before['local_actor']['credits'] + 300)
        if after['phase'] == 'post':
            expected = min(9000, expected + (2700 if round_won else 1900))
        c.facts['objective_transition'] = {'before_action': command, 'after_action': completed,
                                          'score_before_raw_snapshot': full_before, 'score_after_raw_snapshot': full_after,
                                          'expected_credits_after': expected, 'actual_credits_after': after['local_actor']['credits']}
        c.row('raw_player_contribution_and_objective_currency_exact', lambda:
              after['local_contribution'] == before['local_contribution'] + 1 and after['local_actor']['credits'] == expected,
              'verify_offline_match.py:427–488')
        c.row('same_living_local_player_completed_objective', lambda:
              after['local_actor']['id'] == before['local_actor']['id'] == i['local_actor']['id']
              and after['local_actor']['alive'] is True and 0 < after['local_actor']['health'] <= 100,
              'verify_offline_match.py:480')
        c.row('final_hold_completion_within_original_separate_wall_watchdog', lambda:
              0 <= completed['seconds'] - c.capture('05-objective-hold')['seconds'] <= required * 3,
              'verify_offline_match.py:459–466')
    except (KeyError, IndexError, ValueError, TypeError) as error:
        c.facts['final_hold_reconstruction_error'] = type(error).__name__ + ': ' + str(error)
    for label, capture in [('Natural objective round resolution', '07-objective-round-resolved'),
                           ('Natural next round after objective resolution', '08-natural-next-round')]:
        try:
            c.facts[label] = {'observed_action': c.observed(label), 'capture_action': c.capture(capture)}
        except (KeyError, ValueError) as error:
            c.facts[label] = {'unavailable': str(error)}
    c.row('natural_device_resolution_not_elimination_only', lambda:
          c.observed('Natural objective round resolution')['observed']['phase'] in ('post', 'match_over')
          and any(x.get('event') == 'notification' and any(t in x.get('message', '') for t in
                  ('Relay device defused', 'Relay device detonated')) for x in ev), 'verify_offline_match.py:503–506')
    c.row('next_natural_buy_round_within_original12s_bound', lambda:
          c.observed('Natural next round after objective resolution')['observed']['round_number'] == i['round_number'] + 1
          and c.observed('Natural next round after objective resolution')['observed']['phase'] == 'buy'
          and 0 <= c.observed('Natural next round after objective resolution')['seconds'] - c.capture('07-objective-round-resolved')['seconds'] < 12,
          'verify_offline_match.py:508–512')
    if scenario == 'plant':
        def living_role():
            states = [c.observed('Actual attacker HUD restores post-plant role guidance')['observed'], c.capture('06b-postplant-role-guidance')['observed']]
            c.facts['postplant_role_states'] = states
            return all(s['phase'] == 'live' and s['round_number'] == i['round_number'] and s['objective_state'] == 'planted'
                       and s['local_actor']['id'] == i['local_actor']['id'] and s['local_actor']['team'] == 0
                       and s['local_actor']['alive'] is True and 0 < s['local_actor']['health'] <= 100 for s in states)
        c.row('same_living_attacker_at_postplant_role_observation_and_capture', living_role, 'verify_offline_match.py:40–55,494–502')
        c.facts['role_text_limit'] = 'Action projection omits ui.status_text; inspect the raw06b PNG. Frozen source predicates are not additional raw UI observations.'
    profiles = list(c.directory.rglob('offline_training.json'))
    c.facts['restart_scope'] = 'Objective run is incomplete training. If no profile file exists, the original controller compares initial defaults on both sides; this does not establish earned runtime-profile loading.'
    c.facts['profile_file_count'] = len(profiles)
    if profiles:
        c.facts['stored_objective_profiles'] = {str(p.relative_to(c.directory)): read(p) for p in profiles}
    return c.output()


def full_match(base):
    c = Case(base, 'full-match')
    c.common(1800)
    r, i, ev = c.receipt, c.initial, c.events
    c.row('stock_initial_conditions_without_scenario_or_seed_override', lambda:
          i['initial_conditions'] == 'stock_spawns_teams_random_seeds' and not any(
              x.startswith(('--offline-seed=', '--offline-scenario=')) for x in r['commands'][0]['command']),
          'verify_offline_match.py:103–104,669–672,689–691')
    completed = [x for x in ev if x.get('event') == 'completed']
    c.facts['completion_event_count'] = len(completed)
    c.row('one_completion_and_no_duplicate_emission', lambda: len(completed) == 1
          and not any(x.get('event') == 'duplicate_completion' for x in ev), 'verify_offline_match.py:580–602')
    if len(completed) != 1:
        return c.output()
    final = completed[0]
    summary, after, old = final['summary'], final['training_after'], i['initial_profile']
    roster = summary['scoreboard']
    humans = [a for a in roster if a.get('local') is True]
    natural_rounds = [x['round_number'] for x in ev if x.get('event') in ('initial', 'round_number')]
    seventh = [x for x in ev if x.get('event') == 'round_number' and x.get('round_number') == 7]
    xp = old['xp'] + 120 + 15 * summary['kills'] + 50 * summary['objectives']
    level = 1 + int(math.sqrt(xp / 150))
    earned = 100 + (75 if summary['won'] else 0) + (150 if old['last_daily'] != after['last_daily'] else 0) + (level - old['level']) * 250
    c.facts.update(summary=summary, training_before=old, training_after=after,
                   recomputed_xp=xp, recomputed_level=level, recomputed_earned_credits=earned,
                   natural_rounds=natural_rounds, final_raw_completion=final)
    c.row('controller_summary_training_before_and_after_match_raw_events', lambda:
          r['summary'] == summary and r['training_before'] == old and r['training_after'] == after,
          'verify_offline_match.py:616–618')
    c.row('complete_single_emission_zero_dropped', lambda: bool(summary) and final['completion_calls'] == 1
          and final['events_dropped'] == 0, 'verify_offline_match.py:580–581')
    c.row('normal_regulation_score_and_rounds', lambda: summary['offline'] is True
          and 7 <= summary['rounds'] <= 12 and summary['attack_score'] + summary['defend_score'] == summary['rounds']
          and (max(summary['attack_score'], summary['defend_score']) == 7 or summary['rounds'] == 12),
          'verify_offline_match.py:582–584')
    c.row('ten_unique_five_each_one_local_human_roster', lambda: len(roster) == 10
          and len({a['id'] for a in roster}) == 10 and len(humans) == 1
          and all(sum(a['team'] == team for a in roster) == 5 for team in (0, 1)), 'verify_offline_match.py:585–588')
    c.row('human_stats_and_final_team_outcome_exact', lambda:
          all(summary[n] == humans[0][n] for n in ('kills', 'assists', 'deaths', 'objectives'))
          and summary['won'] == (summary['attack_score'] > summary['defend_score'] if humans[0]['team'] == 0
                                 else summary['defend_score'] > summary['attack_score'])
          and summary['draw'] == (summary['attack_score'] == summary['defend_score']), 'verify_offline_match.py:589–593')
    c.row('original_natural_round_coverage_and_halftime_team_switch', lambda:
          set(natural_rounds) == set(range(1, summary['rounds'] + 1)) and len(seventh) >= 1
          and seventh[0]['local_actor']['team'] != i['local_actor']['team'], 'verify_offline_match.py:594–600')
    c.facts['natural_round_sequence_once_in_order'] = natural_rounds == list(range(1, summary['rounds'] + 1))
    c.row('earned_offline_xp_level_and_credits_recomputed', lambda:
          after['xp'] == xp and after['level'] == level and after['credits'] == old['credits'] + earned,
          'verify_offline_match.py:604–613; profile.gd:65–89')
    c.row('one_offline_history_record_and_cumulative_stats_exact', lambda:
          after['scope'] == 'offline_training' and after['matches'] == 1 and len(after['history']) == 1
          and after['history'][0]['credits_earned'] == earned
          and all(after['history'][0][name] == value for name, value in summary.items())
          and all(after[n] == old[n] + delta for n, delta in {'wins': int(summary['won']),
                  'kills': summary['kills'], 'deaths': summary['deaths']}.items()), 'verify_offline_match.py:607–615')
    profiles = list(c.directory.rglob('offline_training.json'))
    c.facts['profile_file_count'] = len(profiles)
    disk = c.directory / 'state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json'
    c.facts['selected_isolated_AppData_profile'] = str(disk.relative_to(c.directory))
    reopened_events = lines(c.directory / 'trace-reopened/events.jsonl')
    reopen = reopened_events[0]
    c.facts['reopened_initial_raw_event'] = reopen
    c.facts['reopened_event_count'] = len(reopened_events)
    c.row('earned_disk_and_runtime_profile_equal_after_normal_reopen', lambda:
          after == read(disk) == reopen['initial_profile'] == r['training_after'] == r['reopened_initial_profile'],
          'verify_offline_match.py:703–743')
    c.row('reopened_stock_uncompleted_buy_phase_and_settings_preserved', lambda:
          reopen['event'] == 'initial' and reopen['initial_conditions'] == 'stock_spawns_teams_random_seeds'
          and reopen['phase'] == 'buy' and reopen['completion_calls'] == 0
          and not any(e.get('event') in ('completed', 'duplicate_completion') for e in reopened_events)
          and after['settings'] == old['settings'], 'verify_offline_match.py:728–743')
    c.row('final_original_and_reopened_raw_status_keep_single_and_zero_completions', lambda:
          read(c.directory / 'trace/status.json')['completion_calls'] == 1
          and read(c.directory / 'trace/status.json')['training_after'] == after
          and read(c.directory / 'trace-reopened/status.json')['completion_calls'] == 0
          and read(c.directory / 'trace-reopened/status.json')['phase'] == 'buy',
          'verify_offline_match.py:637–638,737–743; retained final raw status publications')
    def combat():
        start = c.observed('Standard first live round')['observed']['local_actor']
        moved = c.observed('Real authoritative movement and aim')['observed']['local_actor']
        fired = c.observed('Actual stock sidearm ammunition depletion')['observed']['local_actor']
        begun = c.observed('Native R starts authoritative reload')['observed']['local_actor']
        reloaded = c.observed('Authoritative reload completes')['observed']['local_actor']
        c.facts['raw_first_round_combat_actors'] = {'start': start, 'moved': moved, 'fired': fired,
                                                  'reload_begun': begun, 'reloaded': reloaded}
        return (start['weapon'] == 'sidearm' and start['ammo'] == 15 and start['reserve'] == 60
                and math.dist(start['position'], moved['position']) >= .3
                and (moved['yaw'] != start['yaw'] or moved['pitch'] != start['pitch'])
                and 0 < fired['ammo'] < 15 and fired['reserve'] == 60 and begun['reload'] > 0
                and reloaded['reload'] == 0 and reloaded['ammo'] == 15 and reloaded['reserve'] < 60
                and reloaded['ammo'] + reloaded['reserve'] == fired['ammo'] + fired['reserve'])
    c.row('raw_stock_native_combat_displacement_and_reload_conservation', combat, 'verify_offline_match.py:514–551')
    c.row('held_Tab_matchover_roster_stage_actions_and_release_recorded', lambda:
          c.observed('Actual held Tab displays final roster')['observed']['phase'] == 'match_over'
          and 'Tab' in c.observed('Actual held Tab displays final roster')['held_keys']
          and c.capture('08-final-scoreboard')['observed']['phase'] == 'match_over'
          and 'Tab' in c.capture('08-final-scoreboard')['held_keys']
          and 'Tab' not in c.observed('Actual Tab release dismisses final roster')['held_keys'], 'verify_offline_match.py:620–638')
    c.facts['final_roster_visibility_limit'] = 'Action projections omit scoreboard_visible. Stage names and held Tab alone do not establish rendered roster visibility; inspect raw08-final-scoreboard PNG.'
    c.facts['scope_limit'] = 'Local offline training only; no online wallet/inventory reward, physical device, human-input-feel, performance, collector-completeness or whole-gate claim.'
    return c.output()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('evidence', type=Path, help='Official extracted directory containing offline-plant/defuse/full-match')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = {'source': SOURCE, 'run_id': RUN, 'job_id': JOB, 'official_evidence_path': str(a.evidence.resolve()),
              'scope': __doc__, 'cases': [objective(a.evidence, 'plant'), objective(a.evidence, 'defuse'), full_match(a.evidence)]}
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'cases': [{'scenario': c['scenario'], 'predicates': c['predicate_status_counts']} for c in result['cases']]}))
