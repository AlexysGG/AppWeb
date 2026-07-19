from django.db import models


class RegistroAuditoria(models.Model):
    """
    Bitácora de auditoría. El caso de estudio exige almacenar los
    registros para futuras consultas y auditorías; este modelo deja
    trazabilidad de quién hizo qué, cuándo y desde dónde.
    """

    usuario = models.CharField(max_length=150)
    accion = models.CharField(max_length=100)
    detalle = models.CharField(max_length=255, blank=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    ruta = models.CharField(max_length=255, blank=True)
    metodo_http = models.CharField(max_length=10, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"

    def __str__(self):
        return f"[{self.creado_en:%Y-%m-%d %H:%M}] {self.usuario} - {self.accion}"
