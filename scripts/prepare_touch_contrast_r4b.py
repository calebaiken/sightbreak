#!/usr/bin/env python3
"""Materialize R4B sources/diagnostics only. Never run Godot or generate UIDs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASELINE = "a52022169241df9ff662039547a375e1c46ac1c5"
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
    compact = "var paint_r :=" in source
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
                group = '"icon_surround" if probe_icon_underlay else ("inactive_icon" if probe_depleted else "active_icon")'
            elif kind == "draw_string_outline":
                group = '"label_surround"'
            elif kind in ("draw_circle", "draw_arc") and args[0] == "badge":
                group = '"badge_paint"'
            elif kind == "draw_circle" and args[0] == "point" and "Color(0.7," in args[2]:
                group = '"held_fill"'
            elif kind == "draw_string" and args[2] == "label_text":
                group = '"inactive_label" if depleted else "active_label"'
            elif kind == "draw_string" and args[2] == "digits":
                group = '"empty_count" if depleted else "ready_count"'
            elif kind == "draw_arc" and args[0] == "point" and args[1] in ("r", "rim_r") and args[-1] == "1.25":
                group = '"border"'
            elif kind == "draw_arc" and args[0] == "point" and args[1] in ("r", "rim_r") and args[-1] == "2.0":
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
        if line.strip().startswith("_draw_action_icon(key,"):
            indent = line[:len(line) - len(line.lstrip())]
            lines.append(indent + "probe_depleted = depleted")
            lines.append(indent + "probe_icon_underlay = " + ("true" if "icon_surround" in line else "false"))
        if line.startswith("\tvar origin :="):
            lines.append('\tprobe_action = "move"')
        lines.append(line)
        if line == '\t\tif key == "move": continue':
            lines.append('\t\tprobe_action = key')
        if line.startswith('\t\tvar width := font.get_string_size(label_text,'):
            body, rim, shadow = ("paint_r", "rim_r", "rim_shadow") if compact else ("r", "r", "5.25")
            icon, label = ("icon_y", "label_y") if compact else ("-8.0", "17.0")
            lines.append('\t\tprobe_paint_geometry[key] = {"point": [point.x, point.y], "nominal_radius": r, "hit_radius": r * 1.25, "body_radius": %s, "rim_radius": %s, "rim_shadow": %s, "icon_center": [point.x, point.y + %s], "label_origin": [point.x - width / 2, point.y + %s], "label_width": width, "font_size": 12, "label": label_text, "font_ascent": font.get_ascent(12), "font_descent": font.get_descent(12), "badge_center": [point.x + r * 0.72, point.y - r * 0.72], "badge_radius": 9.0, "badge_shadow": %s, "badge_rim": %s}' % (body, rim, shadow, icon, label, "5.25" if compact else "0.0", "1.25" if compact else "0.0"))
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
var probe_icon_underlay := false
var probe_action := ""
var probe_alphas: Dictionary = {}
var probe_paint_geometry: Dictionary = {}
func _contrast_color(group: String, original: Color) -> Color:
	probe_alphas[group] = minf(float(probe_alphas.get(group, 1.0)), original.a)
	var component := "component_" + probe_action
	probe_alphas[component] = minf(float(probe_alphas.get(component, 1.0)), original.a)
	var selected := group == probe_group or component == probe_group
	if probe_pass == "footprint":
		return Color.WHITE if selected else Color(0, 0, 0, 0)
	if not selected or probe_pass == "normal": return original
	if probe_pass == "underlay": return Color(0, 0, 0, 0)
	if probe_pass == "black": return Color(0, 0, 0, original.a)
	if probe_pass == "white": return Color(1, 1, 1, original.a)
	assert(false, "unknown diagnostic pass")
	return original
'''
    if "func hit_radius(" in source:
        result = result.replace('"hit_radius": r * 1.25', '"hit_radius": hit_radius(key)')
        result = result.replace('point.x + r * 0.72, point.y - r * 0.72',
            'point.x + minf(r * 0.66, (hit_radius(key) - 12.625) / sqrt(2.0)), point.y - minf(r * 0.66, (hit_radius(key) - 12.625) / sqrt(2.0))')
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
        data = (repo / "scripts/fixtures/touch_contrast_r4b" / Path(name).name).read_bytes()
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = {"source": source, "paint_variant": "r4b" if "func hit_radius(" in touch else "r3", "original_touch_sha256": sha(touch.encode()),
                "instrumented_sha256": sha(wrapped.encode()),
                "instrumented_uid_sha256": sha(instrumented_uid), "files": entries,
                "instrumentation": receipt, "fixture": [
                    {"path": x, "sha256": sha((repo / "scripts/fixtures/touch_contrast_r4b" / Path(x).name).read_bytes())} for x in fixture_paths]}
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
