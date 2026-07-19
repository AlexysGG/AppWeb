import hashlib
import io

from django.core.files.base import ContentFile
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

VERDE_BORDE = HexColor("#8fb96a")
GRIS_CAPTION = HexColor("#8a8a8a")
NEGRO = HexColor("#1a1a1a")


def _fecha_larga(fecha):
    return f"{fecha.day} de {MESES[fecha.month]} de {fecha.year}"


def generar_pdf_pagare(pagare) -> ContentFile:
    """
    Genera el PDF del pagaré replicando el formato estándar "Pagaré sin
    aval" (recuadro superior con lugar/fecha de expedición, cuerpo con
    la promesa incondicional de pago y espacios subrayados, datos del
    suscriptor y recuadro de firma) exigido por el despacho, con los
    elementos esenciales de los artículos 170-174 de la LGTOC.
    Calcula además el hash SHA-256 del PDF para garantizar integridad.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    ancho_pag, alto_pag = letter

    # --- geometría de la tarjeta ------------------------------------
    x0, x1 = 50, ancho_pag - 50
    y_top = alto_pag - 90
    alto_fila1 = 65
    y_fila1_bottom = y_top - alto_fila1
    alto_cuerpo = 250
    y_bottom = y_fila1_bottom - alto_cuerpo

    c.setStrokeColor(VERDE_BORDE)
    c.setLineWidth(1.5)
    c.roundRect(x0, y_bottom, x1 - x0, y_top - y_bottom, 8, stroke=1, fill=0)

    c.setFont("Helvetica", 8)
    c.setFillColor(GRIS_CAPTION)
    c.drawString(x0, y_top + 10, f"Folio: {pagare.folio}")

    # --- fila 1: titulo "Pagare" + lugar y fecha de expedicion ------
    x_div1 = x0 + 165
    c.setStrokeColor(VERDE_BORDE)
    c.roundRect(x0 + 15, y_fila1_bottom + 8, x_div1 - x0 - 30, alto_fila1 - 16, 4, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(NEGRO)
    c.drawString(x0 + 28, y_fila1_bottom + 24, "Pagaré")

    c.roundRect(x_div1, y_fila1_bottom + 8, x1 - x_div1 - 15, alto_fila1 - 16, 4, stroke=1, fill=0)
    linea_exp = f"En {pagare.lugar_expedicion}, a {_fecha_larga(pagare.fecha_expedicion)}."
    c.setFont("Helvetica", 11)
    c.setFillColor(NEGRO)
    c.drawCentredString((x_div1 + x1 - 15) / 2, y_fila1_bottom + 34, linea_exp)
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(GRIS_CAPTION)
    c.drawCentredString((x_div1 + x1 - 15) / 2, y_fila1_bottom + 20, "Lugar y fecha de expedición")

    # --- cuerpo ---------------------------------------------------------
    margen_i = x0 + 20
    margen_d = x1 - 20
    y = y_fila1_bottom - 25

    def subrayado(x_ini, x_fin, y_linea):
        c.setStrokeColor(NEGRO)
        c.setLineWidth(0.7)
        c.line(x_ini, y_linea, x_fin, y_linea)

    def caption(texto, x_centro, y_linea):
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(GRIS_CAPTION)
        c.drawCentredString(x_centro, y_linea - 10, texto)

    def texto_sobre_linea(texto, x_ini, x_fin, y_linea, tam=10, centrado=True):
        c.setFont("Helvetica", tam)
        c.setFillColor(NEGRO)
        if centrado:
            c.drawCentredString((x_ini + x_fin) / 2, y_linea + 2, texto)
        else:
            c.drawString(x_ini + 3, y_linea + 2, texto)

    c.setFont("Helvetica", 10.5)
    c.setFillColor(NEGRO)
    etiqueta = "Debo y pagaré incondicionalmente por este pagaré a la orden de"
    c.drawString(margen_i, y, etiqueta)
    ancho_etq = c.stringWidth(etiqueta, "Helvetica", 10.5)
    x_ini_benef = margen_i + ancho_etq + 8
    subrayado(x_ini_benef, margen_d, y - 2)
    texto_sobre_linea(pagare.beneficiario, x_ini_benef, margen_d, y - 2)
    caption("Nombre de la persona a quien ha de pagarse", (x_ini_benef + margen_d) / 2, y - 2)

    y -= 34
    c.drawString(margen_i, y, "en")
    x_ini_lugar = margen_i + 18
    x_fin_lugar = margen_i + 230
    subrayado(x_ini_lugar, x_fin_lugar, y - 2)
    texto_sobre_linea(pagare.lugar_pago, x_ini_lugar, x_fin_lugar, y - 2)
    caption("Lugar de pago", (x_ini_lugar + x_fin_lugar) / 2, y - 2)

    c.drawString(x_fin_lugar + 10, y, "el día")
    x_ini_fecha = x_fin_lugar + 40
    subrayado(x_ini_fecha, margen_d, y - 2)
    texto_sobre_linea(_fecha_larga(pagare.fecha_pago), x_ini_fecha, margen_d, y - 2)
    caption("Fecha de pago", (x_ini_fecha + margen_d) / 2, y - 2)

    y -= 34
    etiqueta2 = "la cantidad de"
    c.drawString(margen_i, y, etiqueta2)
    ancho_etq2 = c.stringWidth(etiqueta2, "Helvetica", 10.5)
    x_ini_monto = margen_i + ancho_etq2 + 8
    subrayado(x_ini_monto, margen_d, y - 2)
    texto_sobre_linea(f"${pagare.cantidad:,.2f} M.N.", x_ini_monto, margen_d, y - 2)

    y -= 30
    subrayado(margen_i, margen_d, y - 2)
    texto_sobre_linea(pagare.cantidad_en_letra, margen_i, margen_d, y - 2, centrado=True)

    y -= 40
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(NEGRO)
    c.drawString(margen_i, y, "Datos del suscriptor")

    y -= 26
    c.setFont("Helvetica", 10.5)
    c.drawString(margen_i, y, "Nombre")
    x_ini_nombre = margen_i + 45
    x_fin_nombre = margen_i + 260
    subrayado(x_ini_nombre, x_fin_nombre, y - 2)
    texto_sobre_linea(pagare.suscriptor.nombre, x_ini_nombre, x_fin_nombre, y - 2, centrado=False)

    y -= 26
    c.drawString(margen_i, y, "Dirección")
    x_ini_dir = margen_i + 55
    x_fin_dir = margen_i + 260
    subrayado(x_ini_dir, x_fin_dir, y - 2)
    texto_sobre_linea(pagare.suscriptor.direccion, x_ini_dir, x_fin_dir, y - 2, centrado=False)

    firma_ancho, firma_alto = 190, 60
    firma_x0 = margen_d - firma_ancho
    firma_y0 = y_bottom + 25
    c.setStrokeColor(VERDE_BORDE)
    c.roundRect(firma_x0, firma_y0, firma_ancho, firma_alto, 4, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(NEGRO)
    c.drawCentredString(firma_x0 + firma_ancho / 2, firma_y0 + firma_alto / 2 - 4, "Firma del suscriptor")

    c.setFont("Helvetica", 8)
    c.setFillColor(GRIS_CAPTION)
    c.drawString(
        x0, y_bottom - 20,
        "Este pagaré se rige por los artículos 170 a 174 de la Ley General de "
        "Títulos y Operaciones de Crédito. Pagaré sin aval.",
    )
    c.drawString(
        x0, y_bottom - 34,
        f"Documento generado por: "
        f"{pagare.abogado.get_full_name() or pagare.abogado.username} "
        f"({pagare.abogado.despacho or 'Despacho jurídico'})",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    contenido = buffer.getvalue()

    nombre_archivo = f"pagare_{pagare.folio}.pdf"
    pagare.pdf_file.save(nombre_archivo, ContentFile(contenido), save=False)
    pagare.hash_documento = hashlib.sha256(contenido).hexdigest()
    pagare.estatus = pagare.Estatus.GENERADO
    pagare.save()

    return pagare.pdf_file
