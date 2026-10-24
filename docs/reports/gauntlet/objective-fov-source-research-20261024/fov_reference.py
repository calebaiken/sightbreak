"""Report-only source predicate and fail-closed numerical adjudicator.

No native equivalence is claimed for Python float64 sin/cos/vector operations.
A trusted native dot interval must come from verifier policy/calibration, never
from the candidate trace. An unavailable or straddling interval is unresolved.
"""
import math


def source_model(actor_position, enemy_position, yaw, elapsed, damaged_at,
                 enemy_id, attacker_id, threshold=-.15):
    values = [*actor_position, *enemy_position, yaw, elapsed, damaged_at, threshold]
    if not all(type(x) in (int, float) and math.isfinite(x) for x in values):
        raise ValueError('finite source geometry required')
    if len(actor_position) != 3 or len(enemy_position) != 3:
        raise ValueError('three-dimensional positions required')
    delta = [b - a for a, b in zip(actor_position, enemy_position)]
    length = math.sqrt(sum(x * x for x in delta))
    if not math.isfinite(length):
        raise ValueError('unresolved overflow in model geometry')
    # Godot normalized() preserves zero as zero, rather than dividing by zero.
    toward = [x / length for x in delta] if length else [0., 0., 0.]
    dot = -math.sin(yaw) * toward[0] - math.cos(yaw) * toward[2]
    age = elapsed - damaged_at
    # Match source's upper-bound-only age check; do not invent age >= 0 here.
    exception = age < 1.2 and enemy_id == attacker_id
    return dict(distance_model=length, dot_model=dot, threshold=threshold,
                age_model=age, specific_recent_attacker=exception,
                in_fov_model=dot > threshold or exception,
                native_numerical_equivalence='UNVERIFIED')


def validate_fov_reason(reason, model, *, native_dot_interval=None):
    """Validate only FOV-stage consistency; range/LOS/score stay separate.

    Recent-attacker timing must already be independently unambiguous. Interval
    endpoints are trusted math bounds, not an epsilon added to acceptance.
    """
    if reason not in ('fov', 'visibility', 'eligible'):
        raise ValueError('FOV adjudication starts only after the range gate')
    if model['specific_recent_attacker']:
        inside = True
    elif native_dot_interval is None:
        return 'UNRESOLVED_NATIVE_NUMERICS'
    else:
        lo, hi = native_dot_interval
        if not all(type(x) in (int, float) and math.isfinite(x) for x in (lo, hi)) or lo > hi:
            raise ValueError('trusted finite ordered interval required')
        threshold = model['threshold']
        if lo > threshold:
            inside = True
        elif hi <= threshold:
            inside = False
        else:
            return 'UNRESOLVED_NATIVE_NUMERICS'
    if (reason == 'fov') == inside:
        raise ValueError('recorded FOV reason contradicts source gate')
    return 'CONSISTENT_FOV_STAGE_ONLY'
