"""Migracion inicial del dominio de casos.

Escrita a mano (equivalente a makemigrations) porque el entorno de desarrollo
no tenia Django/MySQL instalado al generarla. Declara en la base de datos:
- UNIQUE(nombre) en aseguradora
- UNIQUE(siniestro_normalizado, aseguradora) en caso  (restriccion UNIQUE real)
- CHECK del estado del caso
- indices para busqueda y filtros

Verifiquela regenerando con `python manage.py makemigrations casos` en su
entorno local si lo prefiere; el esquema resultante debe coincidir.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Aseguradora",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=150, unique=True, verbose_name="nombre")),
                ("activa", models.BooleanField(default=True, verbose_name="activa")),
            ],
            options={
                "verbose_name": "aseguradora",
                "verbose_name_plural": "aseguradoras",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Caso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero_siniestro", models.CharField(max_length=100, verbose_name="numero de siniestro")),
                ("siniestro_normalizado", models.CharField(editable=False, max_length=100, verbose_name="siniestro normalizado")),
                ("numero_poliza", models.CharField(blank=True, default="", max_length=100, verbose_name="numero de poliza")),
                ("fecha_recepcion", models.DateField(verbose_name="fecha de recepcion")),
                ("asegurado", models.CharField(blank=True, default="", max_length=200, verbose_name="asegurado")),
                ("estado", models.CharField(choices=[("REGISTRADO", "Registrado"), ("ASIGNADO", "Asignado"), ("EN_ANALISIS", "En analisis"), ("ENVIADO_ASEGURADORA", "Enviado a aseguradora"), ("CERRADO", "Cerrado")], default="REGISTRADO", max_length=20, verbose_name="estado")),
                ("observaciones", models.TextField(blank=True, default="", verbose_name="observaciones")),
                ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="actualizado en")),
                ("abogado_asignado", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="casos_asignados", to=settings.AUTH_USER_MODEL, verbose_name="abogado asignado")),
                ("actualizado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="casos_actualizados", to=settings.AUTH_USER_MODEL, verbose_name="actualizado por")),
                ("aseguradora", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="casos", to="casos.aseguradora", verbose_name="aseguradora")),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="casos_creados", to=settings.AUTH_USER_MODEL, verbose_name="creado por")),
            ],
            options={
                "verbose_name": "caso",
                "verbose_name_plural": "casos",
                "ordering": ["-creado_en"],
            },
        ),
        migrations.CreateModel(
            name="Reingreso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_reingreso", models.DateField(verbose_name="fecha de reingreso")),
                ("trae_documentos_nuevos", models.BooleanField(default=False, verbose_name="trae documentos nuevos")),
                ("observaciones", models.TextField(blank=True, default="", verbose_name="observaciones")),
                ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="creado en")),
                ("caso", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reingresos", to="casos.caso", verbose_name="caso")),
                ("registrado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reingresos_registrados", to=settings.AUTH_USER_MODEL, verbose_name="registrado por")),
            ],
            options={
                "verbose_name": "reingreso",
                "verbose_name_plural": "reingresos",
                "ordering": ["-creado_en"],
            },
        ),
        migrations.AddConstraint(
            model_name="aseguradora",
            constraint=models.UniqueConstraint(fields=("nombre",), name="uniq_aseguradora_nombre"),
        ),
        migrations.AddConstraint(
            model_name="caso",
            constraint=models.UniqueConstraint(fields=("siniestro_normalizado", "aseguradora"), name="uniq_siniestro_aseguradora"),
        ),
        migrations.AddConstraint(
            model_name="caso",
            constraint=models.CheckConstraint(
                condition=models.Q(estado__in=["REGISTRADO", "ASIGNADO", "EN_ANALISIS", "ENVIADO_ASEGURADORA", "CERRADO"]),
                name="ck_caso_estado",
            ),
        ),
        migrations.AddIndex(
            model_name="caso",
            index=models.Index(fields=["siniestro_normalizado"], name="idx_caso_siniestro_norm"),
        ),
        migrations.AddIndex(
            model_name="caso",
            index=models.Index(fields=["numero_poliza"], name="idx_caso_poliza"),
        ),
        migrations.AddIndex(
            model_name="caso",
            index=models.Index(fields=["asegurado"], name="idx_caso_asegurado"),
        ),
        migrations.AddIndex(
            model_name="caso",
            index=models.Index(fields=["estado"], name="idx_caso_estado"),
        ),
        migrations.AddIndex(
            model_name="caso",
            index=models.Index(fields=["aseguradora"], name="idx_caso_aseguradora"),
        ),
        migrations.AddIndex(
            model_name="caso",
            index=models.Index(fields=["abogado_asignado"], name="idx_caso_abogado"),
        ),
    ]
