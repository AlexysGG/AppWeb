from django.contrib import admin
from .models import SolicitudFirma


@admin.register(SolicitudFirma)
class SolicitudFirmaAdmin(admin.ModelAdmin):
    list_display = ("pagare", "external_signature_id", "estatus", "creado_en")
    list_filter = ("estatus",)
