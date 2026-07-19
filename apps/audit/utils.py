def _ip_del_request(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def registrar_evento(usuario, accion, request=None, detalle=""):
    """
    Registra un evento en la bitácora de auditoría. Se importa de forma
    perezosa (lazy) el modelo para evitar problemas de import circular
    durante el arranque de la app.
    """
    from .models import RegistroAuditoria

    RegistroAuditoria.objects.create(
        usuario=str(usuario),
        accion=accion,
        detalle=detalle,
        ip_origen=_ip_del_request(request),
        ruta=getattr(request, "path", ""),
        metodo_http=getattr(request, "method", ""),
    )
