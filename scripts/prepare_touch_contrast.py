#!/usr/bin/env python3
"""Materialize a source-bound, isolated native touch fixture; never run Godot."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASELINE = "138a1ab810a29e3c504f5811a0051a08e1ad52b9"
TOUCH = "game/scripts/ui/touch_controls.gd"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def split_args(text):
    args, start, depth, quote = [], 0, 0, None
    for i, c in enumerate(text):
        if quote:
            if c == quote and (i == 0 or text[i - 1] != "\\"):
                quote = None
        elif c in "\"'":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            args.append(text[start:i].strip())
            start = i + 1
    args.append(text[start:].strip())
    return args


def instrument(source):
    """Change only designated foreground color arguments; retain all geometry."""
    lines, receipt, section = [], [], ""
    color_index = {"draw_circle": 2, "draw_arc": 5, "draw_line": 2,
                   "draw_rect": 1, "draw_string": 6, "draw_string_outline": 7}
    for number, line in enumerate(source.splitlines(), 1):
        if line.startswith("func "):
            section = line.split("(")[0][5:]
        match = re.search(r"\b(draw_circle|draw_arc|draw_line|draw_rect|draw_string_outline|draw_string)\((.*)\)$", line)
        group = None
        if match and section in ("_draw", "_draw_action_icon"):
            kind, text = match.groups()
            args = split_args(text)
            if section == "_draw_action_icon":
                group = '"inactive_icon" if probe_depleted else "active_icon"'
            elif kind == "draw_string" and args[2] == "label_text":
                group = '"inactive_label" if depleted else "active_label"'
            elif kind == "draw_string" and args[2] == "digits":
                group = '"empty_count" if depleted else "ready_count"'
            elif kind == "draw_arc" and args[:2] == ["point", "r"] and args[-1] == "1.25":
                group = '"border"'
            elif kind == "draw_arc" and args[:2] == ["point", "r"] and args[-1] == "2.0":
                group = '"held_border"'
            elif kind == "draw_arc" and args[0] == "origin" and "Color(0.8," in args[5]:
                group = '"joystick_ring"'
            elif kind == "draw_circle" and "Color(0.8," in args[2]:
                group = '"joystick_knob"'
            group = group or '"backdrop"'
            if group:
                index = color_index[kind]
                original = args[index]
                args[index] = "_contrast_color(%s, %s)" % (group, original)
                replacement = kind + "(" + ", ".join(args) + ")"
                line = line[:match.start()] + replacement
                receipt.append({"line": number, "call": kind, "group": group,
                                "color": original, "geometry": args[:index] + args[index + 1:]})
        if "\t\t_draw_action_icon(key," in line:
            lines.append("\t\tprobe_depleted = depleted")
        lines.append(line)
    required = {"active_label", "active_icon", "ready_count", "border", "held_border",
                "joystick_ring", "joystick_knob"}
    found = " ".join(x["group"] for x in receipt)
    if any('"' + x + '"' not in found for x in required):
        raise ValueError("unclassified required foreground")
    result = "\n".join(lines) + '''

# Test-only diagnostic state. No product method/input/geometry is changed.
var probe_group := ""
var probe_pass := "normal"
var probe_depleted := false
var probe_alphas: Dictionary = {}
func _contrast_color(group: String, original: Color) -> Color:
	probe_alphas[group] = minf(float(probe_alphas.get(group, 1.0)), original.a)
	if probe_pass == "footprint":
		return Color.WHITE if group == probe_group else Color(0, 0, 0, 0)
	if group != probe_group or probe_pass == "normal": return original
	if probe_pass == "underlay": return Color(0, 0, 0, 0)
	if probe_pass == "black": return Color(0, 0, 0, original.a)
	if probe_pass == "white": return Color(1, 1, 1, original.a)
	assert(false, "unknown diagnostic pass")
	return original
'''
    return result, receipt


def prepare(repo, source, out):
    out.mkdir(parents=True, exist_ok=False)
    entries = []
    # Exact tracked game bytes, ~10 MiB. Typed global-class dependencies include
    # SBActor in the utility's unused grenade branch, so retain their real source.
    paths = git(repo, "ls-tree", "-r", "--name-only", source, "game").decode().splitlines()
    for name in paths:
        data = git(repo, "show", source + ":" + name)
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({"path": name, "sha256": sha(data), "bytes": len(data)})
    touch = (out / TOUCH).read_text()
    wrapped, receipt = instrument(touch)
    # Two class_name TacticalTouch declarations must not share a project.
    wrapped = wrapped.replace("class_name TacticalTouch\n", "", 1)
    wrapped_path = out / "game/tests/touch_contrast_instrumented.gd"
    wrapped_path.write_text(wrapped)
    instrumented_uid = b"uid://d1x3t7c9m2n5p\n"
    wrapped_path.with_suffix(".gd.uid").write_bytes(instrumented_uid)
    fixture_paths = ["game/tests/touch_contrast_capture.gd", "game/tests/touch_contrast_capture.gd.uid"]
    for name in fixture_paths:
        data = (repo / "scripts/fixtures/touch_contrast" / Path(name).name).read_bytes()
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = {"source": source, "original_touch_sha256": sha(touch.encode()),
                "instrumented_sha256": sha(wrapped.encode()),
                "instrumented_uid_sha256": sha(instrumented_uid), "files": entries,
                "instrumentation": receipt, "fixture": [
                    {"path": x, "sha256": sha((repo / "scripts/fixtures/touch_contrast" / Path(x).name).read_bytes())} for x in fixture_paths]}
    (out / "SOURCE.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    for name, source in [("baseline", BASELINE), ("candidate", args.candidate)]:
        source = git(args.repo, "rev-parse", source).decode().strip()
        manifest = prepare(args.repo, source, args.out / name)
        print(name, source, len(manifest["files"]), manifest["instrumented_sha256"])


if __name__ == "__main__":
    main()
