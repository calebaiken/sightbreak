"""Fail-closed parsing of rendered offline HUD text, not private game state."""
import re


def parse_hud_text(status, ammunition):
    health = re.findall(r'^\s*(\d{1,3})[^A-Z0-9\n]*HEALTH\b', status.upper(), re.MULTILINE)
    ammo = re.findall(r'(?<![\w+-])(\d+)\s*/\s*(\d+)(?!\w)', ammunition)
    if (any(word in status.upper() for word in ('ELIMINATED', 'SPECTATING'))
            or len(health) != 1 or not 0 < int(health[0]) <= 100 or len(ammo) != 1):
        raise ValueError('Rendered positive-health/ammunition check failed: ' + repr((status, ammunition)))
    return {'health': int(health[0]), 'ammo': int(ammo[0][0]), 'reserve': int(ammo[0][1]),
            'status_ocr': status, 'ammo_ocr': ammunition}
