"""HU-05 — Busqueda, filtros y paginacion del listado."""
import datetime
import time

from django.test import TestCase, tag
from django.urls import reverse

from casos.models import Caso, EstadoCaso
from casos.normalizacion import normalizar_siniestro
from .base import PASSWORD, crear_aseguradora, crear_roles, crear_usuario


class BusquedaTests(TestCase):
    def setUp(self):
        crear_roles()
        self.alfa = crear_aseguradora("Alfa")
        self.beta = crear_aseguradora("Beta")
        self.coordina = crear_usuario("coordina", rol="Coordinacion")
        self.abogado = crear_usuario("abogado1", rol="Abogado")
        self.client.login(username="coordina", password=PASSWORD)
        self.changelist = reverse("dl_casos_admin:casos_caso_changelist")

    def _caso(self, numero, aseguradora, poliza="", asegurado="", estado=EstadoCaso.REGISTRADO, abogado=None):
        return Caso.objects.create(
            numero_siniestro=numero,
            aseguradora=aseguradora,
            numero_poliza=poliza,
            asegurado=asegurado,
            estado=estado,
            abogado_asignado=abogado,
            fecha_recepcion=datetime.date(2026, 1, 1),
            creado_por=self.coordina,
        )

    def test_ca_05_1_busqueda_por_siniestro_o_poliza(self):
        """CA-05.1: buscar por siniestro o poliza muestra solo coincidencias."""
        self._caso("2026-000001", self.alfa, poliza="POL-AAA")
        self._caso("2026-000002", self.alfa, poliza="POL-BBB")
        resp = self.client.get(self.changelist, {"q": "000001"})
        self.assertContains(resp, "2026-000001")
        self.assertNotContains(resp, "2026-000002")
        resp2 = self.client.get(self.changelist, {"q": "POL-BBB"})
        self.assertContains(resp2, "2026-000002")
        self.assertNotContains(resp2, "2026-000001")

    def test_ca_05_2_filtros_combinados_cumplen_todos(self):
        """CA-05.2: los filtros combinados cumplen todos simultaneamente."""
        objetivo = self._caso(
            "2026-000010", self.alfa, estado=EstadoCaso.CERRADO, abogado=self.abogado
        )
        # Ruido que falla uno u otro filtro.
        self._caso("2026-000011", self.beta, estado=EstadoCaso.CERRADO, abogado=self.abogado)
        self._caso("2026-000012", self.alfa, estado=EstadoCaso.REGISTRADO, abogado=self.abogado)
        self._caso("2026-000013", self.alfa, estado=EstadoCaso.CERRADO, abogado=None)

        resp = self.client.get(
            self.changelist,
            {
                "aseguradora__id__exact": self.alfa.pk,
                "estado__exact": EstadoCaso.CERRADO,
                "abogado_asignado__id__exact": self.abogado.pk,
            },
        )
        cl = resp.context["cl"]
        pks = list(cl.queryset.values_list("pk", flat=True))
        self.assertEqual(pks, [objetivo.pk])

    def test_ca_05_3_paginacion_y_total(self):
        """CA-05.3: con mas de una pagina hay paginacion y total."""
        total = 60  # list_per_page = 50
        for i in range(total):
            self._caso(f"2026-1{i:05d}", self.alfa)
        resp = self.client.get(self.changelist)
        cl = resp.context["cl"]
        self.assertEqual(cl.result_count, total)
        self.assertTrue(cl.result_count > cl.list_per_page)
        # La pagina 2 trae el resto.
        resp2 = self.client.get(self.changelist, {"p": 2})
        self.assertEqual(len(resp2.context["cl"].result_list), total - cl.list_per_page)

    @tag("mysql", "performance")
    def test_ca_05_4_busqueda_responde_con_mas_de_3700_casos(self):
        """CA-05.4: con mas de 3.700 casos la busqueda responde en pocos segundos.

        Depende de los indices de BD y debe ejecutarse sobre MySQL para ser
        representativa (en SQLite el resultado de rendimiento no aplica).
        """
        total = 3800
        lote = [
            Caso(
                numero_siniestro=f"2026-9{i:05d}",
                siniestro_normalizado=normalizar_siniestro(f"2026-9{i:05d}"),
                aseguradora=self.alfa if i % 2 == 0 else self.beta,
                numero_poliza=f"POL-{i:06d}",
                asegurado=f"Asegurado {i:06d}",
                estado=EstadoCaso.REGISTRADO,
                fecha_recepcion=datetime.date(2026, 1, 1),
                creado_por=self.coordina,
            )
            for i in range(total)
        ]
        Caso.objects.bulk_create(lote, batch_size=1000)
        self.assertGreater(Caso.objects.count(), 3700)

        inicio = time.perf_counter()
        resp = self.client.get(
            self.changelist,
            {"q": "900500", "aseguradora__id__exact": self.alfa.pk},
        )
        transcurrido = time.perf_counter() - inicio
        self.assertEqual(resp.status_code, 200)
        # Umbral holgado; en MySQL con indices debe responder en pocos segundos.
        self.assertLess(transcurrido, 3.0)
