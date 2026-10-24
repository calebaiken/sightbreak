"""Preview-only module: the Vectorline with its hands, for render_views.py (not exported)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vectorline as smg  # noqa: E402
import vectorline_hands as hands  # noqa: E402

GROUPS = smg.GROUPS
ANCHORS = smg.ANCHORS


def build():
    static, mag = smg.build()
    hands.build(reset=False)
    return static, mag
