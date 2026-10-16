"""Utilidades compartidas por las pruebas: creacion de roles y usuarios."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from casos.models import Aseguradora
from casos.permisos import MATRIZ_PERMISOS, ROLES

User = get_user_model()

PASSWORD = "ClaveDePrueba123"


def crear_roles():
    """Crea los grupos con sus permisos (equivalente a seed_roles, sin usuarios)."""
    grupos = {}
    for rol in ROLES:
        grupo, _ = Group.objects.get_or_create(name=rol)
        perms = [
            Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
            for app_label, codename in MATRIZ_PERMISOS[rol]
        ]
        grupo.permissions.set(perms)
        grupos[rol] = grupo
    return grupos


def crear_usuario(username, rol=None, is_active=True, is_superuser=False):
    user = User.objects.create_user(
        username=username,
        password=PASSWORD,
        is_staff=True,
        is_active=is_active,
    )
    if is_superuser:
        user.is_superuser = True
        user.save()
    if rol is not None:
        grupo, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(grupo)
    return user


def crear_aseguradora(nombre="Alfa"):
    return Aseguradora.objects.get_or_create(nombre=nombre, defaults={"activa": True})[0]
