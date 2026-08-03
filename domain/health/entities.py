from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentHealth:
    """Outcome of checking one dependency the server needs to serve traffic."""

    name: str
    healthy: bool
    detail: str | None = None


@dataclass(frozen=True)
class HealthStatus:
    components: tuple[ComponentHealth, ...] = ()

    @property
    def is_healthy(self) -> bool:
        return all(component.healthy for component in self.components)
