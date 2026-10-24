"""Preview-only module: the Kestrel 9 with its hands, for render_views.py (not exported)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kestrel_9 as pistol  # noqa: E402
import kestrel_9_hands as hands  # noqa: E402

GROUPS = pistol.GROUPS
ANCHORS = pistol.ANCHORS


def build():
    static, mag = pistol.build()
    hands.build(reset=False)
    return static, mag
