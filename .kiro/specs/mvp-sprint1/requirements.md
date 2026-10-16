# Requisitos — MVP Sprint 1 (Sistema de gestión de casos de RC Médica)

## Introducción

Este documento define los requisitos del **MVP del Sprint 1** del sistema de gestión de casos de Responsabilidad Civil (RC) Médica para **DL Abogados** (firma de derecho de seguros, Medellín). El sistema reemplaza un Excel compartido de ~3.700 registros, eliminando pérdida/alteración accidental de datos, duplicados y la falta de trazabilidad y permisos.

La interfaz es el **Django admin personalizado** (no se construye un frontend aparte). El idioma del dominio, la interfaz y los mensajes es **español**; la zona horaria es **America/Bogota**. La persistencia es **MySQL 8.0 (InnoDB)** con las reglas de integridad declaradas en la base de datos.

### Alcance del Sprint 1

Incluye únicamente las historias **HU-01 a HU-05**:

- **HU-01** — Inicio de sesión seguro por rol.
- **HU-02** — Administración de usuarios, roles y permisos.
- **HU-03** — Registro de un caso.
- **HU-04** — Detección de duplicados y registro de reingresos.
- **HU-05** — Búsqueda, filtros y paginación del listado de casos.

### Fuera de alcance (NO se implementa en el Sprint 1)

- Importación desde Excel.
- Historial de cambios (auditoría de modificaciones campo a campo).
- Transiciones de estado (flujo/workflow entre estados del caso).
- Enlaces a SharePoint.
- Enlaces a Notion.

### Nota sobre el modelo de datos

Los campos del modelo son **provisionales** y se ajustarán a las columnas reales del Excel en iteraciones posteriores. En desarrollo y pruebas se usan **solo datos ficticios** (los datos reales son historias clínicas confidenciales).

---

## Glosario

- **Siniestro normalizado**: valor derivado de `numero_siniestro` transformado a **mayúsculas** y sin **espacios**, **guiones** ni **puntos**. Se usa para comparar duplicados.
- **Matriz de permisos**: la asignación rol → acciones permitidas definida en el requisito 2.
- **Caso asignado a un abogado**: caso cuyo campo `abogado_asignado` referencia al usuario abogado autenticado.
- **Fecha no futura**: fecha de recepción menor o igual a la fecha actual en la zona horaria America/Bogota.

### Roles (grupos de Django)

| Rol | Ver casos | Crear casos | Editar casos | Asignar abogado | Crear reingresos |
|---|---|---|---|---|---|
| Coordinación | Sí | Sí | Sí | Sí | Sí |
| Asistente | Sí | Sí | No | No | Sí |
| Abogado | Sí (todos) | No | Solo los asignados a él | No | No |
| Consulta | Sí | No | No | No | No |
| Superusuario | — administra usuarios y grupos — | | | | |

- **Nadie** puede eliminar casos: no existe opción de borrar en la interfaz para ningún rol (incluido el superusuario a nivel de interfaz de casos).
- Solo el **superusuario** administra usuarios y grupos.

---

## Requisitos

### Requisito 1 — HU-01: Inicio de sesión seguro por rol

**Historia de usuario:** Como persona del equipo de DL Abogados, quiero iniciar sesión de forma segura y acceder solo a lo que mi rol permite, para proteger la información confidencial de los casos.

#### Criterios de aceptación

1. **CA-01.1** — CUANDO un usuario **activo** envía credenciales **correctas** al formulario de inicio de sesión, ENTONCES el sistema DEBERÁ autenticarlo y concederle acceso de acuerdo con los permisos de su rol.
2. **CA-01.2** — CUANDO un usuario envía una **contraseña incorrecta** (o un nombre de usuario inexistente), ENTONCES el sistema DEBERÁ rechazar el acceso y mostrar un mensaje genérico que **no revele** si el nombre de usuario existe.
3. **CA-01.3** — CUANDO un usuario **inactivo** envía credenciales correctas, ENTONCES el sistema DEBERÁ rechazar el acceso.
4. **CA-01.4** — DONDEQUIERA que se almacene o actualice una contraseña, el sistema DEBERÁ guardarla **con hash** y NUNCA en texto plano.

---

### Requisito 2 — HU-02: Administración de usuarios, roles y permisos

**Historia de usuario:** Como administrador (superusuario), quiero crear usuarios y asignarles un rol, para que cada persona pueda hacer únicamente lo que la matriz de permisos permite.

#### Criterios de aceptación

1. **CA-02.1** — CUANDO el **superusuario** crea un usuario y le asigna un **rol** (Coordinación, Asistente, Abogado o Consulta), ENTONCES el sistema DEBERÁ permitir a ese usuario realizar **únicamente** las acciones que la matriz de permisos define para su rol.
2. **CA-02.2** — CUANDO un usuario con rol **Consulta** accede al sistema, ENTONCES el sistema DEBERÁ permitirle **ver** casos pero NO DEBERÁ permitirle crear, editar ni eliminar.
3. **CA-02.3** — CUANDO un usuario que **no es superusuario** intenta crear usuarios o cambiar permisos/grupos, ENTONCES el sistema DEBERÁ **impedirlo** (no exponer esas acciones en su interfaz).
4. **CA-02.4** — DONDEQUIERA que se muestre un caso o un listado de casos, el sistema NO DEBERÁ ofrecer a **ningún** rol la opción de **eliminar** casos.

---

### Requisito 3 — HU-03: Registro de un caso

**Historia de usuario:** Como Coordinación o Asistente, quiero registrar un caso con sus datos obligatorios, para que quede almacenado de forma íntegra y trazable.

#### Criterios de aceptación

1. **CA-03.1** — CUANDO un usuario autorizado intenta guardar un caso **sin** uno o más campos **obligatorios** (`numero_siniestro`, `aseguradora`, `fecha_recepcion`), ENTONCES el sistema NO DEBERÁ guardar el caso y DEBERÁ indicar **cuáles** campos faltan.
2. **CA-03.2** — CUANDO un usuario autorizado guarda un caso con **datos válidos**, ENTONCES el sistema DEBERÁ crearlo con estado **REGISTRADO** y DEBERÁ fijar automáticamente `creado_por` (usuario autenticado) y `creado_en` (fecha-hora actual).
3. **CA-03.3** — CUANDO un usuario envía una `fecha_recepcion` **futura** o **inválida**, ENTONCES el sistema DEBERÁ rechazar el guardado y mostrar un mensaje claro en español.
4. **CA-03.4** — CUANDO un caso se ha creado correctamente, ENTONCES el sistema DEBERÁ mostrarlo en el **listado** y DEBERÁ permitir abrir su **detalle**.

---

### Requisito 4 — HU-04: Detección de duplicados y registro de reingresos

**Historia de usuario:** Como Coordinación o Asistente, quiero que el sistema detecte casos duplicados por siniestro y aseguradora, para evitar registros repetidos y, en su lugar, registrar un reingreso vinculado al caso existente.

#### Criterios de aceptación

1. **CA-04.1** — CUANDO un usuario intenta registrar un caso cuyo **siniestro normalizado** y **aseguradora** ya existen, ENTONCES el sistema NO DEBERÁ crear el duplicado y DEBERÁ mostrar un error con un **enlace al caso existente** y un **enlace para registrar un reingreso** de ese caso.
2. **CA-04.2** — CUANDO el usuario sigue el enlace de reingreso desde el error de duplicado, ENTONCES el sistema DEBERÁ abrir el registro de reingreso con el **caso preseleccionado** y la casilla **"trae documentos nuevos"** disponible, y DEBERÁ permitir guardar el reingreso vinculado al caso.
3. **CA-04.3** — CUANDO el siniestro normalizado y aseguradora **no** corresponden a ningún caso existente, ENTONCES el sistema DEBERÁ registrar el caso **sin** alertas de duplicado.
4. **CA-04.4** — CUANDO el sistema compara dos números de siniestro para la misma aseguradora, ENTONCES la comparación DEBERÁ **ignorar** diferencias de mayúsculas/minúsculas, espacios, guiones y puntos (comparar por `siniestro_normalizado`).

> La garantía dura a nivel de base de datos (restricción `UNIQUE(siniestro_normalizado, aseguradora)`, que impide almacenar un duplicado aunque se evada la validación de la aplicación) se especifica en **RNF-1**.

---

### Requisito 5 — HU-05: Búsqueda, filtros y paginación del listado

**Historia de usuario:** Como usuario del sistema, quiero buscar y filtrar casos de forma combinada y paginada, para localizar casos rápidamente incluso con más de 3.700 registros.

#### Criterios de aceptación

1. **CA-05.1** — CUANDO un usuario busca por `numero_siniestro`, `numero_poliza` o `asegurado`, ENTONCES el sistema DEBERÁ mostrar **solo** los casos que coinciden con el término.
2. **CA-05.2** — CUANDO un usuario aplica filtros combinados por **aseguradora**, **estado** y/o **abogado**, ENTONCES el sistema DEBERÁ mostrar solo los casos que cumplen **todos** los filtros aplicados simultáneamente.
3. **CA-05.3** — CUANDO el resultado abarca **más de una página**, ENTONCES el sistema DEBERÁ ofrecer **paginación** y mostrar el **total** de resultados.
4. **CA-05.4** — CUANDO existen **más de 3.700** casos de prueba, ENTONCES una búsqueda o filtrado DEBERÁ responder en **pocos segundos** (con índices de base de datos que soporten los campos de búsqueda y filtro).

---

## Requisitos no funcionales y restricciones (aplican a todo el Sprint 1)

### RNF-1 — Integridad en la base de datos
- Las reglas de integridad DEBERÁN declararse en la **base de datos** (no solo en el código):
  - `Aseguradora.nombre` **UNIQUE** y **NOT NULL**.
  - `Caso.numero_siniestro` **NOT NULL**; `Caso.fecha_recepcion` **NOT NULL**; `Caso.aseguradora` **FK NOT NULL**.
  - **UNIQUE(`siniestro_normalizado`, `aseguradora`)** en `Caso`.
  - **CHECK** que restrinja `Caso.estado` al conjunto {REGISTRADO, ASIGNADO, EN_ANALISIS, ENVIADO_ASEGURADORA, CERRADO}, con valor por defecto **REGISTRADO**.
  - `Reingreso.caso` **FK NOT NULL**.
- El motor DEBERÁ ser **InnoDB** (soporte de FK y CHECK en MySQL 8.0).

### RNF-2 — Modelo de datos (español, snake_case)
- **Aseguradora**: `nombre` (único), `activa`.
- **Caso**: `numero_siniestro`, `siniestro_normalizado` (calculado), `aseguradora` (FK), `numero_poliza`, `fecha_recepcion`, `asegurado`, `estado` (default REGISTRADO), `abogado_asignado` (FK a usuario, opcional), `observaciones`, `creado_por`, `creado_en`, `actualizado_por`, `actualizado_en`.
- **Reingreso**: `caso` (FK), `fecha_reingreso`, `trae_documentos_nuevos` (booleano), `observaciones`, `registrado_por`, `creado_en`.

### RNF-3 — Rendimiento
- El listado DEBERÁ incluir **índices** adecuados para búsqueda (`siniestro_normalizado`, `numero_poliza`, `asegurado`) y filtros (`aseguradora`, `estado`, `abogado_asignado`), garantizando respuesta en pocos segundos con >3.700 casos.

### RNF-4 — Seguridad y configuración
- Contraseñas con **hash** (mecanismo estándar de Django).
- Configuración por **variables de entorno** (`.env`); **nunca** credenciales en el repositorio.
- Usuarios inactivos sin acceso; mensajes de error de login genéricos.

### RNF-5 — Entorno y entregables
- `docker-compose.yml` **solo con MySQL 8.0**; `.env.example`; `requirements.txt`; `README` con pasos para correr todo (MySQL en Docker, app en venv local).
- Cliente MySQL: **mysqlclient** (alternativa **PyMySQL** si falla en Windows).
- Comando **`seed_roles`**: crea los grupos con sus permisos y usuarios demo (`admin`, `coordinacion`, `asistente`, `abogado1`, `consulta`), con contraseña tomada de una **variable de entorno**.
- Comando **`seed_demo_data --cantidad N`**: genera N casos **ficticios** (aseguradoras Alfa, Beta, Gamma; siniestros tipo `2026-000123` con variantes de formato) para pruebas de rendimiento.

### RNF-6 — Pruebas y trazabilidad
- Pruebas con el **test runner de Django**.
- **Al menos una prueba por cada criterio de aceptación**, con nombre que incluya el ID del criterio (ej. `test_ca_04_1_...`).
- `docs/matriz_ca.md` con la tabla **criterio → prueba**.
- Si el entorno no tiene MySQL, **no** se cambia a SQLite para forzar que pasen las pruebas: las pruebas quedan escritas para MySQL y se indica cuáles no pudieron ejecutarse localmente.
