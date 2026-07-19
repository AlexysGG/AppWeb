from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "despacho", "activo_verificado", "is_active")
    list_filter = ("rol", "activo_verificado", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Datos profesionales", {
            "fields": ("rol", "cedula_profesional", "despacho", "activo_verificado")
        }),
    )
