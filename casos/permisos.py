"""Definicion central de la matriz de roles -> permisos.

Se usan los permisos estandar de Django por modelo. NUNCA se incluye el permiso
delete_caso: nadie puede eliminar casos (CA-02.4).
"""

# Nombres de los grupos (roles).
COORDINACION = "Coordinacion"
ASISTENTE = "Asistente"
ABOGADO = "Abogado"
CONSULTA = "Consulta"

ROLES = [COORDINACION, ASISTENTE, ABOGADO, CONSULTA]

# Permisos por rol expresados como (app_label, codename).
# Modelos: casos.caso, casos.reingreso, casos.aseguradora.
MATRIZ_PERMISOS = {
    COORDINACION: [
        ("casos", "view_caso"),
        ("casos", "add_caso"),
        ("casos", "change_caso"),
        ("casos", "view_reingreso"),
        ("casos", "add_reingreso"),
        ("casos", "view_aseguradora"),
    ],
    ASISTENTE: [
        ("casos", "view_caso"),
        ("casos", "add_caso"),
        ("casos", "view_reingreso"),
        ("casos", "add_reingreso"),
        ("casos", "view_aseguradora"),
    ],
    ABOGADO: [
        ("casos", "view_caso"),
        # change_caso se concede a nivel de grupo, pero el admin restringe por
        # objeto: el abogado solo edita los casos asignados a el.
        ("casos", "change_caso"),
        ("casos", "view_reingreso"),
        ("casos", "view_aseguradora"),
    ],
    CONSULTA: [
        ("casos", "view_caso"),
        ("casos", "view_reingreso"),
        ("casos", "view_aseguradora"),
    ],
}

# Usuarios demo: username -> (rol o None si es superusuario).
USUARIOS_DEMO = {
    "admin": None,  # superusuario
    "coordinacion": COORDINACION,
    "asistente": ASISTENTE,
    "abogado1": ABOGADO,
    "consulta": CONSULTA,
}
