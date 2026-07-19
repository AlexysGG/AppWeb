"""
Cliente para el Web Service de terceros de firma electrónica.

En un entorno real, ESIGN_API_KEY/ESIGN_API_BASE_URL apuntarían al
proveedor contratado por el despacho (ej. un servicio tipo DocuSign /
Mifiel / Weblex, todos con APIs REST equivalentes a la implementada
aquí). Mientras no se cuente con credenciales productivas, el cliente
opera en modo "sandbox local" para que el flujo completo de la
aplicación sea demostrable sin depender de un tercero externo.
"""
import uuid

import requests
from django.conf import settings

SANDBOX_KEYS = {"", "sandbox-api-key"}


class ClienteFirmaElectronica:
    def __init__(self):
        self.base_url = settings.ESIGN_API_BASE_URL
        self.api_key = settings.ESIGN_API_KEY
        self.modo_sandbox = self.api_key in SANDBOX_KEYS

    def crear_solicitud(self, pagare):
        """
        Envía el PDF del pagaré al proveedor de firma electrónica y
        devuelve {"id_externo": ..., "url_firma": ...}.
        """
        if self.modo_sandbox:
            return self._simular_creacion(pagare)

        headers = {"Authorization": f"Bearer {self.api_key}"}
        with pagare.pdf_file.open("rb") as archivo:
            respuesta = requests.post(
                f"{self.base_url}/envelopes",
                headers=headers,
                files={"document": (f"pagare_{pagare.folio}.pdf", archivo, "application/pdf")},
                data={
                    "signer_name": pagare.suscriptor.nombre,
                    "signer_email": pagare.suscriptor.email,
                    "reference": str(pagare.folio),
                },
                timeout=15,
            )
        respuesta.raise_for_status()
        data = respuesta.json()
        return {"id_externo": data["envelope_id"], "url_firma": data["signing_url"]}

    def _simular_creacion(self, pagare):
        id_externo = f"sandbox-{uuid.uuid4().hex[:12]}"
        return {
            "id_externo": id_externo,
            "url_firma": f"{self.base_url}/sign/{id_externo}",
        }

    def verificar_firma_webhook(self, payload, firma_recibida):
        """
        Verifica la firma HMAC del webhook entrante para confirmar que
        la notificación proviene realmente del proveedor de firma
        electrónica (mecanismo de seguridad: autenticidad de webhooks).
        """
        import hashlib
        import hmac

        esperado = hmac.new(
            settings.ESIGN_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(esperado, firma_recibida or "")
