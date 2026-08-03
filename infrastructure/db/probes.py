from django.db import connections

from application.health.interfaces import HealthProbe
from domain.health.entities import ComponentHealth


class DatabaseProbe(HealthProbe):
    """Confirms the configured database answers a trivial query."""

    def __init__(self, alias: str = "default"):
        self._alias = alias

    @property
    def name(self) -> str:
        return "database"

    def check(self) -> ComponentHealth:
        with connections[self._alias].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return ComponentHealth(name=self.name, healthy=True)
