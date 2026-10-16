# Diseño — MVP Sprint 1 (Sistema de gestión de casos de RC Médica)

## Visión general

El sistema es una aplicación **Django 5.2 LTS** (Python 3.12) cuya única interfaz es el **Django admin personalizado**. No se construye un frontend aparte. La persistencia es **MySQL 8.0 con motor InnoDB**, con las reglas de integridad declaradas en la base de datos. El idioma del dominio, los mensajes y la interfaz es **español**; la zona horaria es **America/Bogota**.

> Nota de versión: a octubre de 2026, Django 5.2 es la serie LTS vigente (soporte hasta abril de 2028) y es compatible con Python 3.12. Se fija 5.2 LTS por estabilidad. *(Fuentes: [endoflife.date/django](https://endoflife.date/django), [upgradedjango.com/faq](https://upgradedjango.com/faq/); contenido reformulado para cumplimiento de licencias.)*

Este diseño implementa exactamente las historias **HU-01 a HU-05** y sus 21 criterios de aceptación. Quedan **fuera de alcance**: importación de Excel, historial de cambios, transiciones de estado, enlaces a SharePoint y a Notion.

---

## Arquitectura

### Estructura del proyecto

```
dl-casos/
├── config/                     # proyecto Django
│   ├── __init__.py
│   ├── settings.py             # lee variables de entorno (.env)
│   ├── urls.py                 # enruta al admin personalizado
│   ├── wsgi.py
│   └── asgi.py
├── casos/                      # app de dominio
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py               # Aseguradora, Caso, Reingreso
│   ├── admin.py                # CasoAdmin, ReingresoAdmin, AseguradoraAdmin + AdminSite
│   ├── forms.py                # validaciones (fecha no futura, duplicados)
│   ├── normalizacion.py        # función normalizar_siniestro()
│   ├── permisos.py             # definición de la matriz rol → permisos
│   ├── migrations/
│   ├── management/
│   │   └── commands/
│   │       ├── seed_roles.py
│   │       └── seed_demo_data.py
│   └── tests/
│       ├── __init__.py
│       ├── test_hu01_login.py
│       ├── test_hu02_permisos.py
│       ├── test_hu03_registro.py
│       ├── test_hu04_duplicados.py
│       └── test_hu05_busqueda.py
├── docs/
│   ├── README.md               # (o README en raíz) pasos para correr
│   └── matriz_ca.md            # tabla criterio → prueba
├── docker-compose.yml          # solo MySQL 8.0
├── .env.example
├── .env                        # (ignorado por git)
├── requirements.txt
├── manage.py
└── README.md
```

### Capas y responsabilidades

| Capa | Componente | Responsabilidad |
|---|---|---|
| Configuración | `config/settings.py` | Carga `.env`, define `DATABASES` (MySQL/InnoDB), `LANGUAGE_CODE='es-co'`, `TIME_ZONE='America/Bogota'`, `USE_TZ=True`, hashers de contraseña por defecto de Django. |
| Dominio | `casos/models.py` | Modelos con restricciones de BD (NOT NULL, UNIQUE, CHECK, FK), índices, cálculo de `siniestro_normalizado`. |
| Normalización | `casos/normalizacion.py` | Función pura `normalizar_siniestro(texto)` reutilizada por modelo, forms, comandos y pruebas. |
| Presentación | `casos/admin.py` | AdminSite personalizado: listados, búsqueda, filtros, paginación, detalle, bloqueo de borrado, control de edición por rol. |
| Validación | `casos/forms.py` | Campos obligatorios, fecha no futura, detección de duplicado con enlaces a caso y reingreso. |
| Permisos | `casos/permisos.py` + grupos | Matriz rol → permisos; se aplica vía grupos de Django y `has_*_permission`. |
| Operación | `management/commands/*` | `seed_roles`, `seed_demo_data`. |

### Flujo general (admin personalizado)

Se define un `AdminSite` propio (p. ej. `admin_site = CasosAdminSite()`) para controlar el título, el idioma y asegurar que todas las vistas pasen por autenticación. `config/urls.py` enruta `/admin/` (o `/`) a ese sitio. El login usa el flujo estándar de autenticación de Django (hashers y `authenticate()`), con mensajes de error genéricos.

---

## Modelo de datos

Todos los nombres de modelos y campos en **español** y `snake_case`. Motor **InnoDB** (vía `OPTIONS`/`DATABASES` y `Meta`).

### Aseguradora

| Campo | Tipo | Restricción BD |
|---|---|---|
| `nombre` | CharField(150) | **UNIQUE**, NOT NULL |
| `activa` | BooleanField | NOT NULL, default `True` |

- `Meta.constraints`: `UniqueConstraint(fields=['nombre'])` (respaldado por índice único en BD).

### Caso

| Campo | Tipo | Restricción BD / Notas |
|---|---|---|
| `numero_siniestro` | CharField(100) | NOT NULL (obligatorio) |
| `siniestro_normalizado` | CharField(100) | NOT NULL, **calculado** en `save()`/`clean()`; indexado |
| `aseguradora` | FK → Aseguradora | NOT NULL (`on_delete=PROTECT`) |
| `numero_poliza` | CharField(100) | opcional (blank), indexado |
| `fecha_recepcion` | DateField | NOT NULL; validación: no futura |
| `asegurado` | CharField(200) | opcional, indexado |
| `estado` | CharField(choices) | NOT NULL, default `REGISTRADO`, **CHECK** sobre el conjunto |
| `abogado_asignado` | FK → User | NULL permitido (`on_delete=SET_NULL`, `related_name='casos_asignados'`) |
| `observaciones` | TextField | opcional |
| `creado_por` | FK → User | `on_delete=PROTECT`, `related_name='casos_creados'`; automático |
| `creado_en` | DateTimeField | `auto_now_add=True` |
| `actualizado_por` | FK → User | NULL; `on_delete=SET_NULL`, `related_name='casos_actualizados'` |
| `actualizado_en` | DateTimeField | `auto_now=True` |

Estados (choices): `REGISTRADO`, `ASIGNADO`, `EN_ANALISIS`, `ENVIADO_ASEGURADORA`, `CERRADO`.

> Aclaración de alcance: el campo `estado` existe y su CHECK se declara en BD, pero **no se implementa ningún flujo de transición** entre estados (fuera de alcance). En el Sprint 1 el estado solo nace en `REGISTRADO`.

`Meta` de `Caso`:
- `constraints`:
  - `UniqueConstraint(fields=['siniestro_normalizado', 'aseguradora'], name='uniq_siniestro_aseguradora')` → **CA-04 / RNF-1**.
    - **Debe materializarse como una restricción UNIQUE real en MySQL** (una línea `UNIQUE KEY uniq_siniestro_aseguradora (siniestro_normalizado, aseguradora)` en el `CREATE TABLE` del motor **InnoDB**), no como una validación solo en código. La migración de Django genera este índice único compuesto; la unicidad queda garantizada por el servidor de base de datos: un `INSERT`/`UPDATE` que viole el par produce `IntegrityError` (error 1062 de MySQL) aunque se evada la validación de la aplicación.
    - Verificación operativa: `SHOW CREATE TABLE casos_caso;` debe mostrar la `UNIQUE KEY` sobre `(siniestro_normalizado, aseguradora)`.
  - `CheckConstraint(check=Q(estado__in=[...]), name='ck_caso_estado')` → **RNF-1**.
- `indexes`:
  - `Index(fields=['siniestro_normalizado'])`
  - `Index(fields=['numero_poliza'])`
  - `Index(fields=['asegurado'])`
  - `Index(fields=['estado'])`
  - `Index(fields=['aseguradora'])` (la FK ya crea índice; explícito para claridad)
  - `Index(fields=['abogado_asignado'])`
  → soportan **CA-05.1, CA-05.2, CA-05.4 / RNF-3**.

### Reingreso

| Campo | Tipo | Restricción BD / Notas |
|---|---|---|
| `caso` | FK → Caso | NOT NULL (`on_delete=PROTECT`, `related_name='reingresos'`) |
| `fecha_reingreso` | DateField | NOT NULL |
| `trae_documentos_nuevos` | BooleanField | NOT NULL, default `False` |
| `observaciones` | TextField | opcional |
| `registrado_por` | FK → User | `on_delete=PROTECT`; automático |
| `creado_en` | DateTimeField | `auto_now_add=True` |

### Normalización del siniestro

`casos/normalizacion.py`:

```python
import re

def normalizar_siniestro(valor: str) -> str:
    """Mayúsculas y sin espacios, guiones ni puntos."""
    if valor is None:
        return ""
    return re.sub(r"[\s\-.]", "", valor).upper()
```

`siniestro_normalizado` se calcula en **dos puntos**, usando la misma función `normalizar_siniestro()`, para que el valor sea consistente venga de donde venga el guardado:

1. **En el modelo — `Caso.save()`**: antes de persistir, el modelo recalcula `self.siniestro_normalizado = normalizar_siniestro(self.numero_siniestro)`. Esto garantiza que **cualquier** camino de escritura (admin, shell, comandos `seed_demo_data`, `bulk_create`/`create`, scripts) produzca el valor normalizado correcto, sin depender del formulario. Es la fuente de verdad del campo.

   ```python
   def save(self, *args, **kwargs):
       self.siniestro_normalizado = normalizar_siniestro(self.numero_siniestro)
       super().save(*args, **kwargs)
   ```

2. **En la validación del formulario — `CasoForm.clean()`**: el formulario del admin calcula el valor normalizado del `numero_siniestro` ingresado para **detectar duplicados antes de guardar** y mostrar el error con enlaces (HU-04). Esta normalización en el form ocurre durante `clean()`/`clean_numero_siniestro()`, de modo que la comprobación de `UNIQUE(siniestro_normalizado, aseguradora)` se hace contra el mismo valor que `save()` persistirá.

   ```python
   def clean(self):
       cleaned = super().clean()
       numero = cleaned.get("numero_siniestro")
       aseguradora = cleaned.get("aseguradora")
       cleaned["siniestro_normalizado"] = normalizar_siniestro(numero)
       # ... búsqueda de duplicado por (siniestro_normalizado, aseguradora) ...
       return cleaned
   ```

- Ambos puntos usan **la misma función pura** (`casos/normalizacion.py`), de forma que no puede haber divergencia entre lo que valida el form y lo que escribe el modelo → **CA-04.4**.
- Ejemplos: `"2026-000123"`, `"2026 000123"`, `"2026.000123"`, `"2026000123"` → todos normalizan a `"2026000123"`.

---

## Permisos y roles (HU-01, HU-02)

### Grupos de Django

Se crean cuatro grupos: `Coordinación`, `Asistente`, `Abogado`, `Consulta`. El **superusuario** no es un grupo; es `is_superuser=True`.

### Matriz rol → permisos

Se usan los permisos estándar de Django por modelo (`add_caso`, `change_caso`, `view_caso`, `add_reingreso`, `view_reingreso`, etc.). **No se asigna a nadie `delete_caso`** (CA-02.4).

| Grupo | Caso | Reingreso | Observaciones |
|---|---|---|---|
| Coordinación | view, add, change | view, add | puede asignar `abogado_asignado` |
| Asistente | view, add | view, add | NO change_caso |
| Abogado | view, change | view | change restringido por objeto (solo asignados) |
| Consulta | view | view | solo lectura |

- **Asignar abogado**: capacidad de editar el campo `abogado_asignado`. Coordinación tiene `change_caso` y acceso al campo. Para el resto, el campo es de solo lectura o no editable según rol.
- **Administración de usuarios/grupos**: solo el superusuario ve los modelos `User`/`Group` en el admin → **CA-02.1, CA-02.3**. Los modelos `auth.User` y `auth.Group` se registran de modo que `has_module_permission` sea `True` únicamente para superusuarios.

### Edición por objeto para Abogado — `has_change_permission(request, obj)` (CA-02.1)

La regla "**el Abogado edita solo los casos asignados a él**" se implementa **exclusivamente en `CasoAdmin.has_change_permission(request, obj)`** (control por objeto del `ModelAdmin`), no en el formulario ni en señales. Firma y lógica:

```python
def has_change_permission(self, request, obj=None):
    user = request.user
    if user.is_superuser:
        return True
    # Acceso al changelist / permiso general de cambio (obj is None)
    if obj is None:
        # Puede entrar a la vista de cambio quien tenga change_caso
        # (Coordinación) o quien sea Abogado (para abrir sus propios casos).
        return (
            user.has_perm("casos.change_caso")
            or user.groups.filter(name="Abogado").exists()
        )
    # Control por OBJETO (obj is not None):
    if user.groups.filter(name="Abogado").exists():
        # El Abogado solo edita SU caso asignado.
        return obj.abogado_asignado_id == user.id
    if user.has_perm("casos.change_caso"):
        # Coordinación: edita cualquier caso.
        return True
    # Asistente / Consulta: no editan.
    return False
```

- Cuando `obj is not None` y el usuario es Abogado, se devuelve `True` **solo si** `obj.abogado_asignado_id == request.user.id`; en caso contrario `False` (el caso se muestra en modo solo lectura / se niega el guardado). Esta es la decisión central del punto (3).
- `CasoAdmin.has_view_permission`: el Abogado ve **todos** los casos ("ver todos los casos"), por lo que la **vista** no se restringe por objeto; solo la **edición**.
- `CasoAdmin.has_add_permission`: según permiso `add_caso` (Coordinación y Asistente).

### Bloqueo de eliminación — `has_delete_permission` devuelve `False` para todos (CA-02.4)

```python
def has_delete_permission(self, request, obj=None):
    return False  # Nadie elimina casos, ni siquiera el superusuario.
```

- `CasoAdmin.has_delete_permission()` devuelve **siempre `False`**, sin excepción, incluido el superusuario y para `obj is None` (lo que también quita el botón de borrado del changelist y de la vista de detalle).
- Se **elimina la acción masiva `delete_selected`** del `CasoAdmin` (`def get_actions(...)` que descarta `delete_selected`), para que no exista borrado en lote.
- No se asigna el permiso `delete_caso` a ningún grupo en `seed_roles` (defensa en profundidad).

### Login seguro (HU-01)

- Se usa el flujo de autenticación de Django: `ModelBackend` (verifica `is_active`), hashers por defecto (PBKDF2) → contraseñas con hash (**CA-01.4**).
- Usuario inactivo (`is_active=False`) no autentica → **CA-01.3**.
- Mensaje de error del `AuthenticationForm` es genérico y no distingue "usuario no existe" de "contraseña incorrecta" → **CA-01.2**.
- Acceso según rol tras login correcto → **CA-01.1**.

---

## Comportamiento del admin personalizado

### Registro de caso (HU-03)

`CasoForm` (usado por `CasoAdmin`):
- Campos obligatorios: `numero_siniestro`, `aseguradora`, `fecha_recepcion`. Si falta alguno → error de validación por campo, no se guarda, indica cuáles faltan → **CA-03.1**.
- `clean_fecha_recepcion()`: rechaza fecha futura (comparada con `timezone.localdate()` en America/Bogota) o inválida, con mensaje claro en español → **CA-03.3**.
- `CasoAdmin.save_model()`:
  - En creación: fija `creado_por = request.user`, estado inicial `REGISTRADO` (default del modelo), `creado_en` automático → **CA-03.2**.
  - En edición: fija `actualizado_por = request.user`.
- Tras guardar, el caso aparece en el changelist y su detalle es accesible → **CA-03.4**.

### Detección de duplicados y reingreso (HU-04)

Flujo en `CasoForm.clean()` / `CasoAdmin`:
1. Calcular `siniestro_normalizado` del valor ingresado.
2. Buscar `Caso` existente con el mismo `siniestro_normalizado` **y** `aseguradora`.
3. Si existe (y no es el mismo objeto en edición):
   - **No** se guarda el duplicado.
   - Se lanza `ValidationError` con un mensaje que incluye:
     - enlace al **detalle del caso existente** (`reverse('admin:casos_caso_change', args=[existente.pk])`),
     - enlace para **registrar un reingreso** con el caso preseleccionado:
       `reverse('admin:casos_reingreso_add') + '?caso=<pk>&trae_documentos_nuevos=on'`.
   - El mensaje se renderiza como HTML seguro (`format_html` / `mark_safe`) para que los enlaces sean clicables → **CA-04.1**.
4. Si no existe → el registro continúa sin alertas → **CA-04.3**.

`ReingresoAdmin`:
- Acepta parámetros GET iniciales (`caso`, `trae_documentos_nuevos`) para preseleccionar el caso y marcar la casilla → **CA-04.2**.
- `save_model()` fija `registrado_por = request.user`.

Garantía dura: aunque se evada la validación de la app, la restricción **UNIQUE(`siniestro_normalizado`, `aseguradora`)** en BD impide el duplicado (`IntegrityError`) → **RNF-1**.

### Listado: búsqueda, filtros y paginación (HU-05)

`CasoAdmin`:
- `search_fields = ('numero_siniestro', 'siniestro_normalizado', 'numero_poliza', 'asegurado')` → **CA-05.1**.
- `list_filter = ('aseguradora', 'estado', 'abogado_asignado')` → combinables → **CA-05.2**.
- `list_per_page = 50` → el admin pagina y muestra el total de resultados ("N casos") → **CA-05.3**.
- `list_display = ('numero_siniestro', 'aseguradora', 'numero_poliza', 'asegurado', 'estado', 'abogado_asignado', 'fecha_recepcion')`.
- `list_select_related = ('aseguradora', 'abogado_asignado')` para evitar N+1.
- Índices de BD en los campos de búsqueda/filtro → respuesta en pocos segundos con >3.700 casos → **CA-05.4 / RNF-3**.

---

## Comandos de gestión

### `seed_roles`

- Crea (idempotente) los grupos `Coordinación`, `Asistente`, `Abogado`, `Consulta` y les asigna los permisos según la matriz (sin `delete_caso`).
- Crea usuarios demo: `admin` (superusuario), `coordinacion`, `asistente`, `abogado1`, `consulta`, cada uno en su grupo.
- La contraseña se toma de una **variable de entorno** (p. ej. `SEED_PASSWORD`); si no está definida, el comando aborta con un mensaje claro (no usa una contraseña por defecto insegura).
- Reejecutable sin duplicar (usa `get_or_create` / `set_password`).

### `seed_demo_data --cantidad N`

- Crea las aseguradoras `Alfa`, `Beta`, `Gamma` (si no existen).
- Genera **N** casos **ficticios** con siniestros tipo `2026-000123`, variando el formato (con/sin guion, con puntos, con espacios) para poblar datos de rendimiento.
- Garantiza unicidad de `(siniestro_normalizado, aseguradora)` generando números distintos; usa `bulk_create` por lotes para eficiencia.
- `creado_por` apunta a un usuario demo existente (p. ej. `coordinacion`); si no existe, el comando sugiere correr `seed_roles` primero.

---

## Configuración y entorno

### `settings.py` (variables de entorno)

| Variable | Uso |
|---|---|
| `SECRET_KEY` | clave de Django |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | lista separada por comas |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | conexión MySQL |
| `SEED_PASSWORD` | contraseña de usuarios demo (`seed_roles`) |

- `DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'`, con `OPTIONS` para `charset=utf8mb4` y `sql_mode` estricto; motor InnoDB.
- `LANGUAGE_CODE = 'es-co'`, `TIME_ZONE = 'America/Bogota'`, `USE_TZ = True`.
- Cliente: `mysqlclient` (fallback documentado a `PyMySQL`).

### `docker-compose.yml`

- Un único servicio `db`: imagen `mysql:8.0`, variables desde `.env`, volumen persistente, puerto expuesto, `--default-authentication-plugin` según necesidad. **Solo MySQL** (la app corre en venv local).

### `.env.example`

Plantilla con todas las variables anteriores y valores de ejemplo (sin secretos reales).

### `requirements.txt`

`Django>=5.2,<5.3`, `mysqlclient`, `python-dotenv` (o `django-environ`). `PyMySQL` documentado como alternativa.

---

## Estrategia de pruebas (RNF-6)

- Test runner de Django (`manage.py test`), base de datos de pruebas en **MySQL** (no SQLite).
- **Una prueba (o más) por cada criterio**, con el ID en el nombre del método: `test_ca_01_1_*`, `test_ca_01_2_*`, …, `test_ca_05_4_*`.
- Organización por historia (ver estructura `casos/tests/`).
- `docs/matriz_ca.md`: tabla criterio → archivo::método de prueba.

### Mapeo criterio → prueba (resumen)

| Criterio | Prueba (archivo :: método) |
|---|---|
| CA-01.1 | test_hu01_login :: `test_ca_01_1_usuario_activo_credenciales_correctas_accede` |
| CA-01.2 | test_hu01_login :: `test_ca_01_2_password_incorrecto_mensaje_generico` |
| CA-01.3 | test_hu01_login :: `test_ca_01_3_usuario_inactivo_no_accede` |
| CA-01.4 | test_hu01_login :: `test_ca_01_4_password_se_guarda_con_hash` |
| CA-02.1 | test_hu02_permisos :: `test_ca_02_1_rol_asignado_solo_acciones_permitidas` |
| CA-02.2 | test_hu02_permisos :: `test_ca_02_2_consulta_ve_pero_no_edita` |
| CA-02.3 | test_hu02_permisos :: `test_ca_02_3_no_admin_no_gestiona_usuarios` |
| CA-02.4 | test_hu02_permisos :: `test_ca_02_4_ningun_rol_puede_eliminar_casos` |
| CA-03.1 | test_hu03_registro :: `test_ca_03_1_sin_obligatorios_no_guarda_e_indica_faltantes` |
| CA-03.2 | test_hu03_registro :: `test_ca_03_2_datos_validos_estado_registrado_y_auditoria` |
| CA-03.3 | test_hu03_registro :: `test_ca_03_3_fecha_futura_o_invalida_se_rechaza` |
| CA-03.4 | test_hu03_registro :: `test_ca_03_4_caso_aparece_en_listado_y_detalle` |
| CA-04.1 | test_hu04_duplicados :: `test_ca_04_1_duplicado_no_se_crea_muestra_existente` |
| CA-04.2 | test_hu04_duplicados :: `test_ca_04_2_reingreso_vinculado_documentos_nuevos` |
| CA-04.3 | test_hu04_duplicados :: `test_ca_04_3_sin_coincidencia_registro_sin_alertas` |
| CA-04.4 | test_hu04_duplicados :: `test_ca_04_4_comparacion_ignora_mayusculas_espacios_guiones` |
| CA-05.1 | test_hu05_busqueda :: `test_ca_05_1_busqueda_por_siniestro_o_poliza` |
| CA-05.2 | test_hu05_busqueda :: `test_ca_05_2_filtros_combinados_cumplen_todos` |
| CA-05.3 | test_hu05_busqueda :: `test_ca_05_3_paginacion_y_total` |
| CA-05.4 | test_hu05_busqueda :: `test_ca_05_4_busqueda_responde_con_mas_de_3700_casos` |

> Si el entorno de ejecución no dispone de MySQL, las pruebas **no** se adaptan a SQLite: quedan escritas para MySQL y se reporta cuáles no pudieron ejecutarse localmente (se correrán localmente por el equipo).

### Cómo se prueba cada criterio (diseño de cada prueba)

Convenciones: `Client` de Django para flujos del admin/login; `self.client.force_login()` o `login()` según el CA; fixtures mínimas creadas en `setUp` (aseguradoras Alfa/Beta, usuarios por rol vía helpers que reutilizan la lógica de `seed_roles`). Las aserciones comprueban **el comportamiento observable**, no solo que el código corra.

**HU-01 — Login (`test_hu01_login.py`)**

- **CA-01.1** `test_ca_01_1_usuario_activo_credenciales_correctas_accede`: *Arrange* usuario activo en grupo Coordinación con contraseña conocida. *Act* `client.login()` y GET al changelist de casos. *Assert* login `True`, respuesta `200`, y acceso acorde al rol (ve el listado).
- **CA-01.2** `test_ca_01_2_password_incorrecto_mensaje_generico`: *Act* POST al login con (a) usuario existente + contraseña errónea y (b) usuario inexistente. *Assert* ambos fallan y el **mensaje de error es idéntico/genérico** (no revela si el usuario existe); se compara el texto de error de los dos casos y debe ser el mismo.
- **CA-01.3** `test_ca_01_3_usuario_inactivo_no_accede`: *Arrange* usuario con `is_active=False` y contraseña correcta. *Act* `client.login()`. *Assert* devuelve `False`/no autentica; GET a vista protegida redirige al login.
- **CA-01.4** `test_ca_01_4_password_se_guarda_con_hash`: *Arrange* crear usuario con `set_password("secreto")`. *Assert* `user.password != "secreto"`, empieza por el prefijo del hasher (p. ej. `pbkdf2_`) y `check_password("secreto")` es `True`.

**HU-02 — Permisos (`test_hu02_permisos.py`)**

- **CA-02.1** `test_ca_02_1_rol_asignado_solo_acciones_permitidas`: *Arrange* usuarios en cada grupo (tras aplicar permisos tipo `seed_roles`). *Assert* la matriz: Coordinación `add/change/view`; Asistente `add/view` sin `change`; Abogado `view` + `change` por objeto; Consulta solo `view` — comprobado con `has_perm` y accediendo a URLs del admin (`200`/`403`/redirect).
- **CA-02.2** `test_ca_02_2_consulta_ve_pero_no_edita`: *Act* usuario Consulta GET al changelist y a la vista de cambio de un caso. *Assert* ve el listado (`200`) pero el detalle no permite editar (sin permiso de cambio / campos solo lectura) y el POST de edición no persiste cambios.
- **CA-02.3** `test_ca_02_3_no_admin_no_gestiona_usuarios`: *Act* usuario no superusuario GET a `admin:auth_user_add` / `auth_group_*`. *Assert* `403`/redirect; `User`/`Group` no aparecen en el índice del admin para ese usuario.
- **CA-02.4** `test_ca_02_4_ningun_rol_puede_eliminar_casos`: *Assert* `CasoAdmin.has_delete_permission()` es `False` para superusuario y para cada rol; GET a la URL de borrado del caso da `403`/redirect; `delete_selected` no está en `get_actions()`.

**HU-03 — Registro (`test_hu03_registro.py`)**

- **CA-03.1** `test_ca_03_1_sin_obligatorios_no_guarda_e_indica_faltantes`: *Act* POST de alta de caso sin `numero_siniestro`/`aseguradora`/`fecha_recepcion`. *Assert* no se crea (`Caso.objects.count()==0`), la respuesta contiene errores de formulario que **nombran los campos faltantes**.
- **CA-03.2** `test_ca_03_2_datos_validos_estado_registrado_y_auditoria`: *Act* POST válido como Coordinación. *Assert* se crea 1 caso, `estado=="REGISTRADO"`, `creado_por==usuario`, `creado_en` no nulo.
- **CA-03.3** `test_ca_03_3_fecha_futura_o_invalida_se_rechaza`: *Act* POST con `fecha_recepcion` = mañana (America/Bogota) y, en otro sub-caso, con una fecha inválida. *Assert* no se guarda y hay un mensaje de error claro en español sobre la fecha.
- **CA-03.4** `test_ca_03_4_caso_aparece_en_listado_y_detalle`: *Arrange* crear un caso. *Act* GET al changelist y GET a `admin:casos_caso_change` del pk. *Assert* el changelist lista el caso (aparece el número de siniestro) y el detalle responde `200`.

**HU-04 — Duplicados y reingreso (`test_hu04_duplicados.py`)**

- **CA-04.1** `test_ca_04_1_duplicado_no_se_crea_muestra_existente`: *Arrange* caso existente (Alfa, `2026-000123`). *Act* POST de otro caso con mismo siniestro+aseguradora. *Assert* no se crea segundo caso; la respuesta muestra error con **enlace al caso existente** (URL de change del pk) y **enlace de reingreso** (URL de add de reingreso con `?caso=<pk>`).
- **CA-04.2** `test_ca_04_2_reingreso_vinculado_documentos_nuevos`: *Act* GET a `admin:casos_reingreso_add?caso=<pk>&trae_documentos_nuevos=on` y POST del reingreso. *Assert* el form viene con el caso preseleccionado y la casilla marcada; tras POST se crea un `Reingreso` vinculado al caso con `trae_documentos_nuevos=True` y `registrado_por` fijado.
- **CA-04.3** `test_ca_04_3_sin_coincidencia_registro_sin_alertas`: *Act* POST de caso con siniestro que no existe para esa aseguradora. *Assert* se crea el caso sin errores de duplicado.
- **CA-04.4** `test_ca_04_4_comparacion_ignora_mayusculas_espacios_guiones`: *Arrange* caso con `2026-000123`. *Act* intentar crear `2026 000123`, `2026.000123`, `2026000123`, ` 2026-000123 ` para la misma aseguradora. *Assert* todas se detectan como duplicado (misma `siniestro_normalizado`); además prueba directa de `normalizar_siniestro()` sobre esas variantes → mismo resultado. Caso de control: misma cadena en **otra** aseguradora **sí** se permite.
- *(Garantía de BD)* dentro de `test_hu04` se incluye además una comprobación de que `Caso.objects.create(...)` con par duplicado lanza `IntegrityError`, validando la UNIQUE real de MySQL (se marca para ejecución en MySQL).

**HU-05 — Búsqueda, filtros y paginación (`test_hu05_busqueda.py`)**

- **CA-05.1** `test_ca_05_1_busqueda_por_siniestro_o_poliza`: *Arrange* varios casos. *Act* GET al changelist con `?q=<siniestro>` y luego `?q=<poliza>`. *Assert* el resultado contiene solo las coincidencias y excluye los no coincidentes.
- **CA-05.2** `test_ca_05_2_filtros_combinados_cumplen_todos`: *Act* GET con `?aseguradora__id=..&estado=..&abogado_asignado__id=..`. *Assert* todos los casos mostrados cumplen simultáneamente los tres filtros; los que fallan uno no aparecen.
- **CA-05.3** `test_ca_05_3_paginacion_y_total`: *Arrange* crear más casos que `list_per_page` (p. ej. 60 con `list_per_page=50`). *Act* GET al changelist. *Assert* se muestra el control de paginación y el **total** de resultados (`cl.result_count` / texto "N casos"); la página 2 devuelve el resto.
- **CA-05.4** `test_ca_05_4_busqueda_responde_con_mas_de_3700_casos`: *Arrange* `bulk_create` de >3.700 casos ficticios. *Act* medir el tiempo de una búsqueda filtrada (`time.perf_counter()` alrededor del GET/queryset). *Assert* el conteo es correcto y el tiempo está por debajo de un umbral razonable (p. ej. < 3 s). Esta prueba depende de los índices de BD y se ejecuta sobre **MySQL** (en SQLite el resultado de rendimiento no es representativo; se marca como prueba a correr localmente en MySQL).

> **Dependencia de MySQL.** CA-04.4 (garantía UNIQUE a nivel BD), CA-01.4 en combinación con la BD, y especialmente **CA-05.4** reflejan comportamiento del motor. Si no hay MySQL disponible al ejecutar, estas pruebas se reportan como "no ejecutadas localmente" en lugar de reescribirse para SQLite.

---

## Trazabilidad diseño → requisitos

| Requisito / CA | Elemento de diseño |
|---|---|
| HU-01 (CA-01.1–01.4) | Flujo de login de Django, `ModelBackend`, hashers, mensajes genéricos |
| HU-02 (CA-02.1–02.4) | Grupos + matriz de permisos, `has_delete_permission=False`, registro de User/Group solo para superusuario |
| HU-03 (CA-03.1–03.4) | `CasoForm`, `save_model`, default `REGISTRADO`, `auto_now_add`, changelist/detalle |
| HU-04 (CA-04.1–04.4) | `clean()` con detección por `siniestro_normalizado`, enlaces a caso/reingreso, `ReingresoAdmin` con GET inicial, `normalizar_siniestro()` |
| HU-05 (CA-05.1–05.4) | `search_fields`, `list_filter`, `list_per_page`, índices de BD |
| RNF-1 | `UniqueConstraint`, `CheckConstraint`, FK NOT NULL, InnoDB |
| RNF-2 | Modelos en español/snake_case |
| RNF-3 | Índices en campos de búsqueda/filtro, `list_select_related` |
| RNF-4 | Hashers, `.env`, `is_active` |
| RNF-5 | `docker-compose.yml`, `.env.example`, `requirements.txt`, README, `seed_roles`, `seed_demo_data` |
| RNF-6 | Pruebas por CA con ID en el nombre, `matriz_ca.md`, política MySQL |
