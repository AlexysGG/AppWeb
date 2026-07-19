from django import forms

from .models import Cliente, Pagare


def _bootstrap(campo, **extra):
    attrs = {"class": "form-control"}
    attrs.update(extra)
    campo.widget.attrs.update(attrs)
    return campo


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "direccion", "rfc", "email", "telefono"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-control"


class PagareForm(forms.ModelForm):
    fecha_expedicion = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    fecha_pago = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    class Meta:
        model = Pagare
        fields = [
            "suscriptor", "beneficiario", "lugar_expedicion", "fecha_expedicion",
            "lugar_pago", "fecha_pago", "cantidad", "cantidad_en_letra",
        ]

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre not in ("fecha_expedicion", "fecha_pago"):
                campo.widget.attrs["class"] = "form-control"
        if usuario is not None and not usuario.es_admin():
            self.fields["suscriptor"].queryset = Cliente.objects.filter(abogado=usuario)
        self.fields["suscriptor"].widget.attrs["class"] = "form-select"
