from rest_framework.permissions import BasePermission


class EsAbogadoAutorizado(BasePermission):
    """
    Permite el acceso solo a abogados verificados por el despacho o a
    administradores. Mecanismo de seguridad: control de acceso basado
    en roles (RBAC) a nivel de vista.
    """

    message = "Solo abogados autorizados por el despacho pueden realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.es_admin():
            return True
        return user.es_abogado() and user.activo_verificado

    def has_object_permission(self, request, view, obj):
        # Un abogado solo puede operar sobre los pagarés que él generó,
        # salvo que sea administrador.
        if request.user.es_admin():
            return True
        return getattr(obj, "abogado_id", None) == request.user.id


class EsAdministrador(BasePermission):
    message = "Esta acción requiere privilegios de administrador."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_admin())
