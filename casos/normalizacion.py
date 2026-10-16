"""Normalizacion del numero de siniestro.

El valor normalizado se usa para comparar duplicados ignorando mayusculas,
espacios, guiones y puntos. Es una funcion pura (sin dependencias de Django)
reutilizada por el modelo, los formularios, los comandos y las pruebas.
"""
import re

# Caracteres que se eliminan: espacios (incluye tabs/saltos), guiones y puntos.
_PATRON = re.compile(r"[\s\-.]")


def normalizar_siniestro(valor: str | None) -> str:
    """Devuelve el siniestro en mayusculas y sin espacios, guiones ni puntos.

    Ejemplos:
        "2026-000123"  -> "2026000123"
        "2026 000123"  -> "2026000123"
        "2026.000123"  -> "2026000123"
        " ab-12.3 "     -> "AB123"
    """
    if not valor:
        return ""
    return _PATRON.sub("", str(valor)).upper()
