from django.http import FileResponse, Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.permissions import EsAbogadoAutorizado
from apps.audit.utils import registrar_evento
from apps.firmas.client import ClienteFirmaElectronica
from apps.firmas.models import SolicitudFirma

from .models import Cliente, Pagare
from .serializers import ClienteSerializer, PagareSerializer
from .services.pdf_service import generar_pdf_pagare


class BaseSeguraViewSet(viewsets.ModelViewSet):
    permission_classes = [EsAbogadoAutorizado]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "pagares_write"


class ClienteViewSet(BaseSeguraViewSet):
    serializer_class = ClienteSerializer

    def get_queryset(self):
        qs = Cliente.objects.all()
        if self.request.user.es_admin():
            return qs
        return qs.filter(abogado=self.request.user)

    def perform_create(self, serializer):
        serializer.save(abogado=self.request.user)


class PagareViewSet(BaseSeguraViewSet):
    serializer_class = PagareSerializer

    def get_queryset(self):
        qs = Pagare.objects.select_related("suscriptor", "abogado")
        if self.request.user.es_admin():
            return qs
        return qs.filter(abogado=self.request.user)

    def perform_create(self, serializer):
        pagare = serializer.save(abogado=self.request.user)
        registrar_evento(
            usuario=self.request.user.username,
            accion="PAGARE_CREADO",
            request=self.request,
            detalle=f"folio={pagare.folio}",
        )

    @action(detail=True, methods=["get"], url_path="pdf")
    def descargar_pdf(self, request, pk=None):
        """
        Web Service propio: genera (si hace falta) y entrega el PDF del
        pagaré. Verifica permisos objeto por objeto antes de servir el
        archivo.
        """
        pagare = self.get_object()
        if not pagare.pdf_file:
            generar_pdf_pagare(pagare)
            registrar_evento(
                usuario=request.user.username,
                accion="PAGARE_PDF_GENERADO",
                request=request,
                detalle=f"folio={pagare.folio}",
            )
        try:
            return FileResponse(
                pagare.pdf_file.open("rb"),
                as_attachment=True,
                filename=f"pagare_{pagare.folio}.pdf",
                content_type="application/pdf",
            )
        except FileNotFoundError:
            raise Http404("El PDF no pudo ser localizado.")

    @action(detail=True, methods=["post"], url_path="solicitar-firma")
    def solicitar_firma(self, request, pk=None):
        """
        Web Service propio que orquesta la llamada al Web Service de
        terceros (firma electrónica). Deja registro en SolicitudFirma
        y en la bitácora de auditoría.
        """
        pagare = self.get_object()

        if not pagare.pdf_file:
            generar_pdf_pagare(pagare)

        cliente_firma = ClienteFirmaElectronica()
        try:
            resultado = cliente_firma.crear_solicitud(pagare)
        except Exception as exc:  # noqa: BLE001 - se traduce a respuesta controlada
            return Response(
                {"detail": f"No fue posible contactar al servicio de firma: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        solicitud, _ = SolicitudFirma.objects.update_or_create(
            pagare=pagare,
            defaults={
                "external_signature_id": resultado["id_externo"],
                "signing_url": resultado["url_firma"],
                "estatus": SolicitudFirma.Estatus.PENDIENTE,
            },
        )
        pagare.estatus = Pagare.Estatus.ENVIADO_FIRMA
        pagare.save(update_fields=["estatus"])

        registrar_evento(
            usuario=request.user.username,
            accion="PAGARE_ENVIADO_A_FIRMA",
            request=request,
            detalle=f"folio={pagare.folio} id_externo={solicitud.external_signature_id}",
        )

        return Response(
            {
                "detail": "Solicitud de firma electrónica enviada.",
                "signing_url": solicitud.signing_url,
                "estatus": solicitud.estatus,
            },
            status=status.HTTP_202_ACCEPTED,
        )
