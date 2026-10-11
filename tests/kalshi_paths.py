"""Puts scripts/ on sys.path for the Kalshi tests.

KALSHI_SCRIPTS_DIR overrides it, which is how test_kalshi_mutation.py runs the
suite against a deliberately broken copy of the scripts.
"""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.environ.get("KALSHI_SCRIPTS_DIR") or os.path.join(REPO, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
