from .utils import registrar_evento

MUTACIONES = {"POST", "PUT", "PATCH", "DELETE"}


class AuditLogMiddleware:
    """
    Registra automáticamente cualquier operación de escritura hecha por
    un usuario autenticado sobre la API. Complementa los registros
    explícitos hechos en las vistas (p. ej. generación de PDF, envío a
    firma) con una traza genérica de "quién tocó qué".
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.path.startswith("/api/")
            and request.method in MUTACIONES
            and getattr(request, "user", None)
            and request.user.is_authenticated
            and 200 <= response.status_code < 400
        ):
            registrar_evento(
                usuario=request.user.username,
                accion=f"{request.method}_{request.path}",
                request=request,
            )

        return response
