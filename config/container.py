"""Composition root.

The only module allowed to name concrete infrastructure classes. Everything else depends on
the abstract ports in `application/`.
"""

from application.health.services import CheckHealth
from infrastructure.db.probes import DatabaseProbe


def check_health() -> CheckHealth:
    return CheckHealth(probes=[DatabaseProbe()])
