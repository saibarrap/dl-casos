"""Formularios del admin para el registro de casos.

Concentra las validaciones de HU-03 (campos obligatorios, fecha no futura) y
HU-04 (deteccion de duplicados por siniestro normalizado + aseguradora, con
enlaces al caso existente y al alta de reingreso).
"""
from django import forms
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Caso
from .normalizacion import normalizar_siniestro


class CasoForm(forms.ModelForm):
    class Meta:
        model = Caso
        fields = [
            "numero_siniestro",
            "aseguradora",
            "numero_poliza",
            "fecha_recepcion",
            "asegurado",
            "estado",
            "abogado_asignado",
            "observaciones",
        ]

    def clean_fecha_recepcion(self):
        """La fecha de recepcion no puede ser futura (zona America/Bogota)."""
        fecha = self.cleaned_data.get("fecha_recepcion")
        if fecha is None:
            return fecha
        hoy = timezone.localdate()
        if fecha > hoy:
            raise forms.ValidationError(
                "La fecha de recepcion no puede ser futura."
            )
        return fecha

    def clean(self):
        cleaned = super().clean()
        numero = cleaned.get("numero_siniestro")
        aseguradora = cleaned.get("aseguradora")

        # Si faltan los campos clave, los errores de "campo obligatorio" ya se
        # habran agregado por campo; no se continua con la deteccion de duplicado.
        if not numero or aseguradora is None:
            return cleaned

        normalizado = normalizar_siniestro(numero)

        # Buscar un caso existente con el mismo par (normalizado, aseguradora),
        # excluyendo el propio registro cuando se trata de una edicion.
        existentes = Caso.objects.filter(
            siniestro_normalizado=normalizado, aseguradora=aseguradora
        )
        if self.instance and self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)

        existente = existentes.first()
        if existente is not None:
            url_caso = reverse("admin:casos_caso_change", args=[existente.pk])
            url_reingreso = (
                reverse("admin:casos_reingreso_add")
                + f"?caso={existente.pk}&trae_documentos_nuevos=on"
            )
            mensaje = format_html(
                "Ya existe un caso con ese siniestro para esta aseguradora. "
                "No se creo un duplicado. "
                'Ver el <a href="{}">caso existente</a> o '
                '<a href="{}">registrar un reingreso</a>.',
                url_caso,
                url_reingreso,
            )
            raise forms.ValidationError(mensaje)

        return cleaned
