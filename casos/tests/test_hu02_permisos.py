"""HU-02 — Administracion de usuarios, roles y permisos."""
import datetime

from django.test import TestCase
from django.urls import reverse

from casos.admin import CasoAdmin, admin_site
from casos.models import Caso
from .base import PASSWORD, crear_aseguradora, crear_roles, crear_usuario


class PermisosTests(TestCase):
    def setUp(self):
        crear_roles()
        self.aseguradora = crear_aseguradora("Alfa")
        self.coordina = crear_usuario("coordina", rol="Coordinacion")
        self.asistente = crear_usuario("asistente", rol="Asistente")
        self.abogado = crear_usuario("abogado1", rol="Abogado")
        self.consulta = crear_usuario("consulta", rol="Consulta")
        self.caso_admin = CasoAdmin(Caso, admin_site)

    def _caso(self, numero="2026-000001", abogado=None):
        return Caso.objects.create(
            numero_siniestro=numero,
            aseguradora=self.aseguradora,
            fecha_recepcion=datetime.date(2026, 1, 1),
            abogado_asignado=abogado,
            creado_por=self.coordina,
        )

    def test_ca_02_1_rol_asignado_solo_acciones_permitidas(self):
        """CA-02.1: cada rol solo hace lo que la matriz permite."""
        self.assertTrue(self.coordina.has_perm("casos.add_caso"))
        self.assertTrue(self.coordina.has_perm("casos.change_caso"))
        self.assertTrue(self.asistente.has_perm("casos.add_caso"))
        self.assertFalse(self.asistente.has_perm("casos.change_caso"))
        self.assertFalse(self.consulta.has_perm("casos.add_caso"))
        self.assertFalse(self.consulta.has_perm("casos.change_caso"))
        # Nadie tiene permiso de borrado.
        for u in (self.coordina, self.asistente, self.abogado, self.consulta):
            self.assertFalse(u.has_perm("casos.delete_caso"))

    def test_ca_02_2_consulta_ve_pero_no_edita(self):
        """CA-02.2: Consulta puede ver pero no editar."""
        self.assertTrue(self.consulta.has_perm("casos.view_caso"))
        caso = self._caso()

        class Req:
            user = self.consulta

        self.assertFalse(self.caso_admin.has_change_permission(Req, caso))
        self.assertFalse(self.caso_admin.has_delete_permission(Req, caso))

    def test_ca_02_3_no_admin_no_gestiona_usuarios(self):
        """CA-02.3: quien no es superusuario no gestiona usuarios ni grupos."""
        self.client.login(username="coordina", password=PASSWORD)
        resp = self.client.get(reverse("dl_casos_admin:auth_user_add"))
        self.assertIn(resp.status_code, (302, 403))
        # Un superusuario si puede.
        crear_usuario("admin1", is_superuser=True)
        self.client.login(username="admin1", password=PASSWORD)
        resp_super = self.client.get(reverse("dl_casos_admin:auth_user_add"))
        self.assertEqual(resp_super.status_code, 200)

    def test_ca_02_4_ningun_rol_puede_eliminar_casos(self):
        """CA-02.4: ningun rol (ni superusuario) puede eliminar casos."""
        caso = self._caso()
        for u in (self.coordina, self.abogado, self.consulta):
            class Req:
                user = u
            self.assertFalse(self.caso_admin.has_delete_permission(Req, caso))
        # Ni siquiera el superusuario.
        superu = crear_usuario("super1", is_superuser=True)

        class ReqSuper:
            user = superu

        self.assertFalse(self.caso_admin.has_delete_permission(ReqSuper, caso))
        # La accion masiva delete_selected no esta disponible.

        class ReqActions:
            user = superu
            GET = {}

        self.assertNotIn("delete_selected", self.caso_admin.get_actions(ReqActions))

    def test_ca_02_1_abogado_edita_solo_sus_casos(self):
        """CA-02.1 (detalle): el abogado edita solo los casos asignados a el."""
        propio = self._caso(numero="2026-000010", abogado=self.abogado)
        ajeno = self._caso(numero="2026-000011", abogado=None)

        class Req:
            user = self.abogado

        self.assertTrue(self.caso_admin.has_change_permission(Req, propio))
        self.assertFalse(self.caso_admin.has_change_permission(Req, ajeno))
        # Puede ver todos los casos (vista no restringida por objeto).
        self.assertTrue(self.caso_admin.has_view_permission(Req, ajeno))
