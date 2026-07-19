from django.urls import path

from . import web_views

urlpatterns = [
    path("", web_views.DashboardView.as_view(), name="dashboard"),

    path("pagares/", web_views.PagareListView.as_view(), name="pagare_lista"),
    path("pagares/nuevo/", web_views.PagareCreateView.as_view(), name="pagare_nuevo"),
    path("pagares/<int:pk>/", web_views.PagareDetailView.as_view(), name="pagare_detalle"),
    path("pagares/<int:pk>/editar/", web_views.PagareUpdateView.as_view(), name="pagare_editar"),
    path("pagares/<int:pk>/pdf/", web_views.descargar_pdf, name="pagare_pdf"),
    path("pagares/<int:pk>/firmar/", web_views.solicitar_firma, name="pagare_firmar"),

    path("clientes/", web_views.ClienteListView.as_view(), name="cliente_lista"),
    path("clientes/nuevo/", web_views.ClienteCreateView.as_view(), name="cliente_nuevo"),
]
