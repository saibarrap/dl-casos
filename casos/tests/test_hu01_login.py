"""HU-01 — Inicio de sesion seguro por rol."""
from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase
from django.urls import reverse

from .base import PASSWORD, crear_roles, crear_usuario

User = get_user_model()


class LoginTests(TestCase):
    def setUp(self):
        crear_roles()
        self.login_url = reverse("dl_casos_admin:login")

    def test_ca_01_1_usuario_activo_credenciales_correctas_accede(self):
        """CA-01.1: usuario activo con credenciales correctas accede segun su rol."""
        crear_usuario("coordina1", rol="Coordinacion")
        ok = self.client.login(username="coordina1", password=PASSWORD)
        self.assertTrue(ok)
        # Accede al listado de casos conforme a su rol.
        resp = self.client.get(reverse("dl_casos_admin:casos_caso_changelist"))
        self.assertEqual(resp.status_code, 200)

    def test_ca_01_2_password_incorrecto_mensaje_generico(self):
        """CA-01.2: mensaje generico que no revela si el usuario existe."""
        crear_usuario("existe1", rol="Consulta")

        resp_existe = self.client.post(
            self.login_url,
            {"username": "existe1", "password": "claveMala"},
        )
        resp_inexistente = self.client.post(
            self.login_url,
            {"username": "no_existe", "password": "claveMala"},
        )
        # Ninguno autentica.
        self.assertFalse(resp_existe.wsgi_request.user.is_authenticated)
        self.assertFalse(resp_inexistente.wsgi_request.user.is_authenticated)
        # El mensaje de error es el mismo en ambos casos (no revela existencia).
        err_existe = resp_existe.context["form"].errors.as_text()
        err_inexistente = resp_inexistente.context["form"].errors.as_text()
        self.assertEqual(err_existe, err_inexistente)
        self.assertNotIn("no_existe", err_inexistente)

    def test_ca_01_3_usuario_inactivo_no_accede(self):
        """CA-01.3: usuario inactivo no accede aun con credenciales correctas."""
        crear_usuario("inactivo1", rol="Consulta", is_active=False)
        self.assertIsNone(authenticate(username="inactivo1", password=PASSWORD))
        ok = self.client.login(username="inactivo1", password=PASSWORD)
        self.assertFalse(ok)

    def test_ca_01_4_password_se_guarda_con_hash(self):
        """CA-01.4: las contrasenas no se guardan en texto plano."""
        user = crear_usuario("hash1", rol="Consulta")
        user.refresh_from_db()
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password(PASSWORD))
