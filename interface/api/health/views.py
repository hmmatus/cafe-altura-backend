from rest_framework import status as http
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config import container
from interface.api.health.serializers import HealthStatusSerializer


class HealthView(APIView):
    """Liveness/readiness probe. 200 while every dependency answers, 503 otherwise."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        health = container.check_health().execute()
        code = http.HTTP_200_OK if health.is_healthy else http.HTTP_503_SERVICE_UNAVAILABLE

        return Response(HealthStatusSerializer(health).data, status=code)
