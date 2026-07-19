from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.audit.utils import registrar_evento
from apps.firmas.client import ClienteFirmaElectronica
from apps.firmas.models import SolicitudFirma

from .forms import ClienteForm, PagareForm
from .models import Cliente, Pagare
from .services.pdf_service import generar_pdf_pagare


class AlcanceUsuarioMixin(LoginRequiredMixin):
    """Limita el queryset a los registros del abogado en sesión, salvo
    que sea administrador (misma regla que la API REST)."""

    campo_propietario = "abogado"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.es_admin():
            return qs
        return qs.filter(**{self.campo_propietario: self.request.user})


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pagares/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        pagares = Pagare.objects.all() if user.es_admin() else Pagare.objects.filter(abogado=user)
        clientes = Cliente.objects.all() if user.es_admin() else Cliente.objects.filter(abogado=user)

        ctx["total_pagares"] = pagares.count()
        ctx["total_clientes"] = clientes.count()
        ctx["total_borrador"] = pagares.filter(estatus=Pagare.Estatus.BORRADOR).count()
        ctx["total_generado"] = pagares.filter(estatus=Pagare.Estatus.GENERADO).count()
        ctx["total_enviado_firma"] = pagares.filter(estatus=Pagare.Estatus.ENVIADO_FIRMA).count()
        ctx["total_firmado"] = pagares.filter(estatus=Pagare.Estatus.FIRMADO).count()
        ctx["monto_total"] = sum((p.cantidad for p in pagares), 0)
        ctx["recientes"] = pagares.select_related("suscriptor").order_by("-creado_en")[:5]
        return ctx


# ---------------------------------------------------------------------------
# Clientes (suscriptores)
# ---------------------------------------------------------------------------
class ClienteListView(AlcanceUsuarioMixin, ListView):
    model = Cliente
    template_name = "pagares/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 15


class ClienteCreateView(AlcanceUsuarioMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "pagares/cliente_form.html"
    success_url = reverse_lazy("cliente_lista")

    def form_valid(self, form):
        form.instance.abogado = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Cliente registrado correctamente.")
        registrar_evento(self.request.user.username, "CLIENTE_CREADO", self.request)
        return response


# ---------------------------------------------------------------------------
# Pagarés
# ---------------------------------------------------------------------------
class PagareListView(AlcanceUsuarioMixin, ListView):
    model = Pagare
    template_name = "pagares/pagare_list.html"
    context_object_name = "pagares"
    paginate_by = 15

    def get_queryset(self):
        return super().get_queryset().select_related("suscriptor").order_by("-creado_en")


class PagareDetailView(AlcanceUsuarioMixin, DetailView):
    model = Pagare
    template_name = "pagares/pagare_detail.html"
    context_object_name = "pagare"


class PagareCreateView(AlcanceUsuarioMixin, CreateView):
    model = Pagare
    form_class = PagareForm
    template_name = "pagares/pagare_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.abogado = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Pagaré creado. Ahora puedes generar el PDF.")
        registrar_evento(
            self.request.user.username, "PAGARE_CREADO", self.request,
            detalle=f"folio={self.object.folio}",
        )
        return response

    def get_success_url(self):
        return reverse_lazy("pagare_detalle", kwargs={"pk": self.object.pk})


class PagareUpdateView(AlcanceUsuarioMixin, UpdateView):
    model = Pagare
    form_class = PagareForm
    template_name = "pagares/pagare_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Pagaré actualizado.")
        return reverse_lazy("pagare_detalle", kwargs={"pk": self.object.pk})


def descargar_pdf(request, pk):
    pagare = get_object_or_404(Pagare, pk=pk)
    if not request.user.es_admin() and pagare.abogado_id != request.user.id:
        raise Http404
    if not pagare.pdf_file:
        generar_pdf_pagare(pagare)
        registrar_evento(request.user.username, "PAGARE_PDF_GENERADO", request, f"folio={pagare.folio}")
    return FileResponse(
        pagare.pdf_file.open("rb"), as_attachment=False,
        filename=f"pagare_{pagare.folio}.pdf", content_type="application/pdf",
    )


def solicitar_firma(request, pk):
    pagare = get_object_or_404(Pagare, pk=pk)
    if not request.user.es_admin() and pagare.abogado_id != request.user.id:
        raise Http404
    if request.method != "POST":
        return redirect("pagare_detalle", pk=pk)

    if not pagare.pdf_file:
        generar_pdf_pagare(pagare)

    cliente = ClienteFirmaElectronica()
    try:
        resultado = cliente.crear_solicitud(pagare)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f"No fue posible contactar al servicio de firma: {exc}")
        return redirect("pagare_detalle", pk=pk)

    SolicitudFirma.objects.update_or_create(
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
        request.user.username, "PAGARE_ENVIADO_A_FIRMA", request,
        detalle=f"folio={pagare.folio}",
    )
    messages.success(request, "El pagaré fue enviado al servicio de firma electrónica.")
    return redirect("pagare_detalle", pk=pk)
