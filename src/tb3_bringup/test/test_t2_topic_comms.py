"""T2: Cross-container topic comms — /scan published by turtlebot, received by simulator.

Deferred to Phase 10 (requires physical Raspberry Pi 4 hardware).
Marked xfail so it appears in CI output without blocking the suite.
"""

import pytest


@pytest.mark.xfail(
    reason="T2 deferred to Phase 10: requires physical turtlebot hardware on LAN",
    strict=False,
)
def test_scan_from_turtlebot():
    pytest.fail("T2: cross-container /scan not testable without physical hardware")
