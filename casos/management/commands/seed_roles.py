"""Crea los grupos (roles) con sus permisos y los usuarios demo.

La contrasena de los usuarios demo se toma de la variable de entorno
SEED_PASSWORD (via settings.SEED_PASSWORD). Si no esta definida, el comando
aborta: no se usa una contrasena por defecto insegura.

Es idempotente: puede ejecutarse varias veces sin duplicar.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

from casos.permisos import MATRIZ_PERMISOS, ROLES, USUARIOS_DEMO


class Command(BaseCommand):
    help = "Crea grupos con permisos y usuarios demo (contrasena desde SEED_PASSWORD)."

    def handle(self, *args, **options):
        password = getattr(settings, "SEED_PASSWORD", "") or ""
        if not password:
            raise CommandError(
                "La variable de entorno SEED_PASSWORD no esta definida. "
                "Defina SEED_PASSWORD antes de ejecutar seed_roles."
            )

        User = get_user_model()

        # 1) Crear grupos y asignar permisos segun la matriz.
        grupos = {}
        for rol in ROLES:
            grupo, _ = Group.objects.get_or_create(name=rol)
            grupos[rol] = grupo

            perms = []
            for app_label, codename in MATRIZ_PERMISOS[rol]:
                try:
                    perm = Permission.objects.get(
                        content_type__app_label=app_label, codename=codename
                    )
                except Permission.DoesNotExist:
                    raise CommandError(
                        f"No existe el permiso {app_label}.{codename}. "
                        "Aplique las migraciones antes de ejecutar seed_roles."
                    )
                perms.append(perm)
            grupo.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"Rol '{rol}' con {len(perms)} permisos."))

        # 2) Crear usuarios demo.
        for username, rol in USUARIOS_DEMO.items():
            es_super = rol is None
            user, creado = User.objects.get_or_create(
                username=username,
                defaults={
                    "is_staff": True,  # acceso al admin
                    "is_superuser": es_super,
                    "email": f"{username}@example.com",
                },
            )
            # Asegurar flags correctos tambien en reejecuciones.
            user.is_staff = True
            user.is_superuser = es_super
            user.is_active = True
            user.set_password(password)
            user.save()

            # Grupo del usuario (los superusuarios no necesitan grupo).
            if rol is not None:
                user.groups.set([grupos[rol]])
            else:
                user.groups.clear()

            estado = "creado" if creado else "actualizado"
            etiqueta = "superusuario" if es_super else f"rol {rol}"
            self.stdout.write(
                self.style.SUCCESS(f"Usuario '{username}' {estado} ({etiqueta}).")
            )

        self.stdout.write(self.style.SUCCESS("seed_roles completado."))
