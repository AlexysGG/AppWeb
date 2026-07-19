import hashlib
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Cliente(models.Model):
    """Suscriptor (deudor) del pagaré."""

    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255)
    rfc = models.CharField(max_length=13, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    abogado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="clientes"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Pagare(models.Model):
    """
    Pagaré generado conforme a los artículos 170-174 de la Ley General
    de Títulos y Operaciones de Crédito (LGTOC). Contiene los elementos
    esenciales exigidos por la ley: mención de ser pagaré, promesa
    incondicional de pago, nombre del beneficiario, fecha y lugar de
    vencimiento, fecha y lugar de suscripción, y firma del suscriptor.
    """

    class Estatus(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        GENERADO = "GENERADO", "PDF generado"
        ENVIADO_FIRMA = "ENVIADO_FIRMA", "Enviado a firma electrónica"
        FIRMADO = "FIRMADO", "Firmado"
        CANCELADO = "CANCELADO", "Cancelado"

    folio = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    abogado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pagares"
    )
    suscriptor = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="pagares"
    )

    beneficiario = models.CharField(
        "Nombre de la persona a quien ha de pagarse", max_length=200
    )

    lugar_expedicion = models.CharField(max_length=150)
    fecha_expedicion = models.DateField()

    lugar_pago = models.CharField(max_length=150)
    fecha_pago = models.DateField()

    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_en_letra = models.CharField(max_length=255)

    estatus = models.CharField(
        max_length=20, choices=Estatus.choices, default=Estatus.BORRADOR
    )

    pdf_file = models.FileField(upload_to="pagares_pdf/", blank=True, null=True)
    hash_documento = models.CharField(
        max_length=64, blank=True,
        help_text="SHA-256 del PDF generado, para verificar integridad.",
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Pagaré {self.folio} - {self.suscriptor.nombre}"

    def clean(self):
        # Validación de elementos esenciales del pagaré (LGTOC art. 170)
        errores = {}
        if self.fecha_pago and self.fecha_expedicion and self.fecha_pago < self.fecha_expedicion:
            errores["fecha_pago"] = "La fecha de pago no puede ser anterior a la de expedición."
        if self.cantidad is not None and self.cantidad <= 0:
            errores["cantidad"] = "La cantidad debe ser mayor a cero."
        if errores:
            raise ValidationError(errores)

    def calcular_hash(self):
        if not self.pdf_file:
            return ""
        self.pdf_file.seek(0)
        contenido = self.pdf_file.read()
        self.pdf_file.seek(0)
        return hashlib.sha256(contenido).hexdigest()
