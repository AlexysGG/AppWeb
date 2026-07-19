from django.db import models

from apps.pagares.models import Pagare


class SolicitudFirma(models.Model):
    """Rastrea el ciclo de vida de la firma electrónica de un pagaré
    ante el proveedor externo (Web Service de terceros)."""

    class Estatus(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADA = "COMPLETADA", "Completada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        ERROR = "ERROR", "Error"

    pagare = models.OneToOneField(Pagare, on_delete=models.CASCADE, related_name="solicitud_firma")
    external_signature_id = models.CharField(max_length=100)
    signing_url = models.URLField(blank=True)
    estatus = models.CharField(max_length=20, choices=Estatus.choices, default=Estatus.PENDIENTE)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Firma {self.external_signature_id} - {self.estatus}"
