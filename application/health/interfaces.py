from abc import ABC, abstractmethod

from domain.health.entities import ComponentHealth


class HealthProbe(ABC):
    """A dependency that can report whether it is usable right now."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def check(self) -> ComponentHealth:
        """Return the component's health. May raise; the use case treats that as unhealthy."""
