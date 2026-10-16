# Plan de implementación — MVP Sprint 1 (RC Médica)

Tareas incrementales de codificación para implementar el diseño aprobado. Cada tarea referencia los requisitos/CA que satisface. Alcance: solo HU-01 a HU-05. Fuera de alcance: importación de Excel, historial de cambios, transiciones de estado, SharePoint y Notion.

Convención: se marca `[ ]` pendiente, `[-]` en progreso, `[x]` completada. Se ejecuta una tarea a la vez, en orden.

---

- [ ] 1. Andamiaje del proyecto y configuración por entorno
  - Crear el proyecto Django `config` y la app `casos`; `manage.py` en la raíz.
  - `requirements.txt` con `Django>=5.2,<5.3`, `mysqlclient`, `python-dotenv` (documentar `PyMySQL` como fallback en comentario).
  - `config/settings.py`: cargar `.env`; `DATABASES` apuntando a MySQL/InnoDB (`ENGINE=django.db.backends.mysql`, `OPTIONS` con `charset=utf8mb4` y `sql_mode` estricto); `LANGUAGE_CODE='es-co'`, `TIME_ZONE='America/Bogota'`, `USE_TZ=True`; hashers por defecto de Django.
  - `config/urls.py` enrutando al admin.
  - Verificar que `python manage.py check` pasa (sin requerir BD).
  - _Requisitos: RNF-2, RNF-4, RNF-5; soporte a HU-01 (hashers), zona horaria para HU-03_

- [ ] 2. Función de normalización del siniestro
  - Implementar `casos/normalizacion.py` con `normalizar_siniestro(valor)` (mayúsculas; sin espacios, guiones ni puntos).
  - Función pura, sin dependencias de Django, reutilizable por modelo, forms, comandos y pruebas.
  - _Requisitos: CA-04.4_

- [ ] 3. Modelos de dominio con restricciones en la base de datos
  - [ ] 3.1 Modelo `Aseguradora` (`nombre` UNIQUE NOT NULL, `activa` default True) con `UniqueConstraint(nombre)`.
    - _Requisitos: RNF-1, RNF-2_
  - [ ] 3.2 Modelo `Caso` con todos los campos en español/snake_case; FKs (`aseguradora` PROTECT NOT NULL, `abogado_asignado` SET_NULL opcional, `creado_por` PROTECT, `actualizado_por` SET_NULL); `estado` con choices y default `REGISTRADO`; `creado_en` (`auto_now_add`), `actualizado_en` (`auto_now`).
    - `Caso.save()` recalcula `siniestro_normalizado = normalizar_siniestro(numero_siniestro)` antes de persistir (fuente de verdad).
    - `Meta.constraints`: `UniqueConstraint(['siniestro_normalizado','aseguradora'], name='uniq_siniestro_aseguradora')` (UNIQUE real en MySQL) y `CheckConstraint` del conjunto de estados (`ck_caso_estado`).
    - `Meta.indexes`: `siniestro_normalizado`, `numero_poliza`, `asegurado`, `estado`, `aseguradora`, `abogado_asignado`.
    - _Requisitos: RNF-1, RNF-2, RNF-3, CA-03.2, CA-04.4_
  - [ ] 3.3 Modelo `Reingreso` (`caso` FK PROTECT NOT NULL, `fecha_reingreso`, `trae_documentos_nuevos` default False, `observaciones`, `registrado_por` PROTECT, `creado_en` auto).
    - _Requisitos: RNF-1, RNF-2, CA-04.2_
  - [ ] 3.4 Generar y aplicar migraciones; verificar `UNIQUE KEY` compuesta y `CHECK` del estado en el `CREATE TABLE` (`SHOW CREATE TABLE casos_caso`). Si no hay MySQL, dejar la migración generada y anotar la verificación como pendiente de ejecución local.
    - _Requisitos: RNF-1_

- [ ] 4. Matriz de permisos y comando `seed_roles`
  - [ ] 4.1 `casos/permisos.py`: definir la matriz rol → permisos estándar (Coordinación: view/add/change caso + view/add reingreso; Asistente: view/add caso + view/add reingreso; Abogado: view/change caso + view reingreso; Consulta: view caso + view reingreso). Nunca incluir `delete_caso`.
    - _Requisitos: CA-02.1, CA-02.4_
  - [ ] 4.2 Comando `seed_roles`: crear grupos idempotentes y asignarles los permisos de la matriz; crear usuarios demo (`admin` superusuario, `coordinacion`, `asistente`, `abogado1`, `consulta`) con contraseña desde variable de entorno (`SEED_PASSWORD`); abortar con mensaje claro si la variable no está definida.
    - _Requisitos: CA-01.1, CA-02.1, CA-02.3, RNF-4, RNF-5_

- [ ] 5. Admin personalizado — base y seguridad de casos
  - [ ] 5.1 `CasosAdminSite` (título/idioma en español); registrar `User`/`Group` solo visibles para superusuario (`has_module_permission`).
    - _Requisitos: CA-02.3_
  - [ ] 5.2 `AseguradoraAdmin` básico (lista + búsqueda por nombre).
    - _Requisitos: RNF-2_
  - [ ] 5.3 `CasoAdmin`: `has_delete_permission()` → `False` siempre; quitar `delete_selected` de `get_actions()`; no exponer borrado.
    - _Requisitos: CA-02.4_
  - [ ] 5.4 `CasoAdmin.has_change_permission(request, obj)`: Abogado edita solo su caso asignado (`obj.abogado_asignado_id == request.user.id`); Coordinación edita todos; Asistente/Consulta no editan; `has_view_permission` sin restricción por objeto (Abogado ve todos).
    - _Requisitos: CA-02.1, CA-02.2_
  - [ ] 5.5 `save_model()` del `CasoAdmin`: en alta fija `creado_por=request.user`; en edición fija `actualizado_por=request.user`.
    - _Requisitos: CA-03.2_

- [ ] 6. Registro de caso — formulario y validaciones (HU-03)
  - [ ] 6.1 `CasoForm`: declarar obligatorios `numero_siniestro`, `aseguradora`, `fecha_recepcion`; mensajes de error que nombren los campos faltantes.
    - _Requisitos: CA-03.1_
  - [ ] 6.2 `clean_fecha_recepcion()`: rechazar fecha futura (vs `timezone.localdate()` America/Bogota) e inválida, con mensaje claro en español.
    - _Requisitos: CA-03.3_
  - [ ] 6.3 Verificar visibilidad en listado y acceso al detalle del caso creado (configuración de `CasoAdmin`).
    - _Requisitos: CA-03.4_

- [ ] 7. Detección de duplicados y reingresos (HU-04)
  - [ ] 7.1 `CasoForm.clean()`: calcular `siniestro_normalizado` del valor ingresado; buscar `Caso` con mismo `(siniestro_normalizado, aseguradora)`; si existe (y no es el mismo en edición) lanzar `ValidationError` con `format_html` incluyendo enlace al caso existente (`admin:casos_caso_change`) y enlace al alta de reingreso (`admin:casos_reingreso_add?caso=<pk>&trae_documentos_nuevos=on`). No guardar el duplicado.
    - _Requisitos: CA-04.1, CA-04.4_
  - [ ] 7.2 `ReingresoAdmin`: aceptar parámetros GET iniciales (`caso`, `trae_documentos_nuevos`) para preseleccionar; `save_model()` fija `registrado_por=request.user`.
    - _Requisitos: CA-04.2_
  - [ ] 7.3 Confirmar que, sin coincidencia, el alta procede sin alertas.
    - _Requisitos: CA-04.3_

- [ ] 8. Listado — búsqueda, filtros y paginación (HU-05)
  - `CasoAdmin`: `search_fields=('numero_siniestro','siniestro_normalizado','numero_poliza','asegurado')`; `list_filter=('aseguradora','estado','abogado_asignado')`; `list_per_page=50`; `list_display` y `list_select_related=('aseguradora','abogado_asignado')`.
  - _Requisitos: CA-05.1, CA-05.2, CA-05.3, RNF-3_

- [ ] 9. Comando `seed_demo_data --cantidad N`
  - Crear aseguradoras `Alfa`, `Beta`, `Gamma` (idempotente).
  - Generar N casos ficticios con siniestros tipo `2026-000123` variando formato (con/sin guion, puntos, espacios), garantizando unicidad de `(siniestro_normalizado, aseguradora)`; usar `bulk_create` por lotes.
  - `creado_por` = usuario demo existente (sugerir `seed_roles` si falta).
  - _Requisitos: RNF-5, soporte a CA-05.4_

- [ ] 10. Pruebas automatizadas — HU-01 (login)
  - `casos/tests/test_hu01_login.py` con: `test_ca_01_1_...`, `test_ca_01_2_...` (mensaje genérico idéntico para usuario inexistente vs. clave errónea), `test_ca_01_3_...` (inactivo), `test_ca_01_4_...` (hash).
  - _Requisitos: CA-01.1, CA-01.2, CA-01.3, CA-01.4_

- [ ] 11. Pruebas automatizadas — HU-02 (permisos)
  - `casos/tests/test_hu02_permisos.py`: `test_ca_02_1_...`, `test_ca_02_2_...`, `test_ca_02_3_...`, `test_ca_02_4_...` (incl. `delete_selected` ausente y URL de borrado denegada).
  - _Requisitos: CA-02.1, CA-02.2, CA-02.3, CA-02.4_

- [ ] 12. Pruebas automatizadas — HU-03 (registro)
  - `casos/tests/test_hu03_registro.py`: `test_ca_03_1_...`, `test_ca_03_2_...`, `test_ca_03_3_...`, `test_ca_03_4_...`.
  - _Requisitos: CA-03.1, CA-03.2, CA-03.3, CA-03.4_

- [ ] 13. Pruebas automatizadas — HU-04 (duplicados/reingreso)
  - `casos/tests/test_hu04_duplicados.py`: `test_ca_04_1_...`, `test_ca_04_2_...`, `test_ca_04_3_...`, `test_ca_04_4_...` (variantes de formato + prueba directa de `normalizar_siniestro`); incluir comprobación de `IntegrityError` por la UNIQUE real de MySQL.
  - _Requisitos: CA-04.1, CA-04.2, CA-04.3, CA-04.4, RNF-1_

- [ ] 14. Pruebas automatizadas — HU-05 (búsqueda/filtros/paginación)
  - `casos/tests/test_hu05_busqueda.py`: `test_ca_05_1_...`, `test_ca_05_2_...`, `test_ca_05_3_...` (>`list_per_page`), `test_ca_05_4_...` (>3.700 casos con medición de tiempo; marcada para MySQL).
  - _Requisitos: CA-05.1, CA-05.2, CA-05.3, CA-05.4, RNF-3_

- [ ] 15. Entregables de entorno y documentación
  - [ ] 15.1 `docker-compose.yml` solo con `mysql:8.0` (variables desde `.env`, volumen, puerto).
    - _Requisitos: RNF-5_
  - [ ] 15.2 `.env.example` con todas las variables (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_*`, `SEED_PASSWORD`), sin secretos reales; asegurar `.gitignore` ignora `.env`.
    - _Requisitos: RNF-4, RNF-5_
  - [ ] 15.3 `README.md`: pasos para levantar MySQL en Docker, crear venv, instalar `requirements.txt`, migrar, `seed_roles`, `seed_demo_data`, correr el servidor y las pruebas.
    - _Requisitos: RNF-5_
  - [ ] 15.4 `docs/matriz_ca.md`: tabla criterio → prueba (archivo::método) para los 21 CA.
    - _Requisitos: RNF-6_

- [ ] 16. Ejecución de pruebas y reporte de cobertura MySQL
  - Ejecutar `manage.py test` contra MySQL si está disponible; verificar que las pruebas por CA pasan.
  - Si no hay MySQL, no migrar a SQLite: dejar las pruebas escritas para MySQL y reportar explícitamente cuáles no se pudieron ejecutar localmente (especialmente CA-05.4 y la garantía UNIQUE/`IntegrityError`).
  - _Requisitos: RNF-6_
