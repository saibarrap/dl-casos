"""Modelos de dominio del sistema de gestion de casos de RC Medica.

Nombres y campos en espanol y snake_case. Las reglas de integridad se declaran
en la base de datos (NOT NULL, UNIQUE, CHECK, FK) ademas de validarse en el
codigo, para que un dato invalido nunca pueda almacenarse.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q

from .normalizacion import normalizar_siniestro


class EstadoCaso(models.TextChoices):
    REGISTRADO = "REGISTRADO", "Registrado"
    ASIGNADO = "ASIGNADO", "Asignado"
    EN_ANALISIS = "EN_ANALISIS", "En analisis"
    ENVIADO_ASEGURADORA = "ENVIADO_ASEGURADORA", "Enviado a aseguradora"
    CERRADO = "CERRADO", "Cerrado"


class Aseguradora(models.Model):
    nombre = models.CharField("nombre", max_length=150, unique=True)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "aseguradora"
        verbose_name_plural = "aseguradoras"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre"], name="uniq_aseguradora_nombre"),
        ]

    def __str__(self) -> str:
        return self.nombre


class Caso(models.Model):
    numero_siniestro = models.CharField("numero de siniestro", max_length=100)
    # Calculado automaticamente en save() a partir de numero_siniestro.
    siniestro_normalizado = models.CharField(
        "siniestro normalizado", max_length=100, editable=False
    )
    aseguradora = models.ForeignKey(
        Aseguradora,
        on_delete=models.PROTECT,
        related_name="casos",
        verbose_name="aseguradora",
    )
    numero_poliza = models.CharField(
        "numero de poliza", max_length=100, blank=True, default=""
    )
    fecha_recepcion = models.DateField("fecha de recepcion")
    asegurado = models.CharField("asegurado", max_length=200, blank=True, default="")
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=EstadoCaso.choices,
        default=EstadoCaso.REGISTRADO,
    )
    abogado_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="casos_asignados",
        verbose_name="abogado asignado",
    )
    observaciones = models.TextField("observaciones", blank=True, default="")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="casos_creados",
        verbose_name="creado por",
        null=True,
        blank=True,
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="casos_actualizados",
        verbose_name="actualizado por",
    )
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        verbose_name = "caso"
        verbose_name_plural = "casos"
        ordering = ["-creado_en"]
        constraints = [
            # UNIQUE real en MySQL sobre el par (siniestro_normalizado, aseguradora).
            models.UniqueConstraint(
                fields=["siniestro_normalizado", "aseguradora"],
                name="uniq_siniestro_aseguradora",
            ),
            # CHECK que restringe el estado al conjunto permitido.
            models.CheckConstraint(
                name="ck_caso_estado",
                condition=Q(estado__in=[e.value for e in EstadoCaso]),
            ),
        ]
        indexes = [
            models.Index(fields=["siniestro_normalizado"], name="idx_caso_siniestro_norm"),
            models.Index(fields=["numero_poliza"], name="idx_caso_poliza"),
            models.Index(fields=["asegurado"], name="idx_caso_asegurado"),
            models.Index(fields=["estado"], name="idx_caso_estado"),
            models.Index(fields=["aseguradora"], name="idx_caso_aseguradora"),
            models.Index(fields=["abogado_asignado"], name="idx_caso_abogado"),
        ]

    def save(self, *args, **kwargs):
        # El siniestro normalizado es la fuente de verdad: se recalcula en cada
        # guardado, venga del admin, del shell, de seed_demo_data o de scripts.
        self.siniestro_normalizado = normalizar_siniestro(self.numero_siniestro)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.numero_siniestro} ({self.aseguradora_id})"


class Reingreso(models.Model):
    caso = models.ForeignKey(
        Caso,
        on_delete=models.PROTECT,
        related_name="reingresos",
        verbose_name="caso",
    )
    fecha_reingreso = models.DateField("fecha de reingreso")
    trae_documentos_nuevos = models.BooleanField(
        "trae documentos nuevos", default=False
    )
    observaciones = models.TextField("observaciones", blank=True, default="")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reingresos_registrados",
        verbose_name="registrado por",
        null=True,
        blank=True,
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        verbose_name = "reingreso"
        verbose_name_plural = "reingresos"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"Reingreso de {self.caso_id} ({self.fecha_reingreso})"
