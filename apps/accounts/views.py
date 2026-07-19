from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.audit.utils import registrar_evento
from .models import Usuario
from .serializers import (
    PagareTokenObtainPairSerializer,
    RegistroAbogadoSerializer,
    UsuarioSerializer,
)


class LoginView(TokenObtainPairView):
    """
    Emite el par de tokens JWT (access/refresh).
    Mecanismo de seguridad: throttling ('login': 5/min) para mitigar
    ataques de fuerza bruta sobre credenciales.
    """

    serializer_class = PagareTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            registrar_evento(
                usuario=request.data.get("username", "desconocido"),
                accion="LOGIN_EXITOSO",
                request=request,
            )
        else:
            registrar_evento(
                usuario=request.data.get("username", "desconocido"),
                accion="LOGIN_FALLIDO",
                request=request,
            )
        return response


class RefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class RegistroAbogadoView(generics.CreateAPIView):
    """
    Alta de un nuevo abogado. Queda con activo_verificado=False hasta
    que un administrador del despacho valide su cédula profesional.
    """

    queryset = Usuario.objects.all()
    serializer_class = RegistroAbogadoSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class PerfilView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)
