"""Genera N casos FICTICIOS para pruebas de rendimiento.

Usa aseguradoras Alfa, Beta y Gamma, y numeros de siniestro tipo 2026-000123
con variantes de formato (con/sin guion, con puntos, con espacios). Garantiza
unicidad del par (siniestro_normalizado, aseguradora).

SOLO datos ficticios: nunca usar datos reales (historias clinicas).
"""
import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from casos.models import Aseguradora, Caso, EstadoCaso
from casos.normalizacion import normalizar_siniestro

ASEGURADORAS = ["Alfa", "Beta", "Gamma"]

# Plantillas de formato para variar el aspecto del numero de siniestro.
_FORMATOS = [
    "{anio}-{sec:06d}",   # 2026-000123
    "{anio}{sec:06d}",    # 2026000123
    "{anio}.{sec:06d}",   # 2026.000123
    "{anio} {sec:06d}",   # 2026 000123
]


class Command(BaseCommand):
    help = "Genera N casos ficticios (Alfa/Beta/Gamma) para pruebas de rendimiento."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cantidad",
            type=int,
            required=True,
            help="Numero de casos ficticios a generar.",
        )
        parser.add_argument(
            "--lote",
            type=int,
            default=1000,
            help="Tamano del lote para bulk_create (por defecto 1000).",
        )

    def handle(self, *args, **options):
        cantidad = options["cantidad"]
        lote = max(1, options["lote"])
        if cantidad <= 0:
            raise CommandError("--cantidad debe ser un entero positivo.")

        User = get_user_model()
        creador = (
            User.objects.filter(username="coordinacion").first()
            or User.objects.filter(is_superuser=True).first()
        )
        if creador is None:
            raise CommandError(
                "No hay un usuario para asignar como 'creado_por'. "
                "Ejecute primero: python manage.py seed_roles"
            )

        aseguradoras = [
            Aseguradora.objects.get_or_create(nombre=n, defaults={"activa": True})[0]
            for n in ASEGURADORAS
        ]

        anio = 2026
        estados = [e.value for e in EstadoCaso]
        buffer = []
        creados = 0
        vistos = set()  # pares (normalizado, aseguradora_id) ya generados en esta corrida
        sec = 1

        # Pre-cargar pares ya existentes en BD para no colisionar con la UNIQUE.
        for norm, asid in Caso.objects.values_list("siniestro_normalizado", "aseguradora_id"):
            vistos.add((norm, asid))

        self.stdout.write(f"Generando {cantidad} casos ficticios...")

        while creados < cantidad:
            aseguradora = aseguradoras[sec % len(aseguradoras)]
            formato = _FORMATOS[sec % len(_FORMATOS)]
            numero = formato.format(anio=anio, sec=sec)
            normalizado = normalizar_siniestro(numero)
            clave = (normalizado, aseguradora.id)
            sec += 1
            if clave in vistos:
                continue
            vistos.add(clave)

            caso = Caso(
                numero_siniestro=numero,
                siniestro_normalizado=normalizado,
                aseguradora=aseguradora,
                numero_poliza=f"POL-{anio}-{creados:06d}",
                fecha_recepcion=datetime.date(anio, 1, 1)
                + datetime.timedelta(days=creados % 300),
                asegurado=f"Asegurado Ficticio {creados:06d}",
                estado=estados[creados % len(estados)],
                creado_por=creador,
            )
            buffer.append(caso)
            creados += 1

            if len(buffer) >= lote:
                Caso.objects.bulk_create(buffer)
                buffer.clear()
                self.stdout.write(f"  {creados}/{cantidad}...")

        if buffer:
            Caso.objects.bulk_create(buffer)

        self.stdout.write(
            self.style.SUCCESS(f"Listo: {creados} casos ficticios creados.")
        )
