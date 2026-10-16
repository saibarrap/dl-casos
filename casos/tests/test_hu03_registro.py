"""HU-03 — Registro de un caso."""
import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from casos.models import Caso, EstadoCaso
from .base import PASSWORD, crear_aseguradora, crear_roles, crear_usuario


class RegistroTests(TestCase):
    def setUp(self):
        crear_roles()
        self.aseguradora = crear_aseguradora("Alfa")
        self.coordina = crear_usuario("coordina", rol="Coordinacion")
        self.client.login(username="coordina", password=PASSWORD)
        self.add_url = reverse("dl_casos_admin:casos_caso_add")

    def _datos(self, **over):
        datos = {
            "numero_siniestro": "2026-000123",
            "aseguradora": self.aseguradora.pk,
            "numero_poliza": "POL-1",
            "fecha_recepcion": "2026-01-10",
            "asegurado": "Juan Perez",
            "estado": EstadoCaso.REGISTRADO,
            "observaciones": "",
            # formset de reingresos inline no aplica.
        }
        datos.update(over)
        return datos

    def test_ca_03_1_sin_obligatorios_no_guarda_e_indica_faltantes(self):
        """CA-03.1: sin campos obligatorios no se guarda e indica cuales faltan."""
        resp = self.client.post(
            self.add_url,
            self._datos(numero_siniestro="", aseguradora="", fecha_recepcion=""),
        )
        self.assertEqual(Caso.objects.count(), 0)
        form = resp.context["adminform"].form
        self.assertIn("numero_siniestro", form.errors)
        self.assertIn("aseguradora", form.errors)
        self.assertIn("fecha_recepcion", form.errors)

    def test_ca_03_2_datos_validos_estado_registrado_y_auditoria(self):
        """CA-03.2: con datos validos queda REGISTRADO con usuario y fecha-hora."""
        resp = self.client.post(self.add_url, self._datos(), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Caso.objects.count(), 1)
        caso = Caso.objects.get()
        self.assertEqual(caso.estado, EstadoCaso.REGISTRADO)
        self.assertEqual(caso.creado_por, self.coordina)
        self.assertIsNotNone(caso.creado_en)

    def test_ca_03_3_fecha_futura_o_invalida_se_rechaza(self):
        """CA-03.3: fecha futura o invalida se rechaza con mensaje claro."""
        manana = timezone.localdate() + datetime.timedelta(days=1)
        resp = self.client.post(
            self.add_url, self._datos(fecha_recepcion=manana.isoformat())
        )
        self.assertEqual(Caso.objects.count(), 0)
        form = resp.context["adminform"].form
        self.assertIn("fecha_recepcion", form.errors)
        # Fecha invalida.
        resp2 = self.client.post(
            self.add_url, self._datos(fecha_recepcion="2026-13-40")
        )
        self.assertEqual(Caso.objects.count(), 0)
        self.assertIn("fecha_recepcion", resp2.context["adminform"].form.errors)

    def test_ca_03_4_caso_aparece_en_listado_y_detalle(self):
        """CA-03.4: el caso aparece en el listado y se abre su detalle."""
        caso = Caso.objects.create(
            numero_siniestro="2026-000999",
            aseguradora=self.aseguradora,
            fecha_recepcion=datetime.date(2026, 1, 5),
            creado_por=self.coordina,
        )
        resp_lista = self.client.get(reverse("dl_casos_admin:casos_caso_changelist"))
        self.assertContains(resp_lista, "2026-000999")
        resp_detalle = self.client.get(
            reverse("dl_casos_admin:casos_caso_change", args=[caso.pk])
        )
        self.assertEqual(resp_detalle.status_code, 200)
