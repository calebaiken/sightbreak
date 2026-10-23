"""Dormant report prototype. No current analyzer imports this module."""
import math

import numpy as np

ACTIONS = ("fire", "jump", "crouch", "reload", "interact", "grenade", "smoke",
           "buy", "pause", "switch", "score")


def support(image, shape):
    value = np.asarray(image)
    if value.shape != shape or value.dtype != np.uint8:
        raise ValueError("native RGB8 image dimensions/type differ")
    if np.any(value.max(axis=-1) != value.min(axis=-1)):
        raise ValueError("isolated white footprint is not neutral")
    return value.max(axis=-1) >= 1


def audit_labels(info, grouped, components, labels):
    """Require new actual native label evidence; never reconstruct it here.

    This is only an accounting proposal. Acquisition provenance, exact source,
    normal equivalence and the unchanged contrast/ownership analyzers remain
    separate required checks. Input arrays are explicitly synthetic in controls.
    """
    errors, rows = [], []
    if set(grouped) != {"active_label", "inactive_label"}:
        return {"pass": False, "errors": ["missing exact label groups"]}
    if set(components) != set(ACTIONS) or set(labels) != set(ACTIONS):
        return {"pass": False, "errors": ["missing exact source action evidence"]}
    try:
        width, height = info["size"]
        shape = (height, width, 3)
        groups = {name: support(value, shape) for name, value in grouped.items()}
        parts = {name: support(value, shape) for name, value in components.items()}
        ink = {name: support(value, shape) for name, value in labels.items()}
        geometry = info["geometry"]
        if not set(ACTIONS) <= set(geometry):
            raise ValueError("missing original physical geometry")
        for action in ACTIONS:
            x, y = geometry[action]["point"]
            hit = geometry[action]["hit_radius"]
            if not all(math.isfinite(float(v)) for v in (x, y, hit)) or hit <= 0:
                raise ValueError("invalid original physical geometry")
    except (KeyError, TypeError, ValueError) as exc:
        return {"pass": False, "errors": [str(exc)]}
    assigned = {name: np.zeros((height, width), dtype=np.uint16) for name in groups}
    for action in ACTIONS:
        mask = ink[action]
        group = "inactive_label" if info["counts"].get(action, 1) <= 0 else "active_label"
        assigned[group] += mask
        yy, xx = np.where(mask)
        point = geometry[action]["point"]
        outside_component = int((mask & ~parts[action]).sum())
        outside_group = int((mask & ~groups[group]).sum())
        changed_coverage = int((np.any(labels[action] != grouped[group], axis=-1) & mask).sum())
        outside_hit, wrong_owner = 0, 0
        for y, x in zip(yy, xx):
            center = (float(x) + .5, float(y) + .5)
            distance = math.hypot(center[0] - point[0], center[1] - point[1])
            outside_hit += distance > geometry[action]["hit_radius"]
            eligible = []
            for other in ACTIONS:
                p, h = geometry[other]["point"], geometry[other]["hit_radius"]
                normalized = math.hypot(center[0] - p[0], center[1] - p[1]) / h
                if normalized <= 1:
                    eligible.append((normalized, other))
            winner = min(eligible)[1] if eligible else None
            wrong_owner += winner != action
        row = {"action": action, "group": group, "support_pixels": len(xx),
               "outside_component": outside_component, "outside_group": outside_group,
               "changed_coverage": changed_coverage,
               "outside_hit": int(outside_hit), "wrong_owner": int(wrong_owner)}
        rows.append(row)
        if not len(xx) or any(row[k] for k in
                ("outside_component", "outside_group", "changed_coverage", "outside_hit", "wrong_owner")):
            errors.append(action + ": incomplete or foreign source label support")
    for group, mask in groups.items():
        missing = int((mask & (assigned[group] == 0)).sum())
        duplicate = int((assigned[group] > 1).sum())
        extra = int((~mask & (assigned[group] > 0)).sum())
        if missing or duplicate or extra:
            errors.append(group + ": missing=%d duplicate=%d extra=%d" %
                          (missing, duplicate, extra))
    return {"pass": not errors, "errors": errors, "rows": rows,
            "scope": "PROPOSED_ACCOUNTING_ONLY_REQUIRES_NEW_NATIVE_ACTION_LABEL_FOOTPRINTS"}


def neutral_difference_interval(black, white):
    """Conservative necessary condition under nearest-code final quantization.

    Each observed code has a closed +/-0.5 interval. A single ideal neutral W-B
    contribution must lie in every [W-B-1, W-B+1] interval. Closed endpoints
    deliberately do not assume a tie rule. Feasible does not prove neutrality,
    source-over blending, valid alpha, underlay reconstruction or contrast.
    """
    b, w = np.asarray(black, float), np.asarray(white, float)
    if b.shape != (3,) or w.shape != (3,) or not np.isfinite([b, w]).all():
        raise ValueError("expected two finite RGB triples")
    if np.any(b < 0) or np.any(b > 255) or np.any(w < 0) or np.any(w > 255):
        raise ValueError("RGB codes outside [0,255]")
    delta = w - b
    lo, hi = max(0., float((delta - 1).max())), min(255., float((delta + 1).min()))
    return {"lower": lo, "upper": hi, "feasible": lo <= hi,
            "width": max(0., hi - lo), "endpoint_only": lo == hi,
            "observed_difference": delta.tolist(), "quantization_half_width": .5,
            "scope": "NECESSARY_FINAL_QUANTIZATION_CONDITION_ONLY_NOT_CURRENT_ACCEPTANCE"}
