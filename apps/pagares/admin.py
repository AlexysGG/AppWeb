from django.contrib import admin
from django.utils.html import format_html

from .models import Cliente, Pagare
from .services.pdf_service import generar_pdf_pagare


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "abogado", "email", "telefono", "creado_en")
    search_fields = ("nombre", "rfc", "email")

    def save_model(self, request, obj, form, change):
        if not change and not obj.abogado_id:
            obj.abogado = request.user
        super().save_model(request, obj, form, change)


@admin.register(Pagare)
class PagareAdmin(admin.ModelAdmin):
    list_display = (
        "folio", "suscriptor", "beneficiario", "cantidad", "estatus",
        "abogado", "creado_en", "enlace_pdf",
    )
    list_filter = ("estatus",)
    search_fields = ("folio", "beneficiario", "suscriptor__nombre")
    readonly_fields = ("folio", "hash_documento", "creado_en", "actualizado_en", "enlace_pdf")
    actions = ["accion_generar_pdf"]

    def save_model(self, request, obj, form, change):
        if not change and not obj.abogado_id:
            obj.abogado = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="PDF")
    def enlace_pdf(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Descargar PDF</a>', obj.pdf_file.url)
        return "Aún no generado (usa la acción 'Generar PDF')"

    @admin.action(description="Generar PDF del pagaré seleccionado")
    def accion_generar_pdf(self, request, queryset):
        generados = 0
        for pagare in queryset:
            generar_pdf_pagare(pagare)
            generados += 1
        self.message_user(request, f"PDF generado para {generados} pagaré(s).")
