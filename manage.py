#!/usr/bin/env python
"""Utilidad de linea de comandos de Django para tareas administrativas."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Asegurese de que esta instalado y "
            "disponible en su PYTHONPATH, y de haber activado el entorno "
            "virtual (venv)."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
