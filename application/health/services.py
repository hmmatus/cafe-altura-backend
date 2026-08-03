from collections.abc import Sequence

from application.health.interfaces import HealthProbe
from domain.health.entities import ComponentHealth, HealthStatus


class CheckHealth:
    """Probes every dependency and reports whether the server can serve traffic."""

    def __init__(self, probes: Sequence[HealthProbe]):
        self._probes = probes

    def execute(self) -> HealthStatus:
        results: list[ComponentHealth] = []

        for probe in self._probes:
            try:
                results.append(probe.check())
            except Exception as exc:  # a probe that blows up is itself the bad news
                results.append(ComponentHealth(name=probe.name, healthy=False, detail=str(exc)))

        return HealthStatus(components=tuple(results))
