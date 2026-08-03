"""View tests: status codes and payload shape only."""

from unittest import mock

from django.test import TestCase
from django.urls import reverse

from application.health.services import CheckHealth
from domain.health.entities import ComponentHealth


class HealthViewTests(TestCase):
    def test_returns_200_and_ok_when_healthy(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(200, response.status_code)
        self.assertEqual("ok", response.json()["status"])
        self.assertEqual(
            [{"name": "database", "healthy": True, "detail": None}],
            response.json()["components"],
        )

    def test_returns_503_when_a_component_is_unhealthy(self):
        unhealthy = CheckHealth(probes=[])
        unhealthy.execute = lambda: _status(healthy=False)

        with mock.patch("config.container.check_health", return_value=unhealthy):
            response = self.client.get(reverse("health"))

        self.assertEqual(503, response.status_code)
        self.assertEqual("unhealthy", response.json()["status"])

    def test_failure_detail_is_not_exposed_when_debug_is_off(self):
        unhealthy = CheckHealth(probes=[])
        unhealthy.execute = lambda: _status(healthy=False)

        with (
            self.settings(DEBUG=False),
            mock.patch("config.container.check_health", return_value=unhealthy),
        ):
            response = self.client.get(reverse("health"))

        self.assertIsNone(response.json()["components"][0]["detail"])

    def test_failure_detail_is_exposed_when_debug_is_on(self):
        unhealthy = CheckHealth(probes=[])
        unhealthy.execute = lambda: _status(healthy=False)

        with (
            self.settings(DEBUG=True),
            mock.patch("config.container.check_health", return_value=unhealthy),
        ):
            response = self.client.get(reverse("health"))

        self.assertEqual("down", response.json()["components"][0]["detail"])


def _status(*, healthy: bool):
    from domain.health.entities import HealthStatus

    return HealthStatus(
        components=(ComponentHealth(name="database", healthy=healthy, detail="down"),)
    )
