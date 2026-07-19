from rest_framework import serializers

from .models import Cliente, Pagare


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ("id", "nombre", "direccion", "rfc", "email", "telefono", "creado_en")
        read_only_fields = ("id", "creado_en")


class PagareSerializer(serializers.ModelSerializer):
    suscriptor_nombre = serializers.CharField(source="suscriptor.nombre", read_only=True)
    abogado_nombre = serializers.CharField(source="abogado.username", read_only=True)

    class Meta:
        model = Pagare
        fields = (
            "id", "folio", "abogado", "abogado_nombre", "suscriptor", "suscriptor_nombre",
            "beneficiario", "lugar_expedicion", "fecha_expedicion",
            "lugar_pago", "fecha_pago", "cantidad", "cantidad_en_letra",
            "estatus", "pdf_file", "hash_documento", "creado_en", "actualizado_en",
        )
        read_only_fields = (
            "id", "folio", "abogado", "abogado_nombre", "suscriptor_nombre",
            "estatus", "pdf_file", "hash_documento", "creado_en", "actualizado_en",
        )

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a cero.")
        return value

    def validate(self, attrs):
        fecha_pago = attrs.get("fecha_pago", getattr(self.instance, "fecha_pago", None))
        fecha_exp = attrs.get("fecha_expedicion", getattr(self.instance, "fecha_expedicion", None))
        if fecha_pago and fecha_exp and fecha_pago < fecha_exp:
            raise serializers.ValidationError(
                "La fecha de pago no puede ser anterior a la fecha de expedición."
            )
        return attrs
