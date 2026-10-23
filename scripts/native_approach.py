"""Bounded WASD driving from read-only exported-client observations."""
import math
import statistics
import time


def approach_floor(x, z, *, observe, key, pause, record, deadline, clock=time.monotonic, pulse=None):
    """Walk coarsely, then pulse from rest instead of chasing delayed positions.

    The final pulses use the inspected 28 m/s² ground acceleration to limit
    travel, and the observed simulation/wall ratio to time native key releases.
    Success is determined only from actual later neutral stopped observations.
    """
    directions = ('w', 'a', 's', 'd')
    origin = None
    identity = None
    last_tick = -1
    last_sample = None
    rates = []
    released_tick = -1
    settled = []
    driving = False
    fine = False

    def steer(dx, dz, yaw):
        mx, my = math.cos(yaw) * dx - math.sin(yaw) * dz, -math.sin(yaw) * dx - math.cos(yaw) * dz
        wanted = set()
        if abs(mx) > .15:
            wanted.add('d' if mx > 0 else 'a')
        if abs(my) > .15:
            wanted.add('w' if my > 0 else 's')
        for name in directions:
            key(name, name in wanted)

    def release():
        # Attempt every key-up even when a native delivery call fails.
        errors = []
        for name in directions:
            try:
                key(name, False)
            except Exception as error:
                errors.append(error)
        if errors:
            raise RuntimeError('Native approach could not release all movement keys') from errors[0]

    try:
        release()
        while clock() < deadline:
            state = observe()
            now = clock()
            if now >= deadline:
                break
            actor = state['local_actor']
            current_identity = (actor['id'], state['round_number'], state['phase'])
            if identity is None:
                identity = current_identity
                origin = actor['position'][:]
                released_tick = state['simulation_tick']
            if current_identity != identity or state['phase'] != 'live' or not actor['alive'] or not 0 < actor['health'] <= 100:
                raise RuntimeError('Native approach lost its living player or live round')
            tick, elapsed = state['simulation_tick'], state['elapsed']
            if tick < last_tick:
                raise RuntimeError('Native approach observation tick moved backward')
            values = [*actor['position'], *actor['velocity'], actor['yaw'], elapsed]
            if not all(math.isfinite(value) for value in values):
                raise RuntimeError('Native approach received non-finite motion evidence')
            if tick == last_tick:
                pause(min(.05, max(0, deadline - clock())))
                continue
            if last_sample is not None and now > last_sample[0] and elapsed > last_sample[1]:
                rates.append((elapsed - last_sample[1]) / (now - last_sample[0]))
                rates = rates[-5:]
            last_sample = (now, elapsed)
            last_tick = tick
            dx, dz = x - actor['position'][0], z - actor['position'][2]
            distance = math.hypot(dx, dz)
            speed = math.hypot(actor['velocity'][0], actor['velocity'][2])

            if driving:
                if distance > 2.2:
                    steer(dx, dz, actor['yaw'])
                    pause(min(.05, max(0, deadline - clock())))
                    continue
                release()
                driving = False
                released_tick = tick
                settled.clear()
                record('movement_settle_begin', requested=[x, z], released_after_tick=tick)

            neutral = state.get('local_input', {}).get('move') == [0, 0]
            if not neutral or speed > .05 or tick <= released_tick:
                settled.clear()
                pause(min(.05, max(0, deadline - clock())))
                continue
            settled.append(tick)
            if len(settled) < 2:
                pause(min(.05, max(0, deadline - clock())))
                continue
            if distance < .45:
                end = actor['position'][:]
                record('movement_completed', origin=origin, destination=end, requested=[x, z],
                       target_distance=distance, horizontal_speed=speed,
                       settled_simulation_ticks=settled[-2:])
                return end

            fine = fine or distance <= 2.2
            rate = min(1.0, max(.05, statistics.median(rates))) if rates else 1.0
            # A short acceleration/deceleration pulse travels approximately a*T²
            # from rest. Cap T so even delayed observations cannot bank a long run.
            duration = min(.125, math.sqrt(max(.01, distance - .2) / 28.0)) / rate
            record('movement_control', mode='pulse' if fine else 'walk', distance=distance,
                   simulation_per_wall=rate, pulse_wall_seconds=duration if fine else None)
            command_start = clock()
            if fine and pulse is not None:
                mx = math.cos(actor['yaw']) * dx - math.sin(actor['yaw']) * dz
                my = -math.sin(actor['yaw']) * dx - math.cos(actor['yaw']) * dz
                wanted = tuple(name for name, enabled in (
                    ('w', my > .15), ('a', mx < -.15), ('s', my < -.15), ('d', mx > .15)) if enabled)
                pulse(wanted, min(duration, max(0, deadline - clock())), deadline)
                if clock() >= deadline:
                    raise TimeoutError('Original native approach deadline expired during route pulse')
                settled.clear()
                released_tick = tick
                record('movement_pulse_released', requested=[x, z], released_after_tick=tick)
            else:
                steer(dx, dz, actor['yaw'])
                settled.clear()
                if fine:
                    pause(min(max(0, command_start + duration - clock()), max(0, deadline - clock())))
                    release()
                    released_tick = tick
                    record('movement_pulse_released', requested=[x, z], released_after_tick=tick)
                else:
                    driving = True
            pause(min(.05, max(0, deadline - clock())))
        raise TimeoutError('Legitimate native movement did not reach the requested floor position')
    finally:
        release()
