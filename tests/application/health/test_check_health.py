"""Use-case tests: no database, no HTTP, no Django test case."""

import unittest

from application.health.interfaces import HealthProbe
from application.health.services import CheckHealth
from domain.health.entities import ComponentHealth


class FakeProbe(HealthProbe):
    def __init__(self, name: str, healthy: bool = True, raises: Exception | None = None):
        self._name = name
        self._healthy = healthy
        self._raises = raises

    @property
    def name(self) -> str:
        return self._name

    def check(self) -> ComponentHealth:
        if self._raises is not None:
            raise self._raises
        return ComponentHealth(name=self._name, healthy=self._healthy)


class CheckHealthTests(unittest.TestCase):
    def test_reports_healthy_when_every_probe_passes(self):
        status = CheckHealth(probes=[FakeProbe("database"), FakeProbe("cache")]).execute()

        self.assertTrue(status.is_healthy)
        self.assertEqual(["database", "cache"], [c.name for c in status.components])

    def test_reports_unhealthy_when_a_probe_fails(self):
        status = CheckHealth(probes=[FakeProbe("database", healthy=False)]).execute()

        self.assertFalse(status.is_healthy)

    def test_a_raising_probe_becomes_an_unhealthy_component(self):
        probe = FakeProbe("database", raises=RuntimeError("connection refused"))

        status = CheckHealth(probes=[probe]).execute()

        self.assertFalse(status.is_healthy)
        self.assertEqual("connection refused", status.components[0].detail)

    def test_one_failure_does_not_stop_the_remaining_probes(self):
        probes = [FakeProbe("database", raises=RuntimeError("boom")), FakeProbe("cache")]

        status = CheckHealth(probes=probes).execute()

        self.assertEqual(2, len(status.components))
        self.assertTrue(status.components[1].healthy)

    def test_no_probes_is_healthy(self):
        self.assertTrue(CheckHealth(probes=[]).execute().is_healthy)
