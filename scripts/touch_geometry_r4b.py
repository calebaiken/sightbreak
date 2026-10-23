#!/usr/bin/env python3
"""Pure execution of the product's restricted geometry functions, no engine.

The translator accepts only these small source functions and executes their
actual expressions. It is review support, not evidence of Godot execution.
Continuous disk proofs conservatively cover glyph/plate/badge raster envelopes.
"""
import math
from functools import lru_cache
from pathlib import Path
import re

import numpy as np

FUNCTIONS = ("layout_rect", "effective_scale", "radius", "hit_radius", "resolved_position", "control_point", "action_at")


class Vector2:
    def __init__(self, x=0., y=None): self.x, self.y = float(x), float(x if y is None else y)
    def __add__(self, b): return Vector2(self.x + b.x, self.y + b.y)
    def __sub__(self, b): return Vector2(self.x - b.x, self.y - b.y)
    def __mul__(self, b): return Vector2(self.x * (b.x if isinstance(b, Vector2) else b), self.y * (b.y if isinstance(b, Vector2) else b))
    def min(self, b): return Vector2(min(self.x, b.x), min(self.y, b.y))
    def clamp(self, lo, hi): return Vector2(min(max(self.x, lo.x), hi.x), min(max(self.y, lo.y), hi.y))
    def distance_to(self, b): return math.hypot(self.x - b.x, self.y - b.y)
    def is_equal_approx(self, b): return abs(self.x - b.x) <= 1e-5 and abs(self.y - b.y) <= 1e-5
    def array(self): return np.array([self.x, self.y])


Vector2.ZERO, Vector2.ONE = Vector2(0, 0), Vector2(1, 1)


class Rect2:
    def __init__(self, position, size): self.position, self.size, self.end = position, size, position + size


def gd_value(value):
    return Vector2(value.x, value.y) if isinstance(value, Vector2) else value


def function_source(source, name):
    match = re.search(r"^func " + name + r"\((.*?)\).*?:\n(.*?)(?=^func |\Z)", source, re.M | re.S)
    if not match: raise ValueError("missing geometry function: " + name)
    return match.group(0).rstrip(), match.group(1), match.group(2).rstrip()


@lru_cache(maxsize=32)
def translate(source, name):
    original, args, body = function_source(source, name)
    args = re.sub(r":\s*\w+", "", args)
    lines = ["def " + name + "(" + args + "):"]
    for line in body.splitlines():
        if line.startswith("#") or not line.strip(): continue
        if not line.startswith("\t"): raise ValueError("unexpected source outside function")
        line = line.replace(":=", "=")
        line = re.sub(r"\bvar (\w+)(?::\s*\w+)?", r"\1", line)
        line = line.replace("false", "False").replace("true", "True")
        # GDScript Vector2 assignment copies its value; Python objects do not.
        match = re.match(r"(\s*)(\w+) = (.+)$", line)
        if match: line = match[1] + match[2] + " = gd_value(" + match[3] + ")"
        lines.append(line.expandtabs(4))
    python = "\n".join(lines) + "\n"
    return python, original, compile(python, "product:" + name, "exec")


def geometry(source, size, insets, scale, positions=None, editing=False, reverse=False):
    defaults_text = source.split("const DEFAULT_POSITIONS :=", 1)[1].split("var positions:", 1)[0]
    defaults = {a: Vector2(float(x), float(y)) for a, x, y in re.findall(r'"(\w+)": Vector2\(([\d.]+), ([\d.]+)\)', defaults_text)}
    actual = {a: gd_value(v) for a, v in defaults.items()}
    for a, p in (positions or {}).items(): actual[a] = Vector2(*p)
    if reverse: actual = dict(reversed(list(actual.items())))
    left, top, right, bottom = insets
    env = {"Vector2": Vector2, "Rect2": Rect2, "gd_value": gd_value,
        "minf": min, "maxf": max, "clampf": lambda x, lo, hi: min(max(x, lo), hi), "sqrt": math.sqrt,
        "INF": math.inf, "str": str, "positions": actual, "DEFAULT_POSITIONS": defaults,
        "safe_rect": Rect2(Vector2(left, top), Vector2(size[0] - left - right, size[1] - top - bottom)),
        "size": Vector2(*size), "hud_scale": scale, "editing": editing}
    translated = {}
    current = "func hit_radius(" in source
    for name in FUNCTIONS if current else ("radius", "control_point", "action_at"):
        py, original, code = translate(source, name)
        exec(code, env)
        translated[name] = {"gdscript": original, "python": py}
    if not current:
        env["hit_radius"] = lambda action: env["radius"](action) * 1.25
        env["effective_scale"] = lambda: scale
        env["resolved_position"] = lambda action: gd_value(actual[action])
    points = {a: env["control_point"](a) for a in actual}
    radii = {a: env["radius"](a) for a in actual}
    hits = {a: env["hit_radius"](a) for a in actual}
    # Geometry is constant within this case. Memoize only evaluated source
    # results, while the real translated action_at loop remains unchanged.
    env["control_point"], env["hit_radius"] = points.__getitem__, hits.__getitem__
    return {"env": env, "points": points, "radii": radii, "hits": hits, "translations": translated}


@lru_cache(maxsize=4)
def paint_program(source):
    return [(name, compile(re.search(r"^\t\tvar " + name + r" := (.+)$", source, re.M).group(1), "product:draw:" + name, "eval"))
        for name in ("compact", "paint_r", "rim_r", "rim_shadow", "icon_y", "label_y", "badge_offset", "badge")]


def paint_values(source, model, action):
    env = dict(model["env"], key=action, r=model["radii"][action], point=model["points"][action])
    for name, code in paint_program(source): env[name] = eval(code, env)
    return env


def component_envelopes(source, model, action, reference):
    paint = paint_values(source, model, action)
    point = model["points"][action].array()
    circles = [{"kind": "plate_and_rim", "center": point, "radius": max(paint["paint_r"], paint["rim_r"] + max(paint["rim_shadow"], 2.) / 2) + .75}]
    entry = reference[action]
    original = np.array(entry["point"])
    for kind, old_y, extra in (("label", 17, 3.75), ("icon", -8, 1.75)):
        xy = np.array(entry["support"][kind], dtype=float) + .5 - original
        xy[:, 1] += paint[kind + "_y"] - old_y
        lo, hi = xy.min(axis=0), xy.max(axis=0)
        center = (lo + hi) / 2
        circles.append({"kind": kind + "_with_surround", "center": point + center, "radius": float(np.linalg.norm((hi - lo) / 2)) + extra})
    if action in ("grenade", "smoke"):
        circles.append({"kind": "badge_and_digits", "center": paint["badge"].array(), "radius": 11.625 + .75})
    return circles


def ownership_minimum(center, radius, own, neighbor, own_hit, neighbor_hit):
    """Exact minimum of neighbor distance² minus own distance² over a disk."""
    dc, do = center - neighbor, center - own
    a = 1 / neighbor_hit ** 2 - 1 / own_hit ** 2
    linear = 2 * (dc / neighbor_hit ** 2 - do / own_hit ** 2)
    constant = np.dot(dc, dc) / neighbor_hit ** 2 - np.dot(do, do) / own_hit ** 2
    length = float(np.linalg.norm(linear))
    distance = min(radius, length / (2 * a)) if a > 0 else radius
    value = float(constant - length * distance + a * distance ** 2)
    witness = center - linear / length * distance if length else center
    return value, witness


def check_case(source, size, insets, scale, reference, positions=None, sample=False):
    model = geometry(source, size, insets, scale, positions)
    env, points, hits = model["env"], model["points"], model["hits"]
    rect, errors, envelopes = env["layout_rect"](), [], {}
    minimum_margin, minimum_clearance = math.inf, math.inf
    for action in points:
        point = points[action]
        safe = min(point.x - rect.position.x, point.y - rect.position.y, rect.end.x - point.x, rect.end.y - point.y) - hits[action]
        if safe < -.00001: errors.append({"kind": "full_target_unsafe", "action": action, "margin": safe})
        if action != "move": envelopes[action] = component_envelopes(source, model, action, reference)
    for action, circles in envelopes.items():
        for circle in circles:
            c, r = circle["center"], circle["radius"]
            own_distance = float(np.linalg.norm(c - points[action].array())) + r
            if own_distance > hits[action] + .00001: errors.append({"kind": "unclaimed_affordance", "action": action, "primitive": circle["kind"], "excess": own_distance - hits[action]})
            for other in envelopes:
                if other == action: continue
                margin, witness = ownership_minimum(c, r, points[action].array(), points[other].array(), hits[action], hits[other])
                minimum_margin = min(minimum_margin, margin)
                if margin <= 0:
                    errors.append({"kind": "wrong_owner", "action": action, "neighbor": other, "primitive": circle["kind"], "minimum_margin": margin,
                        "witness_xy": witness.tolist(), "actual_action_at": env["action_at"](Vector2(*witness))})
            if sample:
                for angle in np.linspace(0, 2 * math.pi, 9)[:-1]:
                    xy = c + r * np.array([math.cos(angle), math.sin(angle)])
                    actual = env["action_at"](Vector2(*xy))
                    if actual != action: errors.append({"kind": "actual_source_owner", "action": action, "actual": actual, "xy": xy.tolist()})
    items = list(envelopes)
    for index, action in enumerate(items):
        for other in items[index + 1:]:
            for a in envelopes[action]:
                for b in envelopes[other]:
                    gap = float(np.linalg.norm(a["center"] - b["center"])) - a["radius"] - b["radius"]
                    minimum_clearance = min(minimum_clearance, gap)
                    if gap <= 0: errors.append({"kind": "paint_envelope_overlap", "actions": [action, other], "primitives": [a["kind"], b["kind"]], "clearance": gap})
    return {"size": list(size), "insets": list(insets), "requested_scale": scale, "effective_scale": env["effective_scale"](),
        "errors": errors, "minimum_normalized_squared_ownership_margin": minimum_margin, "minimum_paint_clearance": minimum_clearance,
        "geometry": {a: {"point": p.array().tolist(), "radius": model["radii"][a], "hit_radius": hits[a], "resolved_position": env["resolved_position"](a).array().tolist()} for a, p in points.items()}}


def snapshot(source, size, insets, scale, reference):
    model = geometry(source, size, insets, scale)
    names = [a for a in model["points"] if a != "move"]
    circles = [(index, c) for index, a in enumerate(names) for c in component_envelopes(source, model, a, reference)]
    return {"points": np.array([model["points"][a].array() for a in names]), "hits": np.array([model["hits"][a] for a in names]),
        "centers": np.array([c["center"] for _, c in circles]), "radii": np.array([c["radius"] for _, c in circles]),
        "owners": np.array([i for i, _ in circles]), "names": names, "rect": model["env"]["layout_rect"]()}


def critical_scales(source, size, insets):
    model = geometry(source, size, insets, .7)
    rect = model["env"]["layout_rect"]()
    scales = {.7, 1.5, min(rect.size.x / 640, rect.size.y / 480, 1.5), 26 / 35, 26 / 28, 32 / 28, 31 / 35,
        (31 - 12.625) / math.sqrt(2) / (28 * .66), 12.625 / (35 - 28 * .66 * math.sqrt(2))}
    for action in model["points"]:
        p = model["env"]["resolved_position"](action)
        coefficient = (65 if action == "move" else 40 if action == "fire" else 28) * 1.25
        scales.update((edge - 1) / coefficient for edge in (p.x * rect.size.x, (1 - p.x) * rect.size.x, p.y * rect.size.y, (1 - p.y) * rect.size.y))
    return sorted(s for s in scales if .7 <= s <= 1.5)


def interval_certificate(source, size, insets, reference):
    """Bound every scale on registered piecewise-linear branches, recursively.

    For each interval, center/radius/hit variation is bounded by its endpoints.
    Native ownership is still unexecuted; the reviewer must audit the critical
    scale list and the translator's GDScript value semantics independently.
    """
    cache, leaves, failures = {}, [], []
    def snap(value):
        if value not in cache: cache[value] = snapshot(source, size, insets, value, reference)
        return cache[value]
    def visit(lo, hi, depth):
        mid = (lo + hi) / 2
        a, b, m = snap(lo), snap(hi), snap(mid)
        # Detect a missed branch; no certificate is issued through a nonlinear
        # or discontinuous source region. Native source remains separately gated.
        linear = max(float(np.max(np.abs((a[k] + b[k]) / 2 - m[k]))) for k in ("points", "hits", "centers", "radii")) < 1e-7
        if not linear:
            if depth < 24: visit(lo, mid, depth + 1); visit(mid, hi, depth + 1); return
            failures.append({"lo": lo, "hi": hi, "reason": "unresolved source branch"}); return
        owners, p, h, c, r = m["owners"], m["points"], m["hits"], m["centers"], m["radii"]
        point_shift = np.maximum(np.linalg.norm(a["points"] - p, axis=1), np.linalg.norm(b["points"] - p, axis=1))
        shape_shift = np.maximum(np.linalg.norm(a["centers"] - c, axis=1) + abs(a["radii"] - r), np.linalg.norm(b["centers"] - c, axis=1) + abs(b["radii"] - r))
        hmin, hmax = np.minimum(a["hits"], b["hits"]), np.maximum(a["hits"], b["hits"])
        dn, do = c[:, None, :] - p[None, :, :], c - p[owners]
        qa = 1 / h[None, :] ** 2 - 1 / h[owners, None] ** 2
        ql = 2 * (dn / h[None, :, None] ** 2 - do[:, None, :] / h[owners, None, None] ** 2)
        qc = np.sum(dn * dn, axis=-1) / h[None, :] ** 2 - np.sum(do * do, axis=-1)[:, None] / h[owners, None] ** 2
        ll = np.linalg.norm(ql, axis=-1)
        distance = np.where(qa > 0, np.minimum(r[:, None], ll / np.maximum(2 * qa, 1e-30)), r[:, None])
        margin = qc - ll * distance + qa * distance ** 2
        tn, to = shape_shift[:, None] + point_shift[None, :], shape_shift + point_shift[owners]
        nmax = np.linalg.norm(dn, axis=-1) + r[:, None] + tn
        omax = np.linalg.norm(do, axis=-1) + r + to
        en = (2 * nmax * tn + tn * tn) / hmin[None, :] ** 2 + nmax ** 2 * (1 / hmin[None, :] ** 2 - 1 / hmax[None, :] ** 2)
        eo = (2 * omax * to + to * to) / hmin[owners] ** 2 + omax ** 2 * (1 / hmin[owners] ** 2 - 1 / hmax[owners] ** 2)
        bounded = margin - en - eo[:, None]
        bounded[np.arange(len(owners)), owners] = math.inf
        own_margin = hmin[owners] - (np.linalg.norm(do, axis=-1) + r + to)
        gaps = np.linalg.norm(c[:, None, :] - c[None, :, :], axis=-1) - r[:, None] - r[None, :] - shape_shift[:, None] - shape_shift[None, :]
        gaps[owners[:, None] == owners[None, :]] = math.inf
        minimum = [float(bounded.min()), float(own_margin.min()), float(gaps.min())]
        if min(minimum) <= 1e-8:
            actual_bad = float(np.min(np.where(np.arange(len(h))[None, :] == owners[:, None], math.inf, margin))) <= 0
            if depth < 24 and not actual_bad: visit(lo, mid, depth + 1); visit(mid, hi, depth + 1); return
            failures.append({"lo": lo, "hi": hi, "reason": "ownership/target/paint bound failed", "bounds": minimum}); return
        leaves.append({"lo": lo, "hi": hi, "ownership_squared_margin_lower": minimum[0], "inside_hit_margin_lower": minimum[1], "paint_clearance_lower": minimum[2]})
    critical = critical_scales(source, size, insets)
    endpoints = [check_case(source, size, insets, x, reference, sample=True) for x in critical]
    for lo, hi in zip(critical, critical[1:]):
        # Each discontinuity endpoint is checked above; nextafter selects the
        # one-sided open branch. Sixteen ULPs exceed expression roundoff here.
        left, right = lo, hi
        for _ in range(16): left, right = np.nextafter(left, hi), np.nextafter(right, lo)
        visit(float(left), float(right), 0)
    # Full hit safety follows directly from the source clamp when the maximum
    # target+1 fits both safe dimensions; movement's larger target is included.
    full = geometry(source, size, insets, 1.5)
    rect = full["env"]["layout_rect"]()
    target_fits = 2 * (max(full["hits"].values()) + 1) <= min(rect.size.x, rect.size.y)
    return {"size": list(size), "insets": list(insets), "critical_scales": critical, "endpoints": endpoints,
        "intervals": leaves, "failures": failures, "full_targets_fit_safe_dimensions": target_fits,
        "pass": bool(target_fits and not failures and all(not row["errors"] for row in endpoints))}
