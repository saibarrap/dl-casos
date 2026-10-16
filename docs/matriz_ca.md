# Matriz criterio de aceptacion -> prueba

Cada criterio de aceptacion (HU-01 a HU-05) tiene al menos una prueba automatizada
cuyo nombre incluye su ID. Las pruebas usan el test runner de Django y estan
escritas para MySQL.

| Criterio | Descripcion | Prueba (archivo :: metodo) |
|---|---|---|
| CA-01.1 | Usuario activo con credenciales correctas accede segun su rol | `casos/tests/test_hu01_login.py :: test_ca_01_1_usuario_activo_credenciales_correctas_accede` |
| CA-01.2 | Contrasena incorrecta: mensaje generico que no revela si el usuario existe | `casos/tests/test_hu01_login.py :: test_ca_01_2_password_incorrecto_mensaje_generico` |
| CA-01.3 | Usuario inactivo no accede | `casos/tests/test_hu01_login.py :: test_ca_01_3_usuario_inactivo_no_accede` |
| CA-01.4 | Las contrasenas no se guardan en texto plano | `casos/tests/test_hu01_login.py :: test_ca_01_4_password_se_guarda_con_hash` |
| CA-02.1 | Rol asignado solo hace lo que la matriz permite (incluye abogado edita solo sus casos) | `casos/tests/test_hu02_permisos.py :: test_ca_02_1_rol_asignado_solo_acciones_permitidas` y `:: test_ca_02_1_abogado_edita_solo_sus_casos` |
| CA-02.2 | Consulta puede ver pero no editar | `casos/tests/test_hu02_permisos.py :: test_ca_02_2_consulta_ve_pero_no_edita` |
| CA-02.3 | Quien no es administrador no gestiona usuarios ni permisos | `casos/tests/test_hu02_permisos.py :: test_ca_02_3_no_admin_no_gestiona_usuarios` |
| CA-02.4 | Ningun rol tiene opcion de eliminar casos | `casos/tests/test_hu02_permisos.py :: test_ca_02_4_ningun_rol_puede_eliminar_casos` |
| CA-03.1 | Sin campos obligatorios no se guarda e indica cuales faltan | `casos/tests/test_hu03_registro.py :: test_ca_03_1_sin_obligatorios_no_guarda_e_indica_faltantes` |
| CA-03.2 | Con datos validos queda REGISTRADO con usuario y fecha-hora automaticos | `casos/tests/test_hu03_registro.py :: test_ca_03_2_datos_validos_estado_registrado_y_auditoria` |
| CA-03.3 | Fecha futura o invalida se rechaza con mensaje claro | `casos/tests/test_hu03_registro.py :: test_ca_03_3_fecha_futura_o_invalida_se_rechaza` |
| CA-03.4 | El caso aparece en el listado y se abre su detalle | `casos/tests/test_hu03_registro.py :: test_ca_03_4_caso_aparece_en_listado_y_detalle` |
| CA-04.1 | Siniestro+aseguradora existentes: no se crea el duplicado y se muestra el existente | `casos/tests/test_hu04_duplicados.py :: test_ca_04_1_duplicado_no_se_crea_muestra_existente` |
| CA-04.2 | Se registra un reingreso vinculado indicando documentos nuevos | `casos/tests/test_hu04_duplicados.py :: test_ca_04_2_reingreso_vinculado_documentos_nuevos` |
| CA-04.3 | Si no existe, el registro sigue sin alertas | `casos/tests/test_hu04_duplicados.py :: test_ca_04_3_sin_coincidencia_registro_sin_alertas` |
| CA-04.4 | La comparacion ignora mayusculas, espacios, guiones y puntos | `casos/tests/test_hu04_duplicados.py :: test_ca_04_4_comparacion_ignora_mayusculas_espacios_guiones` |
| CA-05.1 | Buscar por siniestro o poliza muestra solo coincidencias | `casos/tests/test_hu05_busqueda.py :: test_ca_05_1_busqueda_por_siniestro_o_poliza` |
| CA-05.2 | Los filtros combinados cumplen todos | `casos/tests/test_hu05_busqueda.py :: test_ca_05_2_filtros_combinados_cumplen_todos` |
| CA-05.3 | Con mas de una pagina hay paginacion y total | `casos/tests/test_hu05_busqueda.py :: test_ca_05_3_paginacion_y_total` |
| CA-05.4 | Con mas de 3.700 casos la busqueda responde en pocos segundos | `casos/tests/test_hu05_busqueda.py :: test_ca_05_4_busqueda_responde_con_mas_de_3700_casos` |

## Pruebas adicionales de respaldo (garantias de BD)

| Garantia | Prueba |
|---|---|
| UNIQUE real en MySQL sobre (siniestro_normalizado, aseguradora) lanza IntegrityError | `casos/tests/test_hu04_duplicados.py :: test_ca_04_db_unique_integrityerror` |

> Nota de ejecucion: CA-05.4 y la garantia UNIQUE (`test_ca_04_db_unique_integrityerror`)
> dependen de MySQL/InnoDB. Si no hay MySQL disponible, no se migran a SQLite:
> se dejan escritas y se reporta que no pudieron ejecutarse localmente.
