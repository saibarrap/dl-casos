"""Enrutamiento principal: todo pasa por el admin personalizado."""
from django.urls import path

from casos.admin import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
]
