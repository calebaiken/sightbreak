#!/usr/bin/env python3
"""Exact declaration compatibility only; no Godot or native acceptance."""
import ast
import re
from pathlib import Path
import subprocess
import unittest

from touch_geometry_r4b import paint_program

REPO = Path(__file__).resolve().parents[1]
OLD = '\t\tvar compact := key != "fire" and r < 32.0'
NEW = '\t\tvar compact: bool = key != "fire" and r < 32.0'
FAILED_SOURCE = "b001fc5087960729535f63c896b40d6dc25bd272"


class ExactCompactDeclaration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = subprocess.check_output([
            "git", "-C", str(REPO), "show",
            FAILED_SOURCE + ":game/scripts/ui/touch_controls.gd"]).decode()
        cls.after = (REPO / "game/scripts/ui/touch_controls.gd").read_text()
        old_helper = subprocess.check_output([
            "git", "-C", str(REPO), "show",
            FAILED_SOURCE + ":scripts/touch_geometry_r4b.py"]).decode()
        function = next(node for node in ast.parse(old_helper).body
                        if isinstance(node, ast.FunctionDef) and node.name == "paint_program")
        function.decorator_list = []
        module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
        namespace = {"re": re}
        exec(compile(module, "exact-rejected-helper-b001fc5", "exec"), namespace)
        cls.old_parser = staticmethod(namespace["paint_program"])

    def test_entire_product_delta_is_one_annotation(self):
        self.assertEqual(self.before.count(OLD), 1)
        self.assertEqual(self.after, self.before.replace(OLD, NEW, 1))

    def test_both_exact_forms_preserve_all_compiled_expressions(self):
        old_program = self.old_parser(self.before)
        for source in (self.before, self.after):
            with self.subTest(explicit_bool=NEW in source):
                program = paint_program(source)
                self.assertEqual([name for name, _ in program], [name for name, _ in old_program])
                for (name, actual), (_, expected) in zip(program, old_program):
                    self.assertEqual(actual.co_code, expected.co_code, name)
                    self.assertEqual(actual.co_consts, expected.co_consts, name)
                    self.assertEqual(actual.co_names, expected.co_names, name)

    def test_original_parser_rejection_is_retained(self):
        with self.assertRaises(AttributeError):
            self.old_parser(self.after)

    def test_wrong_explicit_types_reject(self):
        for kind in ("int", "float", "Variant", "String", "BOOL"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                paint_program(self.after.replace("var compact: bool =", "var compact: " + kind + " =", 1))

    def test_changed_expressions_reject_in_both_forms(self):
        for expression in ('key == "fire" and r < 32.0',
                           'key != "fire" and r <= 32.0',
                           'key != "fire" and r < 31.0',
                           'r < 32.0 and key != "fire"',
                           'True', 'bool(key != "fire" and r < 32.0)'):
            for source in (self.before, self.after):
                with self.subTest(expression=expression, explicit_bool=NEW in source), self.assertRaises(ValueError):
                    paint_program(source.replace('key != "fire" and r < 32.0', expression, 1))

    def test_missing_duplicate_and_unsupported_declarations_reject(self):
        cases = [self.after.replace(NEW + "\n", "", 1),
                 self.after.replace(NEW, NEW + "\n" + NEW, 1),
                 self.after.replace(NEW, NEW + "\n" + OLD, 1),
                 self.after.replace(NEW, NEW.replace("compact:", "compact :"), 1),
                 self.after.replace(NEW, NEW.replace(": bool =", ": bool :="), 1),
                 self.after.replace(NEW, NEW.replace("compact", "compactness"), 1)]
        for index, source in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                paint_program(source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
