from django.urls import path
from .views import LoginView, RefreshView, RegistroAbogadoView, PerfilView

urlpatterns = [
    path("token/", LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("registro/", RegistroAbogadoView.as_view(), name="registro_abogado"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
]
