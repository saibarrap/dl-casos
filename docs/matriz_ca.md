# Matriz criterio de aceptacion -> prueba

Cada criterio de aceptacion (HU-01 a HU-05) tiene al menos una prueba automatizada
cuyo nombre incluye su ID. Las pruebas usan el test runner de Django y estan
escritas para MySQL.

## Estado de ejecucion

> **Las pruebas NO se pudieron ejecutar en el entorno de desarrollo del agente.**
> El sandbox no tiene acceso a PyPI (no se pudo instalar Django ni mysqlclient) ni
> MySQL/Docker daemon disponibles. Siguiendo la indicacion del equipo, **no se
> cambio a SQLite** para forzar que pasaran. Por lo tanto, la columna "Resultado"
> **no** puede marcarse como "Cumple" todavia: se marca como **"Pendiente de
> ejecucion local (MySQL)"**. Si verifico la logica de forma estatica, se indica
> en la columna "Verificacion estatica".
>
> Para obtener el resultado real: levante MySQL (`docker compose up -d`), instale
> dependencias y ejecute `python manage.py test`. Luego actualice la columna
> "Resultado" a **Cumple / No cumple** segun la salida.

Leyenda de "Resultado":
- **Pendiente (MySQL)** — prueba escrita, no ejecutada por falta de MySQL en el entorno.
- **Cumple / No cumple** — a diligenciar tras ejecutar `manage.py test` localmente.

## Cobertura por criterio

| Criterio | Descripcion | Prueba (archivo :: metodo) | Verificacion estatica | Resultado |
|---|---|---|---|---|
| CA-01.1 | Usuario activo con credenciales correctas accede segun su rol | `test_hu01_login.py :: test_ca_01_1_usuario_activo_credenciales_correctas_accede` | Compila; logica revisada | Pendiente (MySQL) |
| CA-01.2 | Contrasena incorrecta: mensaje generico que no revela si el usuario existe | `test_hu01_login.py :: test_ca_01_2_password_incorrecto_mensaje_generico` | Compila; logica revisada | Pendiente (MySQL) |
| CA-01.3 | Usuario inactivo no accede | `test_hu01_login.py :: test_ca_01_3_usuario_inactivo_no_accede` | Compila; logica revisada | Pendiente (MySQL) |
| CA-01.4 | Las contrasenas no se guardan en texto plano | `test_hu01_login.py :: test_ca_01_4_password_se_guarda_con_hash` | Compila; logica revisada | Pendiente (MySQL) |
| CA-02.1 | Rol asignado solo hace lo que la matriz permite (incluye abogado edita solo sus casos) | `test_hu02_permisos.py :: test_ca_02_1_rol_asignado_solo_acciones_permitidas` y `:: test_ca_02_1_abogado_edita_solo_sus_casos` | Compila; refactor con RequestFactory | Pendiente (MySQL) |
| CA-02.2 | Consulta puede ver pero no editar | `test_hu02_permisos.py :: test_ca_02_2_consulta_ve_pero_no_edita` | Compila; refactor con RequestFactory | Pendiente (MySQL) |
| CA-02.3 | Quien no es administrador no gestiona usuarios ni permisos | `test_hu02_permisos.py :: test_ca_02_3_no_admin_no_gestiona_usuarios` | Compila; logica revisada | Pendiente (MySQL) |
| CA-02.4 | Ningun rol tiene opcion de eliminar casos | `test_hu02_permisos.py :: test_ca_02_4_ningun_rol_puede_eliminar_casos` | Compila; refactor con RequestFactory | Pendiente (MySQL) |
| CA-03.1 | Sin campos obligatorios no se guarda e indica cuales faltan | `test_hu03_registro.py :: test_ca_03_1_sin_obligatorios_no_guarda_e_indica_faltantes` | Compila; logica revisada | Pendiente (MySQL) |
| CA-03.2 | Con datos validos queda REGISTRADO con usuario y fecha-hora automaticos | `test_hu03_registro.py :: test_ca_03_2_datos_validos_estado_registrado_y_auditoria` | Compila; logica revisada | Pendiente (MySQL) |
| CA-03.3 | Fecha futura o invalida se rechaza con mensaje claro | `test_hu03_registro.py :: test_ca_03_3_fecha_futura_o_invalida_se_rechaza` | Compila; logica revisada | Pendiente (MySQL) |
| CA-03.4 | El caso aparece en el listado y se abre su detalle | `test_hu03_registro.py :: test_ca_03_4_caso_aparece_en_listado_y_detalle` | Compila; logica revisada | Pendiente (MySQL) |
| CA-04.1 | Siniestro+aseguradora existentes: no se crea el duplicado y se muestra el existente | `test_hu04_duplicados.py :: test_ca_04_1_duplicado_no_se_crea_muestra_existente` | Compila; logica revisada | Pendiente (MySQL) |
| CA-04.2 | Se registra un reingreso vinculado indicando documentos nuevos | `test_hu04_duplicados.py :: test_ca_04_2_reingreso_vinculado_documentos_nuevos` | Compila; logica revisada | Pendiente (MySQL) |
| CA-04.3 | Si no existe, el registro sigue sin alertas | `test_hu04_duplicados.py :: test_ca_04_3_sin_coincidencia_registro_sin_alertas` | Compila; logica revisada | Pendiente (MySQL) |
| CA-04.4 | La comparacion ignora mayusculas, espacios, guiones y puntos | `test_hu04_duplicados.py :: test_ca_04_4_comparacion_ignora_mayusculas_espacios_guiones` | **Logica central ejecutada OK** (normalizar_siniestro verificada aparte) | Pendiente (MySQL) |
| CA-05.1 | Buscar por siniestro o poliza muestra solo coincidencias | `test_hu05_busqueda.py :: test_ca_05_1_busqueda_por_siniestro_o_poliza` | Compila; logica revisada | Pendiente (MySQL) |
| CA-05.2 | Los filtros combinados cumplen todos | `test_hu05_busqueda.py :: test_ca_05_2_filtros_combinados_cumplen_todos` | Compila; logica revisada | Pendiente (MySQL) |
| CA-05.3 | Con mas de una pagina hay paginacion y total | `test_hu05_busqueda.py :: test_ca_05_3_paginacion_y_total` | Compila; logica revisada | Pendiente (MySQL) |
| CA-05.4 | Con mas de 3.700 casos la busqueda responde en pocos segundos | `test_hu05_busqueda.py :: test_ca_05_4_busqueda_responde_con_mas_de_3700_casos` | Compila; requiere MySQL para ser representativa | Pendiente (MySQL) |

## Pruebas adicionales de respaldo (garantias de BD)

| Garantia | Prueba | Resultado |
|---|---|---|
| UNIQUE real en MySQL sobre (siniestro_normalizado, aseguradora) lanza IntegrityError | `test_hu04_duplicados.py :: test_ca_04_db_unique_integrityerror` | Pendiente (MySQL) |

## Verificacion de datos ficticios (confidencialidad)

Se reviso que **ninguna** prueba (ni los comandos de seed) use datos reales:
no hay cedulas, historias clinicas, telefonos ni nombres de personas reales.
Datos usados: aseguradoras `Alfa`/`Beta`/`Gamma`, asegurados tipo
`"Asegurado 000001"` / `"Juan Perez"` (placeholder), siniestros `2026-0000NN`
fabricados y correos `@example.com` (dominio reservado para ejemplos). **Cumple.**

> Nota: CA-05.4 y la garantia UNIQUE dependen de MySQL/InnoDB. No se migran a
> SQLite; se dejan escritas y se ejecutan localmente.
