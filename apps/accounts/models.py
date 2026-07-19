from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuario del sistema. Extiende el modelo base de Django para
    incorporar control de acceso basado en roles (RBAC).
    """

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        ABOGADO = "ABOGADO", "Abogado autorizado"

    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.ABOGADO)
    cedula_profesional = models.CharField(max_length=20, blank=True)
    despacho = models.CharField(max_length=150, blank=True)
    activo_verificado = models.BooleanField(
        default=False,
        help_text="Indica si el despacho validó la cédula profesional del abogado.",
    )

    def es_admin(self):
        # Un superusuario de Django (createsuperuser) siempre cuenta
        # como administrador del sistema, aunque el campo 'rol' no se
        # haya asignado explícitamente.
        return self.rol == self.Rol.ADMIN or self.is_superuser

    def es_abogado(self):
        return self.rol == self.Rol.ABOGADO

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"
