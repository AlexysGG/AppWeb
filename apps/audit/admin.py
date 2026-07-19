from django.contrib import admin
from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "usuario", "accion", "ip_origen", "ruta")
    list_filter = ("accion",)
    search_fields = ("usuario", "accion", "detalle", "ip_origen")
    readonly_fields = [f.name for f in RegistroAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
