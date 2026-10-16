"""HU-04 — Deteccion de duplicados y registro de reingresos."""
import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from casos.models import Caso, Reingreso
from casos.normalizacion import normalizar_siniestro
from .base import PASSWORD, crear_aseguradora, crear_roles, crear_usuario


class DuplicadosTests(TestCase):
    def setUp(self):
        crear_roles()
        self.alfa = crear_aseguradora("Alfa")
        self.beta = crear_aseguradora("Beta")
        self.coordina = crear_usuario("coordina", rol="Coordinacion")
        self.client.login(username="coordina", password=PASSWORD)
        self.add_url = reverse("dl_casos_admin:casos_caso_add")
        self.existente = Caso.objects.create(
            numero_siniestro="2026-000123",
            aseguradora=self.alfa,
            fecha_recepcion=datetime.date(2026, 1, 1),
            creado_por=self.coordina,
        )

    def _datos(self, numero, aseguradora):
        return {
            "numero_siniestro": numero,
            "aseguradora": aseguradora.pk,
            "numero_poliza": "",
            "fecha_recepcion": "2026-02-01",
            "asegurado": "",
            "estado": "REGISTRADO",
            "observaciones": "",
        }

    def test_ca_04_1_duplicado_no_se_crea_muestra_existente(self):
        """CA-04.1: no se crea el duplicado y se muestra el caso existente."""
        resp = self.client.post(self.add_url, self._datos("2026-000123", self.alfa))
        self.assertEqual(Caso.objects.filter(aseguradora=self.alfa).count(), 1)
        contenido = resp.content.decode()
        url_caso = reverse("dl_casos_admin:casos_caso_change", args=[self.existente.pk])
        # Enlace al caso existente y enlace para registrar un reingreso.
        self.assertIn(url_caso, contenido)
        self.assertIn(f"caso={self.existente.pk}", contenido)

    def test_ca_04_2_reingreso_vinculado_documentos_nuevos(self):
        """CA-04.2: se registra un reingreso vinculado indicando documentos nuevos."""
        # El formulario de alta de reingreso viene preseleccionado por GET.
        add_reingreso = reverse("dl_casos_admin:casos_reingreso_add")
        resp_get = self.client.get(
            add_reingreso, {"caso": self.existente.pk, "trae_documentos_nuevos": "on"}
        )
        self.assertEqual(resp_get.status_code, 200)
        # Guardar el reingreso.
        resp = self.client.post(
            add_reingreso,
            {
                "caso": self.existente.pk,
                "fecha_reingreso": "2026-03-01",
                "trae_documentos_nuevos": "on",
                "observaciones": "Trae examenes nuevos",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Reingreso.objects.count(), 1)
        r = Reingreso.objects.get()
        self.assertEqual(r.caso_id, self.existente.pk)
        self.assertTrue(r.trae_documentos_nuevos)
        self.assertEqual(r.registrado_por, self.coordina)

    def test_ca_04_3_sin_coincidencia_registro_sin_alertas(self):
        """CA-04.3: si no existe, el registro sigue sin alertas."""
        resp = self.client.post(
            self.add_url, self._datos("2026-999999", self.alfa), follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Caso.objects.filter(
                siniestro_normalizado="2026999999", aseguradora=self.alfa
            ).exists()
        )

    def test_ca_04_4_comparacion_ignora_mayusculas_espacios_guiones(self):
        """CA-04.4: la comparacion ignora mayusculas, espacios, guiones y puntos."""
        # La funcion de normalizacion colapsa todas las variantes.
        for variante in ["2026-000123", "2026 000123", "2026.000123", "2026000123", " 2026-000123 "]:
            self.assertEqual(normalizar_siniestro(variante), "2026000123")
        # Y cada variante se detecta como duplicado para la misma aseguradora.
        for variante in ["2026 000123", "2026.000123", "2026000123"]:
            resp = self.client.post(self.add_url, self._datos(variante, self.alfa))
            self.assertEqual(resp.status_code, 200)  # re-render con error, no redirect
            self.assertEqual(Caso.objects.filter(aseguradora=self.alfa).count(), 1)
        # Control: la misma cadena en OTRA aseguradora si se permite.
        resp_ok = self.client.post(
            self.add_url, self._datos("2026-000123", self.beta), follow=True
        )
        self.assertTrue(
            Caso.objects.filter(
                siniestro_normalizado="2026000123", aseguradora=self.beta
            ).exists()
        )

    def test_ca_04_db_unique_integrityerror(self):
        """Garantia de BD: la UNIQUE real de MySQL impide el duplicado.

        Nota: requiere un backend que imponga la restriccion UNIQUE
        (MySQL/InnoDB). Se marca como prueba a ejecutar en MySQL.
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Caso.objects.create(
                    numero_siniestro="2026000123",  # mismo normalizado que el existente
                    aseguradora=self.alfa,
                    fecha_recepcion=datetime.date(2026, 1, 2),
                    creado_por=self.coordina,
                )
