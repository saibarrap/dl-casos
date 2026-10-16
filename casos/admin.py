"""Admin personalizado: unica interfaz del sistema.

Controla seguridad (borrado deshabilitado para todos, edicion por objeto para
el abogado, administracion de usuarios/grupos solo para superusuario), el
registro de casos y el listado con busqueda, filtros y paginacion.
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User

from .forms import CasoForm
from .models import Aseguradora, Caso, Reingreso
from .permisos import ABOGADO


class CasosAdminSite(AdminSite):
    site_header = "DL Abogados — Gestion de casos de RC Medica"
    site_title = "DL Casos"
    index_title = "Panel de administracion"


admin_site = CasosAdminSite(name="dl_casos_admin")


def _es_abogado(user) -> bool:
    return user.groups.filter(name=ABOGADO).exists()


class SoloSuperusuarioMixin:
    """Oculta el modelo a quien no sea superusuario (gestion de usuarios/grupos)."""

    def has_module_permission(self, request):
        return bool(request.user and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)


class UsuarioAdmin(SoloSuperusuarioMixin, UserAdmin):
    pass


class GrupoAdmin(SoloSuperusuarioMixin, GroupAdmin):
    pass


@admin.register(Aseguradora, site=admin_site)
class AseguradoraAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)


@admin.register(Caso, site=admin_site)
class CasoAdmin(admin.ModelAdmin):
    form = CasoForm

    list_display = (
        "numero_siniestro",
        "aseguradora",
        "numero_poliza",
        "asegurado",
        "estado",
        "abogado_asignado",
        "fecha_recepcion",
    )
    list_filter = ("aseguradora", "estado", "abogado_asignado")
    search_fields = (
        "numero_siniestro",
        "siniestro_normalizado",
        "numero_poliza",
        "asegurado",
    )
    list_per_page = 50
    list_select_related = ("aseguradora", "abogado_asignado")
    readonly_fields = (
        "siniestro_normalizado",
        "creado_por",
        "creado_en",
        "actualizado_por",
        "actualizado_en",
    )
    ordering = ("-creado_en",)

    # --- Seguridad de permisos ---

    def has_delete_permission(self, request, obj=None):
        # Nadie elimina casos, ni siquiera el superusuario.
        return False

    def get_actions(self, request):
        # Quitar la accion masiva de borrado.
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def has_change_permission(self, request, obj=None):
        user = request.user
        if user.is_superuser:
            return True
        if obj is None:
            # Acceso al changelist / vista de cambio en general.
            return user.has_perm("casos.change_caso") or _es_abogado(user)
        # Control por objeto.
        if _es_abogado(user):
            # El abogado solo edita el caso asignado a el.
            return obj.abogado_asignado_id == user.id
        if user.has_perm("casos.change_caso"):
            return True
        return False

    # --- Autoria automatica ---

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Reingreso, site=admin_site)
class ReingresoAdmin(admin.ModelAdmin):
    list_display = ("caso", "fecha_reingreso", "trae_documentos_nuevos", "registrado_por")
    list_filter = ("trae_documentos_nuevos",)
    search_fields = ("caso__numero_siniestro",)
    autocomplete_fields = ()
    readonly_fields = ("registrado_por", "creado_en")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)


# Registrar gestion de usuarios y grupos (visible solo para superusuario).
admin_site.register(User, UsuarioAdmin)
admin_site.register(Group, GrupoAdmin)
