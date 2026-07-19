from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = (
            "id", "username", "first_name", "last_name", "email",
            "rol", "cedula_profesional", "despacho", "activo_verificado",
        )
        read_only_fields = ("id", "activo_verificado")


class RegistroAbogadoSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = Usuario
        fields = (
            "id", "username", "first_name", "last_name", "email",
            "password", "cedula_profesional", "despacho",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = Usuario(rol=Usuario.Rol.ABOGADO, activo_verificado=False, **validated_data)
        usuario.set_password(password)  # hash seguro (PBKDF2)
        usuario.save()
        return usuario


class PagareTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende el token JWT estándar para incluir el rol del usuario en el
    payload, útil para que el frontend adapte la interfaz sin llamadas
    adicionales.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["rol"] = user.rol
        token["nombre"] = user.get_full_name() or user.username
        token["verificado"] = user.activo_verificado
        return token
