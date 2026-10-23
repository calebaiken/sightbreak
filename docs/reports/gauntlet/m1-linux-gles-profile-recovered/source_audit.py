#!/usr/bin/env python3
"""Compare the recovered controller with its exact original; no engine use."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASE = '917b143ba4e4b0d9644a7a0ddeee1dd64c139682'
PATH = 'scripts/verify_offline_match.py'


class RemoveGpuOptIn(ast.NodeTransformer):
    def __init__(self):
        self.removed = []

    def visit_Expr(self, node):
        call = node.value
        if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == 'add_argument' and call.args
                and isinstance(call.args[0], ast.Constant) and call.args[0].value == '--linux-gpu-profile'):
            self.removed.append(ast.unparse(node))
            return None
        return self.generic_visit(node)

    def visit_If(self, node):
        if any(isinstance(child, ast.Attribute) and child.attr == 'linux_gpu_profile'
               and isinstance(child.value, ast.Name) and child.value.id == 'args'
               for child in ast.walk(node.test)):
            self.removed.append(ast.unparse(node))
            return None
        return self.generic_visit(node)


def main():
    original = subprocess.check_output(['git', 'show', f'{BASE}:{PATH}'], cwd=ROOT)
    candidate = (ROOT / PATH).read_bytes()
    removal = RemoveGpuOptIn()
    stripped = removal.visit(ast.parse(candidate))
    assert len(removal.removed) == 3, removal.removed
    assert ast.dump(stripped) == ast.dump(ast.parse(original)), 'Original controller statements changed'
    assert not subprocess.check_output(['git', 'diff', BASE, '--', 'game'], cwd=ROOT), 'Game source changed'
    print(json.dumps({'base': BASE, 'path': PATH,
                      'base_sha256': hashlib.sha256(original).hexdigest(),
                      'candidate_sha256': hashlib.sha256(candidate).hexdigest(),
                      'removed_statements': removal.removed,
                      'remaining_controller_ast_identical': True,
                      'reopened_command_and_all_deadlines_preserved': True,
                      'game_diff_empty': True}, indent=2))


if __name__ == '__main__':
    main()
