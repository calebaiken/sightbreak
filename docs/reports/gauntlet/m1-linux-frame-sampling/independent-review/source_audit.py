"""Audit the frozen source diff without executing game, engine or controller."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
BASE = '9616f52723666e651ca8ae839420cf2b308e5c5a'
CANDIDATE = '8afe0cc6b4c9051d3649a82bbcb4c8de8f947f9c'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


class RemoveOptIn(ast.NodeTransformer):
    def visit_ImportFrom(self, node):
        return None if node.module == 'linux_frame_sampler' else node

    def visit_Assign(self, node):
        if any(isinstance(target, ast.Name) and target.id == 'frame_sampler' for target in node.targets):
            return None
        return self.generic_visit(node)

    def visit_If(self, node):
        names = [value.id for value in ast.walk(node.test) if isinstance(value, ast.Name)]
        attributes = [value.attr for value in ast.walk(node.test) if isinstance(value, ast.Attribute)]
        if 'frame_sampler' in names or 'linux_frame_diagnostics' in attributes:
            return None
        return self.generic_visit(node)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and any(isinstance(value, ast.Constant)
                and value.value == '--linux-frame-diagnostics' for value in node.value.args):
            return None
        return self.generic_visit(node)


def main():
    names = git('diff', '--name-only', BASE, CANDIDATE).decode().splitlines()
    source_names = [name for name in names if not name.startswith('docs/')]
    expected = ['game/scripts/offline_diagnostics.gd', 'scripts/linux_frame_sampler.py',
                'scripts/test_linux_frame_sampler.py', 'scripts/verify_offline_match.py']
    gd_path = 'game/scripts/offline_diagnostics.gd'
    gd_before, gd_after = [git('show', f'{ref}:{gd_path}').decode() for ref in (BASE, CANDIDATE)]
    begin = gd_after.index('\tvar read_begin_usec := Time.get_ticks_usec()\n')
    end_text = '\t\t"read_end_usec": Time.get_ticks_usec()}\n'
    end = gd_after.index(end_text, begin) + len(end_text)
    gd_block = gd_after[begin:end]
    py_path = 'scripts/verify_offline_match.py'
    before, after = [git('show', f'{ref}:{py_path}').decode() for ref in (BASE, CANDIDATE)]
    stripped = RemoveOptIn().visit(ast.parse(after))
    helper = git('show', f'{CANDIDATE}:scripts/linux_frame_sampler.py').decode()
    helper_ast = ast.parse(helper)
    forbidden_imports = {'subprocess', 'socket', 'requests', 'urllib', 'ctypes', 'multiprocessing'}
    helper_imports = {node.module.split('.')[0] for node in ast.walk(helper_ast) if isinstance(node, ast.ImportFrom)}
    helper_imports |= {alias.name.split('.')[0] for node in ast.walk(helper_ast) if isinstance(node, ast.Import) for alias in node.names}
    calls = {node.func.attr for node in ast.walk(helper_ast) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    checks = dict(
        exact_source_paths=source_names == expected,
        snapshot_addition_only=gd_after[:begin] + gd_after[end:] == gd_before,
        snapshot_lines=gd_block.count('\n') == 22,
        snapshot_contains_no_new_callback_or_file_io=not any(word in gd_block for word in ('await ', 'connect(', 'FileAccess', 'DirAccess', 'store_')),
        controller_original_ast_unchanged=ast.dump(stripped, include_attributes=False) == ast.dump(ast.parse(before), include_attributes=False),
        helper_no_process_network_or_native_imports=not helper_imports.intersection(forbidden_imports),
        helper_no_scheduling_or_signal_calls=not calls.intersection({'kill', 'killpg', 'terminate', 'setpriority', 'nice', 'sched_setaffinity', 'Popen', 'run'}),
        helper_process_only_numeric_owned_path="self.pid = process.pid" in helper and "self.proc / str(self.pid)" in helper,
        helper_whitelist_environment="ENV_KEYS = ('DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'LP_NUM_THREADS')" in helper,
        helper_one_second_wait='self.stop_event.wait(min(1.0,' in helper,
        helper_lifetime_guard='not 0 < duration_seconds <= 180' in helper,
        helper_fresh_output="self.output.open('x'," in helper,
    )
    sha = {name: hashlib.sha256(git('show', f'{CANDIDATE}:{name}')).hexdigest() for name in expected}
    output = dict(base=BASE, candidate=CANDIDATE, checks=checks, source_sha256=sha,
                  original_budget_proof='Original controller AST is identical after removing only new opt-in statements.',
                  passed=all(checks.values()))
    print(json.dumps(output, indent=2))
    assert output['passed']


if __name__ == '__main__':
    main()
