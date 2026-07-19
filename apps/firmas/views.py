from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.utils import registrar_evento
from apps.pagares.models import Pagare

from .client import ClienteFirmaElectronica
from .models import SolicitudFirma


@method_decorator(csrf_exempt, name="dispatch")
class WebhookFirmaView(APIView):
    """
    Endpoint público que consume el Web Service de terceros para
    notificar el resultado de la firma electrónica. Está exento de
    CSRF (no lo llama un navegador con sesión) pero exige verificación
    de firma HMAC en el header 'X-Signature' como mecanismo de
    autenticidad, evitando que cualquiera pueda marcar un pagaré como
    firmado.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "webhook"

    def post(self, request):
        firma_header = request.headers.get("X-Signature", "")
        cliente = ClienteFirmaElectronica()

        if not cliente.verificar_firma_webhook(request.body, firma_header):
            registrar_evento(
                usuario="webhook-firmas",
                accion="WEBHOOK_FIRMA_RECHAZADO",
                request=request,
                detalle="Firma HMAC inválida",
            )
            return Response({"detail": "Firma inválida."}, status=status.HTTP_401_UNAUTHORIZED)

        id_externo = request.data.get("id_externo")
        nuevo_estatus = request.data.get("estatus")  # COMPLETADA | RECHAZADA

        try:
            solicitud = SolicitudFirma.objects.select_related("pagare").get(
                external_signature_id=id_externo
            )
        except SolicitudFirma.DoesNotExist:
            return Response({"detail": "Solicitud no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if nuevo_estatus not in dict(SolicitudFirma.Estatus.choices):
            return Response({"detail": "Estatus no válido."}, status=status.HTTP_400_BAD_REQUEST)

        solicitud.estatus = nuevo_estatus
        solicitud.save(update_fields=["estatus", "actualizado_en"])

        if nuevo_estatus == SolicitudFirma.Estatus.COMPLETADA:
            solicitud.pagare.estatus = Pagare.Estatus.FIRMADO
            solicitud.pagare.save(update_fields=["estatus"])

        registrar_evento(
            usuario="webhook-firmas",
            accion="WEBHOOK_FIRMA_PROCESADO",
            request=request,
            detalle=f"id_externo={id_externo} estatus={nuevo_estatus}",
        )
        return Response({"detail": "Notificación procesada."}, status=status.HTTP_200_OK)
