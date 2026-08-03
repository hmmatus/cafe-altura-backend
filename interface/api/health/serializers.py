from django.conf import settings
from rest_framework import serializers


class ComponentHealthSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    healthy = serializers.BooleanField(read_only=True)
    detail = serializers.SerializerMethodField()

    def get_detail(self, component) -> str | None:
        # Probe failures quote driver errors containing host, port and credentials context.
        # The endpoint is unauthenticated, so the reason stays server-side outside debug.
        return component.detail if settings.DEBUG else None


class HealthStatusSerializer(serializers.Serializer):
    status = serializers.SerializerMethodField()
    components = ComponentHealthSerializer(many=True, read_only=True)

    def get_status(self, status) -> str:
        return "ok" if status.is_healthy else "unhealthy"
